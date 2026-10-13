"""Private run diagnostics and conservative, explicitly provisional usage estimates."""
import json
import os
import time
from pathlib import Path


def run_metadata(deps, status: str, failure: str | None = None) -> dict:
    usage = deps.run_usage
    unresolved = deps.provider_requests_started > deps.provider_requests_finished or (deps.run_usage.requests > 0 and deps.provider_requests_started == 0)
    # Peak DeepSeek Flash rates; charge all input as uncached. This overestimates
    # cache/off-peak savings, but excludes any provider call lacking usage.
    flash = deps.model_name.removeprefix("openai:") == "deepseek-flash"
    known_estimate = round((usage.input_tokens * 0.30 + usage.output_tokens * 1.20) / 1_000_000, 8) if flash else None
    return {"run_id": deps.run_id, "status": status, "failure_type": failure,
            "finish_reason": deps.finish_reason or "completed", "latency_seconds": round(time.monotonic() - deps.started_at, 3),
            "model": deps.model_name, "usage": {"requests": usage.requests, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
            "usage_unresolved": unresolved, "estimated_cost_usd": known_estimate,
            "cost_basis": "DeepSeek Flash peak rates, all input uncached; known usage only; provisional, not billing reconciliation" if flash else "Model pricing unavailable",
            "provider_requests_started": deps.provider_requests_started, "provider_requests_finished": deps.provider_requests_finished,
            "retrieval_calls": deps.retrieval_count, "cache_hits": list(dict.fromkeys(deps.cache_hits))}


def save_run(deps, status: str, failure: str | None = None, response=None) -> dict:
    metadata = run_metadata(deps, status, failure)
    path = Path(os.environ.get("RESEARCH_RUN_DIR", str(Path(__file__).resolve().parents[1] / "output" / "research-runs")))
    try:
        path.mkdir(parents=True, exist_ok=True)
        # No credentials, private reasoning, model messages, conversation history
        # or provider error bodies. These files are ignored by Git.
        record = {"metadata": metadata, "tools": [
            {key: value for key, value in item.items() if key in {"tool", "status", "reason_code", "retrieved_at", "evidence", "data_gaps"}}
            for item in deps.tool_results]}
        if response is not None:
            record["report"] = response.model_dump()
        temp = path / f"{deps.run_id}.tmp"
        temp.write_text(json.dumps(record, ensure_ascii=False, default=str), encoding="utf-8")
        temp.replace(path / f"{deps.run_id}.json")
    except OSError:
        metadata["diagnostics_saved"] = False
    else:
        metadata["diagnostics_saved"] = True
    return metadata
