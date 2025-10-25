# 📁 Ashare-AI-Strategy-Analyst 项目结构 v2.0

## 🎯 项目架构总览

本项目已完成结构性瘦身与增强，采用模块化设计，目录层级控制在6层以内。

## 📂 目录结构

```
Ashare-AI-Strategy-Analyst/
│
├── 📱 app/                      # Streamlit 前端与页面逻辑
│   ├── __init__.py
│   ├── app_config.py            # 应用配置和路由管理
│   ├── styles.py                # 统一样式管理
│   ├── pages/                   # 页面模块
│   │   ├── __init__.py
│   │   ├── home_page.py         # 首页
│   │   ├── config_page.py       # 配置页面（智能搜索）
│   │   ├── analysis_page.py     # 分析页面
│   │   ├── charts_page.py       # 图表页面
│   │   └── ai_insights_page.py  # AI洞察页面
│   └── styles/                  # 样式模块
│       ├── __init__.py
│       └── custom_css.py        # 自定义CSS
│
├── 🔧 ashare/                   # 核心功能模块
│   ├── __init__.py
│   ├── analyzer.py              # 股票分析器（主类）
│   ├── data.py                  # 数据获取模块
│   ├── indicators.py            # 技术指标计算
│   ├── charts.py                # 图表生成（Plotly）
│   ├── report.py                # 报告生成
│   ├── signals.py               # 交易信号
│   ├── search.py                # 智能股票搜索
│   ├── llm.py                   # AI分析模块
│   ├── strategy.py              # 策略分析
│   ├── helpers.py               # 辅助函数
│   ├── logging.py               # 日志管理
│   ├── notify.py                # 推送通知
│   └── config.py                # 配置管理
│
├── 🎨 assets/                   # 静态资源
│   ├── css/
│   │   └── report.css           # 报告样式
│   ├── fonts/
│   │   └── 微软雅黑.ttf         # 中文字体
│   └── templates/
│       └── report_template.html # 报告模板
│
├── ⚙️ config/                   # 环境与依赖配置
│   ├── .env.example             # 环境变量示例
│   ├── requirements.txt         # Python依赖
│   ├── Dockerfile               # Docker配置
│   └── Procfile                 # 部署配置
│
├── 🚀 scripts/                  # 辅助运行脚本
│   ├── run_web.sh               # 启动Web应用
│   └── run_cli.sh               # 启动命令行
│
├── 📝 docs/                     # 文档目录
│   ├── README.md                # 项目说明
│   └── PROJECT_STRUCTURE.md     # 本文档
│
├── 📊 logs/                     # 日志目录
│
├── 📄 主入口文件
│   ├── streamlit_app.py         # Streamlit Web应用入口
│   └── main.py                  # 命令行版本入口
│
└── 📋 其他文件
    ├── README.md                # 项目说明
    ├── LICENSE                  # 许可证
    └── .gitignore              # Git忽略文件
```

## 🔑 核心模块说明

### 1. app/ - Streamlit应用模块
- **app_config.py**: 主应用配置，包含页面路由和导航
- **styles.py**: 统一的CSS样式管理
- **pages/**: 各功能页面模块，职责分明

### 2. ashare/ - 核心业务模块
- **analyzer.py**: 股票分析器主类，整合所有分析功能
- **data.py**: 统一的数据获取接口
- **indicators.py**: 技术指标计算（RSI, MACD, 布林带等）
- **charts.py**: 基于Plotly的交互式图表
- **report.py**: HTML报告生成器
- **signals.py**: 交易信号生成和分析
- **search.py**: 智能股票搜索功能
- **llm.py**: AI大语言模型集成
- **config.py**: 统一配置管理

### 3. assets/ - 静态资源
- 存放CSS、字体、HTML模板等静态资源
- 用于生成美观的分析报告

### 4. config/ - 配置管理
- 集中管理所有配置文件
- 包含依赖、环境变量、部署配置

### 5. scripts/ - 运行脚本
- 提供便捷的启动脚本
- 简化应用部署和运行流程

## 🚀 启动方式

### Web应用（推荐）
```bash
# 方式1：使用脚本
./scripts/run_web.sh

# 方式2：直接启动
streamlit run streamlit_app.py
```

### 命令行版本
```bash
# 方式1：使用脚本
./scripts/run_cli.sh

# 方式2：直接运行
python main.py
```

## 📊 与旧版本对比

| 方面 | 旧版本 | 新版本 |
|------|--------|--------|
| 目录数量 | 12+ | 6 |
| 核心模块 | 分散在core/和utils/ | 统一在ashare/ |
| 配置文件 | 散落在根目录 | 集中在config/ |
| 入口文件 | 多个入口混乱 | 2个清晰入口 |
| 静态资源 | static/ | assets/ |
| 文档管理 | 分散 | 集中在docs/ |

## 🔄 主要改进

1. **✅ 目录瘦身**：从12+个目录精简到6个主要目录
2. **✅ 模块整合**：core/和utils/统一整合到ashare/
3. **✅ 配置集中**：所有配置文件移至config/
4. **✅ 命名规范**：采用清晰的命名约定
5. **✅ 结构清晰**：职责分明，易于维护和扩展

## 📝 开发规范

### 1. 添加新功能
- 在对应模块中添加，保持模块化结构
- 更新__init__.py导出必要的类和函数

### 2. 修改样式
- 编辑 `app/styles.py` 统一管理样式

### 3. 添加页面
- 在 `app/pages/` 下创建新文件
- 在 `app/app_config.py` 中注册新页面

### 4. 配置管理
- 统一使用 `ashare/config.py` 管理配置
- 敏感信息放在 `.env` 文件

### 5. 日志记录
- 使用 `ashare/logging.py` 进行统一日志管理
- 所有日志文件存放在 `logs/` 目录

## ✨ 项目特性

- 🎯 **模块化设计**：功能模块化，职责清晰
- 📦 **易于维护**：代码结构清晰，便于定位和修改
- 🚀 **快速扩展**：新增功能只需添加对应模块
- 👥 **团队协作**：结构规范，多人可并行开发
- ⚡ **性能优化**：按需加载，减少资源占用

## 📈 项目统计

- **Python文件**: 30+个
- **配置文件**: 4个
- **静态资源**: 3个
- **文档文件**: 2个
- **运行脚本**: 2个
- **主要模块**: 6个

## 🎉 重构完成

项目已完成结构性瘦身与增强，现在拥有：
- ✅ 清晰的目录结构
- ✅ 统一的命名规范
- ✅ 模块化的代码组织
- ✅ 完整的功能保留
- ✅ 更好的可维护性

---

**版本**: 2.0.0  
**最后更新**: 2025-10-25

