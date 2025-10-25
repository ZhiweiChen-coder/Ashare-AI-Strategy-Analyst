#!/bin/bash
# 启动Streamlit Web应用

echo "🚀 启动 Ashare AI Strategy Analyst Web应用..."

# 进入项目根目录
cd "$(dirname "$0")/.." || exit 1

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查依赖
if [ ! -f "config/requirements.txt" ]; then
    echo "❌ 依赖文件不存在"
    exit 1
fi

# 安装依赖（可选）
# echo "📦 安装依赖..."
# pip3 install -r config/requirements.txt

# 启动应用
echo "🌐 启动Web应用..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
