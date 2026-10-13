"""Workspace mutations use durable shared storage without paid model requests."""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

from api import main
from api.agent_pydantic import AgentDeps, AgentOutput, build_agent_response, create_agent, execute_watchlist, run_agent_async
from api.research_capability import ResearchCapability
from api.schemas import StockSearchResult
from api.supabase_config import SupabaseConfig
from api.watchlist import LocalWatchlistStore, CloudWatchlistStore


def dependencies(store):
    return AgentDeps(*[SimpleNamespace() for _ in range(5)], watchlist_store=store, language="en-US")


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    store = LocalWatchlistStore(tmp_path / "watchlist.db")
    monkeypatch.setattr(main, "workspace_watchlist_store", store)
    monkeypatch.setattr(main, "supabase_config", SupabaseConfig())
    monkeypatch.setattr(main, "credit_service", main.CreditService(SupabaseConfig()))
    monkeypatch.setattr(main, "agent_memory_store", main.AgentMemoryStore(tmp_path / "memory.db"))
    monkeypatch.setattr(main, "_resolve_watchlist_stock", lambda code: {"code": "US.MRNA", "name": "Moderna", "market": "us", "identity_verified": True})
    return store, TestClient(main.app)


def test_migration_preserves_existing_list_and_empty_lists(tmp_path):
    store = LocalWatchlistStore(tmp_path / "list.db")
    assert not store.get()["initialized"]
    assert store.initialize([])["items"] == []
    assert store.initialize([{"code": "US.AAPL", "name": "Apple"}])["items"] == []
    assert LocalWatchlistStore(store.path).get() == {"initialized": True, "items": []}


def test_concurrent_adds_are_idempotent_and_do_not_drop_existing_stocks(tmp_path):
    store = LocalWatchlistStore(tmp_path / "list.db")
    originals = [{"code": f"sh{index:06}", "name": f"Stock {index}"} for index in range(30)]
    store.initialize(originals)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.mutate("add", "us.mrna", "Moderna"), range(8)))
    assert sum(result["changed"] for result in results) == 1
    assert len(LocalWatchlistStore(store.path).get()["items"]) == 31
    assert store.mutate("remove", "US.MRNA")["changed"]
    assert not store.mutate("remove", "US.MRNA")["changed"]
    assert store.get()["items"] == originals


def test_limit_rejects_new_add_without_evicting_stocks(tmp_path):
    store = LocalWatchlistStore(tmp_path / "list.db")
    items = [{"code": f"sh{index:06}", "name": "Stock"} for index in range(200)]
    store.initialize(items)
    with pytest.raises(ValueError, match="full"):
        store.mutate("add", "US.MRNA", "Moderna")
    assert store.get()["items"] == items


def test_api_and_chat_share_persisted_watchlist_without_model(workspace, monkeypatch):
    store, client = workspace
    monkeypatch.setattr(main, "_get_pydantic_agent", lambda: pytest.fail("Simple watchlist commands must not call a model"))
    response = client.post("/api/workspace/watchlist/initialize", json={"items": [{"code": "US.AAPL", "name": "Apple"}]})
    assert response.status_code == 200
    report = client.post("/api/agent/query", json={"query": "Add US.MRNA to my watchlist?", "language": "en-US", "session_id": "first-chat"}).json()
    assert report["intent"] == "watchlist"
    assert report["summary"] == "Added Moderna (US.MRNA) to your watchlist."
    assert report["payload"]["_meta"]["usage"]["requests"] == 0
    assert report["payload"]["watchlist"]["changed"]
    assert [row["code"] for row in client.get("/api/workspace/watchlist").json()["items"]] == ["US.MRNA", "US.AAPL"]
    second = client.post("/api/agent/query", json={"query": "Add US.MRNA to my watchlist", "language": "en-US", "session_id": "second-chat"}).json()
    assert "already" in second["summary"]
    assert len(LocalWatchlistStore(store.path).get()["items"]) == 2
    assert client.post("/api/workspace/watchlist", json={"action": "remove", "code": "US.MRNA"}).json()["changed"]
    listed = client.post("/api/agent/query", json={"query": "show my watchlist", "language": "en-US"}).json()
    assert "US.MRNA" not in listed["summary"] and "US.AAPL" in listed["summary"]


def test_streaming_chinese_watchlist_command(workspace, monkeypatch):
    _, client = workspace
    monkeypatch.setattr(main, "_get_pydantic_agent", lambda: pytest.fail("No paid model"))
    response = client.post("/api/agent/query/stream", json={"query": "把US.MRNA加入我的自选股", "language": "zh-CN"})
    assert response.status_code == 200
    assert '"manage_watchlist"' in response.text and 'event: result' in response.text
    assert "已添加" in response.text


def test_identity_failure_leaves_watchlist_unchanged(workspace, monkeypatch):
    store, client = workspace
    store.initialize([])
    def unavailable(code):
        raise ValueError("Ambiguous identity")
    monkeypatch.setattr(main, "_resolve_watchlist_stock", unavailable)
    assert client.post("/api/workspace/watchlist", json={"action": "add", "code": "US.MRNA"}).status_code == 422
    report = client.post("/api/agent/query", json={"query": "Add US.MRNA to my watchlist", "language": "en-US"}).json()
    assert "not changed" in report["summary"]
    assert not store.get()["items"]


def test_tool_rejects_unverified_stock_and_failed_storage(tmp_path):
    deps = dependencies(LocalWatchlistStore(tmp_path / "list.db"))
    asyncio.run(execute_watchlist(deps, "add", "US.MRNA"))
    assert deps.tool_results[-1]["status"] == "unavailable"
    deps.verified_us_codes.add("US.MRNA")
    deps.record_tool({"tool": "search_stocks", "data": [{"code": "US.MRNA", "name": "Moderna"}]})
    def failed(*args):
        raise OSError("Disk unavailable")
    deps.watchlist_store.mutate = failed
    asyncio.run(execute_watchlist(deps, "add", "US.MRNA"))
    response = build_agent_response(AgentOutput(summary="Save failed."), deps.tool_results)
    assert "watchlist" not in response.payload
    assert deps.tool_results[-1]["status"] == "unavailable"
    assert not LocalWatchlistStore(deps.watchlist_store.path).get()["items"]


def test_mutations_are_not_reused_as_retrieval_cache(tmp_path):
    async def run():
        deps = dependencies(LocalWatchlistStore(tmp_path / "list.db"))
        deps.verified_us_codes.add("US.MRNA")
        deps.record_tool({"tool": "search_stocks", "data": [{"code": "US.MRNA", "name": "Moderna"}]})
        capability = ResearchCapability()
        async def handler(args):
            return deps.watchlist_store.mutate(args["action"], "US.MRNA", "Moderna")
        for action in ["add", "remove", "add"]:
            await capability.wrap_tool_execute(SimpleNamespace(deps=deps), call=None, tool_def=SimpleNamespace(name="manage_watchlist"), args={"action": action, "stock_code": "US.MRNA"}, handler=handler)
        assert deps.watchlist_store.get()["items"] == [{"code": "US.MRNA", "name": "Moderna"}]
        assert not deps.cache_hits
    asyncio.run(run())


def test_real_installed_pydantic_agent_can_persist_watchlist(tmp_path):
    async def run():
        store = LocalWatchlistStore(tmp_path / "list.db")
        deps = dependencies(store)
        deps.stock_service.search_stocks = lambda *a, **kw: [StockSearchResult(code="US.MRNA", name="Moderna", market="us")]
        deps.sec_service = SimpleNamespace(resolve=lambda *a: {"status": "ok", "candidates": [{"code": "US.MRNA", "name": "Moderna", "market": "us", "identity_verified": True}]})
        def model(messages, info):
            returned = [part for message in messages for part in message.parts if isinstance(part, ToolReturnPart)]
            if not returned:
                return ModelResponse(parts=[ToolCallPart("search_stocks", {"query": "US.MRNA"})])
            if not any(part.tool_name == "manage_watchlist" for part in returned):
                return ModelResponse(parts=[ToolCallPart("manage_watchlist", {"action": "add", "stock_code": "US.MRNA"})])
            return ModelResponse(parts=[ToolCallPart("final_result", {"summary": "Moderna was added to your watchlist.", "evidence_ids": [v["id"] for item in deps.tool_results for v in item["evidence"]]})])
        agent = create_agent(api_key="offline-test", model="deepseek-flash")
        with agent.override(model=FunctionModel(model)):
            result = await run_agent_async(agent, deps, "Add Moderna to the watchlist after verifying its company identity")
        assert result.payload["watchlist"]["changed"]
        assert LocalWatchlistStore(store.path).get()["items"] == [{"code": "US.MRNA", "name": "Moderna"}]
        assert [item.tool for item in result.research_steps] == ["search_stocks", "manage_watchlist"]
    asyncio.run(run())


def test_cloud_operations_keep_owner_filters_and_do_not_migrate_local_data(monkeypatch):
    calls = []
    rows = []
    class Client:
        def select(self, table, **kw):
            calls.append((table, kw))
            assert kw["filters"]["user_id"] == "owner-a"
            return [{"id": "list-a"}] if table == "watchlists" else list(rows)
        def upsert(self, table, body, **kw):
            assert body["user_id"] == "owner-a" and body["watchlist_id"] == "list-a"
            rows.append({"symbol": body["symbol"], "display_name": body["display_name"]})
    monkeypatch.setattr("api.watchlist.SupabaseWorkspaceStore", lambda *a: SimpleNamespace(client=Client()))
    store = CloudWatchlistStore(None, SimpleNamespace(id="owner-a", access_token="offline"))
    assert not store.initialize([{"code": "US.AAPL", "name": "Apple"}])["items"]
    assert store.mutate("add", "US.MRNA", "Moderna")["items"] == [{"code": "US.MRNA", "name": "Moderna"}]
    assert len(calls) >= 3


def test_local_mode_works_with_configured_cloud_credentials(workspace, monkeypatch):
    store, client = workspace
    monkeypatch.setattr(main, "supabase_config", SupabaseConfig(url="https://offline.supabase.co", anon_key="offline", require_auth=False))
    response = client.get("/api/workspace/watchlist")
    assert response.status_code == 200 and response.json() == store.get()


def test_required_cloud_auth_does_not_fall_back_to_local(workspace, monkeypatch):
    store, client = workspace
    monkeypatch.setattr(main, "supabase_config", SupabaseConfig(url="https://offline.supabase.co", anon_key="offline", require_auth=True))
    response = client.get("/api/workspace/watchlist")
    assert response.status_code == 401
    assert not store.get()["initialized"]
