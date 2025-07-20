#!/usr/bin/env python3
"""
Ashare AI 股票策略分析师 Web应用启动器

快速启动Streamlit Web界面
"""

import os
import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = [
        'streamlit',
        'streamlit-option-menu', 
        'plotly',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包：")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n🔧 请运行以下命令安装依赖：")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n或者安装完整依赖：")
        print("pip install -r requirements_mac.txt")
        return False
    
    return True


def setup_environment():
    """设置运行环境"""
    # 确保当前目录在Python路径中
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # 设置环境变量
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'false'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    
    return True


def main():
    """主程序入口"""
    print("🚀 启动 Ashare AI 股票策略分析师 Web应用")
    print("=" * 50)
    
    # 检查依赖
    print("📦 检查依赖包...")
    if not check_dependencies():
        return 1
    
    print("✅ 所有依赖包已就绪")
    
    # 设置环境
    print("⚙️ 设置运行环境...")
    setup_environment()
    print("✅ 环境设置完成")
    
    # 启动Streamlit应用
    print("🌐 正在启动Web应用...")
    print("📱 应用将在浏览器中自动打开")
    print("🔗 如果没有自动打开，请访问: http://localhost:8501")
    print("⏹️ 按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        # 运行Streamlit应用
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', 
            'streamlit_app.py',
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--browser.gatherUsageStats', 'false'
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 应用已停止")
        return 0
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 启动失败: {e}")
        return 1
    
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 