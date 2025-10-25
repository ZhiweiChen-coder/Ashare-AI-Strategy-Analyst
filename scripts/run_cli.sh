#!/bin/bash
# 启动命令行版本

echo "🚀 启动 Ashare AI Strategy Analyst 命令行版本..."

# 进入项目根目录
cd "$(dirname "$0")/.." || exit 1

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 启动应用
echo "💻 启动命令行应用..."
python3 main.py
