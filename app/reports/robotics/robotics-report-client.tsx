"use client";

import Link from "next/link";
import type { CSSProperties } from "react";

import { useLanguage } from "@/components/language-provider";

export function RoboticsReportClient() {
  const { locale } = useLanguage();
  const en = locale === "en";

  return (
    <main style={styles.page}>
      <section style={styles.header}>
        <div>
          <p style={styles.kicker}>{en ? "RESEARCH REPORT · ARCHIVE" : "专题报告 · 存档"}</p>
          <h1 style={styles.title}>{en ? "Robotics industry research" : "机器人产业链投研报告"}</h1>
          <p style={styles.subtitle}>
            {en
              ? "An archived report covering company fundamentals, price action, industry news, and risk context. The source document is preserved in Chinese."
              : "存档报告涵盖公司基本面、价格走势、行业新闻与风险背景。原始报告保留为中文。"}
          </p>
        </div>
        <div style={styles.actions}>
          <Link href={`/work?lang=${locale}`} style={styles.secondaryButton}>
            {en ? "Back to research" : "返回工作台"}
          </Link>
          <a href="/reports/robotics/raw" target="_blank" rel="noreferrer" style={styles.primaryButton}>
            {en ? "Open original · Chinese ↗" : "打开原始报告 ↗"}
          </a>
        </div>
      </section>

      <section style={styles.archive} aria-label={en ? "Archived source report" : "存档报告正文"}>
        <p style={styles.archiveLabel}>{en ? "SOURCE LANGUAGE" : "原始语言"}</p>
        <h2 style={styles.archiveTitle}>{en ? "This report is available in Chinese." : "本报告为中文原文。"}</h2>
        <p style={styles.archiveText}>
          {en
            ? "Open the source document to read its full analysis and tables. The original wording and figures are preserved as published."
            : "打开原始文档可查看完整分析与表格。原文内容与数据均按存档版本保留。"}
        </p>
        <a href="/reports/robotics/raw" target="_blank" rel="noreferrer" style={styles.archiveLink}>
          {en ? "Read the original Chinese report ↗" : "阅读中文原始报告 ↗"}
        </a>
      </section>

      <details style={styles.details}>
        <summary style={styles.detailsSummary}>{en ? "Show the original report here · Chinese" : "在此处展开原始报告"}</summary>
        <iframe
          title={en ? "Original robotics industry report in Chinese" : "机器人产业链投研报告原文"}
          src="/reports/robotics/raw"
          style={styles.iframe}
          sandbox="allow-popups allow-popups-to-escape-sandbox"
        />
      </details>
    </main>
  );
}

const styles = {
  page: {
    display: "flex",
    minHeight: "calc(100vh - var(--nav-height) - 56px)",
    flexDirection: "column",
    gap: 16,
  },
  header: {
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: 20,
    border: "1px solid var(--line)",
    borderRadius: 8,
    background: "linear-gradient(135deg, rgba(251,250,246,0.98), rgba(236,231,223,0.92)), linear-gradient(90deg, rgba(15,138,123,0.14), transparent)",
    padding: "20px 22px",
    boxShadow: "var(--shadow)",
  },
  kicker: { margin: "0 0 6px", color: "var(--accent)", fontSize: 12, fontWeight: 800, letterSpacing: "0.08em" },
  title: { margin: 0, fontSize: "clamp(26px, 3vw, 40px)", letterSpacing: 0, lineHeight: 1.08 },
  subtitle: { maxWidth: 820, margin: "10px 0 0", color: "var(--muted)", fontSize: 15, lineHeight: 1.7 },
  actions: { display: "flex", flexShrink: 0, flexWrap: "wrap", gap: 10, justifyContent: "flex-end" },
  primaryButton: { display: "inline-flex", alignItems: "center", minHeight: 38, borderRadius: 8, background: "var(--surface-contrast)", color: "#fff", fontSize: 14, fontWeight: 800, padding: "8px 14px" },
  secondaryButton: { display: "inline-flex", alignItems: "center", minHeight: 38, border: "1px solid var(--line-strong)", borderRadius: 8, background: "rgba(255,255,255,0.62)", color: "var(--ink)", fontSize: 14, fontWeight: 800, padding: "8px 14px" },
  archive: { width: "min(100%, 760px)", margin: "clamp(36px, 8vh, 88px) auto", padding: "clamp(24px, 5vw, 48px)", border: "1px solid var(--line)", borderRadius: 8, background: "var(--surface)", boxShadow: "var(--shadow)" },
  archiveLabel: { margin: "0 0 10px", color: "var(--accent)", fontSize: 11, fontWeight: 800, letterSpacing: "0.1em" },
  archiveTitle: { margin: 0, fontSize: "clamp(22px, 3vw, 30px)", lineHeight: 1.2 },
  archiveText: { margin: "14px 0 22px", maxWidth: 600, color: "var(--muted)", fontSize: 15, lineHeight: 1.7 },
  archiveLink: { color: "var(--accent)", fontWeight: 800, textDecoration: "underline", textUnderlineOffset: 4 },
  details: { border: "1px solid var(--line)", borderRadius: 8, background: "var(--surface)", overflow: "hidden" },
  detailsSummary: { padding: "16px 20px", color: "var(--accent)", cursor: "pointer", fontSize: 14, fontWeight: 800 },
  iframe: { display: "block", width: "100%", height: "78vh", minHeight: 680, border: 0, background: "#fff" },
} satisfies Record<string, CSSProperties>;
