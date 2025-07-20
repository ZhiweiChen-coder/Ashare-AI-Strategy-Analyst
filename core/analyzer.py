"""
股票分析器核心模块

主要的股票分析器类，整合数据获取、技术指标计算和分析逻辑
"""

import pandas as pd
from typing import Dict, List, Optional, Any
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os
import pytz
from datetime import datetime

from .data_fetcher import DataFetcher
from .indicators import TechnicalIndicators
from .report_generator import ReportGenerator
from utils.logger import get_logger
from utils.trading_signals import generate_trading_signals
from llm import LLMAnalyzer
from push_notification import PushNotifier
from config import Config

logger = get_logger(__name__)


class StockAnalyzer:
    """股票分析器主类"""
    
    def __init__(self, stock_info: Dict[str, str], count: int = 120, 
                 llm_api_key: Optional[str] = None, llm_base_url: Optional[str] = None, 
                 llm_model: Optional[str] = None, enable_push: bool = True, 
                 config: Optional[Config] = None):
        """
        初始化股票分析器

        Args:
            stock_info: 股票信息字典 {股票名称: 股票代码}
            count: 获取的数据条数
            llm_api_key: LLM API密钥，默认从配置文件获取
            llm_base_url: LLM API基础URL，默认从配置文件获取
            llm_model: LLM 模型名称，默认从配置文件获取
            enable_push: 是否启用推送通知
            config: 配置实例，如果不提供则创建新的
        """
        logger.info("初始化股票分析器...")
        
        # 加载配置
        self.config = config or Config()
        
        # 基本配置
        self.stock_codes = list(stock_info.values())
        self.stock_names = stock_info
        self.count = count or self.config.data_count
        self.data = {}
        self.analysis_results = {}
        self.enable_push = enable_push and self.config.enable_push
        
        # 初始化子组件
        self.data_fetcher = DataFetcher(default_count=self.count)
        self.indicators_calculator = TechnicalIndicators()
        self.report_generator = ReportGenerator()
        
        # 配置matplotlib字体
        self._setup_matplotlib_fonts()

        # 从配置获取API密钥和基础URL
        self.llm_api_key = llm_api_key or self.config.llm_api_key
        self.llm_base_url = llm_base_url or self.config.llm_base_url
        self.llm_model = llm_model or self.config.llm_model

        # 初始化LLM分析器
        self.llm = LLMAnalyzer(self.llm_api_key, self.llm_base_url, self.llm_model) if self.llm_api_key else None
        
        # 初始化推送通知器
        self.push_notifier = PushNotifier() if self.enable_push else None
        
        logger.info(f"股票分析器初始化完成，将分析{len(self.stock_codes)}只股票")

    def _setup_matplotlib_fonts(self):
        """设置matplotlib中文字体"""
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False

            # 检查字体文件是否存在
            font_path = './static/fonts/微软雅黑.ttf'
            if os.path.exists(font_path):
                try:
                    # 注册字体文件
                    custom_font = fm.FontProperties(fname=font_path)
                    fm.fontManager.addfont(font_path)
                    # 设置字体
                    plt.rcParams['font.sans-serif'] = [custom_font.get_name()]
                    logger.info("成功加载自定义字体")
                except Exception as e:
                    logger.warning(f"字体文件加载失败，使用默认字体: {str(e)}")
            else:
                logger.info(f"字体文件不存在: {font_path}，使用默认字体")
                plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
                
        except Exception as e:
            logger.error(f"设置matplotlib字体失败: {str(e)}")

    def get_stock_name(self, code: str) -> str:
        """根据股票代码获取股票名称"""
        return {v: k for k, v in self.stock_names.items()}.get(code, code)

    def fetch_data(self) -> bool:
        """
        获取所有股票数据
        
        Returns:
            是否成功获取数据
        """
        logger.info("开始获取股票数据...")
        
        try:
            # 批量获取数据
            self.data = self.data_fetcher.fetch_multiple_stocks(
                self.stock_codes, self.count, '1d'
            )
            
            if not self.data:
                logger.error("没有获取到任何有效的股票数据")
                return False
            
            logger.info(f"成功获取 {len(self.data)} 只股票的数据")
            
            # 记录数据获取详情
            for code, df in self.data.items():
                stock_name = self.get_stock_name(code)
                logger.info(f"  {stock_name} ({code}): {len(df)} 条记录")
            
            return True
            
        except Exception as e:
            logger.error(f"获取股票数据失败: {str(e)}")
            return False

    def calculate_indicators(self, code: str) -> Optional[pd.DataFrame]:
        """
        计算指定股票的技术指标
        
        Args:
            code: 股票代码
            
        Returns:
            包含技术指标的DataFrame，失败时返回None
        """
        if code not in self.data:
            logger.error(f"股票代码 {code} 没有数据")
            return None

        try:
            logger.info(f"计算股票 {code} 的技术指标...")
            
            # 验证数据
            is_valid, error_msg = self.indicators_calculator.validate_data(self.data[code])
            if not is_valid:
                logger.error(f"数据验证失败: {error_msg}")
                return None
            
            # 计算技术指标
            df_with_indicators = self.indicators_calculator.calculate_all_indicators(self.data[code])
            
            if df_with_indicators is not None:
                logger.info(f"股票 {code} 技术指标计算完成")
            
            return df_with_indicators
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return None

    def generate_analysis_data(self, code: str) -> Dict[str, Any]:
        """
        生成股票分析数据
        
        Args:
            code: 股票代码
            
        Returns:
            分析数据字典
        """
        stock_name = self.get_stock_name(code)
        
        if code not in self.data:
            logger.error(f"股票代码 {code} 没有数据，无法生成分析")
            return self._create_error_analysis(code, stock_name, "数据获取失败")

        df = self.data[code]

        # 检查数据是否为空
        if df.empty:
            logger.error(f"股票代码 {code} 数据为空")
            return self._create_error_analysis(code, stock_name, "数据为空")

        # 计算技术指标
        latest_df = self.calculate_indicators(code)

        if latest_df is None:
            logger.error(f"股票代码 {code} 技术指标计算失败")
            return self._create_error_analysis(code, stock_name, "技术指标计算失败")

        try:
            logger.info(f"生成股票 {code} 的分析数据...")
            
            # 构建分析数据
            analysis_data = self._build_analysis_data(code, df, latest_df)
            
            # 生成交易信号
            signals = generate_trading_signals(latest_df)
            analysis_data["技术分析建议"] = signals
            
            logger.info(f"股票 {code} 分析数据生成完成")
            return analysis_data

        except Exception as e:
            error_msg = f"生成分析数据时出错: {str(e)}"
            logger.error(error_msg)
            return self._create_error_analysis(code, stock_name, error_msg)

    def _create_error_analysis(self, code: str, stock_name: str, error: str) -> Dict[str, Any]:
        """创建错误分析结果"""
        return {
            "基础数据": {
                "股票代码": code,
                "股票名称": stock_name,
                "数据状态": error,
                "错误信息": "请检查股票代码格式是否正确"
            },
            "技术指标": {},
            "技术分析建议": [f"分析失败: {error}"]
        }

    def _build_analysis_data(self, code: str, df: pd.DataFrame, 
                           latest_df: pd.DataFrame) -> Dict[str, Any]:
        """构建分析数据结构"""
        stock_name = self.get_stock_name(code)
        
        # 基础数据
        basic_data = {
            "股票代码": code,
            "股票名称": stock_name,
            "最新收盘价": f"{df['close'].iloc[-1]:.2f}",
            "涨跌幅": f"{((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100):.2f}%",
            "最高价": f"{df['high'].iloc[-1]:.2f}",
            "最低价": f"{df['low'].iloc[-1]:.2f}",
            "成交量": f"{int(df['volume'].iloc[-1]):,}",
        }
        
        # 技术指标数据
        technical_indicators = {
            "MA指标": {
                "MA5": f"{latest_df['MA5'].iloc[-1]:.2f}",
                "MA10": f"{latest_df['MA10'].iloc[-1]:.2f}",
                "MA20": f"{latest_df['MA20'].iloc[-1]:.2f}",
                "MA60": f"{latest_df['MA60'].iloc[-1]:.2f}",
            },
            "趋势指标": {
                "MACD (指数平滑异同移动平均线)": f"{latest_df['MACD'].iloc[-1]:.2f}",
                "DIF (差离值)": f"{latest_df['DIF'].iloc[-1]:.2f}",
                "DEA (讯号线)": f"{latest_df['DEA'].iloc[-1]:.2f}",
                "TRIX (三重指数平滑平均线)": f"{latest_df['TRIX'].iloc[-1]:.2f}",
                "PDI (上升方向线)": f"{latest_df['PDI'].iloc[-1]:.2f}",
                "MDI (下降方向线)": f"{latest_df['MDI'].iloc[-1]:.2f}",
                "ADX (趋向指标)": f"{latest_df['ADX'].iloc[-1]:.2f}",
            },
            "摆动指标": {
                "RSI (相对强弱指标)": f"{latest_df['RSI'].iloc[-1]:.2f}",
                "KDJ-K (随机指标K值)": f"{latest_df['K'].iloc[-1]:.2f}",
                "KDJ-D (随机指标D值)": f"{latest_df['D'].iloc[-1]:.2f}",
                "KDJ-J (随机指标J值)": f"{latest_df['J'].iloc[-1]:.2f}",
                "BIAS (乖离率)": f"{latest_df['BIAS1'].iloc[-1]:.2f}",
                "CCI (顺势指标)": f"{latest_df['CCI'].iloc[-1]:.2f}",
            },
            "成交量指标": {
                "VR (成交量比率)": f"{latest_df['VR'].iloc[-1]:.2f}",
                "AR (人气指标)": f"{latest_df['AR'].iloc[-1]:.2f}",
                "BR (意愿指标)": f"{latest_df['BR'].iloc[-1]:.2f}",
            },
            "动量指标": {
                "ROC (变动率)": f"{latest_df['ROC'].iloc[-1]:.2f}",
                "MTM (动量指标)": f"{latest_df['MTM'].iloc[-1]:.2f}",
                "DPO (区间振荡)": f"{latest_df['DPO'].iloc[-1]:.2f}",
            },
            "布林带": {
                "BOLL上轨": f"{latest_df['BOLL_UP'].iloc[-1]:.2f}",
                "BOLL中轨": f"{latest_df['BOLL_MID'].iloc[-1]:.2f}",
                "BOLL下轨": f"{latest_df['BOLL_LOW'].iloc[-1]:.2f}",
            }
        }
        
        return {
            "基础数据": basic_data,
            "技术指标": technical_indicators
        }

    def generate_html_report(self) -> str:
        """
        生成HTML格式的分析报告
        
        Returns:
            HTML报告内容
        """
        logger.info("开始生成HTML报告...")
        
        try:
            # 生成所有股票的分析数据
            stock_analyses = []
            for code in self.stock_codes:
                analysis_data = self.generate_analysis_data(code)
                stock_analyses.append((code, analysis_data))
            
            # 使用报告生成器生成HTML
            html_content = self.report_generator.generate_report(
                stock_analyses, 
                getattr(self, 'pool_ai_analysis', None)
            )
            
            logger.info("HTML报告生成完成")
            return html_content
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {str(e)}")
            raise

    def run_analysis(self, output_path: str = 'public/index.html') -> Optional[str]:
        """
        运行完整的股票分析流程
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            成功时返回输出文件路径，失败时返回None
        """
        logger.info("开始运行股票分析...")

        try:
            # 1. 获取数据
            logger.info("步骤1: 获取股票数据")
            if not self.fetch_data():
                logger.error("数据获取失败，终止分析")
                return None

            # 2. 生成报告
            logger.info("步骤2: 生成HTML报告")
            html_report = self.generate_html_report()

            # 3. 保存报告
            logger.info("步骤3: 保存报告文件")
            success = self._save_report(html_report, output_path)
            
            if success:
                logger.info(f"✅ 分析完成！报告已保存到: {output_path}")
                return output_path
            else:
                logger.error("保存报告失败")
                return None

        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}")
            return None

    def _save_report(self, html_content: str, output_path: str) -> bool:
        """
        保存HTML报告到文件
        
        Args:
            html_content: HTML内容
            output_path: 输出路径
            
        Returns:
            是否保存成功
        """
        try:
            # 创建输出目录
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 写入HTML报告
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"报告已保存到: {output_path}")
            
            # 尝试打开浏览器
            try:
                import webbrowser
                webbrowser.open(output_path)
            except Exception as e:
                logger.warning(f"打开浏览器失败: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存报告文件失败: {str(e)}")
            return False

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要信息"""
        summary = {
            'total_stocks': len(self.stock_codes),
            'successful_data_fetch': len(self.data),
            'stocks_with_data': list(self.data.keys()),
            'failed_stocks': [code for code in self.stock_codes if code not in self.data],
            'analysis_time': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return summary 