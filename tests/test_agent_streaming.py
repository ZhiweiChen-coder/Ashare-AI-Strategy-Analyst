"""Exercise the real Pydantic adapter and SSE route without any paid network."""
import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from openai import AsyncOpenAI
from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, ToolCallPart, ToolCallPartDelta, ThinkingPart, TextPart

from api.agent_pydantic import AgentDeps, _stream_answer, create_agent, run_agent_async


def dependencies(**kwargs):
    return AgentDeps(stock_service=SimpleNamespace(), news_service=SimpleNamespace(),
        hotspot_service=SimpleNamespace(), portfolio_service=SimpleNamespace(),
        web_search_service=SimpleNamespace(), language="en-US", **kwargs)


def chunk(delta, finish=None, usage=None):
    payload = {"id": "offline-stream", "object": "chat.completion.chunk", "created": 0,
        "model": "deepseek-flash", "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
    if usage:
        payload["usage"] = usage
    return ("data: " + json.dumps(payload) + "\n\n").encode()


@pytest.mark.parametrize("mode", ["quick", "deep"])
def test_adapter_keeps_draft_private_and_reports_checks_before_completion(monkeypatch, mode):
    async def scenario():
        checking = asyncio.Event()
        release = asyncio.Event()
        closed = asyncio.Event()
        events, requests = [], []
        output = {"summary": "## Research scope\nChoose a company to research.", "actions": [], "evidence_ids": [], "financial_fact_ids": [], "data_gaps": []}
        encoded = json.dumps(output)
        split = encoded.index("Choose") + len("Choose")

        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield chunk({"role": "assistant", "reasoning_content": "private reasoning must stay hidden"})
                yield chunk({"content": "internal preamble must stay hidden"})
                yield chunk({"tool_calls": [{"index": 0, "id": "call_final", "type": "function", "function": {"name": "final_result", "arguments": encoded[:split]}}]})
                await release.wait()
                yield chunk({"tool_calls": [{"index": 0, "function": {"arguments": encoded[split:]}}]})
                yield chunk({}, "tool_calls", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
                yield b"data: [DONE]\n\n"
            async def aclose(self):
                closed.set()

        def handler(request):
            body = json.loads(request.content)
            requests.append(body)
            assert body["stream"] is True
            expected_max_tokens = 10000 if mode == "deep" else 2500
            assert body.get("max_tokens", body.get("max_completion_tokens")) == expected_max_tokens
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Stream())

        client = AsyncOpenAI(api_key="offline-test", base_url="https://offline.invalid", max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        monkeypatch.setattr("api.agent_pydantic.AsyncOpenAI", lambda **kw: client)
        agent = create_agent(api_key="offline-test", model="deepseek-flash")
        def report(stage, pct, message, meta):
            events.append((stage, message, meta))
            if stage == "check_facts":
                checking.set()
        task = asyncio.create_task(run_agent_async(agent, dependencies(research_mode=mode), "Explain the research scope", report))
        try:
            try:
                await asyncio.wait_for(checking.wait(), 3)
            except TimeoutError:
                if task.done():
                    await task
                raise
            assert not task.done(), "Progress must arrive while the provider response is still open"
            assert not closed.is_set()
            assert not any(stage == "answer_delta" for stage, _, _ in events)
            release.set()
            result = await asyncio.wait_for(task, 3)
            assert not any(stage == "answer_delta" for stage, _, _ in events)
            assert "private reasoning" not in str(events) and "internal preamble" not in str(events)
            assert "evidence_ids" not in str(events)
            assert result.summary == output["summary"]
            assert result.payload["_meta"]["usage"] == {"requests": 1, "input_tokens": 100, "output_tokens": 50}
            assert requests[0]["thinking"]["type"] == ("enabled" if mode == "deep" else "disabled")
            assert closed.is_set()
        finally:
            release.set()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await client.close()
    asyncio.run(scenario())


def test_partial_output_and_retried_drafts_never_reach_the_answer_channel():
    async def scenario():
        events = []
        def report(stage, pct, message, meta):
            events.append((stage, message, meta))
        deps = dependencies(progress_callback=report)
        deps.tool_results = [{"evidence": [{"id": "ev_abc", "url": "https://www.sec.gov/fixture"}]}]
        async def first_attempt():
            yield PartStartEvent(index=0, part=ThinkingPart(content="never render thoughts"))
            yield PartStartEvent(index=1, part=TextPart(content="never render intermediates"))
            yield PartStartEvent(index=2, part=ToolCallPart(tool_name="web_search", args='{"query":"secret args"}'))
            yield PartStartEvent(index=3, part=ToolCallPart(tool_name="final_result", args='{"summary":"Draft \\u4e'))
            yield PartDeltaEvent(index=3, delta=ToolCallPartDelta(args_delta='2d\\nQuote: \\"yes\\" [ev_'))
            yield PartDeltaEvent(index=3, delta=ToolCallPartDelta(args_delta='abc].","actions":[]}'))
        await _stream_answer(deps, first_attempt())
        async def retry():
            yield PartStartEvent(index=0, part=ToolCallPart(tool_name="final_result", args={"summary": "Validated replacement"}))
        await _stream_answer(deps, retry())
        assert [stage for stage, _, _ in events] == ["check_facts", "check_facts"]
        assert "Draft" not in str(events) and "Validated replacement" not in str(events)
        assert "ev_" not in str(events)
        assert "secret args" not in str(events) and "never render" not in str(events)
    asyncio.run(scenario())


def test_adapter_validation_retry_is_private_and_preserves_accounting(monkeypatch):
    async def scenario():
        events, requests = [], []
        outputs = ["## 研究范围\n这是中文回答，请先选择要研究的公司。", "## Research scope\nChoose a company to research."]
        class Stream(httpx.AsyncByteStream):
            def __init__(self, summary):
                self.summary = summary
            async def __aiter__(self):
                args = json.dumps({"summary": self.summary, "actions": [], "evidence_ids": [], "financial_fact_ids": [], "data_gaps": []})
                yield chunk({"tool_calls": [{"index": 0, "id": "call_final", "type": "function", "function": {"name": "final_result", "arguments": args}}]})
                yield chunk({}, "tool_calls", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
                yield b"data: [DONE]\n\n"
        def handler(request):
            requests.append(json.loads(request.content))
            assert len(requests) <= 2, "No extra retry should be admitted"
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Stream(outputs[len(requests) - 1]))
        client = AsyncOpenAI(api_key="offline-test", base_url="https://offline.invalid", max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        monkeypatch.setattr("api.agent_pydantic.AsyncOpenAI", lambda **kw: client)
        agent = create_agent(api_key="offline-test", model="deepseek-flash")
        def report(stage, pct, message, meta):
            events.append((stage, message, meta))
        try:
            result = await run_agent_async(agent, dependencies(), "Explain research scope", report)
            assert result.summary == outputs[1]
            assert not any(stage == "answer_delta" for stage, _, _ in events)
            assert outputs[0] not in str(events)
            assert len([stage for stage, _, _ in events if stage == "check_facts"]) >= 2
            assert len(requests) == result.payload["_meta"]["usage"]["requests"] == 2
            assert result.payload["_meta"]["usage"]["output_tokens"] == 100
            assert not result.research_steps
        finally:
            await client.close()
    asyncio.run(scenario())


def test_cancelling_adapter_stream_closes_provider_without_retry(monkeypatch):
    async def scenario():
        started, closed = asyncio.Event(), asyncio.Event()
        requests = []
        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield chunk({"tool_calls": [{"index": 0, "id": "call_final", "type": "function", "function": {"name": "final_result", "arguments": '{"summary":"Incomplete'}}]})
                await asyncio.Event().wait()
            async def aclose(self):
                closed.set()
        def handler(request):
            requests.append(request)
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Stream())
        client = AsyncOpenAI(api_key="offline-test", base_url="https://offline.invalid", max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        monkeypatch.setattr("api.agent_pydantic.AsyncOpenAI", lambda **kw: client)
        agent = create_agent(api_key="offline-test", model="deepseek-flash")
        def report(stage, pct, message, meta):
            if stage == "check_facts":
                started.set()
        task = asyncio.create_task(run_agent_async(agent, dependencies(), "Explain research scope", report))
        try:
            await asyncio.wait_for(started.wait(), 3)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert closed.is_set() and len(requests) == 1
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await client.close()
    asyncio.run(scenario())


def test_committed_summary_chunks_preserve_one_final_version():
    from api.sse import iter_committed_summary
    async def scenario():
        summary = '## Facts\n\n已核验的来源 [1](https://example.org/filing_(annual)).\n' * 200
        chunks = [part async for part in iter_committed_summary(summary)]
        assert 1 < len(chunks) <= 40
        visible = ''
        for part in chunks:
            visible += part
            assert summary.startswith(visible), 'Every visible prefix must belong to the same final answer'
        assert visible == summary
        assert [part async for part in iter_committed_summary('')] == []
    asyncio.run(scenario())
