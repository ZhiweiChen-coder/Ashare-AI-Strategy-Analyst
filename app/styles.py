"""
统一样式管理
"""
import streamlit as st

def apply_custom_css():
    """应用自定义CSS样式"""
    st.markdown("""
    <style>
        /* 主容器样式 */
        .main > div {
            padding: 1.5rem;
        }
        
        /* 按钮样式 */
        .stButton button {
            border-radius: 12px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* 页面标题样式 */
        .page-title {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        
        /* 卡片样式 */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            margin: 0.5rem 0;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .main > div {
                padding: 1rem;
            }
            
            .page-title {
                font-size: 2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
