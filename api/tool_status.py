"""Distinguish successful empty reads from dependency and provider failures."""


def tool_reason(item: dict) -> str | None:
    if item.get("reason_code"):
        return item["reason_code"]
    if item.get("status") == "unavailable":
        return "provider_error"
    data = item.get("data")
    if not data:
        return "no_matches" if item.get("tool") == "search_stocks" else "no_results"
    return None


def tool_status(item: dict) -> str:
    return "unavailable" if item.get("status") == "unavailable" else "completed"
