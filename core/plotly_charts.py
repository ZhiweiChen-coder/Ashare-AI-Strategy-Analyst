"""
基于Plotly的交互式图表模块

提供股票技术分析的交互式图表，支持缩放、平移、多时间框架切换等功能
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.offline import plot
import base64
import io
from typing import Dict, Any, Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)


class InteractiveCharts:
    """交互式图表生成器"""
    
    def __init__(self):
        """初始化图表生成器"""
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'up': '#00d09c',      # 上涨颜色
            'down': '#ff6b6b',    # 下跌颜色
            'volume': '#9467bd'   # 成交量颜色
        }
    
    def create_main_analysis_chart(self, df: pd.DataFrame, stock_name: str = "股票") -> go.Figure:
        """
        创建主要的技术分析图表（包含价格、指标和成交量）
        
        Args:
            df: 包含OHLCV和技术指标的DataFrame
            stock_name: 股票名称
            
        Returns:
            Plotly Figure对象
        """
        try:
            logger.info(f"生成{stock_name}的交互式分析图表")
            
            # 创建子图：4个子图垂直排列
            fig = sp.make_subplots(
                rows=4, cols=1,
                row_heights=[0.5, 0.2, 0.15, 0.15],
                subplot_titles=[
                    f'{stock_name} - 价格走势与技术指标',
                    'MACD指标',
                    'KDJ指标', 
                    '成交量'
                ],
                vertical_spacing=0.08,
                shared_xaxes=True
            )
            
            # 1. 主图：K线图和移动平均线
            self._add_candlestick_chart(fig, df, row=1)
            self._add_moving_averages(fig, df, row=1)
            self._add_bollinger_bands(fig, df, row=1)
            
            # 2. MACD指标
            self._add_macd_chart(fig, df, row=2)
            
            # 3. KDJ指标  
            self._add_kdj_chart(fig, df, row=3)
            
            # 4. 成交量图
            self._add_volume_chart(fig, df, row=4)
            
            # 设置图表样式和布局
            self._configure_chart_layout(fig, stock_name)
            
            logger.info("交互式图表生成成功")
            return fig
            
        except Exception as e:
            logger.error(f"生成交互式图表失败: {str(e)}")
            # 返回空的图表
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text=f"图表生成失败: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, 
                showarrow=False
            )
            return empty_fig
    
    def _add_candlestick_chart(self, fig: go.Figure, df: pd.DataFrame, row: int):
        """添加K线图"""
        candlestick = go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'], 
            low=df['low'],
            close=df['close'],
            increasing_line_color=self.color_scheme['up'],
            decreasing_line_color=self.color_scheme['down'],
            name="K线",
            showlegend=False
        )
        fig.add_trace(candlestick, row=row, col=1)
    
    def _add_moving_averages(self, fig: go.Figure, df: pd.DataFrame, row: int):
        """添加移动平均线"""
        ma_lines = [
            {'column': 'MA5', 'name': 'MA5', 'color': '#FF6B6B', 'width': 1},
            {'column': 'MA10', 'name': 'MA10', 'color': '#4ECDC4', 'width': 1},
            {'column': 'MA20', 'name': 'MA20', 'color': '#45B7D1', 'width': 2},
            {'column': 'MA60', 'name': 'MA60', 'color': '#96CEB4', 'width': 2}
        ]
        
        for ma in ma_lines:
            if ma['column'] in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[ma['column']],
                        mode='lines',
                        name=ma['name'],
                        line=dict(color=ma['color'], width=ma['width']),
                        opacity=0.8
                    ),
                    row=row, col=1
                )
    
    def _add_bollinger_bands(self, fig: go.Figure, df: pd.DataFrame, row: int):
        """添加布林带"""
        if all(col in df.columns for col in ['BOLL_UP', 'BOLL_MID', 'BOLL_LOW']):
            # 上轨
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BOLL_UP'],
                    mode='lines',
                    name='BOLL上轨',
                    line=dict(color='rgba(128, 128, 128, 0.3)', width=1),
                    fill=None
                ),
                row=row, col=1
            )
            
            # 中轨
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BOLL_MID'],
                    mode='lines',
                    name='BOLL中轨',
                    line=dict(color='rgba(128, 128, 128, 0.5)', width=1),
                    fill=None
                ),
                row=row, col=1
            )
            
            # 下轨（填充区域）
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['BOLL_LOW'],
                    mode='lines',
                    name='BOLL下轨',
                    line=dict(color='rgba(128, 128, 128, 0.3)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(128, 128, 128, 0.1)'
                ),
                row=row, col=1
            )
    
    def _add_macd_chart(self, fig: go.Figure, df: pd.DataFrame, row: int):
        """添加MACD指标图"""
        if all(col in df.columns for col in ['MACD', 'DIF', 'DEA']):
            # MACD柱状图
            colors = ['red' if val < 0 else 'green' for val in df['MACD']]
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['MACD'],
                    name='MACD',
                    marker_color=colors,
                    opacity=0.6
                ),
                row=row, col=1
            )
            
            # DIF线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['DIF'],
                    mode='lines',
                    name='DIF',
                    line=dict(color='blue', width=1)
                ),
                row=row, col=1
            )
            
            # DEA线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['DEA'],
                    mode='lines',
                    name='DEA',
                    line=dict(color='orange', width=1)
                ),
                row=row, col=1
            )
    
    def _add_kdj_chart(self, fig: go.Figure, df: pd.DataFrame, row: int):
        """添加KDJ指标图"""
        if all(col in df.columns for col in ['K', 'D', 'J']):
            # K线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['K'],
                    mode='lines',
                    name='K',
                    line=dict(color='blue', width=1)
                ),
                row=row, col=1
            )
            
            # D线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['D'],
                    mode='lines',
                    name='D',
                    line=dict(color='red', width=1)
                ),
                row=row, col=1
            )
            
            # J线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['J'],
                    mode='lines',
                    name='J',
                    line=dict(color='green', width=1)
                ),
                row=row, col=1
            )
            
            # 添加超买超卖线
            fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=row, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=row, col=1)
    
    def _add_volume_chart(self, fig: go.Figure, df: pd.DataFrame, row: int):
        """添加成交量图"""
        if 'volume' in df.columns:
            # 根据涨跌设置颜色
            colors = []
            for i in range(len(df)):
                if df['close'].iloc[i] >= df['open'].iloc[i]:
                    colors.append(self.color_scheme['up'])
                else:
                    colors.append(self.color_scheme['down'])
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='成交量',
                    marker_color=colors,
                    opacity=0.7,
                    showlegend=False
                ),
                row=row, col=1
            )
    
    def _configure_chart_layout(self, fig: go.Figure, stock_name: str):
        """配置图表布局和样式"""
        fig.update_layout(
            title=dict(
                text=f'{stock_name} - 技术分析图表',
                x=0.5,
                font=dict(size=20, color='#2c3e50')
            ),
            xaxis_rangeslider_visible=False,  # 隐藏默认的rangeslider
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=100, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # 设置x轴样式
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showspikes=True,
            spikecolor="orange",
            spikethickness=2
        )
        
        # 设置y轴样式
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showspikes=True,
            spikecolor="orange",
            spikethickness=2
        )
        
        # 为底部子图添加范围选择器
        fig.update_layout(
            xaxis4=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="7D", step="day", stepmode="backward"),
                        dict(count=30, label="30D", step="day", stepmode="backward"),
                        dict(count=90, label="3M", step="day", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True, thickness=0.05),
                type="date"
            )
        )
    
    def create_indicator_comparison_chart(self, df: pd.DataFrame, indicators: List[str], 
                                        stock_name: str = "股票") -> go.Figure:
        """
        创建指标对比图表
        
        Args:
            df: 数据DataFrame
            indicators: 要对比的指标列表
            stock_name: 股票名称
            
        Returns:
            Plotly Figure对象
        """
        try:
            rows = len(indicators)
            fig = sp.make_subplots(
                rows=rows, cols=1,
                subplot_titles=indicators,
                vertical_spacing=0.1,
                shared_xaxes=True
            )
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for i, indicator in enumerate(indicators):
                if indicator in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[indicator],
                            mode='lines',
                            name=indicator,
                            line=dict(color=colors[i % len(colors)], width=2)
                        ),
                        row=i+1, col=1
                    )
            
            fig.update_layout(
                title=f'{stock_name} - 技术指标对比',
                height=150 * rows,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成指标对比图表失败: {str(e)}")
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text=f"图表生成失败: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, 
                showarrow=False
            )
            return empty_fig
    
    def create_multi_timeframe_chart(self, data_dict: Dict[str, pd.DataFrame], 
                                   stock_name: str = "股票") -> go.Figure:
        """
        创建多时间框架对比图表
        
        Args:
            data_dict: 不同时间框架的数据字典 {'日线': df, '周线': df, '月线': df}
            stock_name: 股票名称
            
        Returns:
            Plotly Figure对象
        """
        try:
            timeframes = list(data_dict.keys())
            fig = sp.make_subplots(
                rows=len(timeframes), cols=1,
                subplot_titles=[f'{tf} - 价格走势' for tf in timeframes],
                vertical_spacing=0.1,
                shared_xaxes=False
            )
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            
            for i, (timeframe, df) in enumerate(data_dict.items()):
                # 添加收盘价线图
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['close'],
                        mode='lines',
                        name=f'{timeframe}收盘价',
                        line=dict(color=colors[i % len(colors)], width=2)
                    ),
                    row=i+1, col=1
                )
                
                # 如果有MA20，也添加
                if 'MA20' in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df['MA20'],
                            mode='lines',
                            name=f'{timeframe}MA20',
                            line=dict(color=colors[i % len(colors)], width=1, dash='dash'),
                            opacity=0.7
                        ),
                        row=i+1, col=1
                    )
            
            fig.update_layout(
                title=f'{stock_name} - 多时间框架分析',
                height=200 * len(timeframes),
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"生成多时间框架图表失败: {str(e)}")
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text=f"图表生成失败: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, 
                showarrow=False
            )
            return empty_fig