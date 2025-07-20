"""
首页模块
"""

import streamlit as st


class HomePage:
    """首页组件"""
    
    def render(self):
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