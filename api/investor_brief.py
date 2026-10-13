"""Collect the explicitly requested brief sources without paid planning turns."""
from __future__ import annotations

import asyncio
import json
import re

from api.company_research import collect_company_evidence, company_from_question, verified_name
from api.comparison_research import brief_needs_quote, comparison_source_matches, comparison_source_priority
from api.localization import localize_stock_analysis
from api.web_research import search_public_sources, read_public_source


def brief_company_query(question: str) -> str:
    ticker = re.search(r"\bUS\.[A-Z]{1,6}(?:\.[A-Z])?\b|[（(]([A-Z]{1,6}(?:\.[A-Z])?)[）)]", question)
    if ticker:
        return ticker.group(1) or ticker.group()
    name = re.search(r"(?:research|analy[sz]e|review)\s+(.+?)\s+(?:for|as)\b", question, re.I)
    return name.group(1).strip() if name else company_from_question(question)


async def prepare_investor_brief(deps) -> list[dict]:
    # Identity, filings and news are source reads, not additional model runs.
    code = await collect_company_evidence(deps, brief_company_query(deps.user_query), "overview")
    if not code:
        return [json.loads(deps.tool_context(item)) for item in deps.tool_results]
    name = verified_name(deps, code) or code
    if brief_needs_quote(deps.user_query):
        async def quote():
            deps.report("tool_running", 50, "正在获取所请求的行情", {"tool": "get_stock_analysis"})
            try:
                data = await asyncio.to_thread(deps.stock_service.get_stock_analysis, code, False)
                result = deps.record_tool({"tool": "get_stock_analysis", "data": localize_stock_analysis(data, deps.language).model_dump()})
                deps.report("tool_completed", 65, "行情已返回", {"tool": "get_stock_analysis"})
                return result
            except Exception:
                return deps.record_tool({"tool": "get_stock_analysis", "status": "unavailable", "data": {"data_gaps": ["Requested price data could not be retrieved."]}})
        await deps.retrieve("get_stock_analysis", {"stock_code": code}, quote)

    if not deps.synthesis_reason():
        await search_public_sources(deps, f'"{name}" {code} latest official earnings results investor relations',
            limit=3, market="us" if code.startswith("US.") else "cn",
            accept_result=lambda row: comparison_source_matches(row, name, code),
            source_priority=lambda row: comparison_source_priority(row, name))
    search = next((item for item in reversed(deps.tool_results) if item.get("tool") == "web_search"), {})
    urls = [row.get("url") for row in search.get("data", []) if isinstance(row, dict)
            and str(row.get("url", "")).startswith("https://") and "news.google.com" not in str(row.get("url"))]
    filings = [filing.get("url") for item in deps.tool_results if item.get("tool") == "get_sec_company_data"
               for filing in (item.get("data") or {}).get("filings", []) if filing.get("url")]
    # Prefer an earnings source plus a filing; never invent an issuer URL.
    selected = list(dict.fromkeys(urls[:1] + filings[:1] + urls[1:]))[:2]
    for url in selected:
        if deps.synthesis_reason():
            break
        await read_public_source(deps, url, deps.user_query)
    return [json.loads(deps.tool_context(item)) for item in deps.tool_results]
