# 📈 Ashare AI Strategy Analyst

> 一个基于AI的A股智能分析系统，提供技术分析、交易信号和智能投资建议。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 项目特色

- 🎯 **智能评分系统**：1-5分制评估股票走势（看涨/中性/看跌）
- 🤖 **AI驱动分析**：集成DeepSeek/OpenAI，提供专业投资建议
- 📊 **25+技术指标**：RSI, MACD, 布林带等全面技术分析
- 🔍 **智能搜索**：支持股票代码、名称、行业关键词搜索
- 📈 **实时数据**：获取最新股票行情和技术指标
- 🎨 **现代化界面**：美观的Streamlit Web界面

## 🚀 快速开始

### 1️⃣ 克隆项目
```bash
git clone https://github.com/your-repo/Ashare-AI-Strategy-Analyst.git
cd Ashare-AI-Strategy-Analyst
```

### 2️⃣ 安装依赖
```bash
pip install -r config/requirements.txt
```

### 3️⃣ 配置API密钥
```bash
# 编辑项目根目录的 .env 文件
nano .env
```

添加您的LLM API配置：
```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 4️⃣ 启动应用

**Web应用（推荐）：**
```bash
streamlit run streamlit_app.py
# 或使用脚本
./scripts/run_web.sh
```

访问：http://localhost:8501

**命令行版本：**
```bash
python main.py
# 或使用脚本
./scripts/run_cli.sh
```

## 📁 项目结构（v2.0 重构版）

```
Ashare-AI-Strategy-Analyst/
│
├── 📱 app/                      # Streamlit Web应用
│   ├── app_config.py            # 应用配置和路由
│   ├── styles.py                # 统一样式管理
│   └── pages/                   # 功能页面
│       ├── home_page.py         # 首页
│       ├── config_page.py       # 配置页面（股票池管理）
│       ├── analysis_page.py     # 分析页面
│       ├── charts_page.py       # 图表页面
│       └── ai_insights_page.py  # AI洞察页面
│
├── 🔧 ashare/                   # 核心业务模块
│   ├── analyzer.py              # 股票分析引擎
│   ├── data.py                  # 数据获取（AKShare）
│   ├── indicators.py            # 技术指标计算（25+指标）
│   ├── charts.py                # 交互式图表生成
│   ├── report.py                # HTML报告生成
│   ├── signals.py               # 交易信号分析（含评分系统）
│   ├── search.py                # 智能股票搜索
│   ├── llm.py                   # AI分析（DeepSeek/OpenAI）
│   ├── strategy.py              # 量化策略
│   ├── helpers.py               # 辅助工具函数
│   ├── logging.py               # 统一日志管理
│   ├── notify.py                # 推送通知
│   └── config.py                # 配置管理（环境变量）
│
├── 🎨 assets/                   # 静态资源
│   ├── css/                     # 样式文件
│   ├── fonts/                   # 字体文件
│   └── templates/               # HTML模板
│
├── ⚙️ config/                   # 配置文件
│   ├── requirements.txt         # Python依赖
│   ├── .env.example             # 环境变量示例
│   ├── Dockerfile               # Docker配置
│   └── Procfile                 # 部署配置
│
├── 🚀 scripts/                  # 运行脚本
│   ├── run_web.sh               # 启动Web应用
│   └── run_cli.sh               # 启动命令行
│
├── 📝 docs/                     # 项目文档
│   ├── README.md
│   └── PROJECT_STRUCTURE.md
│
├── 📊 logs/                     # 日志文件
├── 🗂️ _backup/                 # 旧版本备份
├── 📄 streamlit_app.py          # Web应用主入口
├── 📄 main.py                   # 命令行主入口
├── 📄 .env                      # 环境配置（需自行创建）
├── 📄 Ashare.py                 # 数据源模块
└── 📄 MyTT.py                   # 技术指标库
```

## ✨ 核心功能

### 📊 技术分析
- **25+种技术指标**：MACD, RSI, KDJ, 布林带, DMI, ROC等
- **多时间框架分析**：日线、周线、月线
- **趋势判断**：自动识别金叉、死叉、超买超卖
- **成交量分析**：量价关系研判

### 🎯 智能评分系统（独创）
| 评分 | 信号 | 说明 |
|------|------|------|
| 5分 | 🟢 强烈看涨 | 全是买入信号，强烈推荐 |
| 4分 | 🟢 看涨 | 买入信号占优 |
| 3分 | 🟡 偏多 | 略偏多头 |
| 2分 | 🟡 中性 | 观望或持有 |
| 1分 | 🔴 看跌 | 卖出信号占优 |

### 🤖 AI智能分析
- **DeepSeek集成**：性价比高的AI分析
- **OpenAI支持**：GPT-4级别分析
- **结构化输出**：JSON格式，包含信号、置信度、目标价
- **重试机制**：自动重试保证稳定性

### 🔍 智能股票搜索
- **多种搜索方式**：代码、名称、行业关键词
- **实时建议**：输入时自动提示
- **评分排序**：按匹配度排序
- **预设股票池**：热门指数、个股一键加载

### 📈 股票池管理
- **灵活添加**：搜索添加、手动输入、预设加载
- **批量管理**：支持批量添加和删除
- **即时分析**：创建分析器后立即开始

### 📝 报告生成
- **HTML格式**：美观的可视化报告
- **完整数据**：包含所有技术指标和信号
- **图表展示**：交互式K线图和指标图
- **一键导出**：便于分享和保存

## 🛠️ 技术栈

### 前端框架
- **Streamlit 1.36+**：现代化Web界面
- **自定义CSS**：渐变色、动画效果

### 数据处理
- **Pandas**：数据处理和分析
- **NumPy**：数值计算
- **Numba**：性能加速（可选）

### 数据可视化
- **Plotly**：交互式图表
- **Matplotlib**：静态图表

### AI/ML
- **OpenAI API**：支持GPT-4、GPT-4o-mini
- **DeepSeek API**：高性价比选择
- **Tenacity**：重试机制

### 数据源
- **AKShare**：A股数据获取
- **自定义API**：多数据源支持

### 其他
- **Python-dotenv**：环境变量管理
- **Joblib**：数据缓存
- **Jinja2**：模板引擎

## 📖 使用指南

### 1. 配置股票池
- 进入"⚙️ 配置"页面
- 使用搜索添加股票，或选择预设股票池
- 点击"🔧 创建股票分析器"

### 2. 运行分析
- 切换到"📊 分析"页面
- 点击"🔄 开始分析"
- 查看分析结果和信号评分

### 3. 查看图表
- 切换到"📈 图表"页面
- 查看K线图和技术指标图表
- 支持交互式缩放和平移

### 4. AI洞察
- 切换到"🤖 AI洞察"页面
- 获取AI生成的投资建议
- 查看置信度和目标价格

## 🎨 界面预览

### 系统状态显示
- ✅ **分析器已就绪**：显示股票池数量
- ✅ **LLM API 已配置**：AI分析功能可用
- ⚠️ **待配置**：提示需要配置

### 分析结果概览
- **分析股票**：总股票数量
- **成功分析**：成功获取数据的股票
- **看涨信号**：百分比和比例（如 40% 2/5）
- **分析时间**：最后分析时间

## 🔧 配置说明

### 环境变量（.env文件）
```env
# LLM API配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 日志配置
LOG_LEVEL=INFO
DEBUG=false
```

### 支持的LLM服务
1. **DeepSeek**（推荐）
   - 地址：https://api.deepseek.com
   - 模型：deepseek-chat
   - 优势：性价比高

2. **OpenAI**
   - 地址：https://api.openai.com/v1
   - 模型：gpt-4o-mini, gpt-4
   - 优势：准确度高

## 🚀 项目亮点

1. **v2.0重构**：目录结构从12+个精简到6个核心目录
2. **模块化设计**：清晰的职责划分，易于维护
3. **智能评分**：独创的1-5分评分系统
4. **性能优化**：缓存机制、Numba加速
5. **容错设计**：完善的错误处理和重试机制
6. **现代化UI**：美观的渐变色设计

## 📝 更新日志

### v2.0.0 (2025-10-25)
- ✨ 完成项目结构重构
- ✨ 新增智能评分系统（1-5分）
- ✨ 添加看涨信号统计
- 🔧 修复数据获取问题
- 🔧 优化import路径
- 📚 更新完整文档

### v1.x
- 初始版本功能

## ❓ 常见问题

**Q: 显示"数据获取失败"？**
A: 检查网络连接，确保可以访问股票数据源。

**Q: "LLM API 未配置"？**
A: 在项目根目录创建`.env`文件，添加API密钥。

**Q: 评分总是2分（中性）？**
A: 说明买入和卖出信号数量相当，市场无明显方向。

**Q: 如何添加自定义股票？**
A: 在配置页面使用"手动添加股票"功能，格式：`代码 名称`

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 👨‍💻 作者

Ashare Team

## 🌟 Star History

如果这个项目对您有帮助，请给它一个Star！⭐

---

**注意**：本系统仅供学习交流使用，不构成任何投资建议。投资有风险，入市需谨慎！
