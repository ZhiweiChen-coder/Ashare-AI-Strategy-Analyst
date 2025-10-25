import numpy as np

def trend_signal(df):
    # 简单趋势策略：均线金叉死叉
    if df['MA5'].iloc[-1] > df['MA20'].iloc[-1]:
        return 'buy', 0.8, 'MA5上穿MA20，趋势向好'
    elif df['MA5'].iloc[-1] < df['MA20'].iloc[-1]:
        return 'sell', 0.8, 'MA5下穿MA20，趋势转弱'
    else:
        return 'hold', 0.5, '均线无明显交叉'

def breakout_signal(df):
    # 简单突破策略：收盘价突破近20日高点/低点
    recent_high = df['close'].iloc[-20:].max()
    recent_low = df['close'].iloc[-20:].min()
    close = df['close'].iloc[-1]
    if close >= recent_high:
        return 'buy', 0.9, '收盘价突破20日新高，可能启动'
    elif close <= recent_low:
        return 'sell', 0.9, '收盘价跌破20日新低，需警惕风险'
    else:
        return 'hold', 0.5, '未突破区间高低点'

def ai_sentiment_signal(ai_sentiment):
    # AI情感分析信号，ai_sentiment为[-1,1]区间，>0.3买，<-0.3卖
    if ai_sentiment is None:
        return 'hold', 0.5, '无AI情感数据'
    if ai_sentiment > 0.3:
        return 'buy', 0.7, f'AI情感积极({ai_sentiment:.2f})'
    elif ai_sentiment < -0.3:
        return 'sell', 0.7, f'AI情感消极({ai_sentiment:.2f})'
    else:
        return 'hold', 0.5, f'AI情感中性({ai_sentiment:.2f})'

def select_stocks(stock_data_dict, ai_sentiments=None):
    """
    stock_data_dict: {code: df, ...}
    ai_sentiments: {code: float, ...}  # AI情感分数，可选
    return: {code: {'signal': 'buy/sell/hold', 'score': float, 'reason': str}}
    """
    results = {}
    for code, df in stock_data_dict.items():
        # 趋势信号
        trend_sig, trend_score, trend_reason = trend_signal(df)
        # 突破信号
        breakout_sig, breakout_score, breakout_reason = breakout_signal(df)
        # AI情感信号
        ai_score = ai_sentiments.get(code) if ai_sentiments else None
        ai_sig, ai_sent_score, ai_reason = ai_sentiment_signal(ai_score)
        # 综合决策（可加权平均/优先级/投票等）
        signals = [trend_sig, breakout_sig, ai_sig]
        scores = [trend_score, breakout_score, ai_sent_score]
        reasons = [trend_reason, breakout_reason, ai_reason]
        # 简单投票法
        buy_votes = signals.count('buy')
        sell_votes = signals.count('sell')
        if buy_votes > sell_votes:
            final_signal = 'buy'
        elif sell_votes > buy_votes:
            final_signal = 'sell'
        else:
            final_signal = 'hold'
        final_score = np.mean(scores)
        final_reason = '; '.join(reasons)
        results[code] = {'signal': final_signal, 'score': final_score, 'reason': final_reason}
    return results 