# 📁 Ashare-AI-Strategy-Analyst 项目结构

## 🏗️ 项目架构

```
Ashare-AI-Strategy-Analyst/
├── 📄 主入口文件
│   ├── streamlit_app.py              # Streamlit Web应用主入口 (模块化版本)
│   └── main.py                       # 命令行版本主程序
│
├── 🎨 Streamlit应用模块
│   └── streamlit_app/                # 模块化Streamlit应用
│       ├── app_config.py             # 主应用配置和路由
│       ├── styles/                   # 样式模块
│       │   └── custom_css.py         # 自定义CSS样式
│       └── pages/                    # 页面模块
│           ├── home_page.py          # 首页
│           ├── config_page.py        # 配置页面 (智能搜索)
│           ├── analysis_page.py      # 分析页面
│           ├── charts_page.py        # 图表页面
│           └── ai_insights_page.py   # AI洞察页面
│
├── 🔧 核心功能模块
│   ├── core/                         # 核心分析模块
│   │   ├── analyzer.py               # 股票分析器
│   │   ├── data_fetcher.py           # 数据获取
│   │   ├── indicators.py             # 技术指标计算
│   │   ├── plotly_charts.py          # 图表生成
│   │   └── report_generator.py       # 报告生成
│   │
│   ├── utils/                        # 工具函数
│   │   ├── helpers.py                # 辅助函数
│   │   ├── logger.py                 # 日志管理
│   │   ├── signal_analyzer.py        # 信号分析
│   │   ├── trading_signals.py        # 交易信号
│   │   └── stock_searcher.py         # 智能股票搜索器 ✨
│   │
│   ├── config.py                     # 配置管理
│   ├── llm.py                        # AI分析模块
│   ├── strategy.py                   # 策略分析
│   ├── Ashare.py                     # 股票数据获取
│   ├── MyTT.py                       # 技术指标库
│   └── push_notification.py          # 推送通知
│
├── 📦 静态资源
│   └── static/                       # 静态资源 (用于HTML报告)
│       ├── css/
│       │   └── report.css            # 报告样式
│       ├── fonts/
│       │   └── 微软雅黑.ttf          # 中文字体
│       └── templates/
│           └── report_template.html  # 报告模板
│
├── 📋 配置文件
│   ├── .env                          # 环境变量 (不提交到Git)
│   ├── env.example                   # 环境变量示例
│   ├── .gitignore                    # Git忽略文件
│   ├── .dockerignore                 # Docker忽略文件
│   ├── Dockerfile                    # Docker配置
│   ├── Procfile                      # 部署配置
│   ├── requirement.txt               # Python依赖
│   └── requirements_mac.txt          # Mac专用依赖
│
├── 📝 文档
│   ├── README.md                     # 项目说明
│   ├── PROJECT_STRUCTURE.md          # 项目结构说明
│   ├── LICENSE                       # 许可证
│   └── streamlit_app/README.md       # Streamlit模块说明
│
└── 📊 日志目录
    └── logs/                         # 日志文件目录
```

## 🚀 启动方式

### 1. Streamlit Web应用 (推荐)
```bash
python3 -m streamlit run streamlit_app.py
```
访问: http://localhost:8501

### 2. 命令行版本
```bash
python3 main.py
```

## 📁 文件说明

### 🎯 核心文件
- **`streamlit_app.py`**: 模块化Streamlit应用主入口 (24行，简洁高效)
- **`main.py`**: 命令行版本，适合自动化运行
- **`config.py`**: 统一配置管理，支持环境变量和.env文件

### 🔧 功能模块
- **`core/`**: 核心分析功能，包含数据获取、指标计算、图表生成
- **`utils/`**: 工具函数，包含日志、信号分析、辅助函数
- **`utils/stock_searcher.py`**: ✨ **智能股票搜索器** - 支持多种搜索方式
- **`llm.py`**: AI分析模块，集成大语言模型
- **`strategy.py`**: 策略分析，本地选股策略
- **`Ashare.py`**: 股票数据获取，支持A股和港股
- **`MyTT.py`**: 技术指标库，25+种技术指标

### 🎨 界面模块
- **`streamlit_app/`**: 完整的模块化Web界面
  - **`app_config.py`**: 应用配置和路由管理
  - **`styles/`**: 统一的样式管理
  - **`pages/`**: 功能页面模块
  - **`pages/config_page.py`**: ✨ **智能配置页面** - 集成智能搜索

### 📦 资源文件
- **`static/`**: 静态资源，用于生成HTML报告
- **`logs/`**: 日志文件目录

### ⚙️ 配置文件
- **`.env`**: 环境变量 (包含API密钥等敏感信息)
- **`env.example`**: 环境变量模板
- **`requirement.txt`**: Python依赖包列表

## 🔍 智能股票搜索功能 ✨

### 搜索特性
1. **多种搜索方式**:
   - 精确匹配股票代码 (如: `sh600036`)
   - 精确匹配股票名称 (如: `招商银行`)
   - 模糊匹配股票名称 (如: `招商`)
   - 模糊匹配股票代码 (如: `600036`)
   - 按行业/分类搜索 (如: `新能源`, `医药`, `银行`)
   - 智能代码格式验证

2. **智能评分系统**:
   - 精确代码匹配: 100分
   - 精确名称匹配: 95分
   - 模糊名称匹配: 80-95分
   - 模糊代码匹配: 70-85分
   - 分类匹配: 55-75分
   - 代码验证: 50分

3. **实时搜索建议**:
   - 输入2个字符以上时显示建议
   - 基于股票名称和分类的建议
   - 最多显示5个建议

4. **搜索结果展示**:
   - 股票名称和代码
   - 市场信息 (A股-上海、港股等)
   - 行业分类
   - 匹配分数
   - 一键添加到股票池

### 搜索示例
```python
# 搜索股票名称
"招商银行" → 招商银行 (sh600036) - A股-上海

# 搜索股票代码
"sh600036" → 招商银行 (sh600036) - A股-上海

# 搜索行业
"新能源" → 比亚迪、宁德时代、隆基绿能等

# 搜索关键词
"科技" → 蓝思科技、TCL科技等

# 搜索港股
"腾讯控股" → 腾讯控股 (00700.HK) - 港股
```

## 🗑️ 已清理的文件

以下文件已被清理，不再存在于项目中：

### Python缓存文件
- `__pycache__/` 目录及其所有 `.pyc` 文件
- 所有模块的缓存目录

### 系统文件
- `.DS_Store` (macOS系统文件)

### 重复和过时文件
- `streamlit_app_old.py` (1513行的旧版本，已删除)
- `run_web_app.py` (功能与 `streamlit_app.py` 重复)
- `worker.js` (Cloudflare Worker文件)
- `public/` 目录 (静态HTML文件)

### 空文件
- 空的日志文件

## 📊 项目统计

| 类型 | 文件数量 | 说明 |
|------|----------|------|
| Python文件 | 32个 | 核心功能代码 |
| 配置文件 | 8个 | 环境、依赖、部署配置 |
| 静态资源 | 4个 | CSS、字体、模板 |
| 文档文件 | 4个 | README、LICENSE等 |
| 目录 | 8个 | 模块化组织 |

## 🔄 模块化优势

1. **代码组织**: 功能模块化，职责清晰
2. **维护性**: 易于定位和修改代码
3. **扩展性**: 新增功能只需添加模块
4. **团队协作**: 多人可以并行开发
5. **性能优化**: 按需加载，减少内存占用

## 📝 开发建议

1. **新增功能**: 在对应模块中添加，保持模块化结构
2. **修改样式**: 编辑 `streamlit_app/styles/custom_css.py`
3. **添加页面**: 在 `streamlit_app/pages/` 下创建新文件
4. **配置管理**: 统一使用 `config.py` 管理配置
5. **日志记录**: 使用 `utils/logger.py` 进行日志管理
6. **股票搜索**: 使用 `utils/stock_searcher.py` 进行智能搜索

## ✅ 清理完成

**项目现在只有一个Streamlit应用入口：`streamlit_app.py`**

- ✅ 删除了 `streamlit_app_old.py` (1513行旧版本)
- ✅ 保留了模块化版本 `streamlit_app.py` (24行)
- ✅ 清理了所有缓存文件
- ✅ 项目结构更加清晰
- ✅ 功能完整，性能更好
- ✨ **新增智能股票搜索功能** 