"""Conversation regressions; all model and source responses are offline fixtures."""
import asyncio
from types import SimpleNamespace

import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from api.agent_pydantic import AgentDeps, AgentOutput, create_agent, run_agent_async, validate_research_output, _remove_financial_detail_lines, requests_detailed_research
from api.comparison_research import is_company_news_query, is_broad_stock_comparison, is_financial_stock_comparison
from api.evidence import sources_for_tool
from api.schemas import NewsItem, StockSearchResult
from api.main import _build_enriched_agent_query
from api.schemas import AgentHistoryTurn

QUESTION = ('Research NVIDIA (NVDA) for a first-pass investor brief. Find the latest available company filings, '
            'earnings materials, and dated news. Separate source-backed facts from inference, link sources, '
            'flag any unavailable data, and do not recommend buying or selling.')


def fixtures(sec_outage=False):
    def company(code):
        if sec_outage:
            raise RuntimeError('Offline SEC outage')
        return {'company': {'code': code, 'name': 'NVIDIA', 'cik': '0001045810'},
                'filings': [{'form': '10-Q', 'filed': '2026-08-26', 'report_date': '2026-07-26',
                             'url': 'https://www.sec.gov/Archives/edgar/fixture-nvda-index.html'}],
                'financials': [], 'data_gaps': ['Fixture filing metadata; no complete narrative.']}
    def read(url, question):
        return {'url': url, 'title': 'NVIDIA earnings fixture', 'published_at': '2026-08-27',
                'excerpts': [{'location': 'paragraph 1', 'text': 'Offline earnings evidence only.'}],
                'data_gaps': ['Selected fixture excerpts.']}
    return AgentDeps(
        stock_service=SimpleNamespace(search_stocks=lambda *a, **kw: [StockSearchResult(code='US.NVDA', name='NVIDIA', market='us')]),
        news_service=SimpleNamespace(get_stock_news=lambda *a, **kw: [NewsItem(id='nvda-news', stock_code='US.NVDA',
            stock_name='NVIDIA', title='NVIDIA dated fixture news', source='Fixture', published_at='2026-10-13',
            url='https://investor.nvidia.com/news/fixture', summary='Offline fixture; not a real event.')]),
        hotspot_service=SimpleNamespace(), portfolio_service=SimpleNamespace(),
        web_search_service=SimpleNamespace(search_report=lambda *a, **kw: {'results': [{
            'title': 'NVIDIA official earnings fixture', 'snippet': 'NVIDIA NVDA quarterly results fixture',
            'url': 'https://investor.nvidia.com/results/fixture', 'published_at': '2026-08-27'}], 'data_gaps': []}),
        sec_service=SimpleNamespace(resolve=lambda *a: {'status': 'ok', 'candidates': [
            {'code': 'US.NVDA', 'name': 'NVIDIA', 'market': 'us', 'identity_verified': True}]}, company=company),
        document_reader=SimpleNamespace(read=read), language='en-US', user_query=QUESTION,
    )


def test_mixed_brief_is_not_restricted_to_news_and_benchmark_is_not_a_company_pair():
    assert not is_company_news_query(QUESTION)
    assert not is_company_news_query('NVIDIA: find annual reports, financial statements and latest news')
    assert is_company_news_query('Latest NVIDIA company headlines')
    assert not is_financial_stock_comparison('Compare MSFT returns with the S&P 500 and show earnings')
    assert not is_broad_stock_comparison('Compare MSFT stock performance with Nasdaq')


@pytest.mark.parametrize('sec_outage', [False, True])
def test_brief_collects_requested_sources_before_one_model_turn(sec_outage):
    async def scenario():
        deps = fixtures(sec_outage)
        requests = []
        def model(messages, info):
            requests.append(messages)
            assert len(requests) == 1, 'Source collection must not consume paid planning turns'
            names = [item['tool'] for item in deps.tool_results]
            assert {'search_stocks', 'get_sec_company_data', 'get_stock_news', 'web_search', 'read_public_source'} <= set(names)
            assert 'get_stock_analysis' not in names, 'This user did not ask for a quote or technical analysis'
            assert 'Retrieved source records' in str(messages)
            sec = next(item for item in deps.tool_results if item['tool'] == 'get_sec_company_data')
            assert (sec.get('status') == 'unavailable') == sec_outage
            news = next(item for item in deps.tool_results if item['tool'] == 'get_stock_news')['evidence'][0]['id']
            doc = next(item for item in deps.tool_results if item['tool'] == 'read_public_source')['evidence'][0]['id']
            summary = ('## Verified identity\nNVIDIA is US.NVDA.\n\n'
                f'## Source-backed facts\n- Dated fixture news was retrieved [{news}].\n- Earnings excerpts were read [{doc}].\n\n'
                '## Inference\nNo investment conclusion is drawn from fixture sources.\n\n'
                '## Unavailable data\n' + ('SEC retrieval failed; this does not mean filings do not exist.' if sec_outage else 'Complete filing narratives were not read.'))
            return ModelResponse(parts=[ToolCallPart('final_result', {'summary': summary, 'evidence_ids': [news, doc]})])
        agent = create_agent(api_key='offline-test')
        agent.model = FunctionModel(model)
        result = await run_agent_async(agent, deps, QUESTION)
        assert len(requests) == result.payload['_meta']['usage']['requests'] == 1
        assert 'Source-backed facts' in result.summary
        assert 'only exposes news tools' not in result.summary
        assert result.payload['stock_code'] == 'US.NVDA'
    asyncio.run(scenario())


def test_quote_decimal_does_not_trigger_sec_amount_retry():
    item = {'tool': 'get_sec_company_data', 'retrieved_at': '2026-10-13T00:00:00Z', 'data': {
        'company': {'code': 'US.NVDA'}, 'filings': [], 'financials': [{
            'concept': 'Revenues', 'taxonomy': 'us-gaap', 'unit': 'USD', 'val': 100,
            'start': '2026-01-01', 'end': '2026-03-31', 'filed': '2026-05-01',
            'url': 'https://www.sec.gov/Archives/edgar/fixture.html'}]}}
    item['evidence'] = [ref.model_dump() for ref in sources_for_tool(item)]
    fact_id = item['evidence'][0]['id']
    quote = {'tool': 'get_stock_analysis', 'retrieved_at': item['retrieved_at'], 'data': {
        'stock_code': 'US.NVDA', 'quote': {'current_price': 123.45}, 'chart_series': [{'date': '2026-10-12'}]}}
    quote['evidence'] = [ref.model_dump() for ref in sources_for_tool(quote)]
    quote_id = quote['evidence'][0]['id']
    output = AgentOutput(summary=f'Reported revenue is preserved in the table [{fact_id}]. The delayed quote is USD 123.45 [{quote_id}].',
        evidence_ids=[fact_id, quote_id], financial_fact_ids=[fact_id])
    assert validate_research_output(output, [item, quote]) is output


def test_numeric_comparison_cleanup_preserves_other_sentences():
    summary = 'Microsoft combines cloud and applications. Reported revenue was USD 100. Amazon also operates a retail business.'
    result = _remove_financial_detail_lines(summary, 'en-US')
    assert 'combines cloud and applications' in result and 'retail business' in result
    assert 'USD 100' not in result


def test_explicit_current_company_takes_priority_over_previous_company():
    prompt = _build_enriched_agent_query(QUESTION, [AgentHistoryTurn(role='agent', content='Earlier Microsoft answer', stock_code='US.MSFT')], {'last_stock_code': 'US.MSFT'})
    assert prompt.endswith('当前问题：' + QUESTION)
    assert '不要沿用旧标的替换当前标的' in prompt


@pytest.mark.parametrize('query', [
    "give me a detailed research about NVIDIA's stock",
    'A thorough company review of NVIDIA', 'Research NVIDIA in detail',
    'An in-depth investment analysis of NVDA', 'Full stock report for NVIDIA',
    '详细研究英伟达股票', '给我一份全面的研究', '深入分析英伟达',
])
def test_explicit_detail_wording_is_recognized(query):
    assert requests_detailed_research(query)


def research_report(source_id):
    # Deliberately use analytical fixture prose rather than current financial claims.
    paragraph = (
        f'The retrieved fixture describes a company platform; it does not establish future sales [{source_id}]. '
        'The implication is conditional: a durable customer ecosystem could support repeat demand, while alternative '
        'suppliers could weaken that position. This is an inference, not a measured competitive ranking. The available '
        'record does not quantify customer retention, switching costs or forward spending commitments. A useful follow-up '
        'would compare dated management commentary with independently observed customer adoption. Those observations '
        'would either strengthen the thesis or invalidate its assumptions. No price target or investment action follows '
        'from this fixture alone. Missing disclosures should remain specific evidence gaps rather than being filled with '
        'remembered figures or presented as proof that a relevant document does not exist.'
    )
    return '\n\n'.join(f'## {heading}\n{paragraph}' for heading in [
        'Executive assessment', 'Business and competitive position', 'Financial performance',
        'Valuation and expectations', 'Dated catalysts', 'Price context',
        'Conditional scenarios', 'Risks and monitoring',
    ])


@pytest.mark.parametrize('mode', ['quick', 'deep'])
def test_detailed_report_survives_validation_assembly_and_saving(tmp_path, monkeypatch, mode):
    import json
    monkeypatch.setenv('RESEARCH_RUN_DIR', str(tmp_path))
    async def scenario():
        deps = fixtures()
        deps.user_query = "give me a detailed research about NVIDIA's stock"
        deps.research_mode = mode
        requests, written = [], []
        def model(messages, info):
            requests.append(messages)
            assert len(requests) == 1, 'A full report must not be retried into a compact paragraph'
            prompt = str(messages) + str(info)
            assert 'Explicit detail request' in prompt
            if mode == 'deep':
                assert '800-1400 English words' in prompt
                assert 'Keep the final answer compact' not in prompt
            item = deps.record_tool({'tool': 'get_stock_news', 'data': [
                {'stock_code': 'US.NVDA', 'title': 'Offline platform fixture', 'source': 'Fixture',
                 'url': 'https://example.org/fixture', 'published_at': '2026-10-13'}]})
            source_id = deps.tool_results[-1]['evidence'][0]['id']
            written.append(research_report(source_id))
            return ModelResponse(parts=[ToolCallPart('final_result', {'summary': written[-1], 'evidence_ids': [source_id]})])
        agent = create_agent(api_key='offline-test')
        agent.model = FunctionModel(model)
        result = await run_agent_async(agent, deps, deps.user_query)
        assert result.summary.count('## ') == 8
        assert len(result.summary.split()) > 800
        assert 'Risks and monitoring' in result.summary
        saved = json.loads((tmp_path / f'{deps.run_id}.json').read_text())
        assert saved['report']['summary'] == result.summary
        assert result.payload['_meta']['usage']['requests'] == 1
    asyncio.run(scenario())


def test_short_detailed_answer_is_repaired_without_repeating_retrieval(tmp_path, monkeypatch):
    monkeypatch.setenv('RESEARCH_RUN_DIR', str(tmp_path))
    async def scenario():
        deps = fixtures()
        deps.user_query = "give me a detailed research about NVIDIA's stock"
        deps.research_mode = 'deep'
        requests = []
        def model(messages, info):
            requests.append(messages)
            if len(requests) == 1:
                deps.record_tool({'tool': 'get_stock_news', 'data': [{'stock_code': 'US.NVDA',
                    'title': 'Offline fixture', 'source': 'Fixture', 'url': 'https://example.org/fixture'}]})
            else:
                assert len(requests) == 2
                assert 'explicitly requested detailed research' in str(messages)
            source_id = deps.tool_results[0]['evidence'][0]['id']
            summary = f'A short overview [{source_id}].' if len(requests) == 1 else research_report(source_id)
            return ModelResponse(parts=[ToolCallPart('final_result', {'summary': summary, 'evidence_ids': [source_id]})])
        agent = create_agent(api_key='offline-test')
        agent.model = FunctionModel(model)
        result = await run_agent_async(agent, deps, deps.user_query)
        assert len(deps.tool_results) == 1
        assert result.payload['_meta']['usage']['requests'] == 2
        assert result.summary.count('## ') == 8
    asyncio.run(scenario())


def test_specialist_review_does_not_inherit_the_parent_full_report_policy(tmp_path, monkeypatch):
    monkeypatch.setenv('RESEARCH_RUN_DIR', str(tmp_path))
    async def scenario():
        deps = fixtures()
        deps.user_query = "give me a detailed research about NVIDIA's stock"
        deps.research_mode = 'deep'
        deps.evidence_review_only = True
        calls = []
        def model(messages, info):
            calls.append(True)
            assert len(calls) == 1
            prompt = str(messages) + str(info)
            assert 'Specialist evidence review' in prompt and 'under 120 words' in prompt
            assert 'Explicit detail request:' not in prompt
            deps.record_tool({'tool': 'get_stock_news', 'data': [{'stock_code': 'US.NVDA',
                'title': 'Offline fixture', 'source': 'Fixture', 'url': 'https://example.org/fixture'}]})
            source_id = deps.tool_results[0]['evidence'][0]['id']
            return ModelResponse(parts=[ToolCallPart('final_result', {'summary': f'This fixture leaves customer concentration unknown [{source_id}].', 'evidence_ids': [source_id]})])
        agent = create_agent(api_key='offline-test')
        agent.model = FunctionModel(model)
        result = await run_agent_async(agent, deps, deps.user_query)
        assert result.summary.startswith('This fixture')
        assert result.payload['_meta']['usage']['requests'] == 1
    asyncio.run(scenario())
