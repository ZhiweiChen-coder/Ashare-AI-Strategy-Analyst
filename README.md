# OpenAshare

<p align="center">
  <a href="README.md"><strong>English</strong></a> · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <strong>An open-source stock research desk for US, mainland China, and Hong Kong markets.</strong><br />
  Bring prices, news, company filings, charts, and your research questions into one workspace.
</p>

<p align="center">
  <a href="https://github.com/ZhiweiChen-coder/OpenAshare/stargazers">GitHub stars</a> ·
  <a href="LICENSE">MIT License</a>
</p>

OpenAshare helps you follow a company, review the available evidence, and ask focused follow-up questions. It supports English and Simplified Chinese, with English as the default.

## See it in action

- [Research company news](public/marketing/demo-stock-questions.mp4)
- [Ask about a selected chart period](public/marketing/demo-chart-research.mp4)
- [Follow a research question in depth](public/marketing/demo-deep-research.mp4)

## What you can do

- Search stocks and review price charts and technical context.
- Explore company news, market themes, and available filings.
- Ask follow-up questions with research context carried through the conversation.
- Keep watchlists, portfolio notes, and research conversations together.

OpenAshare is for research only. It does not provide investment advice or place trades.

## Supported markets

| Market | Examples | Coverage |
| --- | --- | --- |
| US | `AAPL`, `NVDA` | Price history, news where available, and SEC filings for eligible companies. |
| Mainland China | `sh600036`, `sz000001` | A-share search and price history, plus China-focused news and market themes. |
| Hong Kong | `00700.HK` | Price history, charts, and Hang Seng market context. |

Data coverage varies by market, symbol, and provider. Some data may be delayed or unavailable; check the linked source and date before relying on it.

## Run locally

You need **Python 3.12+**, **Node.js 22**, and **npm**.

Install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_api.txt
npm install
```

For AI research, create a `.env` file in the project root and add your model provider settings:

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-flash
```

Keep API keys in your local `.env` file. Do not commit them. The app can start without a model key, but AI research features will be limited.

Start the API and web app in separate terminals:

```bash
./scripts/run_api.sh
```

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). For optional provider and SEC configuration, see [US research notes](docs/pydantic-us-research.md) and [.env.docker.example](.env.docker.example).

## Star history

<a href="https://www.star-history.com/?repos=ZhiweiChen-coder%2FOpenAshare&type=date&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=ZhiweiChen-coder/OpenAshare&type=date&theme=dark&legend=top-left" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=ZhiweiChen-coder/OpenAshare&type=date&legend=top-left" />
    <img alt="OpenAshare GitHub Star History Chart" src="https://api.star-history.com/chart?repos=ZhiweiChen-coder/OpenAshare&type=date&legend=top-left" />
  </picture>
</a>

## License

OpenAshare is licensed under the [MIT License](LICENSE).
