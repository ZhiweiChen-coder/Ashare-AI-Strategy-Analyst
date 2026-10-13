"""Measure recent moves from the retrieved daily bars, never model arithmetic."""
import math


def measured_price_moves(bars: list[dict]) -> dict:
    valid = []
    for bar in bars:
        try:
            price = float(bar["close"])
            if price > 0 and math.isfinite(price) and bar.get("date"):
                valid.append({**bar, "close": price})
        except (KeyError, TypeError, ValueError):
            continue
    # A missing/invalid close breaks the daily observation sequence: do not
    # silently relabel the surviving points as consecutive trading days.
    if not valid or len(valid) != len(bars):
        return {"windows": [], "data_gaps": ["Daily close coverage is missing or invalid; recent returns were not calculated."]}
    valid = sorted(valid, key=lambda row: row["date"])
    if len({row["date"] for row in valid}) != len(valid):
        return {"windows": [], "data_gaps": ["Duplicate daily observations prevent reliable return windows."]}
    last = valid[-1]
    windows, gaps = [], []
    for sessions in (1, 5, 20):
        if len(valid) <= sessions:
            gaps.append(f"Insufficient daily bars for the {sessions}-session return.")
            continue
        first = valid[-1 - sessions]
        windows.append({"sessions": sessions, "start": first["date"], "end": last["date"],
                        "start_close": first["close"], "end_close": last["close"],
                        "change_pct": round((last["close"] / first["close"] - 1) * 100, 4)})
    volume_ratio = None
    try:
        volumes = [float(row["volume"]) for row in valid[-21:-1]]
        recent = float(last["volume"])
        if len(volumes) == 20 and all(math.isfinite(value) and value > 0 for value in [*volumes, recent]):
            volume_ratio = round(recent / (sum(volumes) / 20), 4)
    except (KeyError, TypeError, ValueError):
        pass
    if volume_ratio is None:
        gaps.append("A complete previous 20-session volume baseline is unavailable.")
    gaps.extend(["No benchmark-relative return or intraday attribution was calculated.",
                 "Corporate-action adjustment follows the source bars; adjustment details must be checked before interpreting large moves."])
    return {"data_as_of": last["date"], "price_status": "historical_or_delayed", "windows": windows,
            "volume_vs_previous_20_sessions": volume_ratio, "data_gaps": gaps}
