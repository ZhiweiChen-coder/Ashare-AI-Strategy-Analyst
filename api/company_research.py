"""Bounded company identity and evidence collection, independent of model turns."""
from __future__ import annotations

import asyncio
import re
from urllib.parse import urlsplit

from ashare.stock_pool import normalize_stock_code
from api.localization import localize_stock_analysis


def verified_name(deps, code: str) -> str | None:
    return next((row.get("name") for item in reversed(deps.tool_results) if item.get("tool") == "search_stocks" and isinstance(item.get("data"), list)
                 for row in item.get("data", []) if row.get("code", "").upper() == code.upper()), None)


def cached_identity(deps, query: str) -> dict | None:
    """Reuse only a matching, unambiguous identity, never the last global search."""
    ticker_match = re.search(r"\((?:US\.)?([A-Z][A-Z0-9.-]{0,9})\)\s*$", query, re.I)
    requested_code = normalize_stock_code(ticker_match.group(1) if ticker_match else query.strip()).upper()
    def name_key(value):
        words = re.sub(r"[^\w]+", " ", value.casefold()).split()
        while words and words[-1] in {"inc", "incorporated", "corp", "corporation", "ltd", "limited", "plc"}:
            words.pop()
        return " ".join(words)
    name = name_key(query)
    matches = {}
    for item in deps.tool_results:
        rows = item.get("data")
        if item.get("tool") != "search_stocks" or item.get("status") == "unavailable" or not isinstance(rows, list) or len(rows) != 1:
            continue
        row = rows[0]
        code = normalize_stock_code(row.get("code", "")).upper()
        if not code or (code.startswith("US.") and code not in deps.verified_us_codes):
            continue
        company_name = name_key(row.get("name", ""))
        if code == requested_code or (len(name) >= 3 and company_name and (name == company_name or company_name.startswith(name + " "))):
            matches[code] = row
    return next(iter(matches.values())) if len(matches) == 1 else None


async def search_identity(deps, query: str, limit: int = 5) -> str:
    deps.report("tool_running", 35, "正在核验股票身份", {"tool": "search_stocks"})
    try:
        lookup_failed = False
        try:
            results = await asyncio.to_thread(deps.stock_service.search_stocks, query, max_results=min(5, max(1, limit)))
            out = [row.model_dump() if hasattr(row, "model_dump") else dict(row) for row in results]
        except Exception:
            lookup_failed = True
            out = []
        ticker_match = re.search(r"\((?:US\.)?([A-Z][A-Z0-9.-]{0,9})\)\s*$", query, re.I)
        lookup_query = ticker_match.group(1) if ticker_match else query.strip()
        us_codes = [row["code"] for row in out if row["code"].upper().startswith("US.")]
        if us_codes or (not out and re.fullmatch(r"[A-Za-z][A-Za-z0-9 .-]{0,70}", lookup_query)):
            try:
                identity = await asyncio.to_thread(deps.sec_service.resolve, lookup_query, us_codes)
                if identity["candidates"]:
                    out = identity["candidates"] + [row for row in out if not row["code"].upper().startswith("US.")]
                    if identity.get("status") == "ok" or len(identity["candidates"]) == 1:
                        deps.verified_us_codes.add(identity["candidates"][0]["code"].upper())
                else:
                    for row in out:
                        if row["code"].upper().startswith("US."):
                            row["identity_verified"] = False
            except Exception:
                lookup_failed = True
                for row in out:
                    if row["code"].upper().startswith("US."):
                        row["identity_verified"] = False
        if not out and lookup_failed:
            return deps.record_tool({"tool": "search_stocks", "status": "unavailable", "reason_code": "provider_error", "data": {"data_gaps": ["Company identity providers did not return usable data."]}})
        reason = "no_matches" if not out else "ambiguous_identity" if len(out) > 1 else "identity_unverified" if out[0].get("identity_verified") is False else None
        result = deps.record_tool({"tool": "search_stocks", "data": out, "reason_code": reason})
        deps.report("tool_completed", 48, "股票身份核验完成", {"tool": "search_stocks", "reason_code": reason})
        return result
    except Exception:
        return deps.record_tool({"tool": "search_stocks", "status": "unavailable", "reason_code": "provider_error", "data": {"data_gaps": ["Company identity could not be resolved."]}})


def resolved_codes(deps) -> set[str]:
    # A list of ambiguous matches does not establish an identity.
    return {normalize_stock_code(item["data"][0].get("code", "")).upper()
            for item in deps.tool_results if item.get("tool") == "search_stocks"
            and item.get("status") != "unavailable" and isinstance(item.get("data"), list)
            and len(item["data"]) == 1}


async def ensure_identity(deps, code: str) -> bool:
    code = normalize_stock_code(code).upper()
    # A model may request search and news in the same turn. Let its search finish.
    pending = [task for key, task in deps.retrieval_tasks.items() if key.startswith('["search_stocks",')]
    if pending:
        await asyncio.gather(*pending)
    if code not in resolved_codes(deps):
        await deps.retrieve("search_stocks", {"query": code, "limit": 5}, lambda: search_identity(deps, code))
    return code in resolved_codes(deps) and (not code.startswith("US.") or code in deps.verified_us_codes)


async def collect_company_evidence(deps, query: str, focus: str = "catalysts", *, question: str = "", search_queries: list[str] | None = None) -> str | None:
    pending = [task for key, task in deps.retrieval_tasks.items() if key.startswith('["search_stocks",')]
    if pending:
        await asyncio.gather(*pending)
    cached = cached_identity(deps, query)
    if cached:
        rows = [cached]
        deps.cache_hits.append("search_stocks")
    else:
        result = await deps.retrieve("search_stocks", {"query": query, "limit": 5}, lambda: search_identity(deps, query))
        # Concurrent searches may finish in either order; consume this call's result.
        import json
        rows = json.loads(result).get("data")
        rows = rows if isinstance(rows, list) else []
    if len(rows) != 1:
        return None
    code = normalize_stock_code(rows[0]["code"]).upper()
    if not await ensure_identity(deps, code):
        return None
    name = verified_name(deps, code)

    async def fetch(tool, args, function):
        async def execute():
            deps.report("tool_running", 50, "正在收集公司研究证据", {"tool": tool})
            try:
                data = await asyncio.to_thread(function)
                result = deps.record_tool({"tool": tool, "data": data})
                deps.report("tool_completed", 65, "公司研究证据已获取", {"tool": tool})
                return result
            except Exception:
                return deps.record_tool({"tool": tool, "status": "unavailable", "data": {"data_gaps": ["Source data unavailable."]}})
        return await deps.retrieve(tool, args, execute)

    tasks = [fetch("get_stock_news", {"stock_code": code, "limit": 6},
                   lambda: [row.model_dump() for row in deps.news_service.get_stock_news(code, stock_name=name, limit=6)])]
    if focus == "catalysts":
        # Explain the observed move and retrieve contemporaneous company headlines.
        def quote_data():
            analysis = deps.stock_service.get_stock_analysis(code, False)
            if name:
                analysis.stock_name = name
            return localize_stock_analysis(analysis, deps.language).model_dump()
        tasks.append(fetch("get_stock_analysis", {"stock_code": code},
                           quote_data))
    if code.startswith("US.") and focus in {"advantage", "policy", "overview"}:
        tasks.append(fetch("get_sec_company_data", {"stock_code": code}, lambda: deps.sec_service.company(code)))
    await asyncio.gather(*tasks)
    if focus == "catalysts" and deps.research_mode == "deep":
        from api.web_research import search_public_sources, read_public_source

        # Deep catalyst analysis needs evidence beyond the same quote/news feed.
        # Keep the search angles independent: a primary-company/regulatory event
        # and an outside market/sector explanation. Agent-supplied queries refine
        # the question, while generic queries fill any missing angle.
        queries = list(dict.fromkeys(
            re.sub(r"\s+", " ", str(value)).strip()[:300]
            for value in (search_queries or []) if str(value).strip()
        ))[:3]
        defaults = (
            [f"{name} 公司公告 新闻 催化剂 近期 股价", f"{name} 股价上涨原因 行业 板块 市场背景"]
            if not code.startswith("US.") and deps.language != "en-US" else
            [f"{name} official announcement press release recent catalyst clinical trial earnings",
             f"{name} stock price move independent market sector context recent rally"]
        )
        for fallback in defaults:
            if len(queries) >= 2:
                break
            if fallback not in queries:
                queries.append(fallback)

        if not deps.synthesis_reason():
            market = "us" if code.startswith("US.") else "cn"
            search_contexts = await asyncio.gather(*(
                search_public_sources(deps, search_query, limit=3, market=market)
                for search_query in queries
            ))

            def search_rows(context: str) -> list[dict]:
                try:
                    import json
                    data = json.loads(context).get("data", [])
                    return data if isinstance(data, list) else []
                except (TypeError, ValueError):
                    return []

            source_urls = []
            for index, context in enumerate(search_contexts):
                rows = search_rows(context)
                # Prefer first-party/regulatory sources for the first angle;
                # retain an independent result for the second angle.
                if index == 0:
                    name_tokens = [token.casefold() for token in re.findall(r"[A-Za-z0-9]+", name)
                                   if len(token) >= 4 and token.casefold() not in {"inc", "corp", "company", "limited"}]
                    def primary_source(row: dict) -> bool:
                        url = str(row.get("url", ""))
                        host = (urlsplit(url).hostname or "").casefold()
                        path = urlsplit(url).path.casefold()
                        return (host.endswith(".gov") or host == "clinicaltrials.gov"
                                or any(token in host for token in name_tokens)
                                or any(marker in host or marker in path for marker in ("investor", "press-release", "newsroom")))
                    rows = sorted(rows, key=lambda row: not primary_source(row))
                url = next((str(row.get("url", "")) for row in rows
                            if str(row.get("url", "")).startswith("https://")
                            and str(row.get("url", "")) not in source_urls
                            and "news.google.com" not in str(row.get("url", "")).casefold()), None)
                if url:
                    source_urls.append(url)

            # One source from each angle is the minimum; a third distinct result
            # can add a useful counterpoint without turning this into a dump.
            for url in source_urls[:3]:
                if deps.synthesis_reason():
                    break
                await read_public_source(deps, url, question or f"{name} recent price move catalysts and alternative explanations")
    if focus in {"advantage", "policy"}:
        from api.web_research import search_public_sources, read_public_source
        queries = list(dict.fromkeys(search_queries or ([question or f"{name} regulation company exposure", f"{name} annual report regulatory risk"] if focus == "policy" else
                                      [f"{name} products competitive advantage competitors", f"{name} annual report competition risks"])))
        # Collect the initial evidence plan without a run-wide call-count cap;
        # the parent agent can continue with targeted follow-ups afterward.
        for search_query in queries:
            if not deps.synthesis_reason():
                await search_public_sources(deps, search_query)
        rows = [row for item in deps.tool_results if item.get("tool") == "web_search" and isinstance(item.get("data"), list) for row in item["data"]]
        docs = [row["url"] for row in rows if not row["url"].startswith("https://news.google.com/")]
        # Search discovery may be unavailable. A retrieved SEC filing remains a
        # valid first-party narrative source; never guess a company/agency URL.
        filing_urls = [filing["url"] for item in deps.tool_results if item.get("tool") == "get_sec_company_data" for filing in item.get("data", {}).get("filings", []) if filing.get("form") in {"10-K", "10-Q", "20-F"}]
        if focus == "policy":
            regulators = [url for url in docs if (urlsplit(url).hostname or "").endswith(".gov")]
            company_docs = [url for url in docs if url not in regulators]
            docs = regulators[:1] + (company_docs + filing_urls)[:1]
        else:
            docs.extend(filing_urls)
        for url in list(dict.fromkeys(docs)):
            if not deps.synthesis_reason():
                await read_public_source(deps, url, question or f"{name} competition products risks")
    return code


def company_from_question(query: str) -> str:
    ticker = re.search(r"\bUS\.[A-Z]{1,6}(?:\.[A-Z])?\b|\b[A-Z]{2,5}\b", query)
    if ticker:
        return ticker.group()
    # Recovery for questions such as 'why Moderna rise so fast recently?'.
    text = re.sub(r"^(?:why\s+(?:did\s+|has\s+|is\s+)?|research\s+|analyze\s+)", "", query.strip(), flags=re.I)
    text = re.split(r"\s+(?:rise|rising|rose|rally|rallied|soar|surge|shares|stock|competitive|moat|industry)\b", text, maxsplit=1, flags=re.I)[0]
    return text.strip(" ?!。，？！")[:70]
