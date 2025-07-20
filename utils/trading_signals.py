"""
交易信号生成模块

根据技术指标生成买卖信号和投资建议
"""

import pandas as pd
from typing import List
from .logger import get_logger

logger = get_logger(__name__)


def generate_trading_signals(df: pd.DataFrame) -> List[str]:
    """
    生成交易信号和建议
    
    Args:
        df: 包含技术指标的DataFrame
        
    Returns:
        交易信号列表
    """
    signals = []

    # 检查数据是否足够进行分析
    if len(df) < 2:
        logger.warning("数据不足，无法进行技术分析")
        return ["数据不足，无法进行技术分析"]

    try:
        logger.info("开始生成交易信号")
        
        # MACD信号
        macd_signal = _analyze_macd(df)
        if macd_signal:
            signals.append(macd_signal)

        # KDJ信号
        kdj_signal = _analyze_kdj(df)
        if kdj_signal:
            signals.append(kdj_signal)

        # RSI信号
        rsi_signal = _analyze_rsi(df)
        if rsi_signal:
            signals.append(rsi_signal)

        # 布林带信号
        boll_signal = _analyze_boll(df)
        if boll_signal:
            signals.append(boll_signal)

        # DMI信号
        dmi_signal = _analyze_dmi(df)
        if dmi_signal:
            signals.append(dmi_signal)

        # 成交量信号
        volume_signal = _analyze_volume(df)
        if volume_signal:
            signals.append(volume_signal)

        # ROC动量信号
        roc_signal = _analyze_roc(df)
        if roc_signal:
            signals.append(roc_signal)

        logger.info(f"成功生成{len(signals)}个交易信号")
        
    except Exception as e:
        error_msg = f"生成交易信号时出错: {str(e)}"
        logger.error(error_msg)
        signals.append(error_msg)

    return signals if signals else ["当前无明显交易信号"]


def _analyze_macd(df: pd.DataFrame) -> str:
    """分析MACD指标"""
    try:
        if 'MACD' not in df.columns or len(df) < 2:
            return ""
            
        current_macd = df['MACD'].iloc[-1]
        prev_macd = df['MACD'].iloc[-2]
        
        if current_macd > 0 >= prev_macd:
            return "MACD金叉形成，可能上涨"
        elif current_macd < 0 <= prev_macd:
            return "MACD死叉形成，可能下跌"
            
    except Exception as e:
        logger.error(f"MACD分析失败: {str(e)}")
    
    return ""


def _analyze_kdj(df: pd.DataFrame) -> str:
    """分析KDJ指标"""
    try:
        if 'K' not in df.columns or 'D' not in df.columns:
            return ""
            
        current_k = df['K'].iloc[-1]
        current_d = df['D'].iloc[-1]
        
        if current_k < 20 and current_d < 20:
            return "KDJ超卖，可能反弹"
        elif current_k > 80 and current_d > 80:
            return "KDJ超买，注意回调"
            
    except Exception as e:
        logger.error(f"KDJ分析失败: {str(e)}")
    
    return ""


def _analyze_rsi(df: pd.DataFrame) -> str:
    """分析RSI指标"""
    try:
        if 'RSI' not in df.columns:
            return ""
            
        current_rsi = df['RSI'].iloc[-1]
        
        if current_rsi < 20:
            return "RSI超卖，可能反弹"
        elif current_rsi > 80:
            return "RSI超买，注意回调"
            
    except Exception as e:
        logger.error(f"RSI分析失败: {str(e)}")
    
    return ""


def _analyze_boll(df: pd.DataFrame) -> str:
    """分析布林带指标"""
    try:
        required_cols = ['close', 'BOLL_UP', 'BOLL_LOW']
        if not all(col in df.columns for col in required_cols):
            return ""
            
        current_price = df['close'].iloc[-1]
        boll_up = df['BOLL_UP'].iloc[-1]
        boll_low = df['BOLL_LOW'].iloc[-1]
        
        if current_price > boll_up:
            return "股价突破布林上轨，超买状态"
        elif current_price < boll_low:
            return "股价跌破布林下轨，超卖状态"
            
    except Exception as e:
        logger.error(f"布林带分析失败: {str(e)}")
    
    return ""


def _analyze_dmi(df: pd.DataFrame) -> str:
    """分析DMI指标"""
    try:
        required_cols = ['PDI', 'MDI']
        if not all(col in df.columns for col in required_cols) or len(df) < 2:
            return ""
            
        current_pdi = df['PDI'].iloc[-1]
        current_mdi = df['MDI'].iloc[-1]
        prev_pdi = df['PDI'].iloc[-2]
        prev_mdi = df['MDI'].iloc[-2]
        
        if current_pdi > current_mdi and prev_pdi <= prev_mdi:
            return "DMI金叉，上升趋势形成"
        elif current_pdi < current_mdi and prev_pdi >= prev_mdi:
            return "DMI死叉，下降趋势形成"
            
    except Exception as e:
        logger.error(f"DMI分析失败: {str(e)}")
    
    return ""


def _analyze_volume(df: pd.DataFrame) -> str:
    """分析成交量指标"""
    try:
        if 'VR' not in df.columns:
            return ""
            
        current_vr = df['VR'].iloc[-1]
        
        if current_vr > 160:
            return "VR大于160，市场活跃度高"
        elif current_vr < 40:
            return "VR小于40，市场活跃度低"
            
    except Exception as e:
        logger.error(f"成交量分析失败: {str(e)}")
    
    return ""


def _analyze_roc(df: pd.DataFrame) -> str:
    """分析ROC动量指标"""
    try:
        required_cols = ['ROC', 'MAROC']
        if not all(col in df.columns for col in required_cols) or len(df) < 2:
            return ""
            
        current_roc = df['ROC'].iloc[-1]
        current_maroc = df['MAROC'].iloc[-1]
        prev_roc = df['ROC'].iloc[-2]
        prev_maroc = df['MAROC'].iloc[-2]
        
        if current_roc > current_maroc and prev_roc <= prev_maroc:
            return "ROC上穿均线，上升动能增强"
        elif current_roc < current_maroc and prev_roc >= prev_maroc:
            return "ROC下穿均线，上升动能减弱"
            
    except Exception as e:
        logger.error(f"ROC分析失败: {str(e)}")
    
    return "" 