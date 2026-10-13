"""Request language selection, independent of saved chat history."""
import re
import html


def resolve_language(query: str, preference: str = "auto") -> str:
    if re.search(r"(?:用|以|输出|回答).{0,4}英文|\b(?:in|answer in|respond in) English\b", query, re.I):
        return "en-US"
    if re.search(r"(?:用|以|输出|回答).{0,4}中文|\b(?:in|answer in|respond in) Chinese\b", query, re.I):
        return "zh-CN"
    if preference in {"en-US", "zh-CN"}:
        return preference
    return "zh-CN" if re.search(r"[\u3400-\u9fff]", query) else "en-US"


def localize_stock_analysis(analysis, language: str):
    """Render deterministic observations from supplied indicators, without an LLM."""
    if language != "en-US":
        return analysis
    indicators = analysis.technical_indicators
    comments = []
    rsi = indicators.get("RSI")
    if rsi is not None:
        band = "above the conventional overbought threshold" if rsi > 70 else "below the conventional oversold threshold" if rsi < 30 else "in the conventional neutral range"
        comments.append(f"RSI (14) is {rsi:.2f}, {band}.")
    macd = indicators.get("MACD")
    if macd is not None:
        comments.append(f"MACD is {macd:.2f}; momentum is {'positive' if macd > 0 else 'negative' if macd < 0 else 'flat'}.")
    ma20 = indicators.get("MA20")
    if ma20 is not None:
        comments.append(f"The last available price is {'above' if analysis.quote.current_price >= ma20 else 'below'} the 20-day moving average ({ma20:.2f}).")
    return analysis.model_copy(update={"stock_name": html.unescape(analysis.stock_name), "technical_commentary": comments})


def localize_market(market, language: str):
    if language != "en-US":
        if market.is_loading:
            return market
        if market.status == "unavailable":
            return market.model_copy(update={"summary": "数据不可用，无法判断市场状态。", "action_bias": "", "position_guidance": "", "notes": []})
        summary = {"risk_on": "所获取标的的价格趋势总体偏强。", "neutral": "所获取标的的价格趋势存在分化。", "risk_off": "所获取标的的价格趋势总体偏弱。"}[market.regime]
        notes = [f"{len(market.indices)} 个标的中，{sum(i.above_ma20 for i in market.indices)} 个站上 20 日均线。", f"{len(market.indices)} 个标的中，{sum(i.above_ma60 for i in market.indices)} 个站上 60 日均线。"]
        return market.model_copy(update={"summary": summary, "action_bias": "基于历史行情的趋势指标，并非预测或仓位建议。", "position_guidance": "", "notes": notes})
    if market.is_loading:
        return market.model_copy(update={"summary": "Loading market data.", "action_bias": "Waiting for source data.", "position_guidance": "", "notes": []})
    if market.status == "unavailable":
        return market.model_copy(update={"summary": "Market data is unavailable. There is not enough evidence to classify this market.", "action_bias": "", "position_guidance": "", "notes": []})
    summaries = {
        "risk_on": "The retrieved instruments show broadly positive price trends.",
        "neutral": "The retrieved instruments show mixed price trends.",
        "risk_off": "The retrieved instruments show broadly weaker price trends.",
    }
    notes = [f"{sum(i.above_ma20 for i in market.indices)} of {len(market.indices)} instruments are above their 20-day moving average.",
             f"{sum(i.above_ma60 for i in market.indices)} of {len(market.indices)} instruments are above their 60-day moving average."]
    return market.model_copy(update={"summary": summaries[market.regime], "action_bias": "Historical trend indicator; not a forecast or allocation recommendation.", "position_guidance": "", "notes": notes})


def validate_response_language(output, language: str):
    if language == "en-US":
        text = " ".join([output.summary, *output.actions, *output.data_gaps])
        han = len(re.findall(r"[\u3400-\u9fff]", text))
        if han > 16 or (han > 4 and han > len(text) * 0.2):
            raise ValueError("Use English for the report, actions and data gaps. The question's language does not override the requested response language.")
    return output


def localize_portfolio(analysis, language: str):
    if language != "en-US":
        return analysis
    labels = {
        "当前没有持仓，可先从单股分析页添加股票后再查看组合建议。": "No positions yet. Add a position before requesting a portfolio review.",
        "组合集中度偏高，建议分散至 3 只以上标的。": "The portfolio contains two or fewer positions; concentration may be high.",
        "高风险信号持仓占比较高，建议优先复核止损位。": "A substantial share of positions has weaker technical signals. Review the underlying evidence.",
        "当前组合风险可控，建议继续跟踪消息和技术面变化。": "Continue monitoring company news and historical technical indicators; these do not capture all portfolio risks.",
        "继续持有观察": "Monitor the source data and company news.",
        "建议降低仓位或设置更紧止损": "Weaker technical signals; review the evidence and your risk limits.",
    }
    return analysis.model_copy(update={
        "rebalance_suggestions": [labels.get(item, "An observation is unavailable in English.") for item in analysis.rebalance_suggestions],
        "positions": [item.model_copy(update={"suggestion": labels.get(item.suggestion, "Review the underlying source data.")}) for item in analysis.positions],
    })


def localize_fallback(response, language: str):
    """Keep a source-only fallback readable when the model is unavailable."""
    if language != "en-US":
        return response
    payload = response.payload or {}
    quote = payload.get("quote") or {}
    lines = ["## Available source data", "The research model was unavailable. This is a limited source-data response."]
    if quote and payload.get("stock_code"):
        lines.append(f"Company: {payload.get('stock_name') or payload['stock_code']} ({payload['stock_code']}).")
        currency = (payload.get("metadata") or {}).get("currency") or {"us": "USD", "hk": "HKD"}.get(payload.get("market"), "CNY")
        lines.append(f"Last available price: {quote.get('current_price', 'Unavailable')} {currency}; daily change: {quote.get('change_pct', 'Unavailable')}%.")
        date = (payload.get("metadata") or {}).get("data_as_of") or "Unknown"
        lines.append(f"Historical or delayed price data as of {date}. Retrieval time is not the quote time.")
    elif response.intent == "greeting":
        lines = ["Hello! Research companies, filings, news and market data here."]
    else:
        lines.append("Open the research tools for available market data. Company or news coverage may be incomplete.")
    response.summary = "\n\n".join(lines)
    response.actions = ["Research AAPL earnings in English", "Latest NVIDIA news in English"]
    response.payload.setdefault("_meta", {})["response_language"] = language
    return response
