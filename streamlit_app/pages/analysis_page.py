"""
分析页面模块
"""

import streamlit as st
from datetime import datetime
from typing import Dict

from utils.signal_analyzer import SignalAnalyzer


class AnalysisPage:
    """分析页面组件"""
    
    def render(self):
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
            if st.button("🔄 开始分析", type="primary", key="start_analysis_btn"):
                self.run_analysis()
        
        with col2:
            if st.button("💾 导出报告", key="export_report_btn"):
                self.export_report()
        
        with col3:
            auto_refresh = st.checkbox("🔄 自动刷新", value=False, key="auto_refresh_checkbox")
            refresh_interval = st.selectbox("刷新间隔", [30, 60, 300], index=1, format_func=lambda x: f"{x}秒", key="refresh_interval_selectbox")
        
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
            index=0,
            key="stock_selector"
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
                        mime="text/html",
                        key="download_report_button"
                    )
                else:
                    st.error("报告生成失败")
            except Exception as e:
                st.error(f"导出报告失败: {str(e)}") 