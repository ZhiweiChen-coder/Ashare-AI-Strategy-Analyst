# Streamlit App 模块化架构

## 📁 目录结构

```
streamlit_app/
├── __init__.py                 # 包初始化文件
├── main_app.py                 # 主应用入口（备用）
├── app_config.py               # 主应用配置和路由
├── styles/                     # 样式模块
│   ├── __init__.py
│   └── custom_css.py           # 自定义CSS样式
└── pages/                      # 页面模块
    ├── __init__.py
    ├── home_page.py            # 首页
    ├── config_page.py          # 配置页面
    ├── analysis_page.py        # 分析页面
    ├── charts_page.py          # 图表页面
    └── ai_insights_page.py     # AI洞察页面
```

## 🏗️ 架构设计

### 1. 主应用配置 (`app_config.py`)
- **StreamlitApp类**: 应用主类，负责初始化和路由
- **页面路由**: 根据侧边栏选择渲染对应页面
- **会话状态管理**: 初始化和管理全局状态
- **侧边栏渲染**: 统一的导航和状态显示

### 2. 样式模块 (`styles/`)
- **custom_css.py**: 包含所有自定义CSS样式
- **主题色彩**: 统一的颜色变量定义
- **响应式设计**: 移动端适配
- **组件样式**: 按钮、卡片、表格等组件样式

### 3. 页面模块 (`pages/`)

#### 首页 (`home_page.py`)
- 应用介绍和功能展示
- 系统状态概览
- 快速开始按钮

#### 配置页面 (`config_page.py`)
- 股票搜索和添加功能
- 预设股票池管理
- 分析参数配置
- 股票池导出功能

#### 分析页面 (`analysis_page.py`)
- 股票分析执行
- 分析结果展示
- 信号分析显示
- 报告导出功能

#### 图表页面 (`charts_page.py`)
- 交互式图表展示
- 多图表类型支持
- 多时间框架分析

#### AI洞察页面 (`ai_insights_page.py`)
- AI分析功能
- 投资建议生成
- 市场趋势预测

## 🔧 优势

### 1. 代码组织
- **模块化**: 每个功能独立成模块
- **可维护性**: 代码结构清晰，易于维护
- **可扩展性**: 新增功能只需添加新模块

### 2. 性能优化
- **按需加载**: 只加载需要的页面模块
- **内存效率**: 减少重复代码
- **启动速度**: 更快的应用启动

### 3. 开发体验
- **团队协作**: 不同开发者可以并行开发不同模块
- **代码复用**: 通用功能可以在多个页面间共享
- **测试友好**: 每个模块可以独立测试

## 🚀 使用方法

### 启动应用
```bash
python3 -m streamlit run streamlit_app.py
```

### 开发新页面
1. 在 `pages/` 目录下创建新的页面文件
2. 实现页面类，包含 `render()` 方法
3. 在 `app_config.py` 中添加路由

### 修改样式
1. 编辑 `styles/custom_css.py`
2. 修改CSS变量或添加新样式
3. 重启应用查看效果

## 📝 注意事项

1. **唯一Key**: 所有Streamlit组件都需要唯一的key参数
2. **状态管理**: 使用 `st.session_state` 管理全局状态
3. **错误处理**: 每个模块都要包含适当的错误处理
4. **性能考虑**: 避免在页面渲染时进行耗时操作

## 🔄 迁移说明

原来的 `streamlit_app.py` 已被备份为 `streamlit_app_old.py`，新的模块化版本保持了所有原有功能，同时提供了更好的代码组织结构。 