"""
Streamlit应用主配置类
"""

import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
from typing import Dict, List, Optional

from config import Config
from streamlit_app.styles.custom_css import load_custom_css
from streamlit_app.pages.home_page import HomePage
from streamlit_app.pages.config_page import ConfigPage
from streamlit_app.pages.analysis_page import AnalysisPage
from streamlit_app.pages.charts_page import ChartsPage
from streamlit_app.pages.ai_insights_page import AIInsightsPage


class StreamlitApp:
    """Streamlit应用主类"""
    
    def __init__(self):
        """初始化应用"""
        self.setup_page_config()
        self.initialize_session_state()
        self.config = Config()
        
        # 初始化页面组件
        self.home_page = HomePage()
        self.config_page = ConfigPage(self.config)
        self.analysis_page = AnalysisPage()
        self.charts_page = ChartsPage()
        self.ai_insights_page = AIInsightsPage(self.config)
    
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="Ashare AI 股票策略分析师",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 添加现代化的自定义CSS样式
        load_custom_css()
    
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'analyzer' not in st.session_state:
            st.session_state.analyzer = None
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = {}
        if 'current_analysis' not in st.session_state:
            st.session_state.current_analysis = None
        if 'current_stock_pool' not in st.session_state:
            st.session_state.current_stock_pool = {}
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
    
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
    
    def run(self):
        """运行Streamlit应用"""
        # 渲染侧边栏并获取选择的页面
        selected_page = self.render_sidebar()
        
        # 根据选择渲染对应页面
        if selected_page == "🏠 首页":
            self.home_page.render()
        elif selected_page == "⚙️ 配置":
            self.config_page.render()
        elif selected_page == "📊 分析":
            self.analysis_page.render()
        elif selected_page == "📈 图表":
            self.charts_page.render()
        elif selected_page == "🤖 AI洞察":
            self.ai_insights_page.render() 