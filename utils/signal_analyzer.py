"""
技术指标信号分析模块

根据技术指标的数值和趋势生成买卖信号
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class SignalAnalyzer:
    """技术指标信号分析器"""
    
    def __init__(self):
        """初始化信号分析器"""
        self.signal_strength = {
            'STRONG_BUY': 5,
            'BUY': 4,
            'WEAK_BUY': 3,
            'NEUTRAL': 2,
            'WEAK_SELL': 1,
            'SELL': 0,
            'STRONG_SELL': -1
        }
    
    def analyze_all_signals(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        分析所有技术指标信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            信号分析结果字典
        """
        if df is None or df.empty:
            logger.error("数据为空，无法进行信号分析")
            return {}
        
        try:
            signals = {}
            
            # 趋势信号
            signals['trend_signals'] = self._analyze_trend_signals(df)
            
            # 摆动指标信号
            signals['oscillator_signals'] = self._analyze_oscillator_signals(df)
            
            # 成交量信号
            signals['volume_signals'] = self._analyze_volume_signals(df)
            
            # 移动平均线信号
            signals['ma_signals'] = self._analyze_ma_signals(df)
            
            # 综合信号评分
            signals['overall_score'] = self._calculate_overall_score(signals)
            signals['overall_signal'] = self._get_signal_description(signals['overall_score'])
            
            # 详细信号说明
            signals['signal_details'] = self._generate_signal_details(df, signals)
            
            logger.info(f"信号分析完成，综合评分: {signals['overall_score']}")
            return signals
            
        except Exception as e:
            logger.error(f"信号分析失败: {str(e)}")
            return {}
    
    def _analyze_trend_signals(self, df: pd.DataFrame) -> Dict[str, any]:
        """分析趋势指标信号"""
        signals = {}
        
        try:
            # MACD信号
            if 'MACD' in df.columns and 'DIF' in df.columns and 'DEA' in df.columns:
                macd = df['MACD'].iloc[-1]
                dif = df['DIF'].iloc[-1] 
                dea = df['DEA'].iloc[-1]
                prev_dif = df['DIF'].iloc[-2] if len(df) > 1 else dif
                prev_dea = df['DEA'].iloc[-2] if len(df) > 1 else dea
                
                # MACD金叉死叉
                if dif > dea and prev_dif <= prev_dea:
                    signals['MACD'] = {'signal': 'BUY', 'description': 'MACD金叉形成'}
                elif dif < dea and prev_dif >= prev_dea:
                    signals['MACD'] = {'signal': 'SELL', 'description': 'MACD死叉形成'}
                elif macd > 0 and dif > dea:
                    signals['MACD'] = {'signal': 'WEAK_BUY', 'description': 'MACD多头趋势'}
                else:
                    signals['MACD'] = {'signal': 'NEUTRAL', 'description': 'MACD信号中性'}
            
            # DMI信号  
            if all(col in df.columns for col in ['PDI', 'MDI', 'ADX']):
                pdi = df['PDI'].iloc[-1]
                mdi = df['MDI'].iloc[-1] 
                adx = df['ADX'].iloc[-1]
                
                if pdi > mdi and adx > 25:
                    signals['DMI'] = {'signal': 'BUY', 'description': '上涨趋势强劲'}
                elif mdi > pdi and adx > 25:
                    signals['DMI'] = {'signal': 'SELL', 'description': '下跌趋势强劲'}
                else:
                    signals['DMI'] = {'signal': 'NEUTRAL', 'description': '趋势不明确'}
            
            # TRIX信号
            if 'TRIX' in df.columns and 'TRMA' in df.columns:
                trix = df['TRIX'].iloc[-1]
                trma = df['TRMA'].iloc[-1]
                
                if trix > trma and trix > 0:
                    signals['TRIX'] = {'signal': 'BUY', 'description': 'TRIX多头信号'}
                elif trix < trma and trix < 0:
                    signals['TRIX'] = {'signal': 'SELL', 'description': 'TRIX空头信号'}
                else:
                    signals['TRIX'] = {'signal': 'NEUTRAL', 'description': 'TRIX中性'}
                    
        except Exception as e:
            logger.error(f"趋势信号分析失败: {str(e)}")
            
        return signals
    
    def _analyze_oscillator_signals(self, df: pd.DataFrame) -> Dict[str, any]:
        """分析摆动指标信号"""
        signals = {}
        
        try:
            # RSI信号
            if 'RSI' in df.columns:
                rsi = df['RSI'].iloc[-1]
                if rsi > 80:
                    signals['RSI'] = {'signal': 'SELL', 'description': 'RSI超买'}
                elif rsi > 70:
                    signals['RSI'] = {'signal': 'WEAK_SELL', 'description': 'RSI偏高'}
                elif rsi < 20:
                    signals['RSI'] = {'signal': 'BUY', 'description': 'RSI超卖'}
                elif rsi < 30:
                    signals['RSI'] = {'signal': 'WEAK_BUY', 'description': 'RSI偏低'}
                else:
                    signals['RSI'] = {'signal': 'NEUTRAL', 'description': 'RSI正常范围'}
            
            # KDJ信号
            if all(col in df.columns for col in ['K', 'D', 'J']):
                k = df['K'].iloc[-1]
                d = df['D'].iloc[-1]
                j = df['J'].iloc[-1]
                prev_k = df['K'].iloc[-2] if len(df) > 1 else k
                prev_d = df['D'].iloc[-2] if len(df) > 1 else d
                
                # KDJ金叉死叉
                if k > d and prev_k <= prev_d and k < 80:
                    signals['KDJ'] = {'signal': 'BUY', 'description': 'KDJ金叉买入'}
                elif k < d and prev_k >= prev_d and k > 20:
                    signals['KDJ'] = {'signal': 'SELL', 'description': 'KDJ死叉卖出'}
                elif k > 80 and d > 80:
                    signals['KDJ'] = {'signal': 'WEAK_SELL', 'description': 'KDJ超买区域'}
                elif k < 20 and d < 20:
                    signals['KDJ'] = {'signal': 'WEAK_BUY', 'description': 'KDJ超卖区域'}
                else:
                    signals['KDJ'] = {'signal': 'NEUTRAL', 'description': 'KDJ中性'}
            
            # WR信号
            if 'WR' in df.columns:
                wr = df['WR'].iloc[-1]
                if wr > 80:
                    signals['WR'] = {'signal': 'BUY', 'description': '威廉指标超卖'}
                elif wr < 20:
                    signals['WR'] = {'signal': 'SELL', 'description': '威廉指标超买'}
                else:
                    signals['WR'] = {'signal': 'NEUTRAL', 'description': '威廉指标中性'}
            
            # CCI信号
            if 'CCI' in df.columns:
                cci = df['CCI'].iloc[-1]
                if cci > 100:
                    signals['CCI'] = {'signal': 'WEAK_SELL', 'description': 'CCI超买'}
                elif cci < -100:
                    signals['CCI'] = {'signal': 'WEAK_BUY', 'description': 'CCI超卖'}
                else:
                    signals['CCI'] = {'signal': 'NEUTRAL', 'description': 'CCI正常范围'}
            
            # PSY信号
            if 'PSY' in df.columns and 'PSYMA' in df.columns:
                psy = df['PSY'].iloc[-1]
                psyma = df['PSYMA'].iloc[-1]
                
                if psy > 75:
                    signals['PSY'] = {'signal': 'WEAK_SELL', 'description': '心理线过热，市场情绪过于乐观'}
                elif psy < 25:
                    signals['PSY'] = {'signal': 'WEAK_BUY', 'description': '心理线过冷，市场情绪过于悲观'}
                elif psy > psyma and psy > 50:
                    signals['PSY'] = {'signal': 'WEAK_BUY', 'description': '心理线向上，市场信心增强'}
                elif psy < psyma and psy < 50:
                    signals['PSY'] = {'signal': 'WEAK_SELL', 'description': '心理线向下，市场信心不足'}
                else:
                    signals['PSY'] = {'signal': 'NEUTRAL', 'description': '心理线中性'}
                    
        except Exception as e:
            logger.error(f"摆动指标信号分析失败: {str(e)}")
            
        return signals
    
    def _analyze_volume_signals(self, df: pd.DataFrame) -> Dict[str, any]:
        """分析成交量指标信号"""
        signals = {}
        
        try:
            # OBV信号
            if 'OBV' in df.columns and len(df) > 5:
                obv_current = df['OBV'].iloc[-1]
                obv_prev = df['OBV'].iloc[-5]  # 5日前
                close_current = df['close'].iloc[-1]
                close_prev = df['close'].iloc[-5]
                
                # 量价背离
                if close_current > close_prev and obv_current < obv_prev:
                    signals['OBV'] = {'signal': 'WEAK_SELL', 'description': 'OBV量价背离，价涨量跌'}
                elif close_current < close_prev and obv_current > obv_prev:
                    signals['OBV'] = {'signal': 'WEAK_BUY', 'description': 'OBV量价背离，价跌量涨'}
                elif close_current > close_prev and obv_current > obv_prev:
                    signals['OBV'] = {'signal': 'WEAK_BUY', 'description': 'OBV量价同步上涨'}
                else:
                    signals['OBV'] = {'signal': 'NEUTRAL', 'description': 'OBV信号中性'}
            
            # CMF信号
            if 'CMF' in df.columns:
                cmf = df['CMF'].iloc[-1]
                if cmf > 0.1:
                    signals['CMF'] = {'signal': 'WEAK_BUY', 'description': '资金流入'}
                elif cmf < -0.1:
                    signals['CMF'] = {'signal': 'WEAK_SELL', 'description': '资金流出'}
                else:
                    signals['CMF'] = {'signal': 'NEUTRAL', 'description': '资金流动平衡'}
            
            # VR信号
            if 'VR' in df.columns:
                vr = df['VR'].iloc[-1]
                if vr > 350:
                    signals['VR'] = {'signal': 'WEAK_SELL', 'description': '成交量过热'}
                elif vr < 40:
                    signals['VR'] = {'signal': 'WEAK_BUY', 'description': '成交量萎缩，可能反弹'}
                else:
                    signals['VR'] = {'signal': 'NEUTRAL', 'description': '成交量正常'}
                    
        except Exception as e:
            logger.error(f"成交量指标信号分析失败: {str(e)}")
            
        return signals
    
    def _analyze_ma_signals(self, df: pd.DataFrame) -> Dict[str, any]:
        """分析移动平均线信号"""
        signals = {}
        
        try:
            if all(col in df.columns for col in ['close', 'MA5', 'MA10', 'MA20']):
                close = df['close'].iloc[-1]
                ma5 = df['MA5'].iloc[-1]
                ma10 = df['MA10'].iloc[-1] 
                ma20 = df['MA20'].iloc[-1]
                
                # 均线排列
                if ma5 > ma10 > ma20 and close > ma5:
                    signals['MA'] = {'signal': 'BUY', 'description': '多头排列，价格在均线上方'}
                elif ma5 < ma10 < ma20 and close < ma5:
                    signals['MA'] = {'signal': 'SELL', 'description': '空头排列，价格在均线下方'}
                elif close > ma20:
                    signals['MA'] = {'signal': 'WEAK_BUY', 'description': '价格在长期均线上方'}
                elif close < ma20:
                    signals['MA'] = {'signal': 'WEAK_SELL', 'description': '价格在长期均线下方'}
                else:
                    signals['MA'] = {'signal': 'NEUTRAL', 'description': '均线信号中性'}
                    
        except Exception as e:
            logger.error(f"移动平均线信号分析失败: {str(e)}")
            
        return signals
    
    def _calculate_overall_score(self, signals: Dict[str, any]) -> int:
        """计算综合信号评分"""
        total_score = 0
        signal_count = 0
        
        for category in ['trend_signals', 'oscillator_signals', 'volume_signals', 'ma_signals']:
            if category in signals:
                for indicator, signal_info in signals[category].items():
                    if isinstance(signal_info, dict) and 'signal' in signal_info:
                        score = self.signal_strength.get(signal_info['signal'], 2)
                        total_score += score
                        signal_count += 1
        
        return int(total_score / signal_count) if signal_count > 0 else 2
    
    def _get_signal_description(self, score: int) -> str:
        """根据评分获取信号描述"""
        score_map = {
            5: '强烈买入',
            4: '买入', 
            3: '弱买入',
            2: '中性',
            1: '弱卖出',
            0: '卖出',
            -1: '强烈卖出'
        }
        return score_map.get(score, '未知信号')
    
    def _generate_signal_details(self, df: pd.DataFrame, signals: Dict[str, any]) -> List[str]:
        """生成详细的信号说明"""
        details = []
        
        for category in ['trend_signals', 'oscillator_signals', 'volume_signals', 'ma_signals']:
            if category in signals:
                for indicator, signal_info in signals[category].items():
                    if isinstance(signal_info, dict) and 'description' in signal_info:
                        signal_strength = signal_info['signal']
                        description = signal_info['description']
                        details.append(f"【{indicator}】{description} ({signal_strength})")
        
        return details 