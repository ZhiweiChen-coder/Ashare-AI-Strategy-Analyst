# Ashare-AI-Strategy-Analyst

**Language / 语言**: [English](#english-version) | [中文](#中文版本)

---

## 中文版本

一个基于Python的A股智能分析工具，结合大语言模型提供数据驱动的投资建议和市场洞察。

### 项目简介

Ashare-LLM-Analyst 是一个A股市场的技术分析工具，通过[Ashare](https://github.com/mpquant/Ashare)采集股票历史数据，[MyTT](https://github.com/mpquant/MyTT)计算常见技术指标（如MACD、KDJ、RSI等），并利用大语言模型（Deepseek）生成可读性强的投资建议和市场分析。

该工具能够自动生成完整的HTML分析报告，包括基础数据分析、技术指标计算、趋势判断、支撑/阻力位识别以及AI辅助的专业投资建议。

### 开源致谢

本项目是基于 [@Ogannesson](https://github.com/Ogannesson) 的开源项目 [ashare-llm-analyst](https://github.com/Ogannesson/ashare-llm-analyst) 进行开发和增强的。感谢原作者的优秀工作和开源贡献！

在原项目基础上，我们进行了以下改进：
- 🏗️ **模块化重构**：将原有的单文件代码重构为清晰的模块化架构
- ⚙️ **配置系统增强**：添加了完善的配置验证和错误处理机制
- 📝 **日志系统优化**：实现了统一的彩色日志系统和文件日志轮转
- 🔧 **代码质量提升**：添加类型提示、文档字符串和完善的异常处理
- 🎯 **功能扩展**：增加了交易信号生成、推送通知等高级功能
- 🌐 **Web界面**：添加了Streamlit Web应用界面

### 在线预览

您可以访问 [此处](https://ala.oganneson.com) 查看分析报告的示例效果。

### 主要功能

- 自动获取A股历史交易数据
- 计算超过25种技术指标（MA、MACD、KDJ、RSI、BOLL等）
- 生成详细的技术分析图表
- 使用Deepseek大语言模型提供专业的投资分析和建议
- 输出美观的HTML格式分析报告
- 🌐 **Web界面**：现代化的Streamlit Web应用

### 使用方法

#### 前置准备

1. 确保安装了所有必需的依赖项:
```bash
pip install -r requirements.txt
```

2. 配置大语言模型API信息（两种方式）：

**方式一：使用环境变量（推荐）**
```bash
# Linux/Mac
export LLM_API_KEY="your_api_key_here"
export LLM_BASE_URL="https://api.deepseek.com"
export LLM_MODEL="deepseek-chat"

# Windows (命令提示符)
set LLM_API_KEY=your_api_key_here
set LLM_BASE_URL=https://api.deepseek.com
set LLM_MODEL=deepseek-chat

# Windows (PowerShell)
$env:LLM_API_KEY="your_api_key_here"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

**方式二：使用.env文件**
```bash
cp env.example .env
# 编辑.env文件，填入您的API密钥
```

#### 运行方式

**1. 命令行运行**
```bash
python main.py
```

**2. Web界面运行（推荐）**
```bash
streamlit run streamlit_app.py
```

### 🚀 部署指南

#### 方案1：Streamlit Cloud（推荐，免费）

1. **准备代码**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **部署到Streamlit Cloud**
   - 访问 [share.streamlit.io](https://share.streamlit.io)
   - 使用GitHub账户登录
   - 点击"New app"
   - 选择仓库和主文件：`streamlit_app.py`
   - 点击"Deploy"

3. **配置环境变量**
   - 在Streamlit Cloud的App Settings中
   - 点击"Secrets"标签
   - 添加所有API密钥和配置

#### 方案2：VPS服务器部署

1. **安装依赖**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

2. **克隆代码并安装依赖**
   ```bash
   git clone https://github.com/your-username/Ashare-AI-Strategy-Analyst.git
   cd Ashare-AI-Strategy-Analyst
   pip3 install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp env.example .env
   nano .env  # 编辑并填入真实的API密钥
   ```

4. **运行应用**
   ```bash
   streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
   ```

#### 方案3：Docker部署

```bash
# 构建镜像
docker build -t stock-analyzer .

# 运行容器
docker run -d \
  --name stock-analyzer \
  -p 8501:8501 \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="https://api.deepseek.com" \
  -e LLM_MODEL="deepseek-chat" \
  stock-analyzer
```

### 🔐 安全注意事项

- **API密钥安全**：永远不要将API密钥提交到GitHub
- **环境变量**：使用环境变量或部署平台的Secrets功能存储敏感信息
- **文件权限**：确保.env文件有正确的权限设置（600）

### 技术架构

- 数据获取：使用Ashare模块获取A股历史数据
- 技术分析：使用MyTT库进行技术指标计算
- 图表生成：使用Plotly生成交互式技术分析图表
- AI分析：通过Deepseek API获取专业的投资建议
- Web界面：使用Streamlit构建现代化Web应用
- 报告生成：生成包含详细分析的HTML报告

### 输出示例

生成的分析报告包含以下内容：

1. 基础技术分析（收盘价、涨跌幅、成交量等）
2. 技术指标详情（各项指标的最新值）
3. 技术指标图表（多维度的股票走势分析图）
4. 人工智能分析报告（基于历史数据的专业分析和投资建议）

### 重要说明

- **安全提示**：请务必妥善保管你的API密钥，建议使用环境变量或配置文件来存储敏感信息。

- **输出位置**：分析结果会输出到根目录下的`public`文件夹中。如果文件夹不存在，程序会自动创建。

- **免责声明**：本工具仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。用户应对自己的投资决策负责。

### 后续开发计划

- 添加更多技术指标和分析维度
- 提供更丰富的可视化选项
- 增加历史数据对比和回测功能
- 优化AI分析模型和提示词设计

### 许可证

[MIT License](LICENSE)

---

## English Version

A Python-based intelligent analysis tool for Chinese A-shares, combining large language models to provide data-driven investment recommendations and market insights.

### Project Overview

Ashare-AI-Strategy-Analyst is a technical analysis tool for the Chinese A-share market that uses [Ashare](https://github.com/mpquant/Ashare) to collect historical stock data, [MyTT](https://github.com/mpquant/MyTT) to calculate common technical indicators (such as MACD, KDJ, RSI, etc.), and leverages large language models (Deepseek) to generate readable investment recommendations and market analysis.

This tool can automatically generate comprehensive HTML analysis reports, including basic data analysis, technical indicator calculations, trend analysis, support/resistance level identification, and AI-assisted professional investment recommendations.

### Open Source Acknowledgments

This project is developed and enhanced based on the open-source project [ashare-llm-analyst](https://github.com/Ogannesson/ashare-llm-analyst) by [@Ogannesson](https://github.com/Ogannesson). Thanks to the original author for the excellent work and open-source contribution!

Based on the original project, we have made the following improvements:
- 🏗️ **Modular Refactoring**: Refactored the original single-file code into a clear modular architecture
- ⚙️ **Enhanced Configuration System**: Added comprehensive configuration validation and error handling mechanisms
- 📝 **Optimized Logging System**: Implemented unified colored logging system and file log rotation
- 🔧 **Code Quality Improvement**: Added type hints, docstrings, and comprehensive exception handling
- 🎯 **Feature Extension**: Added trading signal generation, push notifications, and other advanced features
- 🌐 **Web Interface**: Added Streamlit Web application interface

### Online Preview

You can visit [here](https://ala.oganneson.com) to view sample analysis reports.

### Key Features

- Automatically fetch Chinese A-share historical trading data
- Calculate over 25 technical indicators (MA, MACD, KDJ, RSI, BOLL, etc.)
- Generate detailed technical analysis charts
- Use Deepseek large language model to provide professional investment analysis and recommendations
- Output beautiful HTML format analysis reports
- 🌐 **Web Interface**: Modern Streamlit Web application

### Usage Instructions

#### Prerequisites

1. Ensure all required dependencies are installed:
```bash
pip install -r requirements.txt
```

2. Configure the Large Language Model API information (two methods):

**Method 1: Using Environment Variables (Recommended)**
```bash
# Linux/Mac
export LLM_API_KEY="your_api_key_here"
export LLM_BASE_URL="https://api.deepseek.com"
export LLM_MODEL="deepseek-chat"

# Windows (Command Prompt)
set LLM_API_KEY=your_api_key_here
set LLM_BASE_URL=https://api.deepseek.com
set LLM_MODEL=deepseek-chat

# Windows (PowerShell)
$env:LLM_API_KEY="your_api_key_here"
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_MODEL="deepseek-chat"
```

**Method 2: Using .env File**
```bash
cp env.example .env
# Edit the .env file and fill in your API key
```

#### Running the Application

**1. Command Line Execution**
```bash
python main.py
```

**2. Web Interface (Recommended)**
```bash
streamlit run streamlit_app.py
```

### 🚀 Deployment Guide

#### Option 1: Streamlit Cloud (Recommended, Free)

1. **Prepare Code**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Login with your GitHub account
   - Click "New app"
   - Select repository and main file: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Environment Variables**
   - In Streamlit Cloud App Settings
   - Click "Secrets" tab
   - Add all API keys and configurations

#### Option 2: VPS Server Deployment

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

2. **Clone Code and Install Dependencies**
   ```bash
   git clone https://github.com/your-username/Ashare-AI-Strategy-Analyst.git
   cd Ashare-AI-Strategy-Analyst
   pip3 install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp env.example .env
   nano .env  # Edit and fill in real API keys
   ```

4. **Run Application**
   ```bash
   streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
   ```

#### Option 3: Docker Deployment

```bash
# Build image
docker build -t stock-analyzer .

# Run container
docker run -d \
  --name stock-analyzer \
  -p 8501:8501 \
  -e LLM_API_KEY="your-api-key" \
  -e LLM_BASE_URL="https://api.deepseek.com" \
  -e LLM_MODEL="deepseek-chat" \
  stock-analyzer
```

### 🔐 Security Notes

- **API Key Security**: Never commit API keys to GitHub
- **Environment Variables**: Use environment variables or deployment platform's Secrets feature to store sensitive information
- **File Permissions**: Ensure .env file has correct permissions (600)

### Technical Architecture

- Data Acquisition: Use Ashare module to fetch Chinese A-share historical data
- Technical Analysis: Use MyTT library for technical indicator calculations
- Chart Generation: Use Plotly to generate interactive technical analysis charts
- AI Analysis: Get professional investment recommendations through Deepseek API
- Web Interface: Build modern Web applications using Streamlit
- Report Generation: Generate HTML reports with detailed analysis

### Output Examples

The generated analysis reports include the following content:

1. Basic Technical Analysis (closing price, price changes, trading volume, etc.)
2. Technical Indicator Details (latest values of various indicators)
3. Technical Indicator Charts (multi-dimensional stock trend analysis charts)
4. Artificial Intelligence Analysis Reports (professional analysis and investment recommendations based on historical data)

### Important Notes

- **Security Warning**: Please keep your API keys secure. It is recommended to use environment variables or configuration files to store sensitive information.

- **Output Location**: Analysis results will be output to the `public` folder in the root directory. If the folder doesn't exist, the program will create it automatically.

- **Disclaimer**: This tool is for learning and research purposes only and does not constitute any investment advice. Investment carries risks, so enter the market with caution. Users should be responsible for their own investment decisions.

### Future Development Plans

- Add more technical indicators and analysis dimensions
- Provide richer visualization options
- Add historical data comparison and backtesting functionality
- Optimize AI analysis models and prompt design

### License

[MIT License](LICENSE)
