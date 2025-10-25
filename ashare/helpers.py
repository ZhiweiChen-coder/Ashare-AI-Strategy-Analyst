"""
辅助函数模块

包含图表生成、数据格式化等辅助功能
"""

import base64
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Any, Union
from ashare.logging import get_logger

logger = get_logger(__name__)


def plot_to_base64(fig) -> str:
    """
    将matplotlib图表转换为base64编码字符串
    
    Args:
        fig: matplotlib figure对象
        
    Returns:
        base64编码的图片字符串
    """
    try:
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        logger.debug("成功将图表转换为base64格式")
        return image_base64
    except Exception as e:
        logger.error(f"转换图表到base64失败: {str(e)}")
        plt.close(fig)  # 确保图表被关闭
        raise


def get_value_class(value: Union[str, float, int]) -> str:
    """
    根据数值返回CSS类名，用于着色显示
    
    Args:
        value: 数值，可以是字符串、浮点数或整数
        
    Returns:
        CSS类名: 'positive', 'negative', 或 'neutral'
    """
    try:
        if isinstance(value, str) and '%' in value:
            # 处理百分比字符串
            numeric_value = float(value.strip('%'))
        elif isinstance(value, str):
            # 其他字符串返回中性
            return 'neutral'
        else:
            numeric_value = float(value)
            
        if numeric_value > 0:
            return 'positive'
        elif numeric_value < 0:
            return 'negative'
        else:
            return 'neutral'
            
    except (ValueError, TypeError) as e:
        logger.warning(f"无法解析数值 {value}，错误信息: {e}")
        return 'neutral'


def generate_table_row(key: str, value: Any) -> str:
    """
    生成表格行HTML，包含样式
    
    Args:
        key: 表格键名
        value: 表格值
        
    Returns:
        HTML表格行字符串
    """
    try:
        value_class = get_value_class(value)
        return f'<tr><td>{key}</td><td class="{value_class}">{value}</td></tr>'
    except Exception as e:
        logger.error(f"生成表格行失败: {str(e)}")
        return f'<tr><td>{key}</td><td class="neutral">N/A</td></tr>'


def format_number(value: Union[int, float], decimal_places: int = 2) -> str:
    """
    格式化数字显示
    
    Args:
        value: 数值
        decimal_places: 小数位数
        
    Returns:
        格式化后的字符串
    """
    try:
        if isinstance(value, (int, float)):
            return f"{value:.{decimal_places}f}"
        return str(value)
    except Exception as e:
        logger.error(f"格式化数字失败: {str(e)}")
        return "N/A"


def format_percentage(value: Union[int, float], decimal_places: int = 2) -> str:
    """
    格式化百分比显示
    
    Args:
        value: 数值
        decimal_places: 小数位数
        
    Returns:
        格式化后的百分比字符串
    """
    try:
        if isinstance(value, (int, float)):
            return f"{value:.{decimal_places}f}%"
        return str(value)
    except Exception as e:
        logger.error(f"格式化百分比失败: {str(e)}")
        return "N/A"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 除零时的默认值
        
    Returns:
        除法结果或默认值
    """
    try:
        if denominator == 0:
            logger.warning("除零错误，返回默认值")
            return default
        return numerator / denominator
    except Exception as e:
        logger.error(f"除法计算失败: {str(e)}")
        return default 