"use client";

import { useLanguage } from "@/components/language-provider";
import type { AgentResponse } from "@/lib/types";
import { researchExport } from "@/lib/research-export";
import { researchWorkLabel, toolActivityOutcome, type ToolActivity } from "@/lib/research-activity";
export type { ToolActivity } from "@/lib/research-activity";

const tools: Record<string, [string, string]> = {
  search_stocks: ["核验股票身份", "Resolve company identity"],
  get_sec_company_data: ["获取 SEC 财报", "Retrieve SEC filings and facts"],
  compare_companies: ["核对财务比较口径", "Compare financial periods and units"],
  get_stock_analysis: ["检查行情与技术指标", "Check prices and indicators"],
  get_stock_news: ["查找公司新闻", "Retrieve company news"],
  get_global_news: ["查找宏观新闻", "Retrieve macro news"],
  get_portfolio_analysis: ["检查持仓", "Review portfolio"],
  list_hotspots: ["检查市场热点", "Review market themes"],
  get_hotspot_detail: ["检查主题资料", "Review theme evidence"],
  web_search: ["检索公开资料", "Search public sources"],
  read_public_source: ["读取来源原文", "Read original source"],
  review_policy_exposure: ["核对政策与公司影响", "Review policy and company exposure"],
  manage_watchlist: ["更新自选股", "Update watchlist"],
  manage_research_goal: ["更新研究目标", "Update research goals"],
  research_company: ["分工研究公司", "Coordinate company research"],
  review_company_position: ["核对产业优势与财务韧性", "Review industry position and resilience"],
  review_catalysts_risks: ["核对催化与反向风险", "Review catalysts and contrary evidence"],
};

const metricLabels: Record<string, [string, string]> = {
  Revenue: ["营业收入", "Revenue"], NetIncomeLoss: ["净利润", "Net income"], ProfitLoss: ["净利润", "Net income"],
  Revenues: ["营业收入", "Revenue"], RevenueFromContractWithCustomerExcludingAssessedTax: ["营业收入", "Revenue"], RevenueFromContractWithCustomerIncludingAssessedTax: ["营业收入", "Revenue"],
  EarningsPerShareDiluted: ["稀释每股收益", "Diluted EPS"], DilutedEarningsLossPerShare: ["稀释每股收益", "Diluted EPS"],
  Assets: ["总资产", "Assets"], CashAndCashEquivalents: ["现金及等价物", "Cash and equivalents"], CashAndCashEquivalentsAtCarryingValue: ["现金及等价物", "Cash and equivalents"],
  Equity: ["股东权益", "Equity"], StockholdersEquity: ["股东权益", "Equity"], NetCashProvidedByUsedInOperatingActivities: ["经营现金流", "Operating cash flow"], CashFlowsFromUsedInOperatingActivities: ["经营现金流", "Operating cash flow"],
  "Net income": ["净利润", "Net income"], "Diluted EPS": ["稀释每股收益", "Diluted EPS"], "Operating cash flow": ["经营现金流", "Operating cash flow"],
};

export function researchToolLabel(tool: string, locale: "zh" | "en") {
  return tools[tool]?.[locale === "en" ? 1 : 0] ?? (locale === "en" ? "Research tool" : "研究工具");
}

export function ResearchTools({ steps, phase, workSeconds }: { steps: ToolActivity[]; phase?: string; workSeconds?: number }) {
  const { locale } = useLanguage();
  const en = locale === "en";
  const worked = researchWorkLabel(workSeconds, locale);
  if (!steps.length && !phase) return worked ? <p className="research-tool-activity">{worked}</p> : null;
  return <details className="research-tool-activity"><summary aria-live={phase ? "polite" : undefined}>{phase ? <i className="research-stream-dot" aria-hidden="true" /> : null}{phase || worked || (en ? "Tools used" : "调用的工具")}<span>{steps.length ? (worked && !phase ? `${steps.length} ${en ? "tools" : "个工具"}` : steps.length) : ""}</span></summary><ol>{steps.map((step, i) => {
    const laterSucceeded = steps.slice(i + 1).some(later => later.tool === step.tool && later.status === "completed" && !later.reasonCode);
    const outcome = toolActivityOutcome(step, locale, laterSucceeded);
    return <li key={`${step.tool}-${i}`}><span>{researchToolLabel(step.tool, locale)}</span><small data-status={outcome.recovered ? "retried" : step.status} title={outcome.detail || undefined}>{outcome.label}</small></li>;
  })}</ol></details>;
}

function downloadReport(response: AgentResponse, format: "sources" | "md", locale: "en" | "zh") {
  const { body, mime } = researchExport(response, format, locale);
  const url = URL.createObjectURL(new Blob([body], { type: mime }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `openashare-${format === "sources" ? "sources" : "research"}-${Date.now()}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ResponseTools({ response }: { response: AgentResponse }) {
  return <ResearchTools steps={(response.research_steps ?? []).map(step => ({tool: step.tool, status: step.status, reasonCode: step.reason_code}))} workSeconds={response.payload?._meta?.latency_seconds} />;
}

export function ResearchTrace({ response, showTools = true }: { response: AgentResponse; showTools?: boolean }) {
  const { locale } = useLanguage();
  const en = locale === "en";
  const metric = (name: string) => metricLabels[name]?.[en ? 1 : 0] ?? name;
  const evidence = response.evidence ?? [];
  const companies = response.payload.sec_companies ?? (response.payload.sec_company ? [response.payload.sec_company] : []);
  const comparison = response.payload.financial_comparison;
  const freshnessLabel = (value: string) => ({
    historical_or_delayed: en ? "Historical / delayed" : "历史／延迟数据",
    older_reported_period: en ? "Older reported period" : "较早报告期",
    reported_period: en ? "Reported period" : "已披露报告期",
    provider_summary: en ? "Provider publication" : "数据源发布",
    source_excerpts: en ? "Original source excerpts" : "来源原文节选",
    identity_mapping: en ? "Company identity mapping" : "公司身份映射",
    retrieved_snapshot: en ? "Retrieved snapshot" : "获取时的快照",
  }[value] ?? (en ? "Freshness unknown" : "时效未知"));
  return <div className="research-trace">
    {showTools ? <ResponseTools response={response} /> : null}
    {comparison ? <details className="research-financial-details">
      <summary>{en ? "Financial comparison" : "财务比较"}<span>{comparison.companies.map(company => company.code.replace("US.", "")).join(" / ")}</span></summary>
      <div className="research-financial-table"><table><thead><tr><th>{en ? "Metric" : "指标"}</th>{comparison.companies.map(company => <th key={company.code}>{company.code.replace("US.", "")}</th>)}<th>{en ? "Comparability" : "可比性"}</th></tr></thead><tbody>{comparison.metrics.map(row => <tr key={row.metric}>
        <td>{metric(row.metric)}</td>{row.values.map(value => <td key={value.code}>{value.fact ? <><a href={value.fact.url} target="_blank" rel="noreferrer">{value.fact.val.toLocaleString(en ? "en-US" : "zh-CN")} {value.fact.unit}</a><small>{value.fact.start ? `${value.fact.start} → ` : ""}{value.fact.end}</small></> : (en ? "Unavailable" : "不可用")}</td>)}
        <td><span className={row.comparable ? "research-comparable" : "research-period-gap"}>{row.comparable ? (en ? "Similar periods" : "报告期相近") : (en ? "No direct ranking" : "不可直接排名")}</span><small>{en ? row.comparison_note : (row.comparable ? "核对各自的准确日期" : "单位、准则或报告期不一致，或数据缺失")}</small></td>
      </tr>)}</tbody></table></div>
    </details> : null}
    {companies.map(sec => <details className="research-financial-details" key={sec.company.code}>
      <summary>{en ? "Reported financial facts" : "已披露财务数据"}<span>SEC · {sec.company.code.replace("US.", "")} · {sec.financials.length}</span></summary>
      <div className="research-sec-card">
      <div><strong>{sec.company.name}</strong><small>{en ? "Values shown in original reporting units" : "数值保留原始报告单位"}</small></div>
      <div className="research-financial-table"><table><thead><tr><th>{en ? "Metric" : "指标"}</th><th>{en ? "Value / unit" : "数值／单位"}</th><th>{en ? "Reporting period" : "报告期"}</th></tr></thead><tbody>
        {sec.financials.map((fact, i) => <tr key={`${fact.concept}-${i}`}><td><a href={fact.url} title={`${fact.taxonomy}: ${fact.concept}`} target="_blank" rel="noreferrer">{metric(fact.concept)}</a><small>{fact.form} · {en ? "Filed" : "披露"} {fact.filed}</small></td><td>{fact.val.toLocaleString(en ? "en-US" : "zh-CN")} {fact.unit}</td><td>{fact.start ? `${fact.start} → ` : ""}{fact.end}<small>{fact.freshness === "older_reported_period" ? (en ? "Older reported period" : "较早报告期") : ""}</small></td></tr>)}
      </tbody></table></div>
      {!sec.financials.length ? <p>{en ? "Standardized financial facts unavailable." : "标准化财务数据不可用。"}</p> : null}
      <div className="research-filing-links">{sec.filings.slice(0, 4).map(filing => <a key={filing.accession} href={filing.url} target="_blank" rel="noreferrer">{filing.form} · {filing.filed} ↗</a>)}</div>
      </div>
    </details>)}
    {evidence.length || response.data_gaps?.length ? <details>
      <summary>{en ? "Sources & data coverage" : "来源与数据覆盖"} <span>{evidence.length} {en ? "sources" : "来源"}</span></summary>
      <div className="research-source-list">{evidence.map(source => <article key={source.id}>
        {source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.source} ↗</a> : <strong>{source.source}</strong>}
        <small>{en ? "Data date" : "数据日期"}: {source.data_as_of || (en ? "Unknown" : "未知")} · {freshnessLabel(source.freshness)}</small>
        <small>{en ? "Retrieved" : "获取时间"}: {source.retrieved_at}</small>
        {source.excerpts?.length ? <details><summary>{en ? "Read source excerpts" : "查看原文节选"}</summary>{source.excerpts.map((excerpt, index) => <blockquote key={index}><small>{excerpt.location}</small><p>{excerpt.text}</p></blockquote>)}</details> : null}
      </article>)}</div>
      {response.data_gaps?.length ? <div className="research-data-gaps"><strong>{en ? "Data gaps" : "数据缺口"}</strong>{response.data_gaps.map((gap, i) => <p key={i}>{gap}</p>)}</div> : null}
    </details> : null}
    <div className="research-export-actions">
      <button type="button" onClick={() => downloadReport(response, "md", locale)}>{en ? "Save report" : "保存报告"} ↓</button>
      {evidence.length ? <button type="button" onClick={() => downloadReport(response, "sources", locale)}>{en ? "Save sources" : "保存来源"} ↓</button> : null}
    </div>
  </div>;
}
