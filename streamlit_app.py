"""
Ashare-AI-Strategy-Analyst Streamlit Web界面 - 模块化版本

提供用户友好的Web界面来配置和运行股票分析
"""

import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append('.')

from streamlit_app.app_config import StreamlitApp


def main():
    """主程序入口"""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main() 