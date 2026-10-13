"""Offline behavior tests for the bilingual, budget-bounded Pydantic research path."""
import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from openai import AsyncOpenAI

from api.agent_pydantic import AgentDeps, AgentOutput, _is_stock_price_move_question, build_agent_response, create_agent, run_agent_async, validate_research_output
from api.financial_comparison import compare_sec_facts
from api.research_capability import ResearchCapability
from pydantic_ai import ModelRetry
from api.localization import resolve_language
from api.localization import localize_market, localize_stock_analysis, validate_response_language
from api.schemas import AgentQuery, StockSearchResult
from api.sec import SecCompanyService, curate_sec
from api.sse import iter_sse
from ashare.config import Config
from ashare.search import StockSearcher


@pytest.mark.parametrize("query,preference,expected", [
    ("Research AAPL earnings", "auto", "en-US"),
    ("分析苹果财报", "auto", "zh-CN"),
    ("分析苹果，输出英文", "zh-CN", "en-US"),
    ("Research AAPL in Chinese", "en-US", "zh-CN"),
    ("AAPL", "zh-CN", "zh-CN"),
    ("分析苹果", "en-US", "en-US"),
])
def test_language_selection(query, preference, expected):
    assert resolve_language(query, preference) == expected


def test_default_model_and_english_company_names(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    assert Config().llm_model == "deepseek-flash"
    searcher = StockSearcher()
    assert searcher.search_stocks("NVIDIA", 1)[0]["code"] == "US.NVDA"
    assert searcher.search_stocks("Apple", 1)[0]["code"] == "US.AAPL"
    assert searcher.search_stocks("Berkshire Hathaway", 1)[0]["code"] == "US.BRK.B"


def test_api_rejects_unsupported_mode():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AgentQuery(query="AAPL", research_mode="unlimited")


def test_stock_price_move_intent_detection_is_company_agnostic():
    assert _is_stock_price_move_question("why moderna stock rise so fast recently?")
    assert _is_stock_price_move_question("为什么北方华创股价最近涨这么快？")
    assert not _is_stock_price_move_question("show me the latest Moderna news")


def sec_fixture(unit="USD"):
    return {"company": {"name": "Apple fixture", "code": "US.AAPL", "cik": "0000320193"},
            "filings": [], "financials": [{"taxonomy": "us-gaap", "concept": "Revenues", "unit": unit, "val": 100,
                "start": "2026-01-01", "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q",
                "accession": "0000320193-26-000001", "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/0000320193-26-000001-index.html"}],
            "data_gaps": ["Fixture; not live financial data."], "retrieved_at": "2026-10-11T00:00:00Z"}


@pytest.mark.parametrize("mode", ["quick", "deep"])
@pytest.mark.parametrize("input_tokens", [100, 20000])
def test_real_pydantic_tool_roundtrip_and_thinking_protocol(monkeypatch, tmp_path, mode, input_tokens):
    """Exercise the installed Pydantic/OpenAI adapter using a mock HTTP provider."""
    monkeypatch.setenv("RESEARCH_RUN_DIR", str(tmp_path))
    async def scenario():
        requests = []
        deps = AgentDeps(stock_service=SimpleNamespace(search_stocks=lambda *a, **k: [StockSearchResult(name="Apple", code="US.AAPL", market="us")]),
            news_service=SimpleNamespace(), hotspot_service=SimpleNamespace(), portfolio_service=SimpleNamespace(), web_search_service=SimpleNamespace(),
            language="en-US", research_mode=mode,
            sec_service=SimpleNamespace(resolve=lambda *a: {"candidates": [{"name": "Apple", "code": "US.AAPL", "market": "us", "identity_verified": True}]}, company=lambda *a: sec_fixture()))
        def handler(request):
            body = json.loads(request.content)
            requests.append(body)
            if len(requests) == 1:
                name, arguments = "search_stocks", {"query": "AAPL"}
            elif len(requests) == 2:
                name, arguments = "get_sec_company_data", {"stock_code": "US.AAPL"}
            else:
                name = next(t["function"]["name"] for t in body["tools"] if "summary" in t["function"]["parameters"].get("properties", {}))
                fact_id = deps.tool_results[-1]["evidence"][0]["id"]
                arguments = {"summary": f"## Financial facts\nReported revenue is shown in the original units [{fact_id}].",
                             "actions": [], "financial_fact_ids": [fact_id], "evidence_ids": [v["id"] for item in deps.tool_results for v in item.get("evidence", [])], "data_gaps": ["Fixture data."]}
            return httpx.Response(200, json={"id": "mock", "object": "chat.completion", "created": 0, "model": "deepseek-flash", "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": None, "reasoning_content": "private model reasoning", "tool_calls": [{"id": f"call_{len(requests)}", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]}}], "usage": {"prompt_tokens": input_tokens, "completion_tokens": 50, "total_tokens": input_tokens + 50}})
        client = AsyncOpenAI(api_key="test-key", base_url="https://api.deepseek.com", max_retries=0, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        monkeypatch.setattr("api.agent_pydantic.AsyncOpenAI", lambda **kw: client)
        agent = create_agent(api_key="test-key", model="deepseek-flash")
        response = await run_agent_async(agent, deps, "Research AAPL earnings")
        assert len(requests) == 3
        assert requests[0]["model"] == "deepseek-flash"
        assert requests[0]["thinking"]["type"] == ("enabled" if mode == "deep" else "disabled")
        if mode == "quick":
            prompt = '\n'.join(str(message.get('content', '')) for message in requests[0]['messages'])
            assert 'Quick research workflow' in prompt and '80-160 English words' in prompt
            assert 'specific gap' in prompt and 'Do not repeat failed searches' in prompt
            assert requests[0].get('max_tokens', requests[0].get('max_completion_tokens')) == 2500
        if mode == "deep":
            assert requests[0]["reasoning_effort"] == "high"
            assert any(m.get("reasoning_content") for m in requests[1]["messages"])
        assert response.payload["sec_company"]["financials"][0]["unit"] == "USD"
        assert response.evidence and response.research_steps
        assert "private model reasoning" not in response.model_dump_json()
        assert response.payload["_meta"]["usage"]["requests"] == 3
        assert response.payload["_meta"]["usage"]["input_tokens"] == input_tokens * 3
        assert response.payload["_meta"]["usage"]["output_tokens"] == 150
        assert response.payload["_meta"]["finish_reason"] == "completed"
        assert "100 USD" in response.summary and "2026-01-01 → 2026-03-31" in response.summary
        await client.close()
    asyncio.run(scenario())


def test_sec_units_periods_and_cash_flow_are_preserved():
    facts = {"facts": {"ifrs-full": {concept: {"units": {unit: [{"val": value, "start": "2025-01-01", "end": "2025-12-31", "filed": "2026-04-01", "form": "20-F", "accn": "0000000001-26-000001"}]}}
             for concept, unit, value in [("Revenue", "TWD", 123), ("CashFlowsFromUsedInOperatingActivities", "TWD", 42)]}}}
    _, financials = curate_sec({}, facts, "0000000001")
    assert {v["concept"] for v in financials} == {"Revenue", "CashFlowsFromUsedInOperatingActivities"}
    assert all(v["unit"] == "TWD" and v["start"] == "2025-01-01" for v in financials)


def test_sec_curation_retains_annual_facts_alongside_newer_interim_periods():
    records = [
        {"start": "2026-04-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q", "accn": "0000000001-26-000001", "val": 30},
        {"start": "2026-01-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q", "accn": "0000000001-26-000002", "val": 60},
        {"start": "2026-01-01", "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q", "accn": "0000000001-26-000003", "val": 25},
        {"start": "2025-10-01", "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q", "accn": "0000000001-26-000004", "val": 55},
        {"start": "2024-10-01", "end": "2025-09-30", "filed": "2025-11-01", "form": "10-K", "accn": "0000000001-25-000001", "val": 365},
    ]
    _, financials = curate_sec({}, {"facts": {"us-gaap": {"Revenues": {"units": {"USD": records}}}}, "retrieved_at": "2026-10-13T00:00:00Z"}, "0000000001")
    assert any(row["start"] == "2024-10-01" and row["end"] == "2025-09-30" for row in financials)
    assert any(row["start"] == "2026-04-01" and row["end"] == "2026-06-30" for row in financials)


def test_sec_cache_and_ambiguous_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "Research test@example.com")
    calls = []
    response = SimpleNamespace(status_code=200, headers={}, raise_for_status=lambda: None,
        json=lambda: {"0": {"ticker": "UAL", "title": "United Airlines", "cik_str": 1}, "1": {"ticker": "UPS", "title": "United Parcel Service", "cik_str": 2}})
    service = SecCompanyService(tmp_path, http=SimpleNamespace(get=lambda *a, **kw: calls.append(kw) or response))
    assert service.resolve("United")["status"] == "ambiguous"
    assert service.resolve("UAL")["status"] == "ok"
    assert len(calls) == 1


def test_unknown_sec_contact_is_an_explicit_gap(monkeypatch, tmp_path):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(ValueError, match="contact"):
        SecCompanyService(tmp_path).resolve("AAPL")


def test_english_summary_is_not_truncated_at_chinese_length():
    text = "## Research\n" + "Evidence-based finding. " * 60
    response = build_agent_response(AgentOutput(summary=text), [])
    assert response.summary == text.strip()


def test_no_data_preserves_unavailable_step():
    deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
    deps.record_tool({"tool": "get_sec_company_data", "status": "unavailable", "data": {"data_gaps": ["Unavailable"]}})
    response = build_agent_response(AgentOutput(summary="No SEC data", data_gaps=["Unavailable"]), deps.tool_results)
    assert response.research_steps[0].status == "unavailable"
    assert not response.evidence
    assert "sec_company" not in response.payload
    assert not response.citations


def test_tool_gaps_survive_missing_model_gap_labels():
    deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
    deps.record_tool({"tool": "get_sec_company_data", "data": sec_fixture()})
    deps.record_tool({"tool": "get_stock_news", "data": []})
    response = build_agent_response(AgentOutput(summary="Limited research"), deps.tool_results)
    assert any("full filing" in gap or "Fixture" in gap for gap in response.data_gaps)
    assert any("get_stock_news" in gap for gap in response.data_gaps)


def test_closing_event_stream_cancels_worker():
    async def scenario():
        cancelled = asyncio.Event()
        async def worker():
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        task = asyncio.create_task(worker())
        await asyncio.sleep(0)
        queue = asyncio.Queue()
        await queue.put("data: fixture\n\n")
        stream = iter_sse(queue, task)
        assert await anext(stream) == "data: fixture\n\n"
        await stream.aclose()
        assert task.cancelled() and cancelled.is_set()
    asyncio.run(scenario())


@pytest.mark.parametrize("change,note", [
    ({"unit": "TWD"}, "currencies"),
    ({"start": "2025-01-01"}, "periods"),
    ({"taxonomy": "ifrs-full"}, "taxonomies"),
    ({"start": "unknown"}, "metadata"),
])
def test_comparison_refuses_incompatible_facts(change, note):
    first, second = sec_fixture(), sec_fixture()
    second["company"]["code"] = "US.MSFT"
    second["financials"][0].update(change)
    row = compare_sec_facts([first, second])["metrics"][0]
    assert not row["comparable"] and note in row["comparison_note"]
    assert row["values"][1]["fact"] == second["financials"][0]


def test_comparison_preserves_missing_metric_instead_of_zero():
    first, second = sec_fixture(), sec_fixture()
    second["financials"] = []
    row = compare_sec_facts([first, second])["metrics"][0]
    assert row["values"][1]["fact"] is None and not row["comparable"]


def test_annual_comparison_selects_only_full_year_sec_facts():
    first, second = sec_fixture(), sec_fixture()
    second["company"]["code"] = "US.MSFT"
    first["financials"].append({**first["financials"][0], "start": "2025-01-01", "end": "2025-12-31", "val": 400})
    second["financials"].append({**second["financials"][0], "start": "2025-01-01", "end": "2025-12-31", "val": 500})
    row = compare_sec_facts([first, second], metrics=["Revenue"], annual=True)["metrics"][0]
    assert row["values"][0]["fact"]["val"] == 400
    assert row["values"][1]["fact"]["val"] == 500
    assert row["comparable"]
    no_annual = compare_sec_facts([sec_fixture(), second], metrics=["Revenue"], annual=True)["metrics"][0]
    assert no_annual["values"][0]["fact"] is None and not no_annual["comparable"]


def test_v2_capability_scopes_and_reuses_tool_execution():
    async def scenario():
        deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
        ctx = SimpleNamespace(deps=deps)
        capability = ResearchCapability()
        tools = [SimpleNamespace(name=name) for name in ["search_stocks", "get_sec_company_data", "compare_companies"]]
        assert [t.name for t in await capability.prepare_tools(ctx, tools)] == ["search_stocks"]
        deps.verified_us_codes.update(["US.AAPL", "US.MSFT"])
        assert len(await capability.prepare_tools(ctx, tools)) == 3
        called = []
        async def handler(args):
            called.append(args)
            await asyncio.sleep(0)
            return "cached factual record"
        kw = {"call": None, "tool_def": tools[1], "args": {"stock_code": "US.AAPL"}, "handler": handler}
        missing = json.loads(await capability.wrap_tool_execute(ctx, **kw))
        assert missing["status"] == "unavailable" and not called
        deps.tool_results.append({"tool": "search_stocks", "data": [{"code": "US.AAPL"}]})
        results = await asyncio.gather(capability.wrap_tool_execute(ctx, **kw), capability.wrap_tool_execute(ctx, **kw))
        assert results == ["cached factual record"] * 2 and len(called) == 1
        assert deps.cache_hits == ["get_sec_company_data"]
    asyncio.run(scenario())


def test_financial_output_guards_citations_and_original_figures():
    deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
    deps.record_tool({"tool": "get_sec_company_data", "data": sec_fixture("TWD")})
    fact_id = deps.tool_results[0]["evidence"][0]["id"]
    output = AgentOutput(summary=f"## Findings\nOriginal reporting units retained [{fact_id}].", evidence_ids=[fact_id], financial_fact_ids=[fact_id])
    assert validate_research_output(output, deps.tool_results) is output
    response = build_agent_response(output, deps.tool_results)
    assert "100 TWD" in response.summary and "2026-01-01 → 2026-03-31" in response.summary and "2026-05-01" in response.summary
    for invalid in [f"Revenue USD 100 [{fact_id}]", f"Revenue 2.894 万亿 [{fact_id}]", "Unknown source [ev_fake]"]:
        with pytest.raises(ModelRetry):
            validate_research_output(output.model_copy(update={"summary": invalid}), deps.tool_results)
    missing_selection = output.model_copy(update={"financial_fact_ids": []})
    validate_research_output(missing_selection, deps.tool_results)
    assert missing_selection.financial_fact_ids == [fact_id]


def test_growth_claim_requires_aligned_periods():
    deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
    data = sec_fixture()
    first = data["financials"][0]
    data["financials"].append({**first, "start": "2025-07-01", "end": "2025-12-31", "val": 80})
    deps.record_tool({"tool": "get_sec_company_data", "data": data})
    ids = [item["id"] for item in deps.tool_results[0]["evidence"]]
    output = AgentOutput(summary=f"Revenue grew [{ids[0]}][{ids[1]}].", evidence_ids=ids, financial_fact_ids=ids)
    with pytest.raises(ModelRetry, match="growth/trend"):
        validate_research_output(output, deps.tool_results)


def test_comparison_context_carries_exact_source_ids_without_refetch():
    deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
    companies = [sec_fixture(), sec_fixture("TWD")]
    companies[1]["company"]["code"] = "US.MSFT"
    for company in companies:
        deps.record_tool({"tool": "get_sec_company_data", "data": company})
    context = json.loads(deps.record_tool({"tool": "compare_companies", "data": compare_sec_facts(companies)}))
    values = context["data"]["metrics"][0]["values"]
    assert all(value["evidence_id"] in {ref["id"] for item in deps.tool_results for ref in item["evidence"]} for value in values)
    assert {value["fact"]["unit"] for value in values} == {"USD", "TWD"}
    assert not context["data"]["metrics"][0]["comparable"]
    assert "url" not in values[0]["fact"]
    assert companies[0]["financials"][0]["url"].startswith("https://")


def test_token_limit_preserves_retrieved_evidence_without_retry(monkeypatch):
    from api import main
    from api.agent_pydantic import UsageLimitExceeded
    deps = AgentDeps(*[SimpleNamespace() for _ in range(5)])
    calls = []
    async def limited(*args, **kwargs):
        calls.append(True)
        deps.run_usage.requests = 2
        deps.run_usage.input_tokens = 100
        deps.run_usage.output_tokens = 20
        deps.retrieval_count = 20
        deps.finish_reason = "token_limit"
        deps.record_tool({"tool": "get_sec_company_data", "data": sec_fixture()})
        raise UsageLimitExceeded("Research reached the token limit.")
    monkeypatch.setattr(main, "_get_pydantic_agent", lambda: (SimpleNamespace(), deps))
    monkeypatch.setattr(main, "_load_agent_runtime", lambda: (AgentDeps, create_agent, limited))
    response = asyncio.run(main._run_agent_request(AgentQuery(query="Research AAPL earnings", language="en-US"), [], {}))
    assert len(calls) == 1 and response.intent == "error"
    assert response.payload["_meta"]["limit_reached"] and response.payload["_meta"]["usage_unresolved"]
    assert response.payload["_meta"]["limit_reason"] == "token_limit"
    assert "token limit" in response.summary and "interpretation is incomplete" in response.summary
    assert response.payload["_meta"]["usage"] == {"requests": 2, "input_tokens": 100, "output_tokens": 20}
    assert response.evidence and response.payload["sec_company"]["financials"][0]["unit"] == "USD"


def test_market_regions_are_independent_and_us_instruments_are_explicit_proxies():
    from api.services import MarketService, MARKET_REGIME_UNIVERSES
    from api.schemas import MarketIndexSnapshot
    service = MarketService(SimpleNamespace())
    seen = []
    def snapshot(code, name):
        seen.append(code)
        return MarketIndexSnapshot(stock_code=code, stock_name=name, current_price=100, change_pct=1,
            above_ma20=True, above_ma60=True, trend_score=75, currency="USD", data_as_of="2026-10-09", is_proxy=code.startswith("US."))
    service._build_index_snapshot = snapshot
    us = service._compute_market_regime("us")
    assert seen == ["US.SPY", "US.QQQ", "US.DIA"]
    assert us.market == "us" and all(i.is_proxy and i.data_as_of == "2026-10-09" for i in us.indices)
    service._response_cache.set("market_regime:us", us, 120)
    service._start_background_refresh = lambda market: None
    china = service.get_market_regime("a_share")
    assert china.is_loading and china.indices == [] and china.market == "a_share"
    assert service.get_market_regime("us") == us
    assert not any(code.startswith("US.") for code, _ in MARKET_REGIME_UNIVERSES["a_share"])


def test_unavailable_market_is_explicit_and_missing_indicators_do_not_create_a_trend():
    from api.services import MarketService
    analysis = SimpleNamespace(quote=SimpleNamespace(current_price=100),technical_indicators={"MA20":None,"MA60":None})
    service = MarketService(SimpleNamespace(get_stock_analysis=lambda *a,**k: analysis))
    market = service._compute_market_regime("us")
    assert market.status == "unavailable" and not market.is_loading
    assert len(market.data_gaps) == 3 and market.indices == []
    english = localize_market(market, "en-US")
    assert "not enough evidence" in english.summary and not english.position_guidance


def test_english_price_notes_preserve_original_values_and_dates():
    from api.schemas import StockAnalysisResponse
    analysis = StockAnalysisResponse(stock_code="US.MU",stock_name="Micron",market="us",
        quote={"stock_name":"Micron","stock_code":"US.MU","current_price":123.45,"change":-0.74,"change_pct":-0.6,"open_price":124,"high_price":125,"low_price":120,"volume":19853000,"amplitude_pct":3.59,"timestamp":"2026-10-09T20:00:00Z"},
        technical_indicators={"RSI":50.2,"MACD":-12.6,"MA20":130},signal_summary={"overall_signal":"中性","overall_score":2},
        technical_commentary=["RSI位于中性区间，短线偏震荡"],ai_insight={"enabled":False},chart_series=[{"date":"2026-10-09"}],metadata={"currency":"USD"})
    localized = localize_stock_analysis(analysis,"en-US")
    assert "neutral range" in localized.technical_commentary[0]
    assert localized.quote == analysis.quote and localized.chart_series == analysis.chart_series and localized.metadata == analysis.metadata
    assert analysis.technical_commentary[0].startswith("RSI位于")


def test_english_output_cannot_silently_revert_to_chinese():
    with pytest.raises(ValueError,match="Use English"):
        validate_response_language(AgentOutput(summary="美光科技当前技术面偏弱，市场存在较大的风险，需要仔细核验数据。"),"en-US")
    assert validate_response_language(AgentOutput(summary="Micron (美光科技) has limited source coverage."),"en-US")


def test_fund_flow_alerts_are_not_promoted_to_global_news():
    from api.services import NewsService
    service = NewsService()
    service.state_store = SimpleNamespace(get_recent_alerts=lambda **k: [{"event_type":"fund_flow","title":"资金流追踪 | 海光信息"}])
    assert service._global_news_from_alerts(min_impact=1) == []


def test_us_news_retains_source_urls_and_declares_basket_coverage(monkeypatch):
    from api.services import NewsService
    from api.schemas import NewsItem
    service = NewsService()
    def stock_news(code, **kwargs):
        return [NewsItem(id=code,stock_code=code,stock_name=code,source="Fixture provider",published_at="2026-10-09",title="Company &amp; earnings",summary="Original provider summary",url="https://example.com/one-source")]
    monkeypatch.setattr(service,"get_stock_news",stock_news)
    news = service.get_global_news(market="us")
    assert len(news) == 1 and news[0].title == "Company & earnings"
    assert news[0].url == "https://example.com/one-source"
    assert "not comprehensive" in news[0].raw_payload["coverage"]
    assert news[0].related_symbols == []


def test_us_news_company_association_requires_a_source_mention(monkeypatch):
    from api.services import NewsService
    from api.schemas import NewsItem
    service = NewsService()
    def stock_news(code, **kwargs):
        return [NewsItem(id="gas",stock_code=code,stock_name=code,source="Fixture",published_at="2026-10-09",title="Natural Gas Pipeline Stocks",summary="Energy market coverage",url="https://example.com/gas"),
                NewsItem(id="apple",stock_code=code,stock_name=code,source="Fixture",published_at="2026-10-09",title="Apple earnings update",summary="Microsoft comparison",url="https://example.com/apple")]
    monkeypatch.setattr(service, "get_stock_news", stock_news)
    news = {item.id: item for item in service.get_global_news(market="us")}
    assert news["gas"].related_symbols == [] and news["gas"].category == "market"
    assert news["apple"].related_symbols == ["US.AAPL", "US.MSFT"]
    assert "US.NVDA" not in news["apple"].related_symbols


def test_portfolio_never_aggregates_different_currencies():
    from api.services import PortfolioService
    from api.schemas import PortfolioPosition, SignalSummary
    from api.localization import localize_portfolio
    positions = [PortfolioPosition(stock_code="US.AAPL",stock_name="Apple",quantity=10,cost_price=90),
                 PortfolioPosition(stock_code="sh600036",stock_name="招商银行",quantity=100,cost_price=30)]
    signals = SignalSummary(overall_score=2,overall_signal="中性")
    def analyze(code, **kwargs):
        return SimpleNamespace(quote=SimpleNamespace(current_price=100 if code.startswith("US.") else 35),
            signal_summary=signals,metadata={"currency":"USD" if code.startswith("US.") else "CNY", "data_as_of":"2026-10-09"})
    service = PortfolioService(analysis_service=SimpleNamespace(get_stock_analysis=analyze))
    service.store = SimpleNamespace(list_positions=lambda: positions)
    result = service.analyze_portfolio()
    assert not result.aggregation_available and result.currency is None
    assert result.total_market_value == result.total_pnl == 0 and result.data_gaps
    assert {item.currency for item in result.positions} == {"USD", "CNY"}
    assert result.positions[0].market_value == 1000 and result.positions[1].market_value == 3500
    english = localize_portfolio(result,"en-US")
    assert english.rebalance_suggestions[0].startswith("The portfolio")
    response = build_agent_response(AgentOutput(summary="Mixed currencies; aggregate values unavailable."), [{"tool":"get_portfolio_analysis","data":english.model_dump()}], "en-US")
    assert response.payload["aggregation_available"] is False and response.payload["data_gaps"]
    service.store = SimpleNamespace(list_positions=lambda: positions[:1])
    single = service.analyze_portfolio()
    assert single.aggregation_available and single.currency == "USD" and single.total_market_value == 1000
