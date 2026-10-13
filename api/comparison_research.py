"""Intent and query helpers for balanced, cross-market company comparisons."""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

from ashare.stock_pool import normalize_stock_code
from api.company_research import cached_identity, search_identity


_COMPARISON_WORDS = re.compile(
    r"对比|比较|异同|区别|差异|compare|comparison|differences?|similarities|versus|\bvs\.?\b",
    re.IGNORECASE,
)
_PAIR_WORDS = re.compile(r"和|与|及|、|\b(?:and|vs\.?|versus)\b|[,/]", re.IGNORECASE)
_STOCK_CONTEXT = re.compile(
    r"股票|个股|公司|两只|两家|shares?|stocks?|companies|equities|tickers?",
    re.IGNORECASE,
)
_MARKET_ONLY = re.compile(
    r"大盘|市场|宏观|\bmarkets?\b|\bindices\b|\bmacro(?:economic)?\b|\beconom(?:y|ies)\b",
    re.IGNORECASE,
)
_EXPLICIT_FINANCIAL_SCOPE = re.compile(
    r"营收|收入|净利润|利润|现金流|财报|财务|毛利率|净利率|每股收益|\b(?:revenue|earnings|net income|cash flow|financials?|margin|eps|ebitda)\b",
    re.IGNORECASE,
)
_NEWS_REQUEST = re.compile(r"headlines?|news|announcements?|消息|新闻|公告|动态|头条", re.IGNORECASE)
_NEWS_CAUSAL = re.compile(r"why|cause|catalyst|drove|rose|rall(?:y|ied)|surge|fall|跌|涨|原因|驱动|催化", re.IGNORECASE)
_GLOBAL_NEWS = re.compile(r"全球|大盘|市场新闻|宏观新闻|\b(?:global|market|macro)\s+news\b", re.IGNORECASE)
_INVESTOR_BRIEF = re.compile(
    r"\b(?:first[\s-]pass|initial|preliminary)\s+(?:investor|investment)\s+(?:brief|overview|memo)\b|"
    r"\binvestor brief\b|初步投资(?:者)?简报|投资者简报",
    re.IGNORECASE,
)
_NON_NEWS_SCOPE = re.compile(
    r"filings?|10[- ]?[kq]|20[- ]?f|financial statements?|earnings materials?|annual reports?|"
    r"valuation|balance sheet|cash flow|competitive advantage|industry analysis|"
    r"财报|申报文件|业绩材料|年报|估值|现金流|资产负债|产业优势|竞争优势|行业分析", re.I,
)
_BENCHMARK_TARGET = re.compile(r"S&P\s*500|Nasdaq|标普\s*500|纳斯达克|benchmark|基准指数", re.I)


def brief_needs_quote(query: str) -> bool:
    return bool(re.search(r"stock price|share price|quote|price performance|stock performance|returns?|股价|行情|涨跌|收益率", query, re.I))


def investor_brief_tools(query: str, *, us_company: bool) -> list[str]:
    tools = (["get_sec_company_data"] if us_company else []) + ["get_stock_news", "web_search"]
    if brief_needs_quote(query):
        tools.append("get_stock_analysis")
    return tools


def is_first_pass_investor_brief(query: str) -> bool:
    """Identify explicit single-company first-pass investor research requests."""
    return bool(_INVESTOR_BRIEF.search(query or ""))


def is_broad_stock_comparison(query: str) -> bool:
    """Catch broad company-pair requests while leaving market and metric-only asks alone."""
    text = (query or "").strip()
    if _BENCHMARK_TARGET.search(text):
        return False
    if not _COMPARISON_WORDS.search(text) or not _PAIR_WORDS.search(text):
        return False
    if _EXPLICIT_FINANCIAL_SCOPE.search(text):
        return False
    if _STOCK_CONTEXT.search(text):
        return True
    if _MARKET_ONLY.search(text):
        return False
    # This agent is a securities research assistant; a direct "compare X and Y"
    # request is a company comparison unless it explicitly names markets instead.
    return True


def is_financial_stock_comparison(query: str) -> bool:
    """Route explicit paired-company SEC metric questions through the comparator."""
    text = (query or "").strip()
    if _BENCHMARK_TARGET.search(text):
        return False
    compare = re.search(r"对比|比较|compare|comparison|differences?|\bvs\.?\b|versus", text, re.I)
    pair = _PAIR_WORDS.search(text)
    return bool(compare and pair and _EXPLICIT_FINANCIAL_SCOPE.search(text))


def is_company_news_query(query: str, *, verified_identity: bool = False) -> bool:
    """Identify single-company news lookups while excluding market/news-cause asks."""
    text = (query or "").strip()
    if is_first_pass_investor_brief(text) or _NON_NEWS_SCOPE.search(text):
        return False
    has_identity_hint = bool(verified_identity or _STOCK_CONTEXT.search(text)
                             or re.search(r"\b(?:US\.)?[A-Z]{1,6}(?:\.[A-Z])?\b", text))
    return bool(_NEWS_REQUEST.search(text) and not _NEWS_CAUSAL.search(text)
                and not _GLOBAL_NEWS.search(text) and not is_broad_stock_comparison(text)
                and not is_financial_stock_comparison(text) and has_identity_hint)


def explicit_ticker_query(company: str) -> str | None:
    """Extract a user-supplied ticker from forms like ``应用材料 AMAT`` or ``US.AMAT``."""
    text = (company or "").strip()
    prefixed = re.search(r"\bUS\.([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\b", text, re.IGNORECASE)
    if prefixed:
        return prefixed.group(1).upper()
    parenthesized = re.search(r"[（(]\s*([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\s*[）)]\s*$", text)
    if parenthesized:
        return parenthesized.group(1).upper()
    trailing = re.search(r"([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\s*$", text)
    if trailing and (trailing.start() > 0 or len(text) <= 6):
        token = trailing.group(1)
        # Avoid interpreting a trailing common English word as a ticker.
        if token.casefold() not in {"and", "the", "stock", "shares", "company", "market"}:
            return token.upper()
    return None


def comparison_web_query(company_name: str, market: str, stock_code: str = "") -> str:
    """Build a company-specific query around comparable business dimensions."""
    name = re.sub(r"\s*/\s*(?:DE|INC|PLC|LTD)\.?$", "", (company_name or "").strip(), flags=re.IGNORECASE)
    name = re.sub(r"\b(?:incorporated|inc\.?|corporation|corp\.?|limited|ltd\.?|plc|company|co\.?)\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip(" ,./") or company_name
    ticker = re.sub(r"^(?:US|HK|SH|SZ)\.?", "", (stock_code or "").upper())
    ticker = re.sub(r"\.HK$", "", ticker)
    if market == "us":
        query = f'"{name}" {ticker} products business segments applications customer industries competitors annual report'
    else:
        query = f'"{name}" {ticker} 主营业务 产品 应用领域 下游市场 客户 竞争格局 年报'
    return re.sub(r"\s+", " ", query).strip()


def comparison_source_matches(row: dict, company_name: str, stock_code: str) -> bool:
    """Reject search hits that only share a generic word with the company name."""
    fields = ("title", "snippet", "source", "url")
    values = [str(row.get(key) or "").casefold() for key in fields]
    if not any(value.strip() for value in values):
        return False

    code = re.sub(r"^(?:US|HK|SH|SZ)\.?", "", (stock_code or "").upper())
    code = re.sub(r"\.HK$", "", code)
    if code and any(re.search(rf"(?<![a-z0-9]){re.escape(code.casefold())}(?![a-z0-9])", value) for value in values):
        return True

    name = re.sub(r"\s*/\s*(?:DE|INC|PLC|LTD)\.?$", "", (company_name or "").strip(), flags=re.IGNORECASE)
    name = re.sub(r"\b(?:incorporated|inc\.?|corporation|corp\.?|limited|ltd\.?|plc|company|co\.?)\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip(" ,./").casefold()
    if re.search(r"[\u3400-\u9fff]", name):
        return any(name in value for value in values)

    tokens = [token.casefold() for token in re.findall(r"[a-z0-9]+", name) if len(token) > 1]
    if not tokens:
        return False
    # Require all meaningful words for multi-word legal names; a generic
    # substring such as "Applied" is not sufficient evidence of AMAT.
    return any(all(re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", value) for token in tokens)
               for value in values)


def comparison_source_priority(row: dict, company_name: str) -> int:
    """Prefer issuer/regulator material when choosing evidence to read first."""
    try:
        host = (urlsplit(str(row.get("url") or "")).hostname or "").casefold().removeprefix("www.")
    except ValueError:
        host = ""
    if not host:
        return 3

    filing_hosts = (
        "cninfo.com.cn", "szse.cn", "sse.com.cn", "hkexnews.hk",
        "hkex.com.hk", "gov.cn", "gov.hk",
    )

    name = re.sub(r"\s*/\s*(?:DE|INC|PLC|LTD)\.?$", "", (company_name or "").strip(), flags=re.IGNORECASE)
    name = re.sub(r"\b(?:incorporated|inc\.?|corporation|corp\.?|limited|ltd\.?|plc|company|co\.?)\b", "", name, flags=re.IGNORECASE)
    compact_name = re.sub(r"[^a-z0-9]", "", name.casefold())
    compact_host = re.sub(r"[^a-z0-9]", "", host)
    if len(compact_name) >= 6 and compact_name in compact_host:
        return 0
    if any(host == domain or host.endswith("." + domain) for domain in filing_hosts):
        return 1
    if host == "sec.gov" or host.endswith(".sec.gov"):
        return 1

    reputable_media = (
        "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com",
        "marketwatch.com", "fool.com", "forbes.com",
    )
    if any(host == domain or host.endswith("." + domain) for domain in reputable_media):
        return 2
    return 3


def prioritize_comparison_sources(search: dict, company_name: str) -> dict:
    """Sort snippets and their evidence references together by source quality."""
    rows = search.get("data")
    if not isinstance(rows, list) or len(rows) < 2:
        return search
    evidence = search.get("evidence")
    order = sorted(range(len(rows)), key=lambda index: (
        comparison_source_priority(rows[index] if isinstance(rows[index], dict) else {}, company_name), index
    ))
    search["data"] = [rows[index] for index in order]
    if isinstance(evidence, list) and len(evidence) == len(rows):
        search["evidence"] = [evidence[index] for index in order]
    return search


async def resolve_comparison_identity(deps, requested: str) -> dict:
    """Resolve one requested side once, requiring an unambiguous verified identity."""
    ticker = explicit_ticker_query(requested)
    lookup = ticker or requested.strip()
    cached = cached_identity(deps, lookup)
    if cached:
        rows = [cached]
    else:
        result = await deps.retrieve(
            "search_stocks", {"query": lookup, "limit": 5},
            lambda: search_identity(deps, lookup, 5),
        )
        try:
            payload = json.loads(result)
            rows = payload.get("data", []) if isinstance(payload, dict) else []
        except (TypeError, ValueError):
            rows = []
        rows = rows if isinstance(rows, list) else []

    name_hint = requested.strip()
    if ticker:
        name_hint = re.sub(r"[（(]?\s*(?:US\.)?" + re.escape(ticker) + r"\s*[）)]?\s*$", "", name_hint, flags=re.IGNORECASE).strip()
    normalized_hint = re.sub(r"[^\w\u3400-\u9fff]+", " ", name_hint.casefold()).strip()
    selected = []
    if ticker:
        target_code = normalize_stock_code("US." + ticker).upper()
        selected = [row for row in rows if normalize_stock_code(str(row.get("code", ""))).upper() == target_code]
    if not selected and normalized_hint:
        selected = [row for row in rows if re.sub(r"[^\w\u3400-\u9fff]+", " ", str(row.get("name", "")).casefold()).strip() == normalized_hint]
    if not selected and len(rows) == 1:
        selected = rows
    if len(selected) != 1:
        return {"status": "ambiguous" if rows else "unavailable", "requested": requested,
                "candidates": [{"name": row.get("name"), "code": row.get("code")} for row in rows[:4]]}

    row = selected[0]
    code = normalize_stock_code(str(row.get("code", ""))).upper()
    if not code or (code.startswith("US.") and (row.get("identity_verified") is False or code not in deps.verified_us_codes)):
        return {"status": "unverified", "requested": requested, "candidates": [{"name": row.get("name"), "code": code}]}
    if len(rows) != 1 or len(selected) != len(rows):
        # Preserve the exact, selected identity as a separate record so downstream
        # tools can verify it without re-running a broad alias search.
        deps.record_tool({"tool": "search_stocks", "data": [row]})
    return {"status": "ok", "requested": requested, "name": row.get("name") or requested,
            "code": code, "market": "us" if code.startswith("US.") else "hk" if code.endswith(".HK") else "cn"}

