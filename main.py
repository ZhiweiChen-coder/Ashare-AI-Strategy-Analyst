"""
Ashare AI Strategy Analyst - 命令行版本主程序
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ashare.logging import get_logger
from ashare.analyzer import StockAnalyzer
from ashare.config import PROJECT_ROOT

logger = get_logger("main")

def main():
    """命令行主程序"""
    logger.info("启动 Ashare AI Strategy Analyst 命令行版本")
    
    try:
        # 这里可以添加命令行逻辑
        # 例如：从配置文件读取股票池，运行分析等
        logger.info("程序运行完成")
        
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()