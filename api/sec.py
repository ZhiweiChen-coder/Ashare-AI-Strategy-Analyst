"""Public SEC company data with bounded facts, caching and shared rate limiting."""
from __future__ import annotations
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
import re
from urllib.parse import quote
import requests

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_DATA = "https://data.sec.gov"
_RATE_LOCK = threading.Lock()
_LAST_REQUEST = 0.0

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def canonical_ticker(value: str) -> str:
    ticker = value.strip().upper().removeprefix("US.").replace("-", ".")
    if not re.fullmatch(r"[A-Z]{1,6}(?:\.[A-Z])?", ticker):
        raise ValueError("Expected a US ticker, including an optional share class")
    return ticker


def filing_url(cik: str, accession: str, document: str = "") -> str:
    if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        raise ValueError("Invalid SEC accession")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"
    return base + (quote(document, safe="") if document else f"{accession}-index.html")


def curate_sec(submissions: dict, facts: dict, cik: str) -> tuple[list[dict], list[dict]]:
    recent = submissions.get("filings", {}).get("recent", {})
    filings = []
    for index, form in enumerate(recent.get("form", [])):
        if form not in {"10-K", "10-Q", "8-K", "20-F", "6-K", "10-K/A", "10-Q/A", "20-F/A"}:
            continue
        try:
            accession = recent["accessionNumber"][index]
            filings.append({"form": form, "filed": recent["filingDate"][index],
                            "report_date": recent.get("reportDate", [""] * len(recent["form"]))[index],
                            "accession": accession, "url": filing_url(cik, accession, recent["primaryDocument"][index])})
        except (KeyError, IndexError, ValueError):
            continue
        if len(filings) == 6:
            break
    selected = []
    tags = {"us-gaap": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax", "NetIncomeLoss", "EarningsPerShareDiluted", "Assets", "CashAndCashEquivalentsAtCarryingValue", "StockholdersEquity", "NetCashProvidedByUsedInOperatingActivities"],
            "ifrs-full": ["Revenue", "ProfitLoss", "DilutedEarningsLossPerShare", "Assets", "CashAndCashEquivalents", "Equity", "CashFlowsFromUsedInOperatingActivities"]}
    for taxonomy, concepts in tags.items():
        for concept in concepts:
            source = facts.get("facts", {}).get(taxonomy, {}).get(concept, {})
            for unit, values in source.get("units", {}).items():
                valid = [v for v in values if v.get("form") in {"10-K", "10-Q", "20-F", "6-K", "10-K/A", "10-Q/A", "20-F/A"} and v.get("end") and v.get("accn")]
                valid.sort(key=lambda v: (v.get("end", ""), v.get("filed", "")), reverse=True)
                seen_annual, seen_interim = set(), set()
                for value in valid:
                    period = (value.get("start"), value.get("end"))
                    try:
                        duration = (datetime.fromisoformat(value["end"]).date() - datetime.fromisoformat(value["start"]).date()).days if value.get("start") else 0
                    except (TypeError, ValueError):
                        duration = 0
                    bucket = seen_annual if 330 <= duration <= 400 else seen_interim
                    if period in bucket or len(bucket) >= 3:
                        continue
                    bucket.add(period)
                    try:
                        selected.append({"taxonomy": taxonomy, "concept": concept, "unit": unit,
                                         **{k: value.get(k) for k in ("val", "start", "end", "fy", "fp", "form", "filed", "frame")},
                                         "accession": value["accn"], "url": filing_url(cik, value["accn"])})
                    except ValueError:
                        continue
    return filings, selected


class SecCompanyService:
    @staticmethod
    def _throttle():
        global _LAST_REQUEST
        with _RATE_LOCK:
            time.sleep(max(0, 0.5 - (time.monotonic() - _LAST_REQUEST)))
            _LAST_REQUEST = time.monotonic()

    def __init__(self, cache: Path | None = None, http=None):
        self.cache = cache or Path(__file__).resolve().parents[1] / "data" / "sec_cache"
        self.http = http or requests.Session()

    def _get(self, url: str, ttl: int = 3600) -> dict:
        global _LAST_REQUEST
        user_agent = os.environ.get("SEC_USER_AGENT", "")
        if "@" not in user_agent:
            raise ValueError("SEC contact is not configured; company filings are unavailable.")
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        try:
            entry = json.loads(path.read_text())
            if time.time() - entry["cached_at"] < ttl:
                return entry
        except (OSError, ValueError, KeyError, TypeError):
            pass
        for attempt in range(3):
            self._throttle()
            response = self.http.get(url, headers={"User-Agent": user_agent, "Accept": "application/json"}, timeout=12, allow_redirects=False)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                try:
                    delay = float(response.headers.get("Retry-After", 2 ** (attempt + 1)))
                except ValueError:
                    delay = 2.0
                time.sleep(min(8, max(1, delay)))
                continue
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("SEC returned no usable data.")
            entry = {"cached_at": time.time(), "retrieved_at": now(), "data": response.json()}
            self.cache.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + f".{threading.get_ident()}.tmp")
            temporary.write_text(json.dumps(entry), encoding="utf-8")
            temporary.replace(path)
            return entry
        raise ValueError("SEC data is unavailable.")

    def resolve(self, query: str, local_codes: list[str] | None = None) -> dict:
        entry = self._get(SEC_TICKERS, ttl=86400)
        mapping = list(entry["data"].values())
        try:
            ticker = canonical_ticker(query)
        except ValueError:
            ticker = ""
        candidates = [v for v in mapping if v["ticker"].replace("-", ".") == ticker]
        codes = {canonical_ticker(v) for v in local_codes or []}
        if not candidates and codes:
            candidates = [v for v in mapping if v["ticker"].replace("-", ".") in codes]
        if not candidates and len(query.strip()) >= 3:
            candidates = [v for v in mapping if query.strip().casefold() in v["title"].casefold()]
        return {"status": "ok" if len(candidates) == 1 else "ambiguous" if candidates else "unavailable",
                "retrieved_at": entry["retrieved_at"], "url": SEC_TICKERS,
                "candidates": [{"name": v["title"], "code": "US." + v["ticker"].replace("-", "."),
                                "market": "us", "cik": str(v["cik_str"]).zfill(10), "identity_verified": True}
                               for v in candidates[:5]]}

    def company(self, stock_code: str) -> dict:
        identity = self.resolve(stock_code)
        if identity["status"] != "ok":
            raise ValueError("US ticker identity is ambiguous or unavailable; clarify the company first.")
        company = identity["candidates"][0]
        cik = company["cik"]
        submissions = self._get(f"{SEC_DATA}/submissions/CIK{cik}.json")
        gaps = ["Selected standardized financial facts and filing metadata only; full filing narratives are not retrieved."]
        facts = {"data": {}, "retrieved_at": submissions["retrieved_at"]}
        try:
            facts = self._get(f"{SEC_DATA}/api/xbrl/companyfacts/CIK{cik}.json")
        except (requests.RequestException, ValueError):
            gaps.append("Standardized SEC facts unavailable. Filing metadata remains available.")
        filings, financials = curate_sec(submissions["data"], facts["data"], cik)
        if not financials:
            gaps.append("No curated GAAP/IFRS financial facts available; do not invent metrics.")
        for record in financials:
            try:
                if (datetime.now(timezone.utc).date() - datetime.fromisoformat(record["end"]).date()).days > 180:
                    record["freshness"] = "older_reported_period"
                else:
                    record["freshness"] = "reported_period"
            except ValueError:
                record["freshness"] = "unknown"
        return {"company": company, "filings": filings, "financials": financials,
                "retrieved_at": submissions["retrieved_at"], "facts_retrieved_at": facts["retrieved_at"],
                "data_gaps": gaps}
