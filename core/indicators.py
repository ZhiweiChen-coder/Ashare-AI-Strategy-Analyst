"""
技术指标计算模块

封装所有技术指标的计算逻辑，提供统一的计算接口
"""

import pandas as pd
import numpy as np
import MyTT as mt
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""
    
    def __init__(self):
        """初始化技术指标计算器"""
        logger.info("技术指标计算器已初始化")
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        计算所有技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            包含所有技术指标的DataFrame，失败时返回None
        """
        if df is None or df.empty:
            logger.error("输入数据为空，无法计算技术指标")
            return None
        
        # 检查数据量是否足够计算技术指标
        if len(df) < 60:
            logger.warning(f"数据量不足 ({len(df)} 条)，可能影响技术指标计算准确性")
        
        try:
            logger.info("开始计算技术指标")
            df_with_indicators = df.copy()
            
            # 提取基础数据
            close = np.array(df['close'])
            open_price = np.array(df['open'])
            high = np.array(df['high'])
            low = np.array(df['low'])
            volume = np.array(df['volume'])
            
            # 计算各类技术指标
            self._calculate_trend_indicators(df_with_indicators, close, high, low, volume)
            self._calculate_oscillator_indicators(df_with_indicators, close, high, low)
            self._calculate_volume_indicators(df_with_indicators, close, open_price, high, low, volume)
            self._calculate_momentum_indicators(df_with_indicators, close)
            self._calculate_moving_averages(df_with_indicators, close)
            self._calculate_volatility_indicators(df_with_indicators, close, high, low)
            
            logger.info("技术指标计算完成")
            return df_with_indicators
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
            return None
    
    def _calculate_trend_indicators(self, df: pd.DataFrame, close: np.ndarray, 
                                   high: np.ndarray, low: np.ndarray, volume: np.ndarray):
        """计算趋势指标"""
        try:
            logger.debug("计算趋势指标...")
            
            # MACD
            dif, dea, macd = mt.MACD(close)
            df['MACD'] = macd
            df['DIF'] = dif
            df['DEA'] = dea
            
            # TRIX - 三重指数平滑平均线
            trix, trma = mt.TRIX(close)
            df['TRIX'] = trix
            df['TRMA'] = trma
            
            # DMI - 动向指标
            pdi, mdi, adx, adxr = mt.DMI(close, high, low)
            df['PDI'] = pdi
            df['MDI'] = mdi
            df['ADX'] = adx
            df['ADXR'] = adxr
            
            # DMA - 平行线差指标
            dif_dma, difma_dma = mt.DMA(close)
            df['DIF_DMA'] = dif_dma
            df['DIFMA_DMA'] = difma_dma
            
            logger.debug("趋势指标计算完成")
            
        except Exception as e:
            logger.error(f"计算趋势指标失败: {str(e)}")
            raise
    
    def _calculate_oscillator_indicators(self, df: pd.DataFrame, close: np.ndarray, 
                                        high: np.ndarray, low: np.ndarray):
        """计算摆动指标"""
        try:
            logger.debug("计算摆动指标...")
            
            # KDJ - 随机指标
            k, d, j = mt.KDJ(close, high, low)
            df['K'] = k
            df['D'] = d
            df['J'] = j
            
            # RSI - 相对强弱指标
            rsi = mt.RSI(close, N=14)
            df['RSI'] = np.nan_to_num(rsi, nan=50)
            
            # PSY - 心理线
            psy, psyma = mt.PSY(close)
            df['PSY'] = psy
            df['PSYMA'] = psyma
            
            # WR - 威廉指标
            wr, wr1 = mt.WR(close, high, low)
            df['WR'] = wr
            df['WR1'] = wr1
            
            # BIAS - 乖离率
            bias1, bias2, bias3 = mt.BIAS(close)
            df['BIAS1'] = bias1
            df['BIAS2'] = bias2
            df['BIAS3'] = bias3
            
            # CCI - 顺势指标
            cci = mt.CCI(close, high, low)
            df['CCI'] = cci
            
            logger.debug("摆动指标计算完成")
            
        except Exception as e:
            logger.error(f"计算摆动指标失败: {str(e)}")
            raise
    
    def _calculate_volume_indicators(self, df: pd.DataFrame, close: np.ndarray, 
                                    open_price: np.ndarray, high: np.ndarray, 
                                    low: np.ndarray, volume: np.ndarray):
        """计算成交量指标"""
        try:
            logger.debug("计算成交量指标...")
            
            # VR - 成交量比率
            vr = mt.VR(close, volume)
            df['VR'] = vr
            
            # AR/BR - 人气意愿指标
            ar, br = mt.BRAR(open_price, close, high, low)
            df['AR'] = ar
            df['BR'] = br
            
            # EMV - 简易波动指标
            emv, maemv = mt.EMV(high, low, volume)
            df['EMV'] = emv
            df['MAEMV'] = maemv
            
            logger.debug("成交量指标计算完成")
            
        except Exception as e:
            logger.error(f"计算成交量指标失败: {str(e)}")
            raise
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame, close: np.ndarray):
        """计算动量指标"""
        try:
            logger.debug("计算动量指标...")
            
            # ROC - 变动率
            roc, maroc = mt.ROC(close)
            df['ROC'] = roc
            df['MAROC'] = maroc
            
            # MTM - 动量指标
            mtm, mtmma = mt.MTM(close)
            df['MTM'] = mtm
            df['MTMMA'] = mtmma
            
            # DPO - 区间振荡指标
            dpo, madpo = mt.DPO(close)
            df['DPO'] = dpo
            df['MADPO'] = madpo
            
            logger.debug("动量指标计算完成")
            
        except Exception as e:
            logger.error(f"计算动量指标失败: {str(e)}")
            raise
    
    def _calculate_moving_averages(self, df: pd.DataFrame, close: np.ndarray):
        """计算移动平均线"""
        try:
            logger.debug("计算移动平均线...")
            
            # 各期移动平均线
            df['MA5'] = mt.MA(close, 5)
            df['MA10'] = mt.MA(close, 10)
            df['MA20'] = mt.MA(close, 20)
            df['MA60'] = mt.MA(close, 60)
            
            logger.debug("移动平均线计算完成")
            
        except Exception as e:
            logger.error(f"计算移动平均线失败: {str(e)}")
            raise
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame, close: np.ndarray,
                                        high: np.ndarray, low: np.ndarray):
        """计算波动率指标"""
        try:
            logger.debug("计算波动率指标...")
            
            # 布林带
            upper, mid, lower = mt.BOLL(close)
            df['BOLL_UP'] = upper
            df['BOLL_MID'] = mid
            df['BOLL_LOW'] = lower
            
            # ATR - 真实波动幅度
            atr = mt.ATR(close, high, low)
            df['ATR'] = atr
            
            logger.debug("波动率指标计算完成")
            
        except Exception as e:
            logger.error(f"计算波动率指标失败: {str(e)}")
            raise
    
    def get_latest_indicator_values(self, df: pd.DataFrame) -> dict:
        """
        获取最新的技术指标值
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            最新指标值字典
        """
        if df is None or df.empty:
            logger.error("无法获取最新指标值：数据为空")
            return {}
        
        try:
            latest_values = {}
            indicator_columns = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
            
            for col in indicator_columns:
                if col in df.columns:
                    latest_values[col] = df[col].iloc[-1]
            
            return latest_values
            
        except Exception as e:
            logger.error(f"获取最新指标值失败: {str(e)}")
            return {}
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        验证输入数据是否符合技术指标计算要求
        
        Args:
            df: 待验证的DataFrame
            
        Returns:
            (是否有效, 错误信息)
        """
        if df is None:
            return False, "数据为空"
        
        if df.empty:
            return False, "DataFrame为空"
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"缺少必要列: {missing_columns}"
        
        if len(df) < 10:
            return False, f"数据量过少: {len(df)} 条，建议至少60条数据"
        
        # 检查数据完整性
        for col in required_columns:
            if df[col].isna().all():
                return False, f"列 {col} 全为空值"
        
        return True, "数据验证通过" 