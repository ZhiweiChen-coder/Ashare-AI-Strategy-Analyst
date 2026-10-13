export type ToolActivity = { tool: string; status: "running" | "completed" | "unavailable"; reasonCode?: string | null; retried?: boolean };

export function researchWorkLabel(seconds: unknown, locale: "zh" | "en"): string | undefined {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) return;
  if (seconds < 1) return locale === "en" ? "Worked for <1s" : "用时不足 1 秒";
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return locale === "en"
    ? `Worked for ${minutes ? `${minutes}m ` : ""}${remainder}s`
    : `用时 ${minutes ? `${minutes} 分 ` : ""}${remainder} 秒`;
}

export function researchProgressLabel(stage: string | undefined, locale: "zh" | "en") {
  const labels: Record<string, [string, string]> = {
    understand_query: ["理解问题", "Understanding your question"],
    load_memory: ["查看对话上下文", "Reviewing context"],
    select_engine: ["准备研究", "Preparing research"],
    check_facts: ["核对事实与来源", "Checking facts and sources"],
    compose_response: ["整理回答", "Preparing the answer"],
    persist_memory: ["保存研究结果", "Saving the report"],
    publish_answer: ["呈现回答", "Presenting the answer"],
  };
  return labels[stage ?? ""]?.[locale === "en" ? 1 : 0] ?? (locale === "en" ? "Researching sources" : "正在研究资料");
}

export function updateToolActivity(previous: ToolActivity[], incoming: ToolActivity): ToolActivity[] {
  const index = previous.findLastIndex(step => step.tool === incoming.tool);
  if (index < 0) return [...previous, incoming];
  const prior = previous[index];
  const hadIssue = prior.status === "unavailable" || Boolean(prior.reasonCode);
  const next = { ...incoming, retried: prior.retried || (hadIssue && incoming.status === "running"), reasonCode: incoming.reasonCode ?? (incoming.status === "running" ? undefined : prior.status === "running" ? undefined : prior.reasonCode) };
  return previous.map((step, i) => i === index ? next : step);
}

const reasons: Record<string, [string, string]> = {
  no_matches: ["没有匹配", "No match"], no_results: ["暂无结果", "No results"],
  ambiguous_identity: ["需要确认代码", "Choose ticker"], identity_unverified: ["身份未核验", "Not verified"],
  identity_required: ["等待身份核验", "Needs identity"],
  specialist_error: ["复核未完成", "Review failed"], provider_error: ["来源不可用", "Source unavailable"],
};

export function toolActivityOutcome(step: ToolActivity, locale: "zh" | "en", laterSucceeded = false) {
  const en = locale === "en";
  const reason = reasons[step.reasonCode ?? ""]?.[en ? 1 : 0];
  if (step.status === "running") return { label: en ? "Working" : "调用中", detail: "", recovered: false };
  if (laterSucceeded && (step.status === "unavailable" || reason)) return { label: en ? "Retried" : "已重试", detail: `${reason || (en ? "This attempt did not complete" : "本次调用未完成")}. ${en ? "A later call to this tool completed." : "后续调用已完成。"}`, recovered: true };
  if (reason) return { label: reason, detail: "", recovered: false };
  if (step.status === "completed") return { label: step.retried ? (en ? "Done after retry" : "重试后完成") : (en ? "Done" : "完成"), detail: "", recovered: Boolean(step.retried) };
  return { label: en ? "Unavailable" : "不可用", detail: "", recovered: false };
}
