"use client";

import { useLanguage } from "@/components/language-provider";

export default function AgentLoading() {
  const { locale } = useLanguage();
  return <section className="panel section"><p className="muted">{locale === "en" ? "Opening the research workspace…" : "正在进入工作台…"}</p></section>;
}
