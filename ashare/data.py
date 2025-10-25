"""
股票数据获取模块

提供统一的股票数据获取接口，支持多种数据源
"""

import pandas as pd
from typing import Dict, List, Optional
from ashare.logging import get_logger

# 尝试导入数据源
try:
    import sys
    from pathlib import Path
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # 尝试导入旧的Ashare模块
    try:
        import Ashare as as_api
    except ImportError:
        # 如果找不到，尝试从备份加载
        backup_ashare = project_root / '_backup' / '_old_Ashare.py'
        if backup_ashare.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("Ashare", backup_ashare)
            as_api = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(as_api)
        else:
            as_api = None
except Exception as e:
    as_api = None
    print(f"警告: 无法加载Ashare数据源模块: {e}")

logger = get_logger(__name__)


class DataFetcher:
    """股票数据获取器"""
    
    def __init__(self, default_count: int = 120):
        """
        初始化数据获取器
        
        Args:
            default_count: 默认获取的数据条数
        """
        self.default_count = default_count
        self.data_cache = {}
        logger.info(f"数据获取器已初始化，默认获取{default_count}条数据")
    
    def fetch_stock_data(self, code: str, count: Optional[int] = None, 
                        frequency: str = '1d') -> Optional[pd.DataFrame]:
        """
        获取单只股票数据
        
        Args:
            code: 股票代码
            count: 获取的数据条数
            frequency: 数据频率 ('1d', '1w', '1m' 等)
            
        Returns:
            股票数据DataFrame，失败时返回None
        """
        count = count or self.default_count
        cache_key = f"{code}_{count}_{frequency}"
        
        # 检查缓存
        if cache_key in self.data_cache:
            logger.debug(f"从缓存获取股票数据: {code}")
            return self.data_cache[cache_key]
        
        try:
            logger.info(f"正在获取股票 {code} 的数据...")
            df = as_api.get_price(code, count=count, frequency=frequency)
            
            # 检查数据是否有效
            if df is None or df.empty:
                logger.warning(f"股票 {code} 返回空数据")
                self._log_stock_code_help(code)
                return None
            
            logger.info(f"成功获取 {code} 数据，共 {len(df)} 条记录")
            logger.info(f"数据时间范围: {df.index[0]} 到 {df.index[-1]}")
            
            # 缓存数据
            self.data_cache[cache_key] = df
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {code} 数据失败: {str(e)}")
            self._log_stock_code_help(code)
            return None
    
    def fetch_multiple_stocks(self, codes: List[str], count: Optional[int] = None,
                             frequency: str = '1d') -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据
        
        Args:
            codes: 股票代码列表
            count: 获取的数据条数
            frequency: 数据频率
            
        Returns:
            股票代码到DataFrame的映射
        """
        logger.info(f"开始批量获取{len(codes)}只股票的数据")
        result = {}
        
        for code in codes:
            df = self.fetch_stock_data(code, count, frequency)
            if df is not None:
                result[code] = df
        
        logger.info(f"成功获取{len(result)}只股票的数据")
        return result
    
    def get_stock_info(self, code: str) -> Dict[str, str]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票基本信息字典
        """
        try:
            # 这里可以扩展获取更多股票信息
            return {
                'code': code,
                'exchange': self._get_exchange_from_code(code),
                'status': 'active'  # 可以扩展获取实际状态
            }
        except Exception as e:
            logger.error(f"获取股票 {code} 信息失败: {str(e)}")
            return {'code': code, 'exchange': 'unknown', 'status': 'unknown'}
    
    def validate_stock_code(self, code: str) -> bool:
        """
        验证股票代码格式
        
        Args:
            code: 股票代码
            
        Returns:
            是否为有效格式
        """
        if not code:
            return False
        
        code = code.upper()
        
        # 检查上交所格式 (SH开头)
        if code.startswith('SH') and len(code) == 8:
            return True
        
        # 检查深交所格式 (SZ开头)
        if code.startswith('SZ') and len(code) == 8:
            return True
        
        # 检查港股格式 (以.HK结尾)
        if code.endswith('.HK') and len(code) >= 6:
            return True
        
        logger.warning(f"股票代码格式可能不正确: {code}")
        return False
    
    def clear_cache(self):
        """清空数据缓存"""
        self.data_cache.clear()
        logger.info("数据缓存已清空")
    
    def get_cache_info(self) -> Dict[str, int]:
        """获取缓存信息"""
        return {
            'cached_items': len(self.data_cache),
            'cache_keys': list(self.data_cache.keys())
        }
    
    def _get_exchange_from_code(self, code: str) -> str:
        """从股票代码推断交易所"""
        code = code.upper()
        if code.startswith('SH'):
            return '上交所'
        elif code.startswith('SZ'):
            return '深交所'
        elif code.endswith('.HK'):
            return '港交所'
        else:
            return '未知'
    
    def _log_stock_code_help(self, code: str):
        """记录股票代码格式帮助信息"""
        logger.info("请检查股票代码格式是否正确。常见格式:")
        logger.info("  - 上交所: sh000001 (上证指数), sh600036 (招商银行)")
        logger.info("  - 深交所: sz399001 (深证成指), sz000001 (平安银行)")
        logger.info("  - 港股: 00700.HK (腾讯控股)")
        logger.info("建议检查:")
        logger.info("  1. 股票代码格式是否正确")
        logger.info("  2. 网络连接是否正常")
        logger.info("  3. 股票是否已停牌或退市")
    
    def fetch_multi_timeframe_data(self, code: str, count: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        获取多个时间框架的股票数据
        
        Args:
            code: 股票代码  
            count: 获取的数据条数
            
        Returns:
            包含不同时间框架数据的字典
        """
        timeframes = {
            '日线': '1d',
            '周线': '1w', 
            '月线': '1M'
        }
        
        results = {}
        for name, freq in timeframes.items():
            try:
                df = self.fetch_stock_data(code, count, freq)
                if df is not None:
                    results[name] = df
                    logger.info(f"{code} {name}数据获取成功，共{len(df)}条记录")
                else:
                    logger.warning(f"{code} {name}数据获取失败")
            except Exception as e:
                logger.error(f"获取{code} {name}数据失败: {str(e)}")
                
        return results 