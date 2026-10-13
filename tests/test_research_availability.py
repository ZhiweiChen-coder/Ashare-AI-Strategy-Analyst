from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import api.main as main
from api.schemas import AgentResponse
from api.supabase_config import SupabaseConfig

client = TestClient(main.app)


def hosted(monkeypatch, authenticated=True):
    monkeypatch.delenv("OPENASHARE_PUBLIC_BETA", raising=False)
    config = SupabaseConfig(url="https://fixture.supabase.co", anon_key="fixture", require_auth=True)
    monkeypatch.setattr(main, "supabase_config", config)
    def user(*_):
        if not authenticated:
            from fastapi import HTTPException
            raise HTTPException(401, "Sign in")
        return SimpleNamespace(id="fixture-user", access_token="fixture-token")
    monkeypatch.setattr(main, "require_supabase_user", user)


@pytest.mark.parametrize("endpoint", ["/api/agent/query", "/api/agent/query/stream"])
@pytest.mark.parametrize("language", ["en-US", "zh-CN"])
def test_hosted_deep_rejects_before_credit_or_model_calls(monkeypatch, endpoint, language):
    hosted(monkeypatch)
    def forbidden(*_, **__):
        raise AssertionError("Suspended Deep must not reserve credits, call research or persist a turn")
    monkeypatch.setattr(main, "credit_service", SimpleNamespace(reserve=forbidden))
    monkeypatch.setattr(main, "_run_agent_request", forbidden)
    monkeypatch.setattr(main, "_persist_agent_turns", forbidden)
    response = client.post(endpoint, json={"query": "Research NVIDIA", "research_mode": "deep", "language": language})
    assert response.status_code == 503
    assert ("unavailable at the moment" if language == "en-US" else "暂时不可用") in response.json()["detail"]
    assert "text/event-stream" not in response.headers["content-type"]


def test_public_capabilities_need_no_auth_and_expose_no_workspace_data(monkeypatch):
    hosted(monkeypatch, authenticated=False)
    response = client.get("/api/agent/capabilities")
    assert response.status_code == 200
    assert response.json() == {
        "quick_available": True, "deep_available": False,
        "deep_unavailable_reason": "public_beta_suspended",
        "deep_unavailable_message": "Deep research is unavailable at the moment. Please use Quick research.",
    }
    assert client.post("/api/agent/query", json={"query": "Hello"}).status_code == 401


@pytest.mark.parametrize("endpoint", ["/api/agent/query", "/api/agent/query/stream"])
def test_local_deep_remains_available(monkeypatch, endpoint):
    monkeypatch.delenv("OPENASHARE_PUBLIC_BETA", raising=False)
    monkeypatch.setattr(main, "supabase_config", SupabaseConfig())
    monkeypatch.setattr(main, "credit_service", main.CreditService(SupabaseConfig()))
    received = []
    async def fake_run(payload, *_, **__):
        received.append(payload.research_mode)
        return AgentResponse(intent="stock", summary="Offline fixture report", actions=[], citations=[], payload={})
    monkeypatch.setattr(main, "_run_agent_request", fake_run)
    monkeypatch.setattr(main, "_persist_agent_turns", lambda *_: None)
    response = client.post(endpoint, json={"query": "Research NVIDIA", "research_mode": "deep"})
    assert response.status_code == 200
    assert received == ["deep"]
    assert client.get("/api/agent/capabilities").json()["deep_available"] is True


@pytest.mark.parametrize("endpoint", ["/api/agent/query", "/api/agent/query/stream"])
def test_hosted_quick_still_runs(monkeypatch, endpoint):
    hosted(monkeypatch)
    # Keep the fixture offline; production auth is still exercised by middleware.
    monkeypatch.setattr(main, "credit_service", main.CreditService(SupabaseConfig()))
    monkeypatch.setattr(main, "_watchlist_store_for_request", lambda *_: None)
    received = []
    async def fake_run(payload, *_, **__):
        received.append(payload.research_mode)
        return AgentResponse(intent="stock", summary="Offline Quick report", actions=[], citations=[], payload={})
    monkeypatch.setattr(main, "_run_agent_request", fake_run)
    monkeypatch.setattr(main, "_persist_agent_turns", lambda *_: None)
    response = client.post(endpoint, json={"query": "Research NVIDIA", "research_mode": "quick"})
    assert response.status_code == 200
    assert received == ["quick"]


def test_explicit_public_beta_flag_blocks_direct_origin_requests(monkeypatch):
    monkeypatch.setenv("OPENASHARE_PUBLIC_BETA", "true")
    monkeypatch.setattr(main, "supabase_config", SupabaseConfig())
    assert client.get("/api/agent/capabilities").json()["deep_available"] is False
    assert client.post("/api/agent/query", json={"query": "Research", "research_mode": "deep"}).status_code == 503
