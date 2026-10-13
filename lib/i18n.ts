export type Language = "zh" | "en";

const english: Record<string, string> = {
  "科技": "Technology", "金融": "Financials", "能源": "Energy", "新能源": "Clean energy", "医药": "Healthcare", "消费": "Consumer", "AI与科技巨头": "AI and large technology companies", "全球宏观与央行": "Global macro and central banks", "能源与大宗商品": "Energy and commodities", "中东局势与战争": "Middle East developments",
  "high": "High", "medium": "Medium", "low": "Low", "no_positions": "No positions", "中性": "Neutral", "买入": "Positive", "卖出": "Negative",
  "未形成": "Not set", "上次整理 ·": "Last update · ", "创业板指": "ChiNext", "研究工具": "Research tools", "市场概览": "Market overview", "新闻与催化": "News & catalysts",
  "云端同步未完成": "Cloud sync unavailable", "使用本地记录": "Using local records",
  "SEC 财报": "SEC filings", "已加载会话记忆与历史上下文": "Chat context loaded", "已选择智能引擎，准备执行工具调用": "Preparing research tools", "智能引擎失败，切换到规则分析": "Research model unavailable; using source data", "已选择规则分析引擎": "Using source data", "会话记忆已更新": "Chat saved", "响应流已结束": "Research stream complete",
  "你好，我是 Ashare Agent。可以直接问全球新闻、热点、个股和持仓。": "Welcome to OpenAshare. Ask about US stocks, SEC filings, news and your portfolio.",
  "上证指数": "Shanghai Composite", "深证成指": "Shenzhen Component", "恒生指数": "Hang Seng", "沪深300": "CSI 300",
  "市场脉搏": "Market pulse", "我的持仓": "My portfolio", "新对话": "New chat", "返回 OpenAshare 首页": "OpenAshare home",
  "研究工作台": "Research desk", "市场研究中": "Market research", "云端已连接": "Cloud connected", "同步中": "Syncing", "云端异常": "Sync unavailable", "本地模式": "Local mode",
  "Agent 使用 Credit 余额": "Research credit balance", "本地模式 · Credits 不限": "Local · unlimited credits", "隐藏列表": "Hide list", "显示列表": "Show list", "隐藏研究": "Hide research", "显示研究": "Show research",
  "自选股和会话": "Watchlist and chats", "我的研究": "My research", "新建对话": "New chat", "添加股票或代码": "Add company or ticker", "自选股": "Watchlist", "项目": "Projects", "建立项目": "Create project",
  "例如：新能源产业链": "e.g. Semiconductor research", "项目名称": "Project name", "建立": "Create", "项目筛选": "Filter projects", "全部对话": "All chats", "未归类": "Unassigned", "最近会话": "Recent chats", "未归类对话": "Unassigned chats", "项目对话": "Project chats", "未命名对话": "Untitled chat",
  "这个项目还没有对话。点击右键可移动已有对话，或新建一个。": "No chats yet. Create a chat or right-click an existing chat to move it here.",
  "账户菜单": "Account menu", "个人研究空间": "Personal research space", "Agent 对话": "Research chat", "研究上下文": "Research context", "对话操作": "Chat actions", "对话名称": "Chat name", "输入新名称": "Enter a new name", "取消": "Cancel", "保存": "Save",
  "重命名对话": "Rename chat", "移动到项目": "Move to project", "先建立一个项目": "Create a project first", "删除对话": "Delete chat", "项目操作": "Project actions", "输入项目名称": "Enter project name", "重命名项目": "Rename project", "删除项目": "Delete project", "项目内对话将保留到“未归类”。": "Chats will be kept under Unassigned.",
  "研究数据暂时不可用": "Research data is temporarily unavailable", "取消固定研究上下文": "Unpin context", "固定当前研究上下文": "Pin context", "等待股票研究结果…": "Waiting for stock research…", "最新价": "Last available price", "展开 K 线": "Expand chart", "关闭 K 线图": "Close chart", "振幅": "Range", "成交量": "Volume",
  "技术观察": "Technical observations", "相关新闻": "Company news", "暂无相关新闻": "No company news available", "刷新研究": "Refresh research", "等待热点研究结果…": "Waiting for theme research…", "热度": "Activity", "相关标的": "Related stocks", "相关消息": "Related news",
  "等待市场数据…": "Waiting for market data…", "市场数据加载中…": "Loading market data…", "市场状态": "Market regime", "风险偏好": "Risk on", "风险收缩": "Risk off", "中性盘面": "Neutral", "评分": "Score", "主要指数": "Market indices", "全球新闻": "Global news", "等待持仓数据…": "Waiting for portfolio data…",
  "总市值": "Market value", "总盈亏": "Total P&L", "收益率": "Return", "技术风险": "Technical risk", "组合提示": "Portfolio observations", "重点持仓": "Positions", "动能差值": "Momentum", "14日强弱": "14-day strength", "摆动指标": "Oscillator", "20日均线": "20-day average", "技术指标": "Indicators", "基于最新行情计算": "Based on available daily data",
  "指标用于描述历史价格与成交量状态，不构成投资建议。": "Indicators describe historical prices and volume; they are research observations.", "你的研究会出现在这里": "Your research, with context", "点击左侧自选股，或直接问 Agent 一个问题。": "Select a watchlist stock or ask a research question.", "K 线": "Price chart", "新闻": "News", "热点": "Themes", "正在整理研究上下文": "Preparing research context", "刚刚": "Just now",
  "分析 sh600036": "Analyze AAPL price action", "看看海光信息最近消息": "Latest NVIDIA news", "分析我的持仓并结合世界局势": "Review my portfolio and macro risks",
  "等待输入": "Ready", "已提交实验 query，等待 Agent 事件流": "Request submitted; awaiting research events", "正在连接进度流": "Connecting", "正在请求分析结果": "Starting research", "正在调用研究工具": "Retrieving evidence", "最终回答已生成": "Report ready", "回答已生成": "Report ready", "未知错误": "Unknown error", "消息、热点、个股统一问答": "Stocks, filings, news and portfolio research",
  "收起历史": "Hide history", "历史记录": "History", "AI 生成内容可能出错或过时，请结合来源核验；不构成投资建议。": "AI reports can be wrong or outdated. Check the sources. Research only.", "历史对话": "Chat history", "切换、搜索、置顶、重命名": "Search, pin and organize", "搜索历史记录": "Search history", "置顶 · ": "Pinned · ", "取消置顶": "Unpin", "置顶": "Pin", "重命名": "Rename", "删除": "Delete", "输入会话名称": "Chat name", "暂无历史对话": "No chats yet",
  "直接提问": "Start your research", "支持全球新闻、热点、个股和持仓问答。": "Research US, Hong Kong and China stocks, SEC filings, news and portfolios.", "你": "You", "Agent 正在研究": "Research in progress", "整理研究结果": "Preparing report", "Agent 工作阶段": "Research progress", "理解问题": "Understand", "选择工具": "Retrieve", "整理证据": "Check evidence", "生成回答": "Report",
  "输入问题，Enter 发送，Shift+Enter 换行": "Ask about a company or ticker. Enter to send; Shift+Enter for a new line.", "清空": "Clear", "发送": "Send", "Agent 对话页": "Research assistant", "当前接入的是后端轻量 Agent，负责意图判断、服务调度和结果整合。": "Research company data, market structure and news in one conversation.", "对话": "Chat", "提问": "Ask", "你的问题": "Your question", "例如：分析我的持仓": "e.g. Review AAPL earnings", "发送给 Agent": "Start research",
  "最新消息": "Latest news", "板块对比": "Compare peers", "完整分析": "Full analysis", "全球影响": "Macro impact", "本次调用": "Sources used", " · 缓存": " · cached", "股票": "Stock", "全球重点新闻": "Global headlines", "影响": "Impact", "联网搜索结果": "Web sources", "消息卡片": "Company news", "查看该股消息": "Company news", "热点卡片": "Market themes", "只相关标的": "related stocks", "继续询问持仓": "Explore portfolio", "持仓卡片": "Portfolio", "组合表现": "Portfolio performance", "把盈亏、收益率和重点持仓收进一张卡片里。": "Returns, P&L and positions together.", "风险": "Risk", "盈亏": "P&L",
  "股票检索": "Company identity", "技术分析": "Price analysis", "个股消息": "Company news", "全球消息": "Global news", "热点列表": "Market themes", "热点详情": "Theme details", "联网搜索": "Web search", "持仓分析": "Portfolio analysis",
  "记忆": "Memory", "已记住这些偏好": "Saved preferences", "最近更新": "Updated", "偏好市场": "Market preference", "最近标的": "Last company", "暂无": "Unavailable", "当前目标": "Research goal", "上次整理 · ": "Last update · ", "A股": "China A-shares", "港股": "Hong Kong", "美股": "US stocks",
  "信号": "Signals", "指标": "Indicators", "画线": "Draw", "指针": "Pointer", "趋势线": "Trend line", "水平线": "Horizontal line", "清除": "Clear", "图表画线区域": "Chart drawing area", "已选择起点，再点击一次完成趋势线。": "Select the endpoint to finish the trend line.",
  "设置加载失败": "Could not load settings", "连接设置已保存。模型仍由平台统一管理。": "Connection saved. The model is configured by the server.", "保存失败": "Could not save", "正在加载当前设置...": "Loading settings…", "连接设置": "Connection settings", "模型由平台统一托管，用户不能选择或替换模型。这里仅管理连接状态。": "The server configures the model. Manage your local API connection here.", "平台模型": "Research model", "当前使用模型": "Current model", "由平台配置": "Server configured", "统一模型策略由服务端控制，用于 credit system 的成本和用量管理。": "The server controls model selection and research credit usage.",
  "云端 Beta 使用平台托管的模型与密钥，连接配置不会暴露给账户或写入共享服务。": "Cloud Beta uses server-managed credentials.", "本地 API 连接": "Local API connection", "留空则使用服务端默认地址": "Leave blank for the server default", "已配置，可留空保持不变": "Configured; leave blank to keep", "填写服务端使用的 API Key": "API key for your local server", "保存中...": "Saving…", "保存连接设置": "Save connection", "运行状态": "Status", "模型策略": "Model policy", "平台统一管理": "Server managed", "已配置": "Configured", "未配置": "Not configured", "服务端默认": "Server default",
  "已登录，正在同步工作台": "Signed in; syncing workspace", "Supabase 环境变量未配置": "Cloud authentication is not configured", "注册成功，请先查收确认邮件，再回来登录。": "Check your confirmation email before signing in.", "Supabase 登录失败": "Sign-in failed", "已退出登录": "Signed out", "退出登录失败": "Sign-out failed", "Google 登录失败": "Google sign-in failed", "Supabase 未配置": "Cloud not configured", "已登录": "Signed in", "退出中…": "Signing out…", "退出登录": "Sign out", "云端 · ": "Cloud · ", "云端 ·": "Cloud ·", "自选股保存失败": "Could not save the watchlist.", "Supabase 工作台同步失败": "Could not sync the workspace.", "退出": "Sign out", "登录 / 注册": "Sign in / Register", "登录研究空间": "Sign in to your workspace", "正在跳转…": "Redirecting…", "使用 Google 登录": "Continue with Google", "或使用邮箱": "Or use email", "邮箱": "Email", "密码（至少 6 位）": "Password (at least 6 characters)", "处理中…": "Working…", "登录": "Sign in", "注册": "Register", "拖动调整 Agent 宽度": "Resize assistant panel", "拖动调整宽度": "Drag to resize"
};

export function translateLabel(text: string, language: Language): string {
  const decoded = decodeEntities(text);
  return language === "en" ? english[decoded] ?? decoded : decoded;
}

export function decodeEntities(text: string): string {
  return text.replace(/&#(x[0-9a-f]+|\d+);/gi, (match, value: string) => {
    const code = value[0].toLowerCase() === "x" ? parseInt(value.slice(1), 16) : Number(value);
    return code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : match;
  }).replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
}

export function formatQuantity(value: number, language: Language): string {
  if (!Number.isFinite(value)) return "—";
  if (language === "en") return new Intl.NumberFormat("en-US", {notation:"compact", maximumFractionDigits:1}).format(value);
  if (Math.abs(value) >= 100000000) return `${(value / 100000000).toFixed(1)}亿`;
  if (Math.abs(value) >= 10000) return `${(value / 10000).toFixed(1)}万`;
  return value.toLocaleString("zh-CN");
}
