"""
股票搜索工具模块

提供智能股票搜索功能，支持多种搜索方式和数据源
"""

import re
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time


class StockSearcher:
    """智能股票搜索器"""
    
    def __init__(self):
        """初始化搜索器"""
        self.base_stock_db = self._load_base_database()
        self.search_cache = {}
        self.cache_expiry = 3600  # 缓存1小时
    
    def _load_base_database(self) -> Dict:
        """加载基础股票数据库"""
        return {
            # A股主要股票
            "招商银行": {"code": "sh600036", "market": "A股-上海", "category": "银行"},
            "平安银行": {"code": "sz000001", "market": "A股-深圳", "category": "银行"},
            "贵州茅台": {"code": "sh600519", "market": "A股-上海", "category": "白酒"},
            "五粮液": {"code": "sz000858", "market": "A股-深圳", "category": "白酒"},
            "中国平安": {"code": "sh601318", "market": "A股-上海", "category": "保险"},
            "万科A": {"code": "sz000002", "market": "A股-深圳", "category": "地产"},
            "格力电器": {"code": "sz000651", "market": "A股-深圳", "category": "家电"},
            "美的集团": {"code": "sz000333", "market": "A股-深圳", "category": "家电"},
            "海康威视": {"code": "sz002415", "market": "A股-深圳", "category": "科技"},
            "比亚迪": {"code": "sz002594", "market": "A股-深圳", "category": "新能源车"},
            "宁德时代": {"code": "sz300750", "market": "A股-创业板", "category": "新能源"},
            "隆基绿能": {"code": "sh601012", "market": "A股-上海", "category": "新能源"},
            "中国中免": {"code": "sh601888", "market": "A股-上海", "category": "消费"},
            "恒瑞医药": {"code": "sh600276", "market": "A股-上海", "category": "医药"},
            "药明康德": {"code": "sh603259", "market": "A股-上海", "category": "医药"},
            "北方稀土": {"code": "sh600111", "market": "A股-上海", "category": "稀土"},
            "中航沈飞": {"code": "sh600760", "market": "A股-上海", "category": "军工"},
            "中国船舶": {"code": "sh600150", "market": "A股-上海", "category": "军工"},
            "航发动力": {"code": "sh600893", "market": "A股-上海", "category": "军工"},
            
            # 主要指数
            "上证指数": {"code": "sh000001", "market": "指数-上海", "category": "指数"},
            "深证成指": {"code": "sz399001", "market": "指数-深圳", "category": "指数"},
            "创业板指": {"code": "sz399006", "market": "指数-创业板", "category": "指数"},
            "科创50": {"code": "sh000688", "market": "指数-科创板", "category": "指数"},
            "沪深300": {"code": "sh000300", "market": "指数-沪深", "category": "指数"},
            "中证500": {"code": "sh000905", "market": "指数-中证", "category": "指数"},
            
            # 港股主要股票
            "腾讯控股": {"code": "00700.HK", "market": "港股", "category": "科技"},
            "阿里巴巴": {"code": "09988.HK", "market": "港股", "category": "科技"},
            "美团": {"code": "03690.HK", "market": "港股", "category": "科技"},
            "小米集团": {"code": "01810.HK", "market": "港股", "category": "科技"},
            "京东集团": {"code": "09618.HK", "market": "港股", "category": "电商"},
            "网易": {"code": "09999.HK", "market": "港股", "category": "科技"},
            "百度集团": {"code": "09888.HK", "market": "港股", "category": "科技"},
            "快手": {"code": "01024.HK", "market": "港股", "category": "科技"},
            "比亚迪股份": {"code": "01211.HK", "market": "港股", "category": "新能源车"},
            "中国移动": {"code": "00941.HK", "market": "港股", "category": "通信"},
            "中国联通": {"code": "00762.HK", "market": "港股", "category": "通信"},
            "中国电信": {"code": "00728.HK", "market": "港股", "category": "通信"},
            "美图公司": {"code": "01357.HK", "market": "港股", "category": "科技"},
            "国泰君安国际": {"code": "01788.HK", "market": "港股", "category": "金融"},
            
            # 银行股
            "工商银行": {"code": "sh601398", "market": "A股-上海", "category": "银行"},
            "建设银行": {"code": "sh601939", "market": "A股-上海", "category": "银行"},
            "农业银行": {"code": "sh601288", "market": "A股-上海", "category": "银行"},
            "中国银行": {"code": "sh601988", "market": "A股-上海", "category": "银行"},
            "交通银行": {"code": "sh601328", "market": "A股-上海", "category": "银行"},
            "浦发银行": {"code": "sh600000", "market": "A股-上海", "category": "银行"},
            "兴业银行": {"code": "sh601166", "market": "A股-上海", "category": "银行"},
            "民生银行": {"code": "sh600016", "market": "A股-上海", "category": "银行"},
            "中信银行": {"code": "sh601998", "market": "A股-上海", "category": "银行"},
            "光大银行": {"code": "sh601818", "market": "A股-上海", "category": "银行"},
            
            # 科技股
            "中兴通讯": {"code": "sz000063", "market": "A股-深圳", "category": "科技"},
            "京东方A": {"code": "sz000725", "market": "A股-深圳", "category": "科技"},
            "TCL科技": {"code": "sz000100", "market": "A股-深圳", "category": "科技"},
            "立讯精密": {"code": "sz002475", "market": "A股-深圳", "category": "科技"},
            "歌尔股份": {"code": "sz002241", "market": "A股-深圳", "category": "科技"},
            "蓝思科技": {"code": "sz300433", "market": "A股-创业板", "category": "科技"},
            "欧菲光": {"code": "sz002456", "market": "A股-深圳", "category": "科技"},
            
            # 新能源
            "阳光电源": {"code": "sz300274", "market": "A股-创业板", "category": "新能源"},
            "通威股份": {"code": "sh600438", "market": "A股-上海", "category": "新能源"},
            "天合光能": {"code": "sh688599", "market": "A股-科创板", "category": "新能源"},
            "晶澳科技": {"code": "sz002459", "market": "A股-深圳", "category": "新能源"},
            "福斯特": {"code": "sh603806", "market": "A股-上海", "category": "新能源"},
            "中环股份": {"code": "sz002129", "market": "A股-深圳", "category": "新能源"},
            
            # 医药股
            "复星医药": {"code": "sh600196", "market": "A股-上海", "category": "医药"},
            "云南白药": {"code": "sz000538", "market": "A股-深圳", "category": "医药"},
            "片仔癀": {"code": "sh600436", "market": "A股-上海", "category": "医药"},
            "同仁堂": {"code": "sh600085", "market": "A股-上海", "category": "医药"},
            "东阿阿胶": {"code": "sz000423", "market": "A股-深圳", "category": "医药"},
            "华润三九": {"code": "sz000999", "market": "A股-深圳", "category": "医药"},
            "丽珠集团": {"code": "sz000513", "market": "A股-深圳", "category": "医药"},
            "长春高新": {"code": "sz000661", "market": "A股-深圳", "category": "医药"},
        }
    
    def search_stocks(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        智能搜索股票
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表
        """
        query = query.strip()
        if not query:
            return []
        
        # 检查缓存
        cache_key = f"{query}_{max_results}"
        if cache_key in self.search_cache:
            cache_time, cache_results = self.search_cache[cache_key]
            if time.time() - cache_time < self.cache_expiry:
                return cache_results
        
        results = []
        query_lower = query.lower()
        
        # 1. 精确匹配股票代码
        exact_code_matches = self._exact_code_match(query_lower)
        results.extend(exact_code_matches)
        
        # 2. 精确匹配股票名称
        if not results:
            exact_name_matches = self._exact_name_match(query_lower)
            results.extend(exact_name_matches)
        
        # 3. 模糊匹配股票名称
        if not results:
            fuzzy_name_matches = self._fuzzy_name_match(query_lower)
            results.extend(fuzzy_name_matches)
        
        # 4. 模糊匹配股票代码
        if not results:
            fuzzy_code_matches = self._fuzzy_code_match(query_lower)
            results.extend(fuzzy_code_matches)
        
        # 5. 按行业/分类搜索
        if not results:
            category_matches = self._category_match(query_lower)
            results.extend(category_matches)
        
        # 6. 智能代码格式识别
        if not results:
            code_validation = self._validate_and_create_stock(query)
            if code_validation:
                results.append(code_validation)
        
        # 7. 尝试在线搜索（如果本地搜索无结果）
        if not results:
            online_results = self._online_search(query)
            results.extend(online_results)
        
        # 去重和排序
        unique_results = self._deduplicate_results(results)
        sorted_results = self._sort_results(unique_results, query_lower)
        
        # 限制结果数量
        final_results = sorted_results[:max_results]
        
        # 缓存结果
        self.search_cache[cache_key] = (time.time(), final_results)
        
        return final_results
    
    def _exact_code_match(self, query: str) -> List[Dict]:
        """精确匹配股票代码"""
        results = []
        for name, info in self.base_stock_db.items():
            if query == info['code'].lower():
                results.append({
                    'name': name,
                    'code': info['code'],
                    'market': info['market'],
                    'category': info.get('category', ''),
                    'score': 100,  # 最高分
                    'match_type': 'exact_code'
                })
        return results
    
    def _exact_name_match(self, query: str) -> List[Dict]:
        """精确匹配股票名称"""
        results = []
        for name, info in self.base_stock_db.items():
            if query == name.lower():
                results.append({
                    'name': name,
                    'code': info['code'],
                    'market': info['market'],
                    'category': info.get('category', ''),
                    'score': 95,
                    'match_type': 'exact_name'
                })
        return results
    
    def _fuzzy_name_match(self, query: str) -> List[Dict]:
        """模糊匹配股票名称"""
        results = []
        for name, info in self.base_stock_db.items():
            if query in name.lower():
                # 计算匹配分数
                score = self._calculate_fuzzy_score(name.lower(), query)
                results.append({
                    'name': name,
                    'code': info['code'],
                    'market': info['market'],
                    'category': info.get('category', ''),
                    'score': score,
                    'match_type': 'fuzzy_name'
                })
        return results
    
    def _fuzzy_code_match(self, query: str) -> List[Dict]:
        """模糊匹配股票代码"""
        results = []
        for name, info in self.base_stock_db.items():
            if query in info['code'].lower():
                score = self._calculate_fuzzy_score(info['code'].lower(), query)
                results.append({
                    'name': name,
                    'code': info['code'],
                    'market': info['market'],
                    'category': info.get('category', ''),
                    'score': score - 10,  # 代码匹配分数稍低
                    'match_type': 'fuzzy_code'
                })
        return results
    
    def _category_match(self, query: str) -> List[Dict]:
        """按行业/分类搜索"""
        results = []
        for name, info in self.base_stock_db.items():
            if 'category' in info and query in info['category'].lower():
                score = self._calculate_fuzzy_score(info['category'].lower(), query)
                results.append({
                    'name': name,
                    'code': info['code'],
                    'market': info['market'],
                    'category': info.get('category', ''),
                    'score': score - 20,  # 分类匹配分数更低
                    'match_type': 'category'
                })
        return results
    
    def _validate_and_create_stock(self, query: str) -> Optional[Dict]:
        """验证股票代码格式并创建临时结果"""
        if self._is_valid_stock_code(query):
            market = self._get_market_from_code(query)
            return {
                'name': f"未知股票 ({query})",
                'code': query,
                'market': market,
                'category': '未知',
                'score': 50,
                'match_type': 'code_validation',
                'is_unknown': True
            }
        return None
    
    def _online_search(self, query: str) -> List[Dict]:
        """在线搜索股票（预留接口）"""
        # 这里可以集成第三方股票数据API
        # 例如：东方财富、新浪财经等
        return []
    
    def _calculate_fuzzy_score(self, text: str, query: str) -> int:
        """计算模糊匹配分数"""
        if query in text:
            # 基础分数
            base_score = 80
            
            # 位置加分：越靠前分数越高
            position = text.find(query)
            if position == 0:
                base_score += 10
            elif position < len(text) // 2:
                base_score += 5
            
            # 长度匹配加分：查询词越长分数越高
            length_bonus = min(len(query) * 2, 10)
            base_score += length_bonus
            
            return min(base_score, 95)
        return 0
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重结果"""
        seen_codes = set()
        unique_results = []
        for result in results:
            if result['code'] not in seen_codes:
                seen_codes.add(result['code'])
                unique_results.append(result)
        return unique_results
    
    def _sort_results(self, results: List[Dict], query: str) -> List[Dict]:
        """排序结果"""
        # 按分数排序，分数相同时按名称长度排序
        return sorted(results, key=lambda x: (-x['score'], len(x['name'])))
    
    def _is_valid_stock_code(self, code: str) -> bool:
        """验证股票代码格式"""
        # A股代码格式
        if code.startswith(('sh', 'sz')):
            if len(code) == 8:  # sh600036, sz000001
                return True
            elif len(code) == 9:  # sh000001 (指数)
                return True
        
        # 港股代码格式
        if code.endswith('.HK') and len(code) == 8:  # 00700.HK
            return True
        
        return False
    
    def _get_market_from_code(self, code: str) -> str:
        """根据股票代码推断市场"""
        if code.startswith('sh'):
            if code.startswith('sh000'):
                return "指数-上海"
            else:
                return "A股-上海"
        elif code.startswith('sz'):
            if code.startswith('sz399'):
                return "指数-深圳"
            elif code.startswith('sz300'):
                return "A股-创业板"
            else:
                return "A股-深圳"
        elif code.endswith('.HK'):
            return "港股"
        else:
            return "未知市场"
    
    def get_stock_info(self, code: str) -> Optional[Dict]:
        """获取股票详细信息"""
        # 从基础数据库查找
        for name, info in self.base_stock_db.items():
            if info['code'] == code:
                return {
                    'name': name,
                    'code': code,
                    'market': info['market'],
                    'category': info.get('category', ''),
                    'source': 'local'
                }
        
        # 如果本地没有，可以尝试在线获取
        return None
    
    def suggest_keywords(self, partial_query: str) -> List[str]:
        """建议搜索关键词"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # 从股票名称中提取建议
        for name in self.base_stock_db.keys():
            if partial_lower in name.lower() and len(suggestions) < 5:
                suggestions.append(name)
        
        # 从分类中提取建议
        categories = set()
        for info in self.base_stock_db.values():
            if 'category' in info:
                categories.add(info['category'])
        
        for category in categories:
            if partial_lower in category.lower() and len(suggestions) < 8:
                suggestions.append(category)
        
        return suggestions[:8]


# 全局搜索器实例
stock_searcher = StockSearcher() 