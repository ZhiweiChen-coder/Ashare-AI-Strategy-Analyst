import type { LandingLanguage } from "./landing-copy";

export const landingDetails = {
  en: {
    beta: "Public beta", access: "Hosted research requires sign-in and available credits. Deep research is currently unavailable.",
    trust: "MIT licensed. Research only, not investment advice.",
    sourceTitle: "Read the code. Run it yourself.", sourceBody: "OpenAshare is MIT licensed. Inspect the research workflow, adapt it, or run your own research desk with your own model key.",
    sourceLink: "Read the source on GitHub", setupLink: "Follow the local setup guide", setupTitle: "Your own research desk", setupSteps: ["Clone the repository", "Install Python and Node.js dependencies", "Configure your model key locally", "Start the API and web app"],
    faqTitle: "Before your first question",
    faqs: [
      { title: "Which markets does it cover?", body: "US, mainland China (A-shares) and Hong Kong equities. Price history is supported across these markets; company news and eligible US SEC filings depend on the symbol and provider. Support for a market does not mean every data type is available for every stock." },
      { title: "Where does the data come from?", body: "The code integrates Yahoo Finance via yfinance for US and Hong Kong prices, Finnhub for US news and fallback prices, AkShare and Chinese market sources for mainland data, and SEC EDGAR for eligible company filings. Availability depends on provider configuration. Prices may be delayed; this is not a real-time trading feed." },
      { title: "How do citations work?", body: "Research can include links to retrieved news, filings and other sources. Open the source and check its date, scope and reporting period. A citation is evidence to inspect, not a guarantee that an AI interpretation is correct. Missing evidence should remain a gap, not become a confident answer." },
      { title: "Is it free? What does public beta mean?", body: "The source code is free under the MIT License. Hosted AI research requires sign-in and available credits; check your balance in the research desk. Deep research is currently unavailable in the public beta. Self-hosted model and data providers may charge separately. We do not promise unlimited hosted use or future pricing." },
      { title: "Which AI model does it use?", body: "The model is configured by the deployment. The local setup documents DeepSeek and allows a model name, API base URL and API key to be configured. Hosted settings can change; a local example is not a guarantee of the hosted model. Compatibility with other providers depends on their API support." },
      { title: "What happens to my research data?", body: "The app supports local browser storage and account-backed workspace persistence when configured. AI requests send the question and relevant research context to the configured model provider. Self-hosting lets you choose that provider; it does not make external model or market-data requests stay on your device. Avoid entering confidential information." },
      { title: "Is this investment advice?", body: "No. OpenAshare is a research tool and does not place trades. AI answers can contain errors or omit important context. Verify original sources and make your own decisions." },
    ],
    closing: "Bring your next question.", closingBody: "Start with a company, a headline, or a period on a chart.",
    risk: "For research and information only. Nothing here is a recommendation to buy, sell or hold a security. Market data can be delayed or incomplete, and AI-generated answers can be incorrect. Verify original sources. Investing involves risk, including loss of capital.",
    credits: "Data integrations: Yahoo Finance, Finnhub, AkShare and SEC EDGAR. Availability depends on configuration; no affiliation or endorsement implied.",
    maintainer: "Maintained by Zhiwei Chen", contact: "Feedback on GitHub", data: "Data handling", journal: "Research journal",
  },
  zh: {
    beta: "公开测试版", access: "在线 AI 研究需要登录并有可用额度；深入研究目前暂不可用。", trust: "MIT 开源。仅供研究参考，不构成投资建议。",
    sourceTitle: "读懂代码，也能自己部署。", sourceBody: "OpenAshare 采用 MIT 许可证。你可以检查研究流程、按需修改，也可以使用自己的模型密钥搭建研究工作台。",
    sourceLink: "在 GitHub 查看源码", setupLink: "查看本地部署指南", setupTitle: "搭建自己的研究工作台", setupSteps: ["克隆代码仓库", "安装 Python 与 Node.js 依赖", "在本地配置模型密钥", "启动 API 与网页应用"],
    faqTitle: "开始提问之前",
    faqs: [
      { title: "支持哪些市场？", body: "支持美股、中国内地 A 股与港股。这些市场均支持历史行情，公司新闻及符合条件的美股 SEC 披露则取决于股票与数据提供方。支持某个市场，不代表每只股票都有所有类型的数据。" },
      { title: "数据来自哪里？", body: "代码通过 yfinance 接入 Yahoo Finance 的美股和港股行情，通过 Finnhub 获取美股新闻与备用行情，通过 AkShare 等中国市场来源获取内地数据，并通过 SEC EDGAR 获取符合条件公司的披露。实际可用性取决于数据源配置。行情可能延迟，并非实时交易数据流。" },
      { title: "如何核对引用来源？", body: "研究回答可附带检索到的新闻、公司披露和其他来源链接。请打开原文核对日期、范围与报告期。引用提供核验依据，但不保证 AI 的解读一定正确；缺失的证据应被视为缺口，而不是确定结论。" },
      { title: "免费吗？公开测试版有什么限制？", body: "源码按照 MIT 许可证免费开放。在线 AI 研究需要登录并有可用额度，可在研究工作台查看余额。公开测试版目前暂不支持深入研究。自行部署时，模型与数据提供方可能另外收费。我们不承诺无限在线用量或未来定价。" },
      { title: "使用哪个 AI 模型？", body: "模型由部署配置决定。本地部署文档以 DeepSeek 为例，可配置模型名称、API 地址与密钥。在线配置可能调整，本地示例不代表线上一定使用相同模型；其他提供方的兼容性取决于其 API 支持。" },
      { title: "我的研究数据会如何处理？", body: "应用支持浏览器本地存储，也可在配置后通过账户保存工作台数据。AI 请求会将问题和相关研究上下文发送至所配置的模型提供方。自行部署可选择提供方，但不代表外部模型和行情请求都留在你的设备中。请避免输入机密信息。" },
      { title: "这属于投资建议吗？", body: "不属于。OpenAshare 是研究工具，不执行交易。AI 回答可能有误或遗漏重要背景，请核验原始来源并自行作出判断。" },
    ],
    closing: "带着下一个问题，开始研究。", closingBody: "从一家公司、一条新闻，或图表中的一段时间开始。",
    risk: "仅供研究与信息参考，不构成买入、卖出或持有任何证券的建议。行情可能延迟或不完整，AI 回答可能有误，请核验原始来源。投资存在风险，包括本金损失。",
    credits: "数据接入：Yahoo Finance、Finnhub、AkShare 与 SEC EDGAR。实际可用性取决于配置，不代表合作或背书。",
    maintainer: "维护者：Zhiwei Chen", contact: "GitHub 问题反馈", data: "数据处理说明", journal: "研究日志",
  },
} satisfies Record<LandingLanguage, unknown>;
