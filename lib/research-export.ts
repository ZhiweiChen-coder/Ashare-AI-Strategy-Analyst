import type { AgentResponse } from "@/lib/types";

export function researchExport(response: AgentResponse, format: "json" | "md" | "sources", locale: "en" | "zh" = "en") {
  if (format === "json") return { body: JSON.stringify(response, null, 2), mime: "application/json" };
  const en = locale === "en";
  const sources = (response.evidence ?? []).map(source =>
    `- ${source.title || source.source}: ${source.url ?? (en ? "URL unavailable" : "链接不可用")}; ${en ? "data date" : "数据日期"}: ${source.data_as_of ?? (en ? "unknown" : "未知")}; ${en ? "retrieved" : "获取时间"}: ${source.retrieved_at}` + (source.excerpts ?? []).map(excerpt => `\n  ${excerpt.location}: ${excerpt.text}`).join(""),
  );
  return {
    body: [format === "sources" ? (en ? "# Research sources" : "# 研究来源") : response.summary, en ? "\n## Sources" : "\n## 来源", ...sources, en ? "\n## Data gaps" : "\n## 数据缺口", ...(response.data_gaps ?? []).map(gap => `- ${gap}`)].join("\n"),
    mime: "text/markdown;charset=utf-8",
  };
}
