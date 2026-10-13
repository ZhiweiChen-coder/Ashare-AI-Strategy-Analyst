"""Bounded public-source reading and per-run web research, without model calls."""
from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time
from datetime import datetime, timezone
from io import BytesIO
from typing import Callable
from urllib.parse import urljoin, urlsplit

import urllib3
import certifi
from bs4 import BeautifulSoup


class SourceUnavailable(ValueError):
    pass


def public_address(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise SourceUnavailable("Only public HTTPS documents on the standard port are supported.")
    host = parsed.hostname.encode("idna").decode()
    addresses = {row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise SourceUnavailable("Private, local and non-public network addresses are blocked.")
    return host, sorted(addresses)[0]


class PublicDocumentReader:
    """Pin a validated public IP while retaining TLS certificate/hostname checks."""
    def __init__(self, sec_user_agent: str = "OpenAshare research"):
        self.sec_user_agent = sec_user_agent

    def download(self, url: str) -> tuple[str, bytes, str]:
        started = time.monotonic()
        for _ in range(4):
            if time.monotonic() - started > 25:
                raise SourceUnavailable("Source exceeded the document read deadline.")
            host, address = public_address(url)
            parsed = urlsplit(url)
            pool = urllib3.HTTPSConnectionPool(address, 443, server_hostname=host, assert_hostname=host,
                                             cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(), timeout=urllib3.Timeout(connect=5, read=10))
            response = None
            try:
                # Requests cannot follow redirects to private addresses or change DNS
                # between validation and connection. No cookies or credentials are sent.
                headers = {"Host": host, "User-Agent": self.sec_user_agent if host == "sec.gov" or host.endswith(".sec.gov") else
                           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "*/*"}
                if host == "sec.gov" or host.endswith(".sec.gov"):
                    from api.sec import SecCompanyService
                    SecCompanyService._throttle()
                response = pool.urlopen("GET", parsed.path + ("?" + parsed.query if parsed.query else ""), headers=headers,
                                        redirect=False, retries=False, preload_content=False)
                if response.status in (301, 302, 303, 307, 308):
                    url = urljoin(url, response.headers.get("Location", ""))
                    continue
                if response.status != 200:
                    raise SourceUnavailable(f"Source returned HTTP {response.status}.")
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(value in content_type for value in ("html", "pdf", "text/plain")):
                    raise SourceUnavailable("Source format is unsupported; HTML, text and PDF are supported.")
                chunks, size = [], 0
                for chunk in response.stream(65536, decode_content=True):
                    if time.monotonic() - started > 25:
                        raise SourceUnavailable("Source exceeded the document read deadline.")
                    size += len(chunk)
                    if size > 2_000_000:
                        if "html" in content_type or "text/plain" in content_type:
                            chunks.append(chunk[:2_000_000 - (size - len(chunk))])
                            content_type += "; partial-document"
                            break
                        raise SourceUnavailable("PDF exceeds the two-megabyte read limit.")
                    chunks.append(chunk)
                return url, b"".join(chunks), content_type
            finally:
                if response is not None:
                    response.close()
                pool.close()
        raise SourceUnavailable("Source exceeded the redirect limit.")

    def read(self, url: str, question: str = "") -> dict:
        final_url, body, content_type = self.download(url)
        gaps, published, title = [], None, urlsplit(final_url).hostname
        if "partial-document" in content_type:
            gaps.append("Only the first two megabytes of this document were read; later sections are unavailable.")
        if "pdf" in content_type:
            from pypdf import PdfReader
            pdf = PdfReader(BytesIO(body))
            paragraphs = []
            for page_number, page in enumerate(pdf.pages[:20], 1):
                paragraphs.extend((f"page {page_number}", line.strip()) for line in (page.extract_text() or "").split("\n") if line.strip())
            title = str((pdf.metadata or {}).get("/Title") or title)
            if len(pdf.pages) > 20:
                gaps.append(f"Only the first 20 of {len(pdf.pages)} PDF pages were read.")
        else:
            soup = BeautifulSoup(body, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else title
            date = soup.select_one('meta[property="article:published_time"], meta[name="date"], time[datetime]')
            published = (date.get("content") or date.get("datetime")) if date else None
            for node in soup.select("script,style,nav,header,footer,form,noscript,aside"):
                node.decompose()
            root = soup.select_one("article, main") or soup
            paragraphs = [(f"paragraph {i}", re.sub(r"\s+", " ", line).strip()) for i, line in enumerate(root.get_text("\n", strip=True).splitlines(), 1) if len(line.strip()) > 30]
        # Extract, never paraphrase. Record locations and disclose truncated coverage.
        terms = set(re.findall(r"[\w-]{3,}", question.lower())) - {"the", "and", "for", "with", "how", "company", "research"}
        ranked = sorted(enumerate(paragraphs), key=lambda row: (-sum(term in row[1][1].lower() for term in terms), row[0]))
        selected, remaining = [], 6000
        for index, (location, text) in ranked:
            text = text[:min(1500, remaining)]
            if remaining < 100:
                break
            selected.append((index, {"location": location, "text": text}))
            remaining -= len(text)
        if not selected:
            raise SourceUnavailable("Document contains no readable text; it may require JavaScript or OCR.")
        gaps.append("Selected source excerpts only; omitted text may contain qualifications. Publication date is unknown." if not published else "Selected source excerpts only; omitted text may contain qualifications.")
        return {"url": final_url, "requested_url": url, "title": title, "source": urlsplit(final_url).hostname,
                "published_at": published, "fetched_at": datetime.now(timezone.utc).isoformat(),
                "excerpts": [value for _, value in sorted(selected)], "data_gaps": gaps}


async def search_public_sources(
    deps,
    query: str,
    limit: int = 3,
    market: str | None = None,
    accept_result: Callable[[dict], bool] | None = None,
    source_priority: Callable[[dict], int] | None = None,
) -> str:
    query = re.sub(r"\s+", " ", query).strip()[:300]
    market = market or ("us" if deps.verified_us_codes or deps.language == "en-US" else "cn")
    async def execute():
        deps.report("tool_running", 50, "正在检索公开资料", {"tool": "web_search"})
        try:
            if hasattr(deps.web_search_service, "search_report"):
                report = await asyncio.to_thread(deps.web_search_service.search_report, query, limit=limit,
                    language=deps.language, market=market)
            else:
                rows = await asyncio.to_thread(deps.web_search_service.search, query, limit=limit)
                report = {"results": [row.model_dump() for row in rows], "data_gaps": []}
            rows = [row.model_dump() if hasattr(row, "model_dump") else row for row in report.get("results", [])]
            gaps = list(report.get("data_gaps", []))
            rejected = 0
            if accept_result is not None:
                matched = [row for row in rows if isinstance(row, dict) and accept_result(row)]
                rejected = len(rows) - len(matched)
                rows = matched
                if rejected:
                    gaps.append(f"Excluded {rejected} search result(s) that did not identify the requested company.")
                if not rows:
                    gaps.append("No search result explicitly identified the requested company; do not infer its business from similarly named entities.")
            if source_priority is not None:
                rows = sorted(rows, key=source_priority)
            provider_failed = any(re.search(r"\b(?:unavailable|failed|timed out|error)\b", str(gap), re.I) for gap in gaps)
            reason_code = None
            if not rows:
                reason_code = "provider_error" if provider_failed else "no_company_match" if rejected else "no_results"
            result = deps.record_tool({"tool": "web_search", "status": "completed" if rows else "unavailable",
                                      "reason_code": reason_code, "data": rows, "data_gaps": gaps})
            if rows:
                deps.report("tool_completed", 65, "公开资料检索完成", {"tool": "web_search"})
            return result
        except Exception as exc:
            return deps.record_tool({"tool": "web_search", "status": "unavailable", "data": [],
                                     "data_gaps": [f"Search provider unavailable ({type(exc).__name__}); this does not establish that no relevant sources exist."]})
    return await deps.retrieve("web_search", {"query": query, "limit": min(3, max(1, limit)), "market": market}, execute)


async def read_public_source(deps, url: str, question: str = "") -> str:
    known_urls = {source.get("url") for item in deps.tool_results for source in item.get("evidence", [])}
    user_urls = set(re.findall(r"https://[^\s<>]+", deps.user_query))
    if url not in known_urls | user_urls:
        return deps.record_tool({"tool": "read_public_source", "status": "unavailable", "data": {"data_gaps": ["Read only a URL supplied by the user or returned by a source tool; do not guess document links."]}})
    async def execute():
        deps.report("tool_running", 65, "正在读取来源原文", {"tool": "read_public_source"})
        try:
            data = await asyncio.to_thread(deps.document_reader.read, url, question[:300])
            result = deps.record_tool({"tool": "read_public_source", "data": data})
            deps.report("tool_completed", 70, "来源原文读取完成", {"tool": "read_public_source"})
            return result
        except Exception as exc:
            gap = str(exc) if isinstance(exc, SourceUnavailable) else f"Document unavailable ({type(exc).__name__})."
            return deps.record_tool({"tool": "read_public_source", "status": "unavailable", "data": {"data_gaps": [gap]}})
    # A second question does not cause another network read of the same document.
    return await deps.retrieve("read_public_source", {"url": url}, execute)
