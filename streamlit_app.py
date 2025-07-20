"""
Ashare-AI-Strategy-Analyst Streamlit Web界面

提供用户友好的Web界面来配置和运行股票分析
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# 添加项目根目录到Python路径
import sys
sys.path.append('.')

from core import StockAnalyzer
from core.plotly_charts import InteractiveCharts
from utils.signal_analyzer import SignalAnalyzer
from config import Config


class StreamlitApp:
    """Streamlit应用主类"""
    
    def __init__(self):
        """初始化应用"""
        self.setup_page_config()
        self.initialize_session_state()
        self.config = Config()
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="Ashare AI 股票策略分析师",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 添加现代化的自定义CSS样式
        self.load_custom_css()
    
    def load_custom_css(self):
        """加载自定义CSS样式"""
        custom_css = """
        <style>
        /* 主题色彩定义 */
        :root {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --success-color: #2ca02c;
            --danger-color: #d62728;
            --warning-color: #ff7f0e;
            --info-color: #17a2b8;
            --light-bg: #f8f9fa;
            --dark-text: #2c3e50;
            --border-radius: 12px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* 隐藏Streamlit默认元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* 应用整体样式 */
        .main {
            padding-top: 2rem;
        }
        
        /* 标题样式 */
        h1 {
            color: var(--dark-text);
            font-weight: 700;
            margin-bottom: 1.5rem;
            text-align: center;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        h2, h3, h4 {
            color: var(--dark-text);
            font-weight: 600;
        }
        
        /* 卡片样式 */
        .stContainer > div {
            background: white;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            margin-bottom: 1rem;
        }
        
        /* 指标卡片样式 */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 1rem;
            border-radius: var(--border-radius);
            color: white;
            box-shadow: var(--box-shadow);
        }
        
        [data-testid="metric-container"] > div {
            color: white;
        }
        
        [data-testid="metric-container"] label {
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.875rem;
        }
        
        /* 按钮样式 */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color), var(--info-color));
            color: white;
            border: none;
            border-radius: var(--border-radius);
            padding: 0.75rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: var(--box-shadow);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        }
        
        /* 侧边栏样式 - 蓝色渐变主题 */
        .stSidebar, 
        .stSidebar > div,
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
        }
        
        /* 侧边栏标题和文字样式 */
        .stSidebar .stMarkdown,
        .stSidebar .stMarkdown p,
        .stSidebar .stMarkdown div,
        .stSidebar .stMarkdown h1, 
        .stSidebar .stMarkdown h2, 
        .stSidebar .stMarkdown h3, 
        .stSidebar .stMarkdown h4,
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown div,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4 {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* 侧边栏按钮和其他组件 */
        .stSidebar .stButton button,
        .stSidebar label,
        section[data-testid="stSidebar"] .stButton button,
        section[data-testid="stSidebar"] label {
            color: #ffffff !important;
            background-color: rgba(255,255,255,0.15) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
        }
        
        /* 强制覆盖option-menu样式 */
        .stSidebar .nav-link,
        .stSidebar .nav-link span,
        .stSidebar .nav-item,
        section[data-testid="stSidebar"] .nav-link,
        section[data-testid="stSidebar"] .nav-link span,
        section[data-testid="stSidebar"] .nav-item {
            color: #ffffff !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.7) !important;
            font-weight: 600 !important;
        }
        
        .stSidebar .nav-link.active,
        .stSidebar .nav-link.active span,
        section[data-testid="stSidebar"] .nav-link.active,
        section[data-testid="stSidebar"] .nav-link.active span {
            color: #ffffff !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
            font-weight: 700 !important;
        }
        
        /* 选择框样式 */
        .stSelectbox > div > div {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: var(--border-radius);
            transition: border-color 0.3s ease;
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
        }
        
        /* 数据表格样式 */
        .stDataFrame {
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--box-shadow);
        }
        
        /* 进度条样式 */
        .stProgress > div > div {
            background: linear-gradient(90deg, var(--primary-color), var(--success-color));
            border-radius: var(--border-radius);
        }
        
        /* 信息框样式 */
        .stAlert {
            border-radius: var(--border-radius);
            border: none;
            box-shadow: var(--box-shadow);
        }
        
        /* 成功消息样式 */
        .stSuccess {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            color: white;
        }
        
        /* 错误消息样式 */
        .stError {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
        }
        
        /* 警告消息样式 */
        .stWarning {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
        }
        
        /* 信息消息样式 */
        .stInfo {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
        }
        
        /* 展开器样式 */
        .streamlit-expanderHeader {
            background: var(--light-bg);
            border-radius: var(--border-radius);
            border: 1px solid #dee2e6;
        }
        
        /* 滑块样式 */
        .stSlider > div > div > div {
            background: var(--primary-color);
        }
        
        /* 复选框样式 */
        .stCheckbox > label {
            font-weight: 500;
            color: var(--dark-text);
        }
        
        /* 多选框样式 */
        .stMultiSelect > div > div {
            border-radius: var(--border-radius);
            border: 2px solid #e9ecef;
        }
        
        /* 文本区域样式 */
        .stTextArea > div > div {
            border-radius: var(--border-radius);
            border: 2px solid #e9ecef;
        }
        
        /* 特殊装饰元素 */
        .feature-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            text-align: center;
            box-shadow: var(--box-shadow);
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            text-align: center;
            box-shadow: var(--box-shadow);
            border-left: 4px solid var(--primary-color);
        }
        
        /* 动画效果 */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            
            [data-testid="metric-container"] {
                margin-bottom: 1rem;
            }
        }
        </style>
        """
        
        st.markdown(custom_css, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'analyzer' not in st.session_state:
            st.session_state.analyzer = None
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = {}
        if 'current_analysis' not in st.session_state:
            st.session_state.current_analysis = None
    
    def render_sidebar(self) -> str:
        """渲染侧边栏并返回选择的页面"""
        with st.sidebar:
            # 现代化Logo和标题
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="color: white; font-weight: 700; margin-bottom: 0.5rem;">
                    📈 Ashare AI
                </h2>
                <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;">
                    智能股票分析师
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 现代化主菜单
            selected = option_menu(
                None,
                ["🏠 首页", "⚙️ 配置", "📊 分析", "📈 图表", "🤖 AI洞察"],
                icons=['house-fill', 'gear-fill', 'graph-up', 'bar-chart-line-fill', 'robot'],
                menu_icon=None,
                default_index=0,
                styles={
                    "container": {
                        "padding": "0px 0px",
                        "background-color": "transparent",
                        "border-radius": "8px"
                    },
                    "icon": {
                        "color": "#ffffff", 
                        "font-size": "18px"
                    },
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "2px 4px",
                        "padding": "10px 12px",
                        "color": "#ffffff !important",
                        "background-color": "rgba(0,0,0,0.2)",
                        "border-radius": "8px",
                        "border": "1px solid rgba(255,255,255,0.3)",
                        "text-shadow": "0 1px 2px rgba(0,0,0,0.7)"
                    },
                    "nav-link-selected": {
                        "background-color": "rgba(255,255,255,0.3)",
                        "color": "#ffffff !important",
                        "font-weight": "700",
                        "border": "1px solid rgba(255,255,255,0.5)",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.3)",
                        "text-shadow": "0 1px 2px rgba(0,0,0,0.8)"
                    },
                    "nav-link-hover": {
                        "background-color": "rgba(255,255,255,0.15)",
                        "color": "#ffffff"
                    }
                }
            )
            
            st.markdown("---")
            
            # 美化的状态信息
            st.markdown("#### 💡 系统状态")
            
            if st.session_state.analyzer:
                st.markdown("""
                <div style="background: rgba(46,160,67,0.7); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #2ca02c; border: 2px solid rgba(255,255,255,0.3); box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    <div style="color: #ffffff; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.8);">✅ 分析器已就绪</div>
                    <div style="color: #ffffff; font-size: 0.9rem; margin-top: 0.5rem; text-shadow: 0 1px 3px rgba(0,0,0,0.8);">
                        📋 股票池: {} 只股票
                    </div>
                </div>
                """.format(len(st.session_state.analyzer.stock_codes) if hasattr(st.session_state.analyzer, 'stock_codes') else 'N/A'), 
                unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(255,193,7,0.7); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #ffc107; border: 2px solid rgba(255,255,255,0.3); box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    <div style="color: #ffffff; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.8);">⚠️ 待配置</div>
                    <div style="color: #ffffff; font-size: 0.9rem; margin-top: 0.5rem; text-shadow: 0 1px 3px rgba(0,0,0,0.8);">
                        请先配置分析参数
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 美化的API配置状态
            self.show_api_status()
            
            # 添加版权信息
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0; color: rgba(255,255,255,0.6); font-size: 0.8rem;">
                © 2024 Ashare AI<br>
                Powered by AI
            </div>
            """, unsafe_allow_html=True)
            
            return selected
    
    def show_api_status(self):
        """显示API配置状态"""
        st.markdown("#### 🔑 API状态")
        
        # 检查LLM API配置
        if self.config.llm_api_key:
            st.markdown("""
            <div style="background: rgba(46,160,67,0.7); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #2ca02c; border: 2px solid rgba(255,255,255,0.3); box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                <div style="color: #ffffff; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.8);">✅ LLM API 已配置</div>
                <div style="color: #ffffff; font-size: 0.9rem; margin-top: 0.5rem; text-shadow: 0 1px 3px rgba(0,0,0,0.8);">
                    🤖 AI分析功能可用
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(220,53,69,0.7); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #dc3545; border: 2px solid rgba(255,255,255,0.3); box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                <div style="color: #ffffff; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.8);">❌ LLM API 未配置</div>
                <div style="color: #ffffff; font-size: 0.9rem; margin-top: 0.5rem; text-shadow: 0 1px 3px rgba(0,0,0,0.8);">
                    需要配置API密钥
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("⚙️ 配置说明", expanded=False):
                st.markdown("""
                **环境变量方式 (推荐)**
                ```bash
                export LLM_API_KEY="your_api_key"
                export LLM_BASE_URL="https://api.deepseek.com" 
                export LLM_MODEL="deepseek-chat"
                ```
                
                **.env文件方式**
                ```
                LLM_API_KEY=your_api_key
                LLM_BASE_URL=https://api.deepseek.com
                LLM_MODEL=deepseek-chat
                ```
                """)
    
    def render_homepage(self):
        """渲染首页"""
        # 现代化标题设计
        st.markdown("""
        <div class="fade-in" style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🏠 Ashare AI
            </h1>
            <h2 style="color: #6c757d; font-weight: 300; margin-top: 0;">
                智能股票策略分析师
            </h2>
            <p style="font-size: 1.2rem; color: #6c757d; margin-top: 1rem;">
                基于AI驱动的专业股票分析平台，让投资决策更智能
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 主要功能展示区域
        st.markdown("### ✨ 核心功能")
        
        # 使用现代化卡片布局
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            # 功能特色展示 - 使用原生组件
            st.markdown("#### 🚀 核心功能")
            
            # 功能1
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 1.5rem; border-radius: 12px; 
                           margin: 1rem 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h4 style="margin: 0 0 1rem 0; color: white;">📈 智能技术分析</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.9);">
                        计算25+种技术指标，包括MACD、KDJ、RSI、BOLL等，提供全面的技术分析支持
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # 功能2  
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                           color: white; padding: 1.5rem; border-radius: 12px; 
                           margin: 1rem 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h4 style="margin: 0 0 1rem 0; color: white;">🤖 AI驱动洞察</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.9);">
                        集成大语言模型，基于技术指标提供专业的投资建议和市场分析
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # 功能3
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                           color: white; padding: 1.5rem; border-radius: 12px; 
                           margin: 1rem 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h4 style="margin: 0 0 1rem 0; color: white;">📊 交互式图表</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.9);">
                        基于Plotly的动态图表，支持缩放、平移等操作，数据可视化更直观
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # 开始分析按钮
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 立即开始分析", type="primary", use_container_width=True):
                st.session_state.page = "⚙️ 配置"
                st.rerun()
        
        with col2:
            # 系统状态仪表板
            st.markdown("#### 📊 系统概览")
            
            # 使用原生指标组件，添加更好的样式
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric(
                    label="技术指标",
                    value="25+",
                    help="支持MACD、KDJ、RSI等多种技术指标"
                )
                st.metric(
                    label="数据源", 
                    value="实时",
                    help="A股+港股实时数据"
                )
            
            with col_b:
                st.metric(
                    label="AI分析",
                    value="智能",
                    help="GPT/DeepSeek驱动的智能分析"
                )
                st.metric(
                    label="图表",
                    value="交互式",
                    help="Plotly高级可视化"
                )
            
            # 添加一些额外信息
            st.markdown("---")
            st.info("💡 **提示**: 配置API密钥后可享受完整AI分析功能")
            
            # 快速状态检查
            if st.session_state.analyzer:
                st.success("✅ 系统已就绪")
            else:
                st.warning("⚙️ 待配置系统参数")
        
        # 分隔线
        st.markdown("<hr style='margin: 3rem 0; border: 1px solid #e9ecef;'>", unsafe_allow_html=True)
        
        # 核心亮点展示
        st.markdown("### 🆕 核心亮点")
        
        highlight_cols = st.columns(3)
        
        with highlight_cols[0]:
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%); 
                           color: white; padding: 1.5rem; border-radius: 12px; 
                           text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h4 style="margin: 0 0 1rem 0; color: white;">🎯 智能信号</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        多指标融合的买卖信号系统
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with highlight_cols[1]:
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #a8e6cf 0%, #88d8c0 100%); 
                           color: white; padding: 1.5rem; border-radius: 12px; 
                           text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h4 style="margin: 0 0 1rem 0; color: white;">📈 多时间框架</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        日线、周线、月线全方位分析
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with highlight_cols[2]:
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); 
                           color: white; padding: 1.5rem; border-radius: 12px; 
                           text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <h4 style="margin: 0 0 1rem 0; color: white;">🤖 AI洞察</h4>
                    <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        GPT/DeepSeek驱动的投资建议
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    def render_config_page(self):
        """渲染配置页面"""
        # 现代化页面标题
        st.markdown("""
        <div class="fade-in" style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
                ⚙️ 智能配置
            </h1>
            <p style="color: #6c757d; font-size: 1.1rem;">
                个性化配置您的股票分析参数
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 股票池配置
        st.markdown("### 📋 股票池配置")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 预设股票池
            preset_options = {
                "项目股票池": {
                    "北方稀土": "sh600111",
                    "中航沈飞": "sh600760",
                    "药明康德": "sh603259",
                    "美图公司": "01357.HK",
                    "中国船舶": "sh600150",
                    "航发动力": "sh600893",
                    "国泰君安国际": "01788.HK"
                },
                "热门指数": {
                    "上证指数": "sh000001",
                    "深证成指": "sz399001", 
                    "创业板指": "sz399006",
                    "科创50": "sh000688"
                },
                "热门个股": {
                    "招商银行": "sh600036",
                    "平安银行": "sz000001",
                    "贵州茅台": "sh600519",
                    "腾讯控股": "00700.HK"
                },
                "自定义": {}
            }
            
            selected_preset = st.selectbox(
                "选择预设股票池",
                list(preset_options.keys()),
                index=0,
                help="默认使用项目配置的股票池"
            )
            
            if selected_preset == "自定义":
                st.markdown("#### 自定义股票代码")
                custom_stocks = st.text_area(
                    "请输入股票代码（每行一个）",
                    placeholder="sh000001 上证指数\nsz399001 深证成指\nsh600036 招商银行",
                    height=100
                )
                
                stock_pool = {}
                if custom_stocks:
                    for line in custom_stocks.strip().split('\n'):
                        if line.strip():
                            parts = line.strip().split(' ')
                            if len(parts) >= 2:
                                code = parts[0]
                                name = ' '.join(parts[1:])
                                stock_pool[name] = code
            else:
                stock_pool = preset_options[selected_preset]
            
        with col2:
            st.markdown("#### 📊 分析参数")
            
            data_count = st.slider(
                "历史数据天数",
                min_value=60,
                max_value=500,
                value=120,
                step=20,
                help="获取用于分析的历史交易日数据量"
            )
            
            enable_ai = st.checkbox(
                "启用AI分析",
                value=bool(self.config.llm_api_key),
                help="需要配置LLM API密钥",
                disabled=not bool(self.config.llm_api_key)
            )
            
            enable_multi_timeframe = st.checkbox(
                "多时间框架分析",
                value=True,
                help="同时分析日线、周线、月线数据"
            )
        
        # 显示选中的股票
        if stock_pool:
            st.markdown("### 📈 当前股票池")
            pool_df = pd.DataFrame([
                {"股票名称": name, "股票代码": code}
                for name, code in stock_pool.items()
            ])
            st.dataframe(pool_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 开始分析按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("🚀 开始分析", type="primary"):
                if not stock_pool:
                    st.error("请至少选择一只股票")
                    return
                
                # 创建分析器
                with st.spinner("正在初始化分析器..."):
                    try:
                        st.session_state.analyzer = StockAnalyzer(
                            stock_info=stock_pool,
                            count=data_count,
                            config=self.config
                        )
                        
                        st.success("✅ 分析器创建成功！")
                        
                        # 自动跳转到分析页面
                        st.session_state.page = "📊 分析"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 创建分析器失败: {str(e)}")
    
    def render_analysis_page(self):
        """渲染分析页面"""
        # 现代化页面标题
        st.markdown("""
        <div class="fade-in" style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
                📊 智能分析
            </h1>
            <p style="color: #6c757d; font-size: 1.1rem;">
                实时股票数据分析与AI洞察
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.analyzer:
            st.warning("⚠️ 请先在配置页面创建分析器")
            return
        
        analyzer = st.session_state.analyzer
        
        # 分析控制区域
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 开始分析", type="primary"):
                self.run_analysis()
        
        with col2:
            if st.button("💾 导出报告"):
                self.export_report()
        
        with col3:
            auto_refresh = st.checkbox("🔄 自动刷新", value=False)
            refresh_interval = st.selectbox("刷新间隔", [30, 60, 300], index=1, format_func=lambda x: f"{x}秒")
        
        # 显示分析进度和结果
        if st.session_state.current_analysis:
            self.display_analysis_results()
        
        # 自动刷新逻辑
        if auto_refresh:
            st.rerun()
    
    def run_analysis(self):
        """运行股票分析"""
        analyzer = st.session_state.analyzer
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步骤1: 获取数据
            status_text.text("📥 正在获取股票数据...")
            progress_bar.progress(25)
            
            if not analyzer.fetch_data():
                st.error("❌ 数据获取失败")
                return
            
            # 步骤2: 计算技术指标
            status_text.text("🔢 正在计算技术指标...")
            progress_bar.progress(50)
            
            if not analyzer.calculate_indicators():
                st.error("❌ 技术指标计算失败")
                return
            
            # 步骤3: 生成分析结果
            status_text.text("🤖 正在生成AI分析...")
            progress_bar.progress(75)
            
            # 分析每只股票
            results = {}
            for code in analyzer.processed_data_dict.keys():
                stock_name = analyzer.get_stock_name(code)
                analysis = analyzer.analyze_single_stock(code)
                results[stock_name] = analysis
            
            # 步骤4: 生成信号分析
            status_text.text("🎯 正在生成交易信号...")
            progress_bar.progress(90)
            
            signal_analyzer = SignalAnalyzer()
            for stock_name, analysis in results.items():
                if 'processed_data' in analysis:
                    df = analysis['processed_data']
                    signals = signal_analyzer.analyze_all_signals(df)
                    analysis['signal_analysis'] = signals
            
            progress_bar.progress(100)
            status_text.text("✅ 分析完成！")
            
            # 保存结果
            st.session_state.analysis_results = results
            st.session_state.current_analysis = datetime.now()
            
        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()
    
    def display_analysis_results(self):
        """显示分析结果"""
        if not st.session_state.analysis_results:
            return
        
        results = st.session_state.analysis_results
        
        # 结果概览
        st.markdown("### 📊 分析结果概览")
        
        overview_cols = st.columns(4)
        
        with overview_cols[0]:
            st.metric("分析股票", len(results), "只")
        
        with overview_cols[1]:
            success_count = sum(1 for r in results.values() if r.get('基础数据', {}).get('数据状态') == '正常')
            st.metric("成功分析", success_count, "只")
        
        with overview_cols[2]:
            # 计算综合信号强度
            total_signals = 0
            positive_signals = 0
            for analysis in results.values():
                if 'signal_analysis' in analysis:
                    score = analysis['signal_analysis'].get('overall_score', 2)
                    total_signals += 1
                    if score > 2:
                        positive_signals += 1
            
            if total_signals > 0:
                positive_rate = (positive_signals / total_signals) * 100
                st.metric("看涨信号", f"{positive_rate:.1f}%", f"{positive_signals}/{total_signals}")
            else:
                st.metric("看涨信号", "0%", "0/0")
        
        with overview_cols[3]:
            analysis_time = st.session_state.current_analysis
            st.metric("分析时间", analysis_time.strftime("%H:%M:%S"), analysis_time.strftime("%m-%d"))
        
        # 详细结果
        st.markdown("---")
        st.markdown("### 📈 详细分析结果")
        
        # 股票选择器
        selected_stock = st.selectbox(
            "选择查看的股票",
            list(results.keys()),
            index=0
        )
        
        if selected_stock and selected_stock in results:
            self.display_single_stock_analysis(selected_stock, results[selected_stock])
    
    def display_single_stock_analysis(self, stock_name: str, analysis: Dict):
        """显示单只股票的分析结果"""
        st.markdown(f"#### 📊 {stock_name} 分析详情")
        
        # 基础数据
        basic_data = analysis.get('基础数据', {})
        if basic_data.get('数据状态') == '正常':
            
            # 关键指标展示
            metric_cols = st.columns(5)
            
            with metric_cols[0]:
                current_price = basic_data.get('最新价格', '0')
                change = basic_data.get('涨跌', '0')
                st.metric("最新价格", current_price, change)
            
            with metric_cols[1]:
                change_pct = basic_data.get('涨跌幅', '0%')
                st.metric("涨跌幅", change_pct)
            
            with metric_cols[2]:
                volume = basic_data.get('成交量', '0')
                st.metric("成交量", volume)
            
            with metric_cols[3]:
                rsi = basic_data.get('RSI', 'N/A')
                st.metric("RSI", rsi)
            
            with metric_cols[4]:
                ma20 = basic_data.get('MA20', 'N/A')
                st.metric("MA20", ma20)
            
            # 信号分析
            if 'signal_analysis' in analysis:
                st.markdown("#### 🎯 交易信号分析")
                self.display_signal_analysis(analysis['signal_analysis'])
            
            # 技术分析建议
            if '技术分析建议' in analysis:
                st.markdown("#### 💡 技术分析建议")
                suggestions = analysis['技术分析建议']
                for suggestion in suggestions:
                    st.info(suggestion)
        
        else:
            st.error(f"❌ {stock_name} 数据获取失败: {basic_data.get('数据状态', '未知错误')}")
    
    def display_signal_analysis(self, signals: Dict):
        """显示信号分析结果"""
        # 综合评分
        overall_score = signals.get('overall_score', 2)
        overall_signal = signals.get('overall_signal', '中性')
        
        score_color = "🟢" if overall_score > 3 else "🔴" if overall_score < 2 else "🟡"
        st.markdown(f"**综合信号**: {score_color} {overall_signal} (评分: {overall_score}/5)")
        
        # 分类信号展示
        signal_categories = {
            'trend_signals': '📈 趋势信号',
            'oscillator_signals': '📊 摆动指标',
            'volume_signals': '📦 成交量信号',
            'ma_signals': '📉 均线信号'
        }
        
        cols = st.columns(2)
        
        for i, (category, title) in enumerate(signal_categories.items()):
            if category in signals:
                with cols[i % 2]:
                    with st.expander(title):
                        for indicator, signal_info in signals[category].items():
                            if isinstance(signal_info, dict):
                                signal_type = signal_info.get('signal', 'NEUTRAL')
                                description = signal_info.get('description', '')
                                
                                # 信号图标
                                icon = "🟢" if signal_type in ['BUY', 'STRONG_BUY'] else \
                                       "🔴" if signal_type in ['SELL', 'STRONG_SELL'] else \
                                       "🟡" if signal_type in ['WEAK_BUY', 'WEAK_SELL'] else "⚪"
                                
                                st.markdown(f"{icon} **{indicator}**: {description}")
    
    def render_charts_page(self):
        """渲染图表页面"""
        # 现代化页面标题
        st.markdown("""
        <div class="fade-in" style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
                📈 智能图表
            </h1>
            <p style="color: #6c757d; font-size: 1.1rem;">
                高级交互式数据可视化
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.analysis_results:
            st.warning("⚠️ 请先运行分析以生成图表")
            return
        
        results = st.session_state.analysis_results
        
        # 股票选择
        selected_stock = st.selectbox(
            "选择股票",
            list(results.keys()),
            key="chart_stock_selector"
        )
        
        if selected_stock not in results:
            return
        
        analysis = results[selected_stock]
        
        if 'processed_data' not in analysis:
            st.error("❌ 该股票没有处理后的数据")
            return
        
        df = analysis['processed_data']
        
        # 图表类型选择
        chart_types = st.multiselect(
            "选择图表类型",
            ["主要分析图表", "指标对比", "多时间框架"],
            default=["主要分析图表"]
        )
        
        interactive_charts = InteractiveCharts()
        
        # 生成选择的图表
        if "主要分析图表" in chart_types:
            st.markdown("#### 📊 主要技术分析图表")
            try:
                main_chart = interactive_charts.create_main_analysis_chart(df, selected_stock)
                st.plotly_chart(main_chart, use_container_width=True)
            except Exception as e:
                st.error(f"生成主要图表失败: {str(e)}")
        
        if "指标对比" in chart_types:
            st.markdown("#### 📈 技术指标对比")
            
            # 指标选择
            available_indicators = [col for col in df.columns 
                                  if col not in ['open', 'high', 'low', 'close', 'volume']]
            
            selected_indicators = st.multiselect(
                "选择要对比的指标",
                available_indicators,
                default=available_indicators[:4]  # 默认选择前4个
            )
            
            if selected_indicators:
                try:
                    comparison_chart = interactive_charts.create_indicator_comparison_chart(
                        df, selected_indicators, selected_stock
                    )
                    st.plotly_chart(comparison_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"生成指标对比图表失败: {str(e)}")
        
        if "多时间框架" in chart_types:
            st.markdown("#### 🔄 多时间框架分析")
            
            if st.session_state.analyzer:
                with st.spinner("正在获取多时间框架数据..."):
                    try:
                        # 获取股票代码
                        stock_code = None
                        for code, name in st.session_state.analyzer.stock_names.items():
                            if name == selected_stock:
                                stock_code = code
                                break
                        
                        if stock_code:
                            multi_data = st.session_state.analyzer.data_fetcher.fetch_multi_timeframe_data(
                                stock_code, 60
                            )
                            
                            if multi_data:
                                # 为每个时间框架计算MA20
                                for timeframe, tf_df in multi_data.items():
                                    if len(tf_df) >= 20:
                                        tf_df['MA20'] = tf_df['close'].rolling(20).mean()
                                
                                multi_chart = interactive_charts.create_multi_timeframe_chart(
                                    multi_data, selected_stock
                                )
                                st.plotly_chart(multi_chart, use_container_width=True)
                            else:
                                st.warning("未能获取多时间框架数据")
                        else:
                            st.error("未找到对应的股票代码")
                    
                    except Exception as e:
                        st.error(f"生成多时间框架图表失败: {str(e)}")
    
    def render_ai_insights_page(self):
        """渲染AI洞察页面"""
        # 现代化页面标题
        st.markdown("""
        <div class="fade-in" style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;">
                🤖 AI洞察
            </h1>
            <p style="color: #6c757d; font-size: 1.1rem;">
                人工智能驱动的专业投资建议
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not self.config.llm_api_key:
            st.error("❌ 未配置LLM API密钥，无法使用AI功能")
            st.info("请在环境变量或.env文件中配置LLM_API_KEY")
            return
        
        if not st.session_state.analysis_results:
            st.warning("⚠️ 请先运行分析以获取AI洞察")
            return
        
        # AI分析选项
        analysis_type = st.selectbox(
            "选择AI分析类型",
            ["股票池综合分析", "单股深度分析", "市场趋势预测"],
            index=0
        )
        
        if analysis_type == "股票池综合分析":
            if st.button("🤖 生成股票池AI分析", type="primary"):
                with st.spinner("AI正在分析股票池..."):
                    try:
                        if st.session_state.analyzer:
                            ai_analysis = st.session_state.analyzer.generate_pool_ai_analysis()
                            if ai_analysis:
                                st.markdown("### 📝 AI综合分析报告")
                                st.markdown(ai_analysis)
                            else:
                                st.error("AI分析生成失败")
                        else:
                            st.error("分析器未初始化")
                    except Exception as e:
                        st.error(f"AI分析失败: {str(e)}")
        
        elif analysis_type == "单股深度分析":
            selected_stock = st.selectbox(
                "选择分析的股票",
                list(st.session_state.analysis_results.keys())
            )
            
            if st.button("🔍 生成深度分析", type="primary"):
                st.info("🚧 单股深度分析功能开发中...")
        
        else:  # 市场趋势预测
            if st.button("📈 生成趋势预测", type="primary"):
                st.info("🚧 市场趋势预测功能开发中...")
    
    def export_report(self):
        """导出分析报告"""
        if not st.session_state.analyzer:
            st.error("请先运行分析")
            return
        
        with st.spinner("正在生成HTML报告..."):
            try:
                output_path = st.session_state.analyzer.run_analysis()
                if output_path:
                    st.success(f"✅ 报告已保存到: {output_path}")
                    
                    # 提供下载链接
                    with open(output_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    st.download_button(
                        label="💾 下载HTML报告",
                        data=html_content,
                        file_name=f"stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                else:
                    st.error("报告生成失败")
            except Exception as e:
                st.error(f"导出报告失败: {str(e)}")
    
    def run(self):
        """运行Streamlit应用"""
        # 渲染侧边栏并获取选择的页面
        selected_page = self.render_sidebar()
        
        # 根据选择渲染对应页面
        if selected_page == "🏠 首页":
            self.render_homepage()
        elif selected_page == "⚙️ 配置":
            self.render_config_page()
        elif selected_page == "📊 分析":
            self.render_analysis_page()
        elif selected_page == "📈 图表":
            self.render_charts_page()
        elif selected_page == "🤖 AI洞察":
            self.render_ai_insights_page()


def main():
    """主程序入口"""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main() 