import { journalArticles, type JournalArticle } from "./journal-data";

export type LandingLanguage = "en" | "zh";
export type { JournalArticle };

export const landingCopy = {
  en: {
    title: "OpenAshare | AI Stock Research for US, China & Hong Kong",
    description: "An AI stock research desk connecting price charts, company news and cited research across US, mainland China and Hong Kong equities.",
    experience: "Experience", journal: "Journal", approach: "Approach", menu: "Menu", close: "Close", language: "Language", beta: "Join the beta",
    eyebrow: "AN AI RESEARCH DESK", headline: "See the signal.", accent: "Find the story.",
    support: "Stocks, news and AI research. One connected view.", primary: "Open the research desk", secondary: "Watch the demos",
    watchDemo: "Watch the demos", pauseMotion: "Pause motion", playMotion: "Play motion", staticMotion: "Still view",
    studyDescription: "Illustrative candlesticks follow an overall ascending curve with gentle, continuous fluctuations. Not live market data.",
    experienceTitle: "01 / experience",
    videoUnavailable: "The video could not load.", openVideo: "Open video",
    videoPlayer: "Video player", playVideo: "Play video", pauseVideo: "Pause video", replayVideo: "Replay video",
    videoTimeline: "Video timeline", videoSpeed: "Playback speed", muteVideo: "Mute video", unmuteVideo: "Unmute video",
    videoMore: "More video options", videoOptions: "Video options",
    videoFullscreen: "Fullscreen", exitVideoFullscreen: "Exit fullscreen", videoFullscreenUnavailable: "Fullscreen is unavailable in this browser.",
    workflowTabsLabel: "Research workflows",
    workflowItems: [
      { label: "Stock questions", title: "Start with a question.", description: "Ask about a stock or headline and follow the answer alongside company context and sources.", preview: "A QUESTION · COMPANY CONTEXT" },
      { label: "Chart research", title: "Ask about the move you see.", description: "Select a period on the price chart and bring that date range into the conversation.", preview: "SELECTED PERIOD · AGENT CONTEXT" },
      { label: "Deep research", title: "Follow a theme into deeper research.", description: "Trace an industry question through source searches and company context, then explore the research summary. Deep research is unavailable in the public beta at the moment.", preview: "DEEP MODE · SOURCES & SYNTHESIS" },
    ],
    journalLabel: "02 / THE JOURNAL", journalMeta: "Questions worth pursuing.", concept: "RESEARCH IDEA", explore: "Explore the idea",
    articles: journalArticles.en,
    approachLabel: "03 / OUR APPROACH", approachMeta: "Useful by design.", approachTitle: "Research, without the noise.",
    principles: [
      { title: "How is OpenAshare different?", body: "Instead of answering in a blank chat, OpenAshare connects company questions to available market data, charts, relevant news, filings and source links in one research workspace across US, mainland China and Hong Kong equities." },
      { title: "How does it help you research better?", body: "Follow a headline back to a company, check the available evidence, then ask the next question with earlier context in view. Separate source-backed facts, inference and missing data before deciding what matters." },
      { title: "Is OpenAshare open source?", body: "Yes. The project is released under the MIT License. You can read the source code, adapt it, and self-host your own instance." },
    ],
    closingLabel: "STAY CURIOUS", closingTitle: "Look deeper.", closingAccent: "Decide clearer.",
    footer: "Research only. Not investment advice.", markets: "US · MAINLAND CHINA · HONG KONG", skip: "Skip to content",
  },
  zh: {
    title: "OpenAshare｜AI 股票研究工作台：美股、A 股与港股",
    description: "连接行情图表、公司新闻与有来源的 AI 研究，支持美股、内地和香港股票的研究工作台。",
    experience: "产品体验", journal: "研究日志", approach: "研究方式", menu: "菜单", close: "关闭", language: "语言", beta: "申请体验",
    eyebrow: "AI 股票研究工作台", headline: "读懂市场信号。", accent: "看见背后逻辑。",
    support: "让行情、新闻与 AI 研究彼此连接。", primary: "进入研究工作台", secondary: "观看演示",
    watchDemo: "观看演示", pauseMotion: "暂停动效", playMotion: "播放动效", staticMotion: "静态画面",
    studyDescription: "示意蜡烛图整体向右上方延伸，并带有轻微、持续的起伏；并非实时行情。",
    experienceTitle: "01 / 产品体验",
    videoUnavailable: "视频暂时无法加载。", openVideo: "打开视频",
    videoPlayer: "视频播放器", playVideo: "播放视频", pauseVideo: "暂停视频", replayVideo: "重新播放",
    videoTimeline: "视频时间轴", videoSpeed: "播放速度", muteVideo: "静音", unmuteVideo: "取消静音",
    videoMore: "更多视频选项", videoOptions: "视频选项",
    videoFullscreen: "全屏播放", exitVideoFullscreen: "退出全屏", videoFullscreenUnavailable: "当前浏览器暂不支持全屏播放。",
    workflowTabsLabel: "研究工作流",
    workflowItems: [
      { label: "股票问答", title: "从一个问题开始。", description: "围绕股票或新闻直接提问，结合公司信息和来源继续了解。", preview: "自然提问 · 公司上下文" },
      { label: "图表研究", title: "围绕眼前的走势提问。", description: "在行情图表中选中一段时间，将准确的日期区间带入研究对话。", preview: "已选时间段 · Agent 上下文" },
      { label: "深度研究", title: "沿着主题，继续深入。", description: "从产业问题出发，检索来源、连接相关公司，再阅读研究汇总。公开测试版暂时无法使用深入研究。", preview: "深入模式 · 来源与研究汇总" },
    ],
    journalLabel: "02 / 研究日志", journalMeta: "值得继续追问的问题。", concept: "研究思路", explore: "展开研究思路",
    articles: journalArticles.zh,
    approachLabel: "03 / 研究方式", approachMeta: "简单，但有依据。", approachTitle: "让研究少一些噪音。",
    principles: [
      { title: "OpenAshare 和通用 AI 有什么不同？", body: "它将公司检索、行情图表、相关新闻、可用公告与来源链接放在同一个研究工作台，覆盖美股、内地与香港市场，让问题始终连着相关证据。" },
      { title: "它如何帮助你做更好的研究？", body: "从新闻线索追到公司和可核验的依据，保留上下文继续追问，并把来源事实、分析推断和缺失数据分开。结论仍由你判断。" },
      { title: "OpenAshare 是开源项目吗？", body: "是的，项目采用 MIT 许可证发布。你可以阅读源代码、按需修改，并自行部署。" },
    ],
    closingLabel: "保持好奇", closingTitle: "看得更深。", closingAccent: "想得更清楚。",
    footer: "仅供研究参考，不构成投资建议。", markets: "美股 · 内地 · 香港", skip: "跳至正文",
  },
};
