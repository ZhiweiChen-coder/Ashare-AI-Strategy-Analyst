"""Build source references from retrieved data, never model-generated URLs."""
import hashlib
import json
from urllib.parse import urlparse

from api.schemas import ResearchEvidence


def safe_source_url(value) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password:
        return value
    if value.startswith("/api/") and not value.startswith("//"):
        return value
    return None


def sources_for_tool(item: dict) -> list[ResearchEvidence]:
    tool, data = item.get("tool"), item.get("data")
    retrieved = item["retrieved_at"]
    sources = []
    if not data or item.get("status") == "unavailable":
        return []
    if tool == "get_sec_company_data":
        for row in [*data.get("filings", []), *data.get("financials", [])]:
            sources.append(("SEC " + (row.get("concept") or row.get("form", "filing")), row.get("url"), row.get("end") or row.get("report_date") or row.get("filed"), row.get("freshness", "reported_period"), row))
    elif tool in {"get_stock_news", "get_global_news", "web_search"}:
        for row in data:
            sources.append((row.get("source") or "Provider summary", row.get("url"), row.get("published_at"), "provider_summary", row))
    elif tool == "read_public_source":
        sources.append((data.get("source") or "Original document", data.get("url"), data.get("published_at"), "source_excerpts", data))
    elif tool == "get_stock_analysis":
        bars = data.get("chart_series", [])
        date = bars[-1].get("date") if bars else None
        sources.append((str(data.get("metadata", {}).get("source") or "Daily market data"), f"/api/stocks/{data.get('stock_code')}/analysis?include_ai=false", date, "historical_or_delayed", {"stock_code": data.get("stock_code"), "quote": data.get("quote")}))
    elif tool == "search_stocks":
        sources.append(("Stock identity search", "/api/stocks/search", None, "identity_mapping", data))
    elif tool in {"get_portfolio_analysis", "list_hotspots", "get_hotspot_detail"}:
        path = {"get_portfolio_analysis": "/api/portfolio/analysis", "list_hotspots": "/api/hotspots", "get_hotspot_detail": "/api/hotspots"}[tool]
        sources.append((tool, path, None, "retrieved_snapshot", data))
    result = []
    for source, url, date, freshness, row in sources:
        identity = hashlib.sha256(json.dumps([tool, url, row], sort_keys=True, default=str).encode()).hexdigest()[:16]
        result.append(ResearchEvidence(id="ev_" + identity, source=source, url=safe_source_url(url),
            retrieved_at=row.get("fetched_at", retrieved) if isinstance(row, dict) else retrieved,
            data_as_of=date or None, freshness=freshness,
            title=row.get("title") if isinstance(row, dict) else None,
            excerpts=row.get("excerpts", []) if tool == "read_public_source" else []))
    return result
