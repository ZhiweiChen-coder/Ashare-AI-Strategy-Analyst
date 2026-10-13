"""Small, serial, paid research checks. Evidence and the spend ledger stay ignored."""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from pydantic_ai import capture_run_messages
from api.main import _build_agent_deps, settings_store, stock_service
from api.agent_pydantic import create_agent, run_agent_async

CASES = [
    ("aapl-earnings-en", "Research AAPL's latest available SEC revenue and diluted EPS. State reporting periods, filing dates, and data gaps. Answer in English.", "en-US", "quick"),
    ("aapl-msft-comparison", "Compare AAPL and MSFT revenue and operating cash flow from their latest available SEC facts. Check currencies and reporting periods with compare_companies. Answer in English.", "en-US", "quick"),
    ("tsm-foreign-zh", "研究台积电 TSM 的 SEC 财务数据：收入、经营现金流、币种和报告期；如数据较旧必须明确说明。用中文回答。", "zh-CN", "deep"),
    ("missing-news-en", "Retrieve the latest available AAPL company news. If the provider returns no news, state that gap without inventing headlines. Answer in English.", "en-US", "quick"),
]


def save(path: Path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str))
    temporary.replace(path)


async def evaluate(output: Path, budget: float, count: int, revision: str = ""):
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"estimated_usd": 0.0, "entries": []}
    if any(entry["state"] in {"admitted", "unknown_usage"} for entry in ledger["entries"]):
        raise RuntimeError("Unreconciled request found. New paid work is blocked.")
    config = settings_store.build_runtime_config(stock_service.config)
    if config.llm_model != "deepseek-flash" or "deepseek.com" not in config.llm_base_url:
        raise RuntimeError("Live evaluation requires the configured DeepSeek Flash endpoint.")
    agent = create_agent(api_key=config.llm_api_key, base_url=config.llm_base_url, model=config.llm_model)
    for case_id, query, language, mode in CASES[:count]:
        case_id += f"-{revision}" if revision else ""
        if any(entry["case"] == case_id for entry in ledger["entries"]):
            continue
        reserve = 0.05  # Admission reserve, not a provider billing ceiling.
        if ledger["estimated_usd"] + reserve > budget:
            break
        entry = {"case": case_id, "state": "admitted", "reserve_usd": reserve}
        ledger["entries"].append(entry)
        save(ledger_path, ledger)
        deps = _build_agent_deps()
        deps.language, deps.research_mode, deps.user_query = language, mode, query
        started = time.monotonic()
        with capture_run_messages() as messages:
            try:
                response = await run_agent_async(agent, deps, query)
                usage = response.payload.get("_meta", {}).get("usage")
                if not usage:
                    raise RuntimeError("Provider usage unavailable.")
                # Peak prices, all input treated as cache misses: conservative estimate.
                cost = (usage["input_tokens"] * 0.30 + usage["output_tokens"] * 1.20) / 1_000_000
                response.payload["_meta"]["estimated_cost_usd"] = cost
                response.payload["_meta"]["latency_seconds"] = round(time.monotonic() - started, 3)
                known = {value["id"]: value for item in deps.tool_results for value in item.get("evidence", [])}
                audit = {"source_ids_match": all(source.id in known and source.model_dump() == known[source.id] for source in response.evidence),
                         "private_reasoning_excluded": "reasoning_content" not in response.model_dump_json(),
                         "deadline_met": time.monotonic() - started <= (540 if mode == "deep" else 180),
                         "required_tools": "compare_companies" in response.payload["_meta"]["tools_used"] if "comparison" in case_id else "get_stock_news" in response.payload["_meta"]["tools_used"] if "news" in case_id else "get_sec_company_data" in response.payload["_meta"]["tools_used"]}
                save(output / f"{case_id}.json", {"query": query, "language": language, "mode": mode, "response": response.model_dump(), "audit": audit})
                save(output / f"{case_id}.evidence.json", deps.tool_results)
                entry.update(state="completed", estimated_usd=cost, usage=usage, latency_seconds=round(time.monotonic() - started, 3), audit=audit)
                ledger["estimated_usd"] += cost
                print(json.dumps(entry), flush=True)
            except Exception as exc:
                # Capture usage counters only; never persist the model's private reasoning.
                usages = [message.usage for message in messages if getattr(message, "kind", "") == "response"]
                entry.update(state="unknown_usage", error_type=type(exc).__name__, latency_seconds=round(time.monotonic() - started, 3), observed_input_tokens=sum(usage.input_tokens for usage in usages), observed_output_tokens=sum(usage.output_tokens for usage in usages))
                save(output / f"{case_id}.evidence.json", deps.tool_results)
                print(json.dumps(entry), flush=True)
                save(ledger_path, ledger)
                break
            finally:
                save(ledger_path, ledger)
        if not all(entry.get("audit", {}).values()):
            break
    print(json.dumps({"estimated_usd": ledger["estimated_usd"], "completed": sum(entry["state"] == "completed" for entry in ledger["entries"])}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "output/pydantic-v2-live")
    parser.add_argument("--budget-usd", type=float, default=0.25)
    parser.add_argument("--cases", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--revision", default="", help="Explicit revision suffix for a bounded retest; retains the same spend ledger.")
    args = parser.parse_args()
    if args.revision and not args.revision.replace("-", "").isalnum():
        parser.error("revision must contain only letters, digits and hyphens")
    asyncio.run(evaluate(args.output, min(args.budget_usd, 0.25), args.cases, args.revision))
