"""
自定义CSS样式模块
"""

import streamlit as st


def load_custom_css():
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