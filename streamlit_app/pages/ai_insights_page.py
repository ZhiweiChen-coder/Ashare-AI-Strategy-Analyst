"""
AI洞察页面模块
"""

import streamlit as st


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
        
        # AI分析选项
        analysis_type = st.selectbox(
            "选择AI分析类型",
            ["股票池综合分析", "单股深度分析", "市场趋势预测"],
            index=0,
            key="ai_analysis_type_selectbox"
        )
        
        if analysis_type == "股票池综合分析":
            if st.button("🤖 生成股票池AI分析", type="primary", key="generate_pool_analysis_btn"):
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
                list(st.session_state.analysis_results.keys()),
                key="single_stock_selector"
            )
            
            if st.button("🔍 生成深度分析", type="primary", key="generate_single_analysis_btn"):
                st.info("🚧 单股深度分析功能开发中...")
        
        else:  # 市场趋势预测
            if st.button("📈 生成趋势预测", type="primary", key="generate_trend_analysis_btn"):
                st.info("�� 市场趋势预测功能开发中...") 