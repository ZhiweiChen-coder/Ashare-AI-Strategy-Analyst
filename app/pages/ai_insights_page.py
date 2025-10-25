"""
AI洞察页面模块
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional, Any


class AIInsightsPage:
    """AI洞察页面组件"""
    
    def __init__(self, config):
        """初始化AI洞察页面"""
        self.config = config
    
    def render(self):
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
        
        # 创建选项卡
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 技术分析", 
            "📈 基本面分析", 
            "🔍 单股分析", 
            "🌐 市场洞察"
        ])
        
        with tab1:
            self._render_technical_analysis()
        
        with tab2:
            self._render_fundamental_analysis()
            
        with tab3:
            self._render_single_stock_analysis()
            
        with tab4:
            self._render_market_insights()
    
    def _render_technical_analysis(self):
        """渲染技术分析标签页"""
        st.markdown("### 📊 技术分析")
        st.markdown("基于技术指标的股票池综合分析")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            analysis_scope = st.selectbox(
                "选择分析范围",
                ["股票池综合分析", "板块轮动分析", "趋势强度分析"],
                index=0,
                key="tech_analysis_scope"
            )
        
        with col2:
            st.markdown("###")  # 空行对齐
            generate_btn = st.button(
                "🤖 生成技术分析", 
                type="primary", 
                key="generate_tech_analysis_btn",
                use_container_width=True
            )
        
        if generate_btn:
            with st.spinner("AI正在进行技术分析..."):
                try:
                    if st.session_state.analyzer:
                        if analysis_scope == "股票池综合分析":
                            ai_analysis = st.session_state.analyzer.generate_pool_ai_analysis()
                        elif analysis_scope == "板块轮动分析":
                            ai_analysis = st.session_state.analyzer.generate_sector_rotation_analysis()
                        else:  # 趋势强度分析
                            ai_analysis = st.session_state.analyzer.generate_trend_strength_analysis()
                        
                        if ai_analysis:
                            st.markdown("### 📝 技术分析报告")
                            st.markdown(ai_analysis)
                        else:
                            st.error("技术分析生成失败")
                    else:
                        st.error("分析器未初始化")
                except Exception as e:
                    st.error(f"技术分析失败: {str(e)}")
    
    def _render_fundamental_analysis(self):
        """渲染基本面分析标签页"""
        st.markdown("### 📈 基本面分析")
        st.markdown("基于财务数据和宏观经济的深度分析")
        
        # 分析选项配置
        col1, col2 = st.columns(2)
        
        with col1:
            fundamental_type = st.selectbox(
                "基本面分析类型",
                [
                    "财务健康度分析",
                    "估值分析", 
                    "盈利能力分析",
                    "成长性分析",
                    "行业对比分析"
                ],
                index=0,
                key="fundamental_type_selector"
            )
        
        with col2:
            time_period = st.selectbox(
                "分析时间周期",
                ["最近一年", "最近三年", "最近五年"],
                index=0,
                key="fundamental_time_period"
            )
        
        # 高级选项
        with st.expander("🔧 高级分析选项", expanded=False):
            col3, col4 = st.columns(2)
            
            with col3:
                include_macro = st.checkbox("包含宏观经济分析", value=True, key="include_macro")
                include_industry = st.checkbox("包含行业分析", value=True, key="include_industry")
            
            with col4:
                include_competitors = st.checkbox("包含竞争对手分析", value=False, key="include_competitors")
                risk_assessment = st.checkbox("深度风险评估", value=True, key="risk_assessment")
        
        # 生成分析按钮
        if st.button("🔬 生成基本面分析", type="primary", key="generate_fundamental_btn", use_container_width=True):
            with st.spinner("AI正在进行基本面分析..."):
                try:
                    if st.session_state.analyzer:
                        # 收集分析参数
                        analysis_params = {
                            'type': fundamental_type,
                            'time_period': time_period,
                            'include_macro': include_macro,
                            'include_industry': include_industry,
                            'include_competitors': include_competitors,
                            'risk_assessment': risk_assessment
                        }
                        
                        ai_analysis = st.session_state.analyzer.generate_fundamental_analysis(analysis_params)
                        
                        if ai_analysis:
                            st.markdown("### 📊 基本面分析报告")
                            
                            # 使用可展开的区域显示不同部分
                            sections = self._parse_fundamental_analysis(ai_analysis)
                            
                            for section_title, section_content in sections.items():
                                with st.expander(f"📋 {section_title}", expanded=True):
                                    st.markdown(section_content)
                        else:
                            st.error("基本面分析生成失败")
                    else:
                        st.error("分析器未初始化")
                except Exception as e:
                    st.error(f"基本面分析失败: {str(e)}")
        
        # 添加说明信息
        st.info("""
        💡 **基本面分析说明**
        - 财务健康度：资产负债状况、现金流分析
        - 估值分析：PE、PB、PEG等估值指标分析
        - 盈利能力：ROE、ROA、毛利率等指标
        - 成长性：营收增长率、利润增长率分析
        - 行业对比：与同行业公司的比较分析
        """)
    
    def _render_single_stock_analysis(self):
        """渲染单股分析标签页"""
        st.markdown("### 🔍 单股深度分析")
        
        if not st.session_state.analysis_results:
            st.warning("请先运行股票分析")
            return
            
        selected_stock = st.selectbox(
            "选择分析的股票",
            list(st.session_state.analysis_results.keys()),
            key="single_stock_selector"
        )
        
        analysis_depth = st.radio(
            "分析深度",
            ["快速分析", "深度分析", "全面评估"],
            index=1,
            key="analysis_depth"
        )
        
        if st.button("🔍 生成深度分析", type="primary", key="generate_single_analysis_btn"):
            with st.spinner(f"AI正在分析 {selected_stock}..."):
                try:
                    if st.session_state.analyzer:
                        stock_data = st.session_state.analysis_results.get(selected_stock)
                        if stock_data:
                            ai_analysis = st.session_state.analyzer.generate_single_stock_analysis(
                                selected_stock, stock_data, analysis_depth
                            )
                            if ai_analysis:
                                st.markdown(f"### 📈 {selected_stock} 深度分析报告")
                                st.markdown(ai_analysis)
                            else:
                                st.error("单股分析生成失败")
                        else:
                            st.error(f"未找到 {selected_stock} 的分析数据")
                    else:
                        st.error("分析器未初始化")
                except Exception as e:
                    st.error(f"单股分析失败: {str(e)}")
    
    def _render_market_insights(self):
        """渲染市场洞察标签页"""
        st.markdown("### 🌐 市场洞察")
        st.markdown("宏观市场趋势和投资机会分析")
        
        insight_type = st.selectbox(
            "洞察类型",
            ["市场趋势预测", "热点板块分析", "资金流向分析", "情绪指标分析"],
            index=0,
            key="market_insight_type"
        )
        
        if st.button("📈 生成市场洞察", type="primary", key="generate_market_insights_btn"):
            with st.spinner("AI正在分析市场..."):
                try:
                    if st.session_state.analyzer:
                        ai_analysis = st.session_state.analyzer.generate_market_insights(insight_type)
                        if ai_analysis:
                            st.markdown("### 🎯 市场洞察报告")
                            st.markdown(ai_analysis)
                        else:
                            st.error("市场洞察生成失败")
                    else:
                        st.error("分析器未初始化")
                except Exception as e:
                    st.error(f"市场洞察分析失败: {str(e)}")
    
    def _parse_fundamental_analysis(self, analysis_text: str) -> Dict[str, str]:
        """
        解析基本面分析文本，分割成不同的部分
        
        Args:
            analysis_text: AI生成的基本面分析文本
            
        Returns:
            分割后的分析部分字典
        """
        sections = {}
        
        # 尝试按常见的标题分割
        common_headers = [
            "财务健康度分析", "估值分析", "盈利能力分析", "成长性分析", 
            "行业对比分析", "风险评估", "投资建议", "总结"
        ]
        
        current_section = "概述"
        current_content = []
        
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是新的章节标题
            is_header = False
            for header in common_headers:
                if header in line or any(keyword in line for keyword in ["##", "**", "###"]):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                        current_content = []
                    current_section = line.replace('#', '').replace('*', '').strip()
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # 添加最后一个部分
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # 如果没有找到标题，直接返回原文
        if len(sections) <= 1:
            sections = {"基本面分析": analysis_text}
        
        return sections 