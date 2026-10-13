"""Compare retrieved SEC facts without mixing currencies or reporting durations."""
from datetime import date

METRICS = {
    "Revenue": {"Revenues", "Revenue", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax"},
    "Net income": {"NetIncomeLoss", "ProfitLoss"},
    "Diluted EPS": {"EarningsPerShareDiluted", "DilutedEarningsLossPerShare"},
    "Assets": {"Assets"},
    "Operating cash flow": {"NetCashProvidedByUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities"},
}


def metric_label(concept: str, language: str = "en-US") -> str:
    labels = {"Revenue": "营业收入", "Net income": "净利润", "Diluted EPS": "稀释每股收益", "Assets": "总资产", "Operating cash flow": "经营现金流"}
    for name, concepts in METRICS.items():
        if concept in concepts:
            return labels[name] if language == "zh-CN" else name
    extra = {"CashAndCashEquivalentsAtCarryingValue": ("Cash and equivalents", "现金及等价物"), "CashAndCashEquivalents": ("Cash and equivalents", "现金及等价物"), "StockholdersEquity": ("Equity", "股东权益"), "Equity": ("Equity", "股东权益")}
    return extra.get(concept, (concept, concept))[language == "zh-CN"]


def _annual_fact(fact: dict) -> bool:
    try:
        return bool(fact.get("start") and fact.get("end")
                    and 330 <= (date.fromisoformat(fact["end"]) - date.fromisoformat(fact["start"])).days <= 400)
    except (TypeError, ValueError):
        return False


def compare_sec_facts(companies: list[dict], *, metrics: list[str] | None = None, annual: bool = False) -> dict:
    rows = []
    for metric, concepts in METRICS.items():
        if metrics is not None and metric not in metrics:
            continue
        values = []
        for company in companies:
            matches = [fact for fact in company.get("financials", []) if fact["concept"] in concepts]
            if annual:
                matches = [fact for fact in matches if _annual_fact(fact)]
            matches.sort(key=lambda fact: (fact.get("end", ""), fact.get("filed", "")), reverse=True)
            selected = matches[0] if matches else None
            values.append({"code": company["company"]["code"], "fact": selected})
        facts = [value["fact"] for value in values]
        comparable, gap = False, "Metric unavailable for one or more companies."
        if all(facts):
            try:
                durations = [(date.fromisoformat(fact["end"]) - date.fromisoformat(fact["start"])).days if fact.get("start") else 0 for fact in facts]
                ends = [date.fromisoformat(fact["end"]) for fact in facts]
                if len({fact["unit"] for fact in facts}) != 1:
                    gap = "Reporting currencies or units differ; no direct ranking or conversion."
                elif len({fact["taxonomy"] for fact in facts}) != 1:
                    gap = "Accounting taxonomies differ; no direct ranking."
                elif max(durations) - min(durations) > 14 or (max(ends) - min(ends)).days > 45:
                    gap = "Reporting periods differ; no direct ranking."
                else:
                    comparable, gap = True, "Periods are similar, not necessarily identical; review exact dates."
            except (ValueError, TypeError, KeyError):
                gap = "Reporting period metadata unavailable; no direct ranking."
        rows.append({"metric": metric, "values": values, "comparable": comparable, "comparison_note": gap})
    return {"companies": [item["company"] for item in companies], "metrics": rows,
            "data_gaps": list(dict.fromkeys(row["comparison_note"] for row in rows if not row["comparable"]))}
