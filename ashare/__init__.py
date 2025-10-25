"""
Ashare AI Strategy Analyst - 核心模块

整合了数据获取、技术指标、图表生成、报告生成等核心功能
"""

__version__ = "2.0.0"
__author__ = "Ashare Team"

from ashare.analyzer import StockAnalyzer
from ashare.config import Config

__all__ = ['StockAnalyzer', 'Config']
