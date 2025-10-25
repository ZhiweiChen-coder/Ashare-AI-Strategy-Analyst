"""
Ashare AI Strategy Analyst - Streamlit Web应用主入口
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.app_config import main

if __name__ == "__main__":
    main()
