"""PydanticAI V2 research hooks: scoped tools and per-run retrieval reuse."""
from dataclasses import replace
from pydantic_ai.capabilities import Capability
from ashare.stock_pool import normalize_stock_code
from api.company_research import ensure_identity
from api.comparison_research import (
    is_broad_stock_comparison,
    is_company_news_query,
    is_financial_stock_comparison,
    is_first_pass_investor_brief,
    investor_brief_tools,
)
from api.company_research import resolved_codes


class ResearchCapability(Capability):
    async def before_model_request(self, ctx, request_context):
        if ctx.deps.provider_requests_started > ctx.deps.provider_requests_finished:
            from pydantic_ai.exceptions import UsageLimitExceeded
            raise UsageLimitExceeded("Unknown provider usage blocks additional paid model requests.")
        ctx.deps.provider_requests_started += 1
        if ctx.model.model_name.startswith("deepseek") and ctx.deps.synthesis_reason():
            # The final pass should spend its output allowance on the cited report,
            # after the planning and specialist passes have reviewed the evidence.
            settings = dict(request_context.model_settings or {})
            settings["extra_body"] = {**settings.get("extra_body", {}), "thinking": {"type": "disabled"}}
            settings.pop("openai_reasoning_effort", None)
            return replace(request_context, model_settings=settings)
        return request_context

    async def after_model_request(self, ctx, *, request_context, response):
        ctx.deps.provider_requests_finished += 1
        return response

    async def prepare_tools(self, ctx, tool_defs):
        reason = ctx.deps.synthesis_reason()
        if reason:
            ctx.deps.finish_reason = reason
            return []  # Output tools remain available, including validation repair.
        if is_first_pass_investor_brief(ctx.deps.user_query):
            results = ctx.deps.tool_results
            searches = [item for item in results if item.get("tool") == "search_stocks"]
            if not searches:
                return [tool for tool in tool_defs if tool.name == "search_stocks"]
            resolved = resolved_codes(ctx.deps)
            if (len(resolved) != 1 or any(item.get("status") == "unavailable"
                    or (isinstance(item.get("data"), list) and len(item.get("data", [])) != 1)
                    for item in searches)):
                return []
            code = next(iter(resolved))
            if code.startswith("US.") and code not in ctx.deps.verified_us_codes:
                return []

            completed = {item.get("tool") for item in results}
            required = investor_brief_tools(ctx.deps.user_query, us_company=code.startswith("US."))
            missing = set(required) - completed
            if missing:
                return [tool for tool in tool_defs if tool.name in missing]

            web_results = next((item for item in reversed(results)
                                if item.get("tool") == "web_search"), None)
            has_web_sources = bool(web_results and web_results.get("status") != "unavailable"
                                   and any(str(row.get("url") or "").startswith(("https://", "http://"))
                                           for row in web_results.get("data", []) if isinstance(row, dict)))
            if has_web_sources and "read_public_source" not in completed:
                return [tool for tool in tool_defs if tool.name == "read_public_source"]
            return []
        if is_broad_stock_comparison(ctx.deps.user_query):
            comparison = next((item for item in reversed(ctx.deps.tool_results)
                               if item.get("tool") == "research_comparison"), None)
            if comparison is None:
                # Start with one balanced, cross-market evidence pass.
                return [tool for tool in tool_defs if tool.name == "research_comparison"]
            companies = (comparison.get("data") or {}).get("companies", [])
            identities_verified = (
                comparison.get("status") != "unavailable"
                and len(companies) == 2
                and all((company.get("identity") or {}).get("status") == "ok" for company in companies)
            )
            if not identities_verified:
                # An ambiguous pair should be clarified before any further research.
                return []
            search_failures = [item for item in ctx.deps.tool_results if item.get("tool") == "web_search"
                               and item.get("status") == "unavailable"]
            provider_failures = [item for item in search_failures if item.get("reason_code") == "provider_error"]
            has_search_results = any(item.get("tool") == "web_search" and item.get("status") != "unavailable"
                                     and item.get("data") for item in ctx.deps.tool_results)
            if not has_search_results and (len(provider_failures) >= 2 or len(search_failures) >= 4):
                # Repeating a provider that has already failed for both sides
                # or exhausting four unsuccessful searches cannot improve coverage.
                ctx.deps.finish_reason = "source_provider_unavailable" if len(provider_failures) >= 2 else "comparison_search_exhausted"
                return []
            # After the first balanced pass, allow targeted follow-up research
            # without reopening unrelated SEC-only or single-company routes.
            return [tool for tool in tool_defs if tool.name in {"web_search", "read_public_source"}]
        if is_financial_stock_comparison(ctx.deps.user_query):
            searches = [item for item in ctx.deps.tool_results if item.get("tool") == "search_stocks"]
            resolved = resolved_codes(ctx.deps)
            verified = resolved & ctx.deps.verified_us_codes
            has_non_us = any(code and not code.startswith("US.") for code in resolved)
            if has_non_us:
                # SEC cannot compare a mixed-market pair; leave the normal
                # market-specific tools available rather than forcing US-only data.
                return tool_defs
            if len(verified) < 2:
                return [tool for tool in tool_defs if tool.name == "search_stocks"]
            comparison = next((item for item in reversed(ctx.deps.tool_results)
                               if item.get("tool") == "compare_companies"), None)
            if comparison is None:
                return [tool for tool in tool_defs if tool.name == "compare_companies"]
            return []
        if is_company_news_query(ctx.deps.user_query):
            searches = [item for item in ctx.deps.tool_results if item.get("tool") == "search_stocks"]
            resolved = resolved_codes(ctx.deps)
            if not searches:
                return [tool for tool in tool_defs if tool.name == "search_stocks"]
            if len(resolved) != 1 or any(item.get("status") == "unavailable"
                    or (isinstance(item.get("data"), list) and len(item["data"]) != 1) for item in searches):
                return []
            code = next(iter(resolved))
            if code.startswith("US.") and code not in ctx.deps.verified_us_codes:
                return []
            return [tool for tool in tool_defs if tool.name == "get_stock_news"]
        verified = ctx.deps.verified_us_codes
        return [tool for tool in tool_defs
                if (tool.name != "get_sec_company_data" or verified)
                and (tool.name != "compare_companies" or len(verified) >= 2)
                and (tool.name != "research_company" or ctx.deps.research_mode == "deep")]

    async def wrap_tool_execute(self, ctx, *, call, tool_def, args, handler):
        # Mutations and list reads must see the current persisted workspace state.
        if tool_def.name == "manage_watchlist":
            if args.get("action", "").strip().lower() == "add":
                code = normalize_stock_code(args.get("stock_code", "")).upper()
                if not code or not await ensure_identity(ctx.deps, code):
                    return ctx.deps.record_tool({"tool": "manage_watchlist", "status": "unavailable", "reason_code": "identity_required", "data": {"data_gaps": ["Verify an unambiguous company before changing the watchlist."]}})
            return await handler(args)
        # These tools admit their own reads so compound company research shares
        # the same per-run deduplication and retrieval telemetry.
        if tool_def.name in {"web_search", "read_public_source"}:
            return await handler(args)
        if tool_def.name in {"get_stock_analysis", "get_stock_news", "get_sec_company_data"}:
            code = normalize_stock_code(args.get("stock_code", "")).upper()
            if not await ensure_identity(ctx.deps, code):
                return ctx.deps.record_tool({"tool": tool_def.name, "status": "unavailable", "reason_code": "identity_required", "data": {"data_gaps": ["Company identity is ambiguous or could not be verified. Ask for an exact ticker; do not guess."]}})
            args = {**args, "stock_code": code if code.startswith(("US.", "HK.")) else code.lower()}
        # State belongs to the request, not to the shared Agent instance.
        if tool_def.name == "research_comparison":
            # The orchestrator itself is not a source read; its nested identity,
            # quote, search and document calls each consume the shared budget.
            return await ctx.deps.retrieve(tool_def.name, args, lambda: handler(args), use_slot=False, count=False)
        return await ctx.deps.retrieve(tool_def.name, args, lambda: handler(args), use_slot=tool_def.name not in {"research_company", "compare_companies"})
