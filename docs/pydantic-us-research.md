# Bilingual US-stock research

The existing FastAPI service layer now supplies the PydanticAI research agent with US company identity, SEC filing metadata and selected standardized financial facts. Stock analysis, news, themes, portfolio and chat remain the main product paths. This change does not deploy the app.

## Model and setup

The framework is **PydanticAI 2.55.0**, the latest stable release verified on 2026-10-11, with the OpenAI 3.x compatible client. This is distinct from the Pydantic data-validation library, which is already 2.x. See the [release record](https://pypi.org/project/pydantic-ai-slim/) and [V2 migration guide](https://pydantic.dev/docs/ai/overview/migration/).

Install `requirements_api.txt` and use an ignored `.env` with `LLM_API_KEY`, `LLM_BASE_URL=https://api.deepseek.com` and `LLM_MODEL=deepseek-flash`. The official API identifier for DeepSeek V4.1 Flash is `deepseek-flash`; see [DeepSeek model documentation](https://api-docs.deepseek.com/quick_start/pricing/).

Configure `SEC_USER_AGENT` with an application name and a contact email. The SEC receives this identifying header; keep the actual contact information out of tracked files. SEC requests use public ticker mappings, submissions and companyfacts APIs with caching, backoff and a shared two-requests-per-second limit. See [SEC API guidance](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

The workbench has a persistent Chinese/English menu preference. Agent requests accept `language: auto | en-US | zh-CN` and `research_mode: quick | deep`; explicit requested output language takes precedence. English aliases include Apple, NVIDIA, Microsoft, TSMC and Berkshire Hathaway. SEC identity checks can extend agent discovery beyond the local watchlist catalog. Ambiguous results require clarification.

## Research and cost controls

- Quick is the default: DeepSeek thinking is disabled. Its prompt requests one focused evidence pass, reuse of retrieved records, no repeated failed searches, and a concise answer: normally 80–160 English words or comparable brevity in Chinese, with first-pass investor briefs aiming for at most 220 words across the required four sections. Explicit requests for more detail take precedence.
- Detailed research/report/analysis requests in English or Chinese override compact-answer defaults. Deep detailed reports aim for 800–1,400 English words or comparable Chinese when evidence supports it, covering the requested dimensions with cited findings, implications, contrary evidence and specific gaps. The validator rejects a one-paragraph teaser when substantive evidence exists; sparse or unavailable evidence is not padded into a long report. Narrow Deep questions remain focused. Read-only specialist reviews retain their separate short-review policy rather than inheriting the parent's full-report format.
- Research has no application cumulative token, model-request count or tool-call count cap. Quick retains 2,500 output tokens per model request and a 180-second runtime deadline; Deep retains 10,000 output tokens per parent request and a 540-second deadline with thinking enabled. The Next.js proxy allows 190 seconds for Quick and 560 seconds for Deep. Usage accounting and the unknown-provider-usage guard remain active.
- Model client retries are disabled. Structured-output validation allows up to two repair attempts within the run deadline.
- Price analysis tools use `include_ai=false` to avoid another paid analysis inside data retrieval.
- Stop/disconnect cancels the pending server run. A submitted provider request may still incur charges; token/time limits are not a guaranteed monetary ceiling.
- Responses report model calls, input/output tokens, latency and a provisional cost estimate for DeepSeek Flash. Estimates use peak rates and treat all input as uncached; unknown provider usage is excluded and explicitly flagged, never treated as a settled zero charge. Other models have no dollar estimate until pricing is configured.
- A V2 capability scopes SEC and comparison tools to verified identities and reuses repeated retrievals within a run. Two-company comparisons check currency, taxonomy, duration and period end dates in Python; incompatible figures are never directly ranked.
- Comparison tool results include source IDs for the facts they derive from. The model receives compact records; full evidence remains available in the saved response.
- A limit stop preserves retrieved evidence and records the exact limit category. Unknown provider usage blocks further model calls in that run. A completed call with invalid structured output has known usage and can use the remaining bounded repair/synthesis allowance.
- After 95 seconds in Quick or 360 seconds in Deep, function tools are withdrawn to reserve final synthesis and validation repair. Cumulative token usage does not trigger this reserve. It does not guarantee completion if a provider stalls or returns an oversized response.
- The reserved DeepSeek synthesis pass disables additional thinking so its output allowance can be spent on the cited report; earlier Deep planning retains low reasoning effort.
- Web research admits at most two searches and two original-document reads. Failed reads count too; identical reads reuse results. English and US research use US search settings. FCC questions additionally use the official public Federal Register discovery API, with source document type preserved in the results.
- Private reports, source references/excerpts and redacted run diagnostics are saved under ignored `output/research-runs/`. No model reasoning, credentials, provider error bodies or conversation history are saved by this diagnostic path. This is report persistence, not durable execution or automatic paid-run recovery.

Company research now repairs an omitted identity search in Python before fetching news, quotes or SEC data. US identities still require SEC verification; ambiguous results never authorize a company-data read. This avoids an extra paid model turn solely to fix tool order. In-flight reads are deduplicated and at most two independent provider reads run concurrently. Internal prerequisite reads are included in per-run retrieval accounting.

Deep mode exposes `research_company`, with `catalysts`, `advantage`, `policy` and `overview` scopes. The coordinator verifies one company, collects news plus delayed prices or SEC facts, and for policy/advantage also runs up to two scoped web searches and reads discovered original documents. Policy research allocates document coverage to the regulator and company rather than reading two regulator documents. One or two read-only Pydantic analysts review industry position or policy exposure, then catalysts and contrary risks, when budget permits. Each review has an 800-token output allowance with thinking disabled. Their model turns run sequentially against one shared `RunUsage`. Invalid specialist output is isolated; an unknown provider charge stops further model calls and returns source-only evidence. The parent produces the final streamed, validated synthesis. Specialists cannot mutate the watchlist, trade, or recursively delegate. See [Pydantic multi-agent patterns](https://pydantic.dev/docs/ai/guides/multi-agent-applications/).

Industrial advantage is assessed as a source-backed thesis or conditional scenario, with assumptions, horizon, invalidation conditions and coverage gaps. Standardized SEC facts and headlines do not establish product superiority, clinical efficacy or future outcomes. The source reader extracts original HTML/text/PDF passages with locations, publication dates when available and explicit partial-coverage labels. Reads are limited to public HTTPS, two megabytes and the first 20 PDF pages; large HTML documents preserve the readable prefix and disclose truncation. Source URLs must come from retrieved evidence or the user. Competitor product datasets and clinical-trial records remain separate future integrations.

Price tools calculate one-, five- and twenty-observation returns and a previous-20-observation volume baseline in Python, preserving exact start/end dates. Missing or duplicate closes prevent calculation. Benchmark-relative performance and corporate-action adjustment details remain gaps when not supplied. News timing alone does not establish causation.

If synthesis fails, retrieved headlines, quotes, facts and source links remain available in a source-only response. The server no longer treats every tool/validation error as an unavailable model or discards the evidence. It does not start another paid synthesis automatically. Model usage is accumulated for exception paths too; incomplete accounting remains flagged rather than treated as zero.

The evidence view displays actual completed/unavailable tool steps and source metadata. It does not expose private chain-of-thought. DeepSeek reasoning content is returned to the provider when required by its tool-call protocol, and is excluded from product responses and exports.

## Evidence and coverage

SEC facts preserve taxonomy, concept, unit, start/end dates, filing date and accession/source URL. Foreign issuers are supported when their SEC filings and selected GAAP/IFRS facts are available. Reporting currencies can differ from USD trading prices. Facts do not include full filing narratives, estimates or earnings calendars. Old reporting periods and unavailable financial/news data remain explicit gaps.

Prices are historical or delayed daily data; retrieval time is separate from the underlying data date. Existing market pulse and theme services retain their current regional coverage, and the workbench labels the US-theme gap. This is not a complete US market scanner or comprehensive US news feed.

Source IDs and URLs, including inline citations, are checked against retrieved evidence. Identity search alone is not accepted as a source for financial/news claims. Selected financial amounts, original units and exact start/end/filing dates are rendered by the server, rather than converted by the model. Financial trend claims must cite matching-duration facts for the same company, metric, taxonomy and unit. These checks do not prove every generated statement is correct. Qualitative conclusions still require source review.

Reports persist in browser chat history. “Save report” and “Save sources” download readable Markdown documents, preserving source URLs and data/retrieval dates. Storage is local to that browser unless existing cloud workspace synchronization is configured. Raw source content may remain in its original language. The legacy deterministic engine retains its existing behavior when no model is configured; failed configured-model runs preserve available sources without another paid synthesis.

The redesigned workbench retains the warm white, teal and terracotta palette. The desktop layout shows the chart and research panel beside the conversation by default. It follows completed stock reports and restores the stock when a saved chat is reopened. Explicit stock links take priority at startup, pinned context is retained, and panel visibility can be changed in account settings or the header. Narrow screens retain an on-demand drawer. Full financial records, comparisons and sources are expandable. Suggestions prepare a question without submitting a paid request. The composer remains visible on narrow screens. Language, default market, default research depth, reading size and chart-panel visibility live in account settings and persist in this browser. New reports follow the selected language; historical reports retain their original wording.

The chat shows a collapsed execution-progress control while sources are gathered and output is checked. Drafts and validation retries stay private. After response assembly and saving, SSE progressively publishes the canonical summary; its text matches the final saved response. Tool history stays above the answer at completion. Internal reasoning and raw output JSON are excluded. Stopping, switching chats or disconnecting cancels the active transport, and the proxy deadline covers the entire stream. Browser-storage failures produce a prompt to download the report instead of silently claiming it was saved.

## Validation and retired experiments

The temporary managed-runtime implementation and its three experiment-specific test files were moved into ignored `output/managed-agent-trial/archived-implementation/`. Prior reports, usage reserves and checkpoints were retained. Product regression tests remain active.

Initial validation on 2026-10-11:

- All 143 offline backend tests passed, including the required API suite, agent evaluation, US market, stock metadata and research behavior suites.
- Production frontend build passed; targeted changed-component lint passed.
- Installed PydanticAI/OpenAI adapters completed mocked Quick/Deep tool roundtrips, including reasoning-field compatibility and exclusion from output.
- SEC cache, ambiguity, financial units/periods, language choice, unavailable data and stream cancellation were exercised offline.
- Real SEC retrieval returned AAPL/MSFT facts through June 2026. Retrieved TSM standardized facts remained through FY2024 and were labeled older; this does not prove that newer filings do not exist. Real AAPL daily prices had an underlying data date of 2026-10-09 and were labeled historical/delayed.
- Four initial real-model cases returned reports. Human review found a period-label error, a Chinese amount-conversion error and weak citation placement. The subsequent guarded earnings case rendered exact financial values but still made an unsupported growth claim; the final trend guard rejects that pattern in offline tests.
- The next comparison retest hit a usage limit. Five completed runs have a combined conservative estimate of **US$0.039075**. The stopped request has unresolved usage and a retained **US$0.05 reserve**. No further paid requests were admitted. Estimates use peak DeepSeek Flash prices with all input treated as cache misses; they are not settled billing amounts or a guaranteed ceiling.
- Browser checks verified both languages, saved-chat restoration, Chinese/Deep request parameters, expandable comparison/evidence and exact downloaded JSON/Markdown contents. These checks replayed saved real data with reviewed narratives, without another model call. They are UI/export verification, not a live validation of the final model prompt.
- Compact tool records reduced the saved comparison case's tool-content character count by 59.5%; this is a character measurement, not a measured token or billing saving. Final context/citation/trend changes remain to be validated live after usage reconciliation.

The current evaluation is small and **does not establish production financial-research accuracy**. Keep Quick as the default, inspect evidence, and reconcile unresolved usage before running further paid evaluation. The private test report, spend ledger and snapshots are in ignored `output/pydantic-v2-live/`.

Subsequent automatic-retrieval and specialist-review validation on 2026-10-11:

- All 178 backend tests passed, including the required 64 API tests. Production frontend build and changed-component lint passed.
- Offline Pydantic/OpenAI adapter tests exercised omitted identity search, concurrent deduplication, ambiguity, source-only recovery before/after tool execution, English observations, SEC-only research when news is missing, shared usage limits, nested reviews during parent streaming, and cancellation.
- A real Moderna source test verified `US.MRNA` through SEC mappings and retrieved configured company-news and delayed-price data with an offline model. This validates source plumbing, not the truth of each headline or a live model's explanation of the rally. No paid model requests were made during this repair.
- Live DeepSeek synthesis and specialist research remain to be revalidated after prior unresolved usage is reconciled. Existing saved failure responses retain their original wording; fixes apply to new runs.

Run the required checks with `.venv/bin/python -m pytest tests/test_api_app.py -q` and `npm run build`. The broader research checks are in `tests/test_research_product.py`.
