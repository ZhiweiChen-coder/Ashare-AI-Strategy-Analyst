"""Real Pydantic orchestration with offline models; no paid test requests."""
import asyncio
import json
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from api import main
from api.agent_pydantic import AgentDeps, AgentOutput, compact_broad_comparison, create_agent, evidence_fallback, financial_evidence, run_agent_async, validate_research_output
from api.company_research import ensure_identity, search_identity, collect_company_evidence, verified_name
from api.comparison_research import (
    comparison_source_matches,
    comparison_web_query,
    explicit_ticker_query,
    is_broad_stock_comparison,
    is_company_news_query,
    is_financial_stock_comparison,
    prioritize_comparison_sources,
)
from api.research_capability import ResearchCapability
from api.financial_comparison import compare_sec_facts
from api.schemas import AIInsight, AgentQuery, NewsItem, QuoteSnapshot, SignalSummary, StockAnalysisResponse, StockSearchResult
from api.web_research import SourceUnavailable


def dependencies(**kwargs):
    return AgentDeps(
        stock_service=SimpleNamespace(search_stocks=lambda *a, **kw: [StockSearchResult(name="Moderna", code="US.MRNA", market="us")]),
        news_service=SimpleNamespace(get_stock_news=lambda *a, **kw: [NewsItem(id="fixture", stock_code="US.MRNA", stock_name="Moderna", title="Moderna research update", source="Company fixture", published_at="2026-10-10", url="https://example.org/moderna", summary="Test evidence, not a live event.")]),
        hotspot_service=SimpleNamespace(), portfolio_service=SimpleNamespace(), web_search_service=SimpleNamespace(),
        sec_service=SimpleNamespace(resolve=lambda *a: {"status": "ok", "candidates": [{"name": "Moderna", "code": "US.MRNA", "market": "us", "identity_verified": True}]},
                                    company=lambda *a: {"company": {"code": "US.MRNA", "name": "Moderna"}, "filings": [], "financials": [], "data_gaps": ["No full filing narrative in fixture."]}),
        language="en-US", **kwargs,
    )


def final(deps, summary="Retrieved company evidence supports further review"):
    refs = [source["id"] for item in deps.tool_results for source in item.get("evidence", []) if source.get("freshness") != "identity_mapping"]
    return {"summary": f"## Evidence\n{summary} [{refs[0]}].", "evidence_ids": refs, "data_gaps": [], "actions": [], "financial_fact_ids": list(financial_evidence(deps.tool_results))}


def test_broad_comparison_routing_is_generic_and_market_questions_stay_separate():
    assert is_broad_stock_comparison("你可以对比一下北方华创和应用材料amat这两只股票吗？")
    assert is_broad_stock_comparison("Compare AAPL and MSFT stocks")
    assert not is_broad_stock_comparison("比较中国和美国市场表现")
    assert not is_broad_stock_comparison("Compare AAPL and MSFT revenue")
    assert is_financial_stock_comparison("Compare AAPL and MSFT annual revenue")
    assert is_company_news_query("What are NVIDIA's latest available company headlines?")
    assert not is_company_news_query("Why did NVIDIA stock surge after news?")
    assert explicit_ticker_query("应用材料AMAT") == "AMAT"
    assert explicit_ticker_query("Applied Materials (AMAT)") == "AMAT"
    query = comparison_web_query("APPLIED MATERIALS INC /DE", "us", stock_code="US.AMAT")
    assert '"APPLIED MATERIALS" AMAT' in query
    assert '"北方华创" 002371' in comparison_web_query("北方华创", "cn", stock_code="SZ002371")
    assert comparison_source_matches({"title": "Applied Materials expands semiconductor capacity", "snippet": "AMAT products"}, "Applied Materials Inc /DE", "US.AMAT")
    assert not comparison_source_matches({"title": "Applied Industrial Technologies", "snippet": "industrial products"}, "Applied Materials Inc /DE", "US.AMAT")
    assert not comparison_source_matches({"title": "Amazon.com: Applied dog treats", "snippet": "applied dog treat"}, "Applied Materials Inc /DE", "US.AMAT")
    assert comparison_source_matches({"title": "北方华创产品和应用领域"}, "北方华创", "SZ002371")


def test_capability_routes_single_company_news_and_sec_pairs_through_scoped_tools():
    async def run():
        names = ["search_stocks", "get_stock_news", "get_stock_analysis", "web_search",
                 "research_comparison", "get_sec_company_data", "compare_companies"]
        tools = [SimpleNamespace(name=name) for name in names]

        news = dependencies(user_query="What are NVIDIA's latest available company headlines?")
        capability = ResearchCapability()
        ctx = SimpleNamespace(deps=news)
        assert [tool.name for tool in await capability.prepare_tools(ctx, tools)] == ["search_stocks"]
        news.record_tool({"tool": "search_stocks", "data": [{"name": "NVIDIA", "code": "US.NVDA"}]})
        news.verified_us_codes.add("US.NVDA")
        assert [tool.name for tool in await capability.prepare_tools(ctx, tools)] == ["get_stock_news"]

        financials = dependencies(user_query="Compare AAPL and MSFT annual revenue")
        ctx = SimpleNamespace(deps=financials)
        assert [tool.name for tool in await capability.prepare_tools(ctx, tools)] == ["search_stocks"]
        financials.record_tool({"tool": "search_stocks", "data": [{"name": "Apple", "code": "US.AAPL"}]})
        financials.verified_us_codes.add("US.AAPL")
        assert [tool.name for tool in await capability.prepare_tools(ctx, tools)] == ["search_stocks"]
        financials.record_tool({"tool": "search_stocks", "data": [{"name": "Microsoft", "code": "US.MSFT"}]})
        financials.verified_us_codes.add("US.MSFT")
        assert [tool.name for tool in await capability.prepare_tools(ctx, tools)] == ["compare_companies"]
        financials.record_tool({"tool": "compare_companies", "data": {"metrics": []}})
        assert await capability.prepare_tools(ctx, tools) == []

    asyncio.run(run())


def test_comparison_source_order_prefers_primary_sources_and_keeps_citations_paired():
    search = {
        "data": [
            {"title": "Applied Materials profile", "url": "https://pitchgrade.com/companies/applied-materials"},
            {"title": "Annual report", "url": "https://ir.appliedmaterials.com/annual-report-proxy"},
            {"title": "Earnings transcript", "url": "https://www.fool.com/earnings/call-transcripts/example"},
        ],
        "evidence": [{"id": "secondary"}, {"id": "issuer"}, {"id": "media"}],
    }
    prioritize_comparison_sources(search, "Applied Materials Inc /DE")
    assert [row["title"] for row in search["data"]] == ["Annual report", "Earnings transcript", "Applied Materials profile"]
    assert [row["id"] for row in search["evidence"]] == ["issuer", "media", "secondary"]

    cn_search = {"data": [
        {"title": "Sina profile", "url": "https://vip.stock.finance.sina.com.cn/company"},
        {"title": "Annual report", "url": "https://static.cninfo.com.cn/report.pdf"},
    ], "evidence": [{"id": "sina"}, {"id": "cninfo"}]}
    prioritize_comparison_sources(cn_search, "北方华创")
    assert cn_search["evidence"][0]["id"] == "cninfo"


def test_cross_currency_comparison_rejects_unsupported_size_rankings():
    tool_results = [{"tool": "research_comparison", "data": {"companies": [
        {"identity": {"market": "cn", "code": "SZ002371"}},
        {"identity": {"market": "us", "code": "US.AMAT"}},
    ]}}]
    with pytest.raises(ModelRetry, match="different reporting currencies"):
        validate_research_output(AgentOutput(summary="规模上应用材料更大。"), tool_results)
    with pytest.raises(ModelRetry, match="different reporting currencies"):
        validate_research_output(AgentOutput(summary="Applied Materials has more revenue than North Huachuang."), tool_results)
    validate_research_output(AgentOutput(summary="北方华创深耕国内市场，AMAT业务覆盖多个地区。"), tool_results)
    validate_research_output(AgentOutput(summary="规模上应用材料更大。"), [*tool_results, {"tool": "get_fx_rate", "data": {"rate": 7.1, "date": "2026-10-12"}}])


def test_both_modes_have_no_cumulative_token_cap_and_keep_separate_deadlines():
    quick = dependencies(research_mode="quick")
    deep = dependencies(research_mode="deep")
    assert quick.total_token_limit is None and quick.run_deadline_seconds == 180
    assert deep.total_token_limit is None and deep.run_deadline_seconds == 540
    deep.run_usage = SimpleNamespace(total_tokens=1000000)
    assert deep.synthesis_reason() is None
    deep.started_at = time.monotonic() - 361
    assert deep.synthesis_reason() == "time_reserved_for_synthesis"
    deep.started_at = time.monotonic()
    quick.run_usage = SimpleNamespace(total_tokens=23999)
    assert quick.synthesis_reason() is None
    quick.run_usage.total_tokens = 1000000
    assert quick.synthesis_reason() is None


def test_quick_broad_comparison_answers_from_balanced_company_matched_snippets():
    async def run():
        deps = dependencies()
        deps.language = "zh-CN"
        deps.stock_service.search_stocks = lambda query, **kwargs: (
            [StockSearchResult(name="Applied Materials", code="US.AMAT", market="us")]
            if "AMAT" in query.upper() else [StockSearchResult(name="北方华创", code="sz002371", market="sz")]
        )
        deps.stock_service.get_stock_analysis = lambda code, include_ai=False: StockAnalysisResponse(
            stock_name="Applied Materials" if code == "US.AMAT" else "北方华创",
            stock_code=code, market="us" if code == "US.AMAT" else "sz",
            quote=QuoteSnapshot(stock_name="Fixture", stock_code=code, current_price=100,
                change=1, change_pct=1, open_price=100, high_price=101, low_price=99,
                volume=1000, amplitude_pct=2, timestamp=datetime(2026, 10, 12, tzinfo=timezone.utc)),
            technical_indicators={}, signal_summary=SignalSummary(overall_score=50, overall_signal="neutral"),
            technical_commentary=[], ai_insight=AIInsight(enabled=False), chart_series=[],
            metadata={"data_as_of": "2026-10-12", "currency": "USD" if code == "US.AMAT" else "CNY"},
        )
        deps.sec_service.resolve = lambda *args, **kwargs: {
            "status": "ok", "candidates": [{"name": "Applied Materials", "code": "US.AMAT", "market": "us", "identity_verified": True}]
        }
        deps.web_search_service = SimpleNamespace(search_report=lambda query, **kwargs: {
            "results": ([
                {"title": "Applied Materials products and markets", "snippet": "Applied Materials (AMAT) serves chipmakers.", "url": "https://example.org/amat"},
                {"title": "Applied Industrial Technologies", "snippet": "Industrial distribution", "url": "https://example.org/applied"},
            ] if kwargs["market"] == "us" else [
                {"title": "北方华创产品与市场", "snippet": "北方华创半导体设备业务介绍", "url": "https://example.org/naura"}
            ]), "data_gaps": []
        })
        calls = []
        def model(messages, info):
            calls.append(info)
            if len(calls) == 1:
                return ModelResponse(parts=[ToolCallPart("research_comparison", {
                    "companies": ["北方华创", "应用材料AMAT"], "question": "Compare their businesses",
                })])
            comparison = next(item for item in deps.tool_results if item["tool"] == "research_comparison")
            assert all(item["source_read"]["status"] == "not_attempted" for item in comparison["data"]["companies"])
            assert {len(item["business_search"]["data"]) for item in comparison["data"]["companies"]} == {1}
            assert len([item for item in deps.tool_results if item["tool"] == "read_public_source"]) == 0
            source_ids = [ref["id"] for item in deps.tool_results if item["tool"] == "web_search" for ref in item["evidence"]]
            return ModelResponse(parts=[ToolCallPart("final_result", {
                "summary": (
                    "两家公司均服务半导体制造商，具体设备重合度仍需逐类核对。\n\n"
                    "| 维度 | 北方华创 | Applied Materials |\n| --- | --- | --- |\n"
                    f"| 产品与应用 | 来源摘要 [{source_ids[1]}] | 来源摘要 [{source_ids[0]}] |"
                ),
                "evidence_ids": source_ids,
                "ui_components": ["table", "comparison"], "data_gaps": ["Quick mode has not read original documents."],
            })])

        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "你可以对比一下北方华创和应用材料amat这两只股票吗？")
        assert len(calls) == 2
        assert deps.retrieval_count == 6
        assert response.payload["_meta"]["finish_reason"] == "completed"
        assert response.ui_components == ["table"]
        assert len(response.evidence) == 2
        assert not any(item["tool"] in {"get_sec_company_data", "compare_companies", "read_public_source"} for item in deps.tool_results)
    asyncio.run(run())


def test_pair_comparison_fallback_stays_balanced_and_does_not_dump_financial_rows():
    deps = dependencies(user_query="对比北方华创和应用材料 AMAT")
    deps.language = "zh-CN"
    deps.record_tool({"tool": "research_comparison", "data": {"companies": [
        {"identity": {"status": "ok", "name": "北方华创", "code": "SZ002371"}},
        {"identity": {"status": "ok", "name": "Applied Materials", "code": "US.AMAT"}},
    ]}})
    for code, name, currency in (("SZ002371", "北方华创", "CNY"), ("US.AMAT", "Applied Materials", "USD")):
        deps.record_tool({"tool": "get_stock_analysis", "data": {
            "stock_code": code, "stock_name": name, "market": "us" if currency == "USD" else "sz",
            "quote": {"current_price": 100, "change_pct": 1}, "metadata": {"currency": currency},
            "chart_series": [{"date": "2026-10-12", "close": 100}],
        }})
        deps.record_tool({"tool": "web_search", "data": [{
            "title": f"{name} equipment profile", "snippet": f"{name} manufactures semiconductor equipment.",
            "source": name, "url": f"https://example.org/{code}",
        }]})

    response = evidence_fallback(deps, "比较汇总未能完成；以下仅列出两家公司的部分证据。")
    assert "| 维度 | 北方华创 | Applied Materials |" in response.summary
    assert "| 公司业务来源 |" in response.summary
    assert "| 行情快照 |" not in response.summary
    assert len(response.evidence) == 2
    assert "财务" not in response.summary and not response.payload.get("sec_company")


def test_financial_comparison_fallback_keeps_both_sec_companies_and_requested_metrics():
    deps = dependencies(user_query="Compare AAPL and MSFT latest available annual revenue and operating cash flow")
    deps.language = "en-US"
    for code, name, revenue, cash in (("US.AAPL", "Apple Inc.", 1000, 400), ("US.MSFT", "Microsoft Corporation", 2000, 800)):
        data = {"company": {"name": name, "code": code}, "filings": [], "financials": []}
        for concept, value in (("Revenues", revenue), ("NetCashProvidedByUsedInOperatingActivities", cash)):
            data["financials"].append({"taxonomy": "us-gaap", "concept": concept, "unit": "USD", "val": value,
                "start": "2025-07-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-K",
                "url": f"https://example.org/{code}/{concept}"})
        deps.record_tool({"tool": "get_sec_company_data", "data": data})

    response = evidence_fallback(deps, "Synthesis unavailable")
    assert "Apple Inc." in response.summary and "Microsoft Corporation" in response.summary
    assert "Revenue" in response.summary and "Operating cash flow" in response.summary
    assert "1,000 USD" in response.summary and "2,000 USD" in response.summary
    assert "400 USD" in response.summary and "800 USD" in response.summary
    assert "periods, units, or accounting bases differ" not in response.summary
    assert len(response.evidence) == 4
    assert response.payload["_meta"]["synthesis_incomplete"]


def test_sec_tool_context_only_sends_requested_annual_facts():
    deps = dependencies(user_query="Compare latest available annual revenue and operating cash flow")
    data = {"company": {"name": "Apple", "code": "US.AAPL"}, "filings": [
        {"form": "10-K", "filed": "2026-08-01", "report_date": "2026-06-30", "accession": "one", "url": "https://example.org/filing"}],
        "financials": []}
    for concept, value, start, end in (
        ("Revenues", 1000, "2025-07-01", "2026-06-30"),
        ("Revenues", 250, "2026-04-01", "2026-06-30"),
        ("NetIncomeLoss", 200, "2025-07-01", "2026-06-30"),
        ("NetCashProvidedByUsedInOperatingActivities", 400, "2025-07-01", "2026-06-30"),
    ):
        data["financials"].append({"taxonomy": "us-gaap", "concept": concept, "unit": "USD", "val": value,
            "start": start, "end": end, "filed": "2026-08-01", "form": "10-K",
            "url": f"https://example.org/{concept}/{start}"})
    context = json.loads(deps.record_tool({"tool": "get_sec_company_data", "data": data}))
    assert {fact["concept"] for fact in context["data"]["financials"]} == {
        "Revenues", "NetCashProvidedByUsedInOperatingActivities"}
    assert all(fact["start"] == "2025-07-01" for fact in context["data"]["financials"])
    assert context["data"]["filings"] == []


def test_inline_citations_fill_missing_structured_evidence_and_financial_ids():
    deps = dependencies()
    deps.record_tool({"tool": "get_sec_company_data", "data": {
        "company": {"name": "Apple", "code": "US.AAPL"}, "filings": [],
        "financials": [{"taxonomy": "us-gaap", "concept": "Revenues", "unit": "USD", "val": 100,
            "start": "2026-01-01", "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q",
            "url": "https://example.org/apple-q1"}]}})
    fact_id = deps.tool_results[0]["evidence"][0]["id"]
    output = AgentOutput(summary=f"Revenue is reported in USD [{fact_id}].", evidence_ids=[], financial_fact_ids=[])
    validate_research_output(output, deps.tool_results)
    assert output.evidence_ids == [fact_id]
    assert output.financial_fact_ids == [fact_id]


def test_verified_pair_financial_values_are_rendered_by_comparison_card_not_repeated_in_prose():
    from tests.test_research_product import sec_fixture
    deps = dependencies(user_query="Compare AAPL and MSFT revenue")
    deps.language = "en-US"
    first = {"company": {"name": "Apple", "code": "US.AAPL"}, "filings": [], "financials": [
        {**sec_fixture()["financials"][0], "url": "https://example.org/aapl-revenue"}]}
    second = {"company": {"name": "Microsoft", "code": "US.MSFT"}, "filings": [], "financials": [
        {**first["financials"][0], "url": "https://example.org/msft-revenue", "val": 200}]}
    deps.record_tool({"tool": "get_sec_company_data", "data": first})
    deps.record_tool({"tool": "get_sec_company_data", "data": second})
    ids = [item["evidence"][0]["id"] for item in deps.tool_results]
    deps.record_tool({"tool": "compare_companies", "data": compare_sec_facts([first, second], metrics=["Revenue"])})
    output = AgentOutput(summary=f"Apple and Microsoft each reported revenue of USD 100 and USD 200 [{ids[0]}][{ids[1]}].",
                         evidence_ids=ids, financial_fact_ids=ids)
    validate_research_output(output, deps.tool_results, deps.user_query, deps.language)
    assert "USD 100" not in output.summary and "USD 200" not in output.summary
    assert "side-by-side comparison card" in output.summary


def test_broad_comparison_output_drops_stock_card_details_and_oversized_tables():
    quote_id, business_id = "ev_quote", "ev_business"
    output = AgentOutput(
        ui_components=["table", "comparison"],
        summary=(
            "两家公司已完成身份核验 [ev_quote]。\n\n"
            "| 维度 | 北方华创 | Applied Materials |\n| --- | --- | --- |\n"
            "| 最新价 | 587.98 CNY [ev_quote] | 497.53 USD [ev_quote] |\n"
            "| 产品与应用 | 半导体设备 [ev_business] | 半导体设备 [ev_business] |\n"
            "| 当日涨跌幅 | -1.02% [ev_quote] | -1.87% [ev_quote] |\n"
            "| 客户 | 未知 | 未知 |\n| 竞争位置 | 未知 | 未知 |\n| 风险 | 未知 | 未知 |\n"
            "市场数据已核验 [ev_quote]。近20个交易日表现分化 [ev_quote]。"
        ),
        evidence_ids=[quote_id, business_id],
    )
    compact_broad_comparison(output, [
        {"tool": "get_stock_analysis", "evidence": [{"id": quote_id}]},
        {"tool": "web_search", "evidence": [{"id": business_id}]},
    ], include_market_metrics=False)
    assert "587.98" not in output.summary and "497.53" not in output.summary
    assert "RSI" not in output.summary and "近20个交易日" not in output.summary
    assert "产品与应用" in output.summary and "客户" in output.summary
    assert "市场数据已核验" not in output.summary
    assert output.ui_components == ["table"]
    assert output.evidence_ids == [business_id]
    assert len([line for line in output.summary.splitlines() if line.startswith("|")]) <= 7


def test_deep_comparison_stops_repeating_a_search_provider_that_failed_for_both_sides():
    async def run():
        deps = dependencies(user_query="Compare North Huachuang and Applied Materials")
        deps.record_tool({"tool": "research_comparison", "data": {"companies": [
            {"identity": {"status": "ok", "name": "北方华创", "code": "SZ002371"},
             "business_search": {"status": "unavailable"}},
            {"identity": {"status": "ok", "name": "Applied Materials", "code": "US.AMAT"},
             "business_search": {"status": "unavailable"}},
        ]}})
        deps.record_tool({"tool": "web_search", "status": "unavailable", "data": [], "data_gaps": ["provider error"]})
        deps.record_tool({"tool": "web_search", "status": "unavailable", "data": [], "data_gaps": ["provider error"]})
        tools = [SimpleNamespace(name="web_search"), SimpleNamespace(name="read_public_source")]
        available = await ResearchCapability().prepare_tools(SimpleNamespace(deps=deps), tools)
        assert available == []
        assert deps.finish_reason == "source_provider_unavailable"
    asyncio.run(run())


def test_model_can_request_news_before_search_without_fatal_retry():
    async def run():
        deps = dependencies()
        requests = []
        def model(messages, info):
            requests.append(info)
            if len(requests) == 1:
                return ModelResponse(parts=[ToolCallPart("get_stock_news", {"stock_code": "US.MRNA"})])
            return ModelResponse(parts=[ToolCallPart("final_result", final(deps))])
        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "why moderna rise so fast recently?")
        assert [step.tool for step in response.research_steps] == ["search_stocks", "get_stock_news"]
        assert len(requests) == 2 and response.evidence
        assert deps.retrieval_count == 2
        assert "unavailable" not in response.summary.lower()
    asyncio.run(run())


def test_broad_cross_market_comparison_can_gather_followup_evidence_without_count_cap():
    async def run():
        deps = dependencies()
        deps.language = "zh-CN"
        deps.research_mode = "deep"
        identity_rows = {
            "北方华创": StockSearchResult(name="北方华创", code="sz002371", market="sz"),
            "AMAT": StockSearchResult(name="Applied Materials", code="US.AMAT", market="us"),
        }
        identity_queries = []
        def search_stocks(query, **kwargs):
            identity_queries.append(query)
            return [identity_rows["AMAT"] if "AMAT" in query.upper() else identity_rows["北方华创"]]

        def get_stock_analysis(code, include_ai=False):
            name = "Applied Materials" if code == "US.AMAT" else "北方华创"
            currency_price = 260.0 if code == "US.AMAT" else 587.98
            return StockAnalysisResponse(
                stock_name=name, stock_code=code, market="us" if code.startswith("US.") else "sz",
                quote=QuoteSnapshot(stock_name=name, stock_code=code, current_price=currency_price,
                    change=1.0, change_pct=0.4, open_price=currency_price, high_price=currency_price,
                    low_price=currency_price, volume=1000, amplitude_pct=0.5,
                    timestamp=datetime(2026, 10, 12, tzinfo=timezone.utc)),
                technical_indicators={}, signal_summary=SignalSummary(overall_score=60, overall_signal="neutral"),
                technical_commentary=[], ai_insight=AIInsight(enabled=False), chart_series=[{"date": "2026-10-12", "close": currency_price}],
                metadata={"data_as_of": "2026-10-12", "source": "Fixture market data"},
            )

        deps.stock_service = SimpleNamespace(search_stocks=search_stocks, get_stock_analysis=get_stock_analysis)
        deps.sec_service.resolve = lambda query, local_codes=None: {
            "status": "ok", "candidates": [{"name": "Applied Materials", "code": "US.AMAT", "market": "us", "identity_verified": True}]
        }
        def fixture_search_report(query, **kwargs):
            suffix = "followup" if "competitor positioning" in query else "profile"
            if kwargs["market"] == "us":
                good = {"id": f"us-{suffix}", "title": f"Applied Materials {suffix}: equipment products and markets",
                    "snippet": "Applied Materials (AMAT) serves semiconductor manufacturers. Fixture evidence only.",
                    "url": "https://ir.appliedmaterials.com/annual-report-proxy", "source": "Applied Materials IR"}
                fallback = {"id": f"us-{suffix}-independent", "title": "Applied Materials company profile",
                    "snippet": "Applied Materials (AMAT) serves semiconductor manufacturers. Independent fixture evidence only.",
                    "url": "https://www.forbes.com/companies/applied-materials", "source": "Forbes"}
                irrelevant = [
                    {"id": "wrong-applied", "title": "Applied Industrial Technologies", "snippet": "Industrial products", "url": "https://example.org/applied-industrial"},
                    {"id": "wrong-amazon", "title": "Amazon.com: Applied dog treats", "snippet": "Dog treats", "url": "https://example.org/dog-treats"},
                ]
            else:
                good = {"id": f"cn-{suffix}", "title": f"北方华创 {suffix}：产品与市场",
                    "snippet": "北方华创提供半导体设备。Fixture evidence only.",
                    "url": "https://static.cninfo.com.cn/report.pdf", "source": "CNINFO"}
                fallback = {"id": f"cn-{suffix}-independent", "title": "北方华创业务介绍",
                    "snippet": "北方华创半导体设备业务介绍。Independent fixture evidence only.",
                    "url": "https://vip.stock.finance.sina.com.cn/company", "source": "Sina"}
                irrelevant = []
            return {"results": [{**good,
                "published_at": "2026-10-01", "provider": "fixture", "query": query}, fallback, *irrelevant],
                "data_gaps": []}
        deps.web_search_service = SimpleNamespace(search_report=fixture_search_report)
        markets = []
        original_search_report = deps.web_search_service.search_report
        def search_report(query, **kwargs):
            markets.append(kwargs.get("market"))
            return original_search_report(query, **kwargs)
        deps.web_search_service.search_report = search_report
        reads = []
        def fixture_read(url, question):
            reads.append(url)
            if url == "https://ir.appliedmaterials.com/annual-report-proxy":
                raise SourceUnavailable("Source returned HTTP 403.")
            return {
                "url": url, "requested_url": url, "title": "Company business profile", "source": "Company profile fixture",
                "published_at": "2026-10-01", "fetched_at": "2026-10-12T00:00:00+00:00",
                "excerpts": [{"location": "paragraph 1", "text": f"Verified profile excerpt for {url}; evidence is limited to this company fixture."}],
                "data_gaps": ["Selected excerpt only."],
            }
        deps.document_reader = SimpleNamespace(read=fixture_read)

        requests = []
        def model(messages, info):
            requests.append(info)
            if len(requests) == 1:
                assert [tool.name for tool in info.function_tools] == ["research_comparison"]
                return ModelResponse(parts=[ToolCallPart("research_comparison", {
                    "companies": ["北方华创", "应用材料AMAT"],
                    "question": "Compare their products, end markets and stock profiles",
                })])
            if len(requests) == 2:
                assert {tool.name for tool in info.function_tools} == {"web_search", "read_public_source"}
                comparison = next(item for item in deps.tool_results if item["tool"] == "research_comparison")
                amat = next(company for company in comparison["data"]["companies"] if company["identity"]["code"] == "US.AMAT")
                assert [attempt["status"] for attempt in amat["source_read_attempts"]] == ["unavailable", "completed"]
                assert amat["source_read"]["data"]["url"] == "https://www.forbes.com/companies/applied-materials"
                return ModelResponse(parts=[ToolCallPart("web_search", {
                    "query": "Applied Materials competitor positioning and customer end markets",
                    "market": "us",
                })])
            if len(requests) == 3:
                assert {tool.name for tool in info.function_tools} == {"web_search", "read_public_source"}
                result = next(item for item in deps.tool_results if item["tool"] == "web_search" and
                    "competitor positioning" in item["data"][0]["query"])
                return ModelResponse(parts=[ToolCallPart("read_public_source", {
                    "url": result["data"][1]["url"],
                    "question": "Verify Applied Materials' competitor and customer positioning",
                })])
            assert len(requests) == 4
            read_sources = [source for item in deps.tool_results if item["tool"] == "read_public_source"
                for source in item.get("evidence", [])]
            north_source = next(source["id"] for source in read_sources if source["url"].endswith("cninfo.com.cn/report.pdf"))
            amat_source = next(source["id"] for source in read_sources if source["url"].endswith("forbes.com/companies/applied-materials"))
            return ModelResponse(parts=[ToolCallPart("final_result", {
                "summary": (
                    "两家公司均服务半导体制造商，但具体设备产品重合度仍需逐类核对。\n\n"
                    "| 维度 | 北方华创 | Applied Materials |\n| --- | --- | --- |\n"
                    f"| 产品与应用 | 来源节选 [{north_source}] | 来源节选 [{amat_source}] |"
                ),
                "evidence_ids": [north_source, amat_source],
                "ui_components": ["table", "comparison"],
                "data_gaps": ["Business profiles are excerpts; valuation and comparable financial periods were not retrieved."],
            })])

        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "你可以对比一下北方华创和应用材料amat这两只股票吗？")
        assert len(requests) == 4
        assert deps.retrieval_count == 10
        assert set(markets) == {"cn", "us"}
        assert set(identity_queries) == {"北方华创", "AMAT"}
        assert len(reads) == 3
        assert "| 北方华创 | Applied Materials |" in response.summary
        assert response.ui_components == ["table"]
        assert {row["stock_code"].upper() for row in response.payload["stocks"]} == {"SZ002371", "US.AMAT"}
        assert {step.tool for step in response.research_steps}.isdisjoint({"get_sec_company_data", "compare_companies"})
        assert response.payload["_meta"]["finish_reason"] == "completed"
        followup = next(item for item in deps.tool_results if item["tool"] == "web_search" and "competitor positioning" in item["data"][0]["query"])
        assert followup["data"][0]["url"] == "https://ir.appliedmaterials.com/annual-report-proxy"
        assert any(item["tool"] == "read_public_source" and
            item["data"].get("requested_url") == "https://www.forbes.com/companies/applied-materials" for item in deps.tool_results)
        assert all(source.excerpts for source in response.evidence if source.freshness == "source_excerpts")
    asyncio.run(run())


def test_comparison_identity_failure_asks_before_gathering_company_data():
    async def run():
        deps = dependencies()
        deps.language = "zh-CN"
        deps.stock_service.search_stocks = lambda query, **kwargs: (
            [StockSearchResult(name="北方华创", code="sz002371", market="sz")]
            if query == "北方华创" else []
        )
        deps.web_search_service = SimpleNamespace(search_report=lambda *a, **kw: pytest.fail("Do not research before identity is clear"))
        calls = []
        def model(messages, info):
            calls.append(info)
            if len(calls) == 1:
                return ModelResponse(parts=[ToolCallPart("research_comparison", {
                    "companies": ["北方华创", "不认识的公司"],
                })])
            return ModelResponse(parts=[ToolCallPart("final_result", {
                "summary": "请确认第二家公司。",
                "clarification": {"question": "你指的是哪家公司？", "options": ["Applied Materials（AMAT）", "其他公司或代码"]},
            })])

        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "比较北方华创和另一只股票")
        assert response.intent == "clarification" and response.clarification
        assert len(calls) == 2
        assert not any(item["tool"] in {"get_stock_analysis", "web_search", "read_public_source"} for item in deps.tool_results)
    asyncio.run(run())


def test_parallel_search_and_news_reuse_identity_and_deduplicate_reads():
    async def run():
        deps = dependencies()
        seen = []
        async def handler(args):
            seen.append(args)
            await asyncio.sleep(0)
            return "news record"
        capability = ResearchCapability()
        kw = {"call": None, "tool_def": SimpleNamespace(name="get_stock_news"), "args": {"stock_code": "US.MRNA"}, "handler": handler}
        assert await asyncio.gather(*(capability.wrap_tool_execute(SimpleNamespace(deps=deps), **kw) for _ in range(3))) == ["news record"] * 3
        assert len(seen) == 1
        assert len([item for item in deps.tool_results if item["tool"] == "search_stocks"]) == 1
        assert deps.retrieval_count == 2
    asyncio.run(run())


def test_ambiguous_or_unverified_identity_never_fetches_company_data():
    async def run():
        deps = dependencies()
        deps.sec_service.resolve = lambda *a: {"status": "ambiguous", "candidates": [{"code": "US.MRNA"}, {"code": "US.MRNL"}]}
        assert not await ensure_identity(deps, "US.MRNA")
        assert not deps.verified_us_codes
        calls = []
        async def handler(args):
            calls.append(args)
        result = await ResearchCapability().wrap_tool_execute(SimpleNamespace(deps=deps), call=None, tool_def=SimpleNamespace(name="get_stock_news"), args={"stock_code": "US.MRNA"}, handler=handler)
        assert json.loads(result)["status"] == "unavailable" and not calls
    asyncio.run(run())


def test_deep_specialists_share_usage_and_cannot_access_tools_or_mutations():
    async def run():
        deps = dependencies(research_mode="deep")
        requests = []
        def model(messages, info):
            requests.append([tool.name for tool in info.function_tools])
            if len(requests) == 1:
                return ModelResponse(parts=[ToolCallPart("research_company", {"company": "MRNA", "focus": "advantage"})])
            return ModelResponse(parts=[ToolCallPart("final_result", final(deps))])
        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "Research Moderna's industry advantage")
        assert len(requests) == 4  # Parent, two specialists, parent synthesis.
        assert requests[1] == requests[2] == []
        assert response.payload["_meta"]["usage"]["requests"] == 4
        assert response.payload["_meta"]["retrieval_calls"] == 6  # Compound, identity, news, SEC, two bounded web searches.
        assert {"review_company_position", "review_catalysts_risks", "research_company"} <= {step.tool for step in response.research_steps}
        assert response.evidence
        assert not deps.retrieval_tasks
    asyncio.run(run())


def test_deep_price_move_requires_catalyst_research_and_reads_two_source_angles():
    async def run():
        deps = dependencies(research_mode="deep")
        from tests.test_api_app import _make_stock_analysis
        deps.stock_service.get_stock_analysis = lambda code, include_ai=False: _make_stock_analysis(
            code, "Moderna", 62, "偏强", 225.0, 14.2
        )
        searches = []
        def search_report(query, **kwargs):
            searches.append(query)
            primary = "official" in query
            url = "https://moderna.com/press-release" if primary else "https://example.org/biotech-sector"
            return {"results": [{"id": f"result-{len(searches)}", "title": "Recent catalyst context",
                "snippet": "Fixture search evidence only.", "url": url, "source": "Research fixture",
                "published_at": "2026-10-10", "provider": "fixture", "query": query}], "data_gaps": []}
        deps.web_search_service = SimpleNamespace(search_report=search_report)
        reads = []
        deps.document_reader = SimpleNamespace(read=lambda url, question: reads.append(url) or {
            "url": url, "requested_url": url, "title": "Catalyst source fixture", "source": "Research fixture",
            "published_at": "2026-10-10", "fetched_at": "2026-10-12T00:00:00+00:00",
            "excerpts": [{"location": "paragraph 1", "text": f"Evidence excerpt for {url}; fixture only."}],
            "data_gaps": ["Selected excerpt only."],
        })
        requests = []
        def model(messages, info):
            requests.append(info)
            if len(requests) == 1:
                # The output validator must send the model back to research before
                # it can finalize a deep causal stock-move answer.
                return ModelResponse(parts=[ToolCallPart("final_result", {
                    "summary": "Moderna rose recently, but the source record is incomplete.",
                    "evidence_ids": [], "actions": [], "data_gaps": [],
                })])
            if info.function_tools == []:
                return ModelResponse(parts=[ToolCallPart("final_result", final(deps, "Evidence review completed."))])
            if any(tool.name == "research_company" for tool in info.function_tools) and not any(
                item.get("tool") == "research_company" for item in deps.tool_results
            ):
                return ModelResponse(parts=[ToolCallPart("research_company", {
                    "company": "MRNA", "focus": "catalysts",
                    "question": "why moderna stock rise so fast recently?",
                })])
            refs = [source["id"] for item in deps.tool_results for source in item.get("evidence", [])
                    if source.get("freshness") != "identity_mapping"]
            return ModelResponse(parts=[ToolCallPart("final_result", {
                "summary": f"Moderna's recent move has several plausible, time-aligned catalysts, but the sources do not prove causation [{refs[0]}].",
                "evidence_ids": refs, "data_gaps": ["No benchmark-relative return was retrieved."],
                "actions": [], "ui_components": [],
            })])

        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "why moderna stock rise so fast recently?")
        assert searches and len(searches) == 2 and searches[0] != searches[1]
        assert set(reads) == {"https://moderna.com/press-release", "https://example.org/biotech-sector"}
        assert {"research_company", "web_search", "read_public_source"} <= {step.tool for step in response.research_steps}
        assert response.payload["_meta"]["retrieval_calls"] >= 7
        assert "No benchmark-relative return" in " ".join(response.data_gaps)
        assert deps.evidence_review_only is False
    asyncio.run(run())


def test_quick_mode_has_no_delegation_tool_and_retrieval_has_no_count_cap():
    async def run():
        deps = dependencies()
        tools = [SimpleNamespace(name="research_company"), SimpleNamespace(name="search_stocks")]
        scoped = await ResearchCapability().prepare_tools(SimpleNamespace(deps=deps), tools)
        assert [tool.name for tool in scoped] == ["search_stocks"]
        for i in range(20):
            await deps.retrieve("read", {"i": i}, lambda: asyncio.sleep(0, result="record"))
        assert deps.retrieval_count == 20
        assert await deps.retrieve("read", {"i": 0}, lambda: pytest.fail("cached result must be reused")) == "record"
    asyncio.run(run())


def test_deep_review_uses_sec_facts_when_news_is_missing():
    from tests.test_research_product import sec_fixture
    async def run():
        deps = dependencies(research_mode="deep")
        deps.news_service.get_stock_news = lambda *a, **kw: []
        company = sec_fixture()
        company["company"].update(code="US.MRNA", name="Moderna")
        deps.sec_service.company = lambda *a: company
        requests = []
        def model(messages, info):
            requests.append(info)
            if len(requests) == 1:
                return ModelResponse(parts=[ToolCallPart("research_company", {"company": "MRNA", "focus": "advantage"})])
            return ModelResponse(parts=[ToolCallPart("final_result", final(deps))])
        agent = create_agent(api_key="offline", model="offline-model")
        agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "Review Moderna's financial resilience")
        assert len(requests) == 4
        assert {"review_company_position", "review_catalysts_risks"} <= {step.tool for step in response.research_steps}
        assert any(source.source.startswith("SEC") for source in response.evidence)
        assert any("get_stock_news" in gap for gap in response.data_gaps)
    asyncio.run(run())


def test_provider_failure_before_tools_still_recovers_source_data(monkeypatch):
    from tests.test_api_app import _make_stock_analysis
    deps = dependencies()
    queries, calls, quotes = [], [], []
    deps.stock_service.search_stocks = lambda query, **kwargs: queries.append(query) or [StockSearchResult(name="Moderna", code="US.MRNA", market="us")]
    def quote(code, include_ai=False):
        quotes.append((code, include_ai))
        return _make_stock_analysis(code, "Moderna", 2, "中性", 100, 2).model_copy(update={
            "market": "us", "metadata": {"currency": "USD", "data_as_of": "2026-10-09"},
        })
    deps.stock_service.get_stock_analysis = quote
    async def failed(*args, **kwargs):
        calls.append(True)
        raise RuntimeError("Offline provider failure")
    monkeypatch.setattr(main, "_get_pydantic_agent", lambda: (SimpleNamespace(), deps))
    monkeypatch.setattr(main, "_load_agent_runtime", lambda: (AgentDeps, create_agent, failed))
    response = asyncio.run(main._run_agent_request(AgentQuery(query="why moderna rise so fast recently?", language="en-US"), [], {}))
    assert calls == [True] and queries == ["moderna"]
    assert "Moderna research update" in response.summary
    assert {"search_stocks", "get_stock_news", "get_stock_analysis"} <= {step.tool for step in response.research_steps}
    assert response.payload["_meta"]["retrieval_calls"] == 3
    assert quotes == [("US.MRNA", False)]
    assert "100.0 USD" in response.summary and "2026-10-09" in response.summary
    assert response.payload["technical_commentary"][0].startswith("RSI (14)")
    assert response.payload["_meta"]["usage"]["requests"] == 0
    assert not response.payload["_meta"]["usage_unresolved"]


def test_failed_synthesis_preserves_news_and_does_not_retry_paid_run(monkeypatch):
    deps = dependencies()
    calls = []
    async def failed(*args, **kwargs):
        calls.append(True)
        deps.record_tool({"tool": "get_stock_news", "data": [row.model_dump() for row in deps.news_service.get_stock_news("US.MRNA")]})
        raise RuntimeError("Offline validation failure")
    monkeypatch.setattr(main, "_get_pydantic_agent", lambda: (SimpleNamespace(), deps))
    monkeypatch.setattr(main, "_load_agent_runtime", lambda: (AgentDeps, create_agent, failed))
    response = asyncio.run(main._run_agent_request(AgentQuery(query="why moderna rise so fast recently?", language="en-US"), [], {}))
    assert len(calls) == 1
    assert "Moderna research update" in response.summary
    assert "https://example.org/moderna" in response.summary
    assert "Open the research tools" not in response.summary
    assert response.payload["_meta"]["synthesis_incomplete"]
    assert response.evidence and response.research_steps


def test_deep_streaming_adapter_accounts_for_all_specialists(monkeypatch):
    """Exercise nested non-streaming reviews inside a real streamed parent run."""
    import httpx
    from openai import AsyncOpenAI
    from tests.test_agent_streaming import chunk
    async def run():
        deps = dependencies(research_mode="deep")
        requests, events = [], []
        class Stream(httpx.AsyncByteStream):
            def __init__(self, name, arguments):
                self.name, self.arguments = name, json.dumps(arguments)
            async def __aiter__(self):
                yield chunk({"role": "assistant", "reasoning_content": "private reasoning"})
                half = len(self.arguments) // 2
                yield chunk({"tool_calls": [{"index": 0, "id": "call_stream", "type": "function", "function": {"name": self.name, "arguments": self.arguments[:half]}}]})
                yield chunk({"tool_calls": [{"index": 0, "function": {"arguments": self.arguments[half:]}}]})
                yield chunk({}, "tool_calls", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
                yield b"data: [DONE]\n\n"
        def provider(request):
            body = json.loads(request.content)
            requests.append(body)
            name, arguments = ("research_company", {"company": "MRNA", "focus": "advantage"}) if len(requests) == 1 else ("final_result", final(deps))
            if body.get("stream"):
                return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Stream(name, arguments))
            return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "created": 0, "model": "deepseek-flash", "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": None, "tool_calls": [{"id": "call_review", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]}}], "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}})
        client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid", max_retries=0, http_client=httpx.AsyncClient(transport=httpx.MockTransport(provider)))
        monkeypatch.setattr("api.agent_pydantic.AsyncOpenAI", lambda **kwargs: client)
        agent = create_agent(api_key="offline", model="deepseek-flash")
        response = await run_agent_async(agent, deps, "Research Moderna's industry advantage", lambda *args: events.append(args))
        assert len(requests) == 4
        assert [body.get("stream", False) for body in requests] == [True, False, False, True]
        assert all(body.get("max_tokens", body.get("max_completion_tokens")) == 8000 for body in requests[1:3])
        assert all(body["thinking"]["type"] == "enabled" for body in requests[1:3])
        assert all(body["reasoning_effort"] == "high" for body in requests[1:3])
        assert response.payload["_meta"]["usage"] == {"requests": 4, "input_tokens": 400, "output_tokens": 200}
        assert any(event[0] == "check_facts" for event in events)
        assert not any(event[0] == "answer_delta" for event in events)
        assert "private reasoning" not in response.model_dump_json()
        await client.close()
    asyncio.run(run())


def test_cancellation_stops_nested_retrieval_tasks():
    async def run():
        deps = dependencies()
        started, stopped = asyncio.Event(), asyncio.Event()
        async def pending():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()
        task = asyncio.create_task(deps.retrieve("source", {}, pending))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert stopped.is_set() and not deps.retrieval_tasks
    asyncio.run(run())


def test_deep_research_reuses_matching_verified_identity_after_empty_search():
    async def run():
        deps = dependencies()
        await deps.retrieve("search_stocks", {"query": "MRNA", "limit": 5}, lambda: search_identity(deps, "MRNA"))
        deps.record_tool({"tool": "search_stocks", "data": []})
        deps.stock_service.search_stocks = lambda *a, **kw: pytest.fail("Already verified company should not be searched again")
        assert await collect_company_evidence(deps, "Moderna, Inc. (MRNA)", "overview") == "US.MRNA"
        assert deps.retrieval_count == 3  # Identity, news and SEC only.
        assert deps.cache_hits == ["search_stocks"]
    asyncio.run(run())


def test_compound_research_uses_its_own_result_not_last_parallel_search(monkeypatch):
    async def identity(deps, query, limit=5):
        deps.verified_us_codes.add("US.MRNA")
        result = deps.record_tool({"tool": "search_stocks", "data": [{"name": "Moderna", "code": "US.MRNA", "identity_verified": True}]})
        deps.record_tool({"tool": "search_stocks", "data": []})  # Another search completes meanwhile.
        return result
    monkeypatch.setattr("api.company_research.search_identity", identity)
    async def run():
        deps = dependencies()
        assert await collect_company_evidence(deps, "Moderna", "overview") == "US.MRNA"
    asyncio.run(run())


def test_cached_company_cannot_be_reused_for_another_company():
    async def run():
        deps = dependencies()
        await search_identity(deps, "MRNA")
        deps.stock_service.search_stocks = lambda *a, **kw: []
        deps.sec_service.resolve = lambda *a: {"status": "unavailable", "candidates": []}
        deps.news_service.get_stock_news = lambda *a, **kw: pytest.fail("Wrong company must not be fetched")
        assert await collect_company_evidence(deps, "NVIDIA", "overview") is None
        assert json.loads(deps.tool_context())["reason_code"] == "no_matches"
    asyncio.run(run())


def test_sec_identity_fallback_survives_primary_search_outage():
    async def run():
        deps = dependencies()
        def unavailable(*a, **kw): raise RuntimeError("offline primary outage")
        deps.stock_service.search_stocks = unavailable
        result = json.loads(await search_identity(deps, "Moderna, Inc. (MRNA)"))
        assert result["status"] == "completed" and result["data"][0]["code"] == "US.MRNA"
        assert deps.verified_us_codes == {"US.MRNA"}
    asyncio.run(run())


def test_failed_search_record_does_not_break_later_sec_tool():
    async def run():
        deps = dependencies()
        original = deps.stock_service.search_stocks
        sec_resolve = deps.sec_service.resolve
        def search(query, **kwargs):
            if query == "bad": raise RuntimeError("offline provider failure")
            return original(query, **kwargs)
        def resolve(query, *args):
            if query == "bad": raise RuntimeError("offline SEC failure")
            return sec_resolve(query, *args)
        deps.stock_service.search_stocks, deps.sec_service.resolve = search, resolve
        requests = []
        def model(messages, info):
            requests.append(info)
            if len(requests) == 1: return ModelResponse(parts=[ToolCallPart("search_stocks", {"query": "bad"})])
            if len(requests) == 2: return ModelResponse(parts=[ToolCallPart("search_stocks", {"query": "MRNA"})])
            if len(requests) == 3: return ModelResponse(parts=[ToolCallPart("get_sec_company_data", {"stock_code": "US.MRNA"}), ToolCallPart("get_stock_news", {"stock_code": "US.MRNA"})])
            return ModelResponse(parts=[ToolCallPart("final_result", final(deps))])
        agent = create_agent(api_key="offline", model="offline-model"); agent.model = FunctionModel(model)
        response = await run_agent_async(agent, deps, "Research Moderna")
        assert len(requests) == 4
        assert next(step for step in response.research_steps if step.tool == "get_sec_company_data").status == "completed"
        assert response.research_steps[0].reason_code == "provider_error"
        assert verified_name(deps, "US.MRNA") == "Moderna"
    asyncio.run(run())


def test_cached_failed_result_never_reports_success():
    async def run():
        deps = dependencies(); events = []
        deps.progress_callback = lambda *args: events.append(args)
        async def failed(): return deps.record_tool({"tool": "get_stock_news", "status": "unavailable", "data": {"data_gaps": ["offline outage"]}})
        await deps.retrieve("get_stock_news", {"stock_code": "US.MRNA"}, failed)
        await deps.retrieve("get_stock_news", {"stock_code": "US.MRNA"}, lambda: pytest.fail("Failed result must not be repeatedly fetched"))
        assert events[-1][0] == "tool_error" and events[-1][3]["reason_code"] == "provider_error"
    asyncio.run(run())


def test_empty_news_is_a_successful_read_with_no_results():
    from api.agent_pydantic import build_agent_response, AgentOutput
    deps = dependencies()
    deps.record_tool({"tool": "get_stock_news", "data": []})
    response = build_agent_response(AgentOutput(summary="No company news returned", actions=[], evidence_ids=[], data_gaps=[]), deps.tool_results, "en-US")
    assert response.research_steps[0].status == "completed" and response.research_steps[0].reason_code == "no_results"
    assert any("no matching data" in gap for gap in response.data_gaps)


def test_comparison_and_parallel_sec_reads_share_admission_and_sources():
    from tests.test_research_product import sec_fixture
    import time
    async def run():
        deps = dependencies(); calls, requests = [], []
        deps.stock_service.search_stocks = lambda query, **kw: [StockSearchResult(name=query, code=query, market="us")]
        deps.sec_service.resolve = lambda query, *a: {"status": "ok", "candidates": [{"name": query, "code": query, "market": "us", "identity_verified": True}]}
        def company(code):
            calls.append(code); time.sleep(.01)
            result = sec_fixture(); result["company"].update(code=code, name=code)
            result["financials"].append({**result["financials"][0], "start": "2025-01-01", "end": "2025-12-31", "val": 400})
            for i, fact in enumerate(result["financials"]): fact["url"] = f"https://example.org/offline/{code}/{i}"
            for i, filing in enumerate(result["filings"]): filing["url"] = f"https://example.org/offline/{code}/filing/{i}"
            return result
        deps.sec_service.company = company
        def model(messages, info):
            requests.append(info)
            if len(requests) == 1: return ModelResponse(parts=[ToolCallPart("search_stocks", {"query": "US.AAPL"}), ToolCallPart("search_stocks", {"query": "US.MSFT"})])
            if len(requests) == 2: return ModelResponse(parts=[ToolCallPart("compare_companies", {"stock_codes": ["US.AAPL", "US.MSFT"]})])
            return ModelResponse(parts=[ToolCallPart("final_result", final(deps))])
        agent = create_agent(api_key="offline", model="offline-model"); agent.model = FunctionModel(model)
        response = await asyncio.wait_for(run_agent_async(agent, deps, "Compare Apple and Microsoft annual revenue and operating cash flow"), timeout=5)
        assert sorted(calls) == ["US.AAPL", "US.MSFT"]
        assert deps.retrieval_count == 5  # Two identities, compound operation, two actual SEC reads.
        assert next(step for step in response.research_steps if step.tool == "compare_companies").status == "completed"
        assert len(response.payload["financial_comparison"]["companies"]) == 2
        assert [row["metric"] for row in response.payload["financial_comparison"]["metrics"]] == ["Revenue", "Operating cash flow"]
        assert response.ui_components == ["comparison"]
    asyncio.run(run())


def test_watchlist_add_waits_for_inflight_identity_without_caching_mutation():
    async def run():
        deps = dependencies(); started, release = asyncio.Event(), asyncio.Event(); calls = []
        async def search():
            started.set(); await release.wait(); return await search_identity(deps, "MRNA")
        pending = asyncio.create_task(deps.retrieve("search_stocks", {"query": "MRNA", "limit": 5}, search))
        await started.wait()
        async def mutation(args): calls.append(args); return "saved"
        capability = ResearchCapability()
        task = asyncio.create_task(capability.wrap_tool_execute(SimpleNamespace(deps=deps), call=None, tool_def=SimpleNamespace(name="manage_watchlist"), args={"action":"add","stock_code":"US.MRNA"}, handler=mutation))
        await asyncio.sleep(0); assert not calls
        release.set(); await pending; assert await task == "saved" and len(calls) == 1
        assert all('manage_watchlist' not in key for key in deps.retrieval_cache)
    asyncio.run(run())
