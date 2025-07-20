"""
图表页面模块
"""

import streamlit as st
from core.plotly_charts import InteractiveCharts


class ChartsPage:
    """图表页面组件"""
    
    def render(self):
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
            default=["主要分析图表"],
            key="chart_types_multiselect"
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
                default=available_indicators[:4],  # 默认选择前4个
                key="indicator_multiselect"
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