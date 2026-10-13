"use client";

import { useLanguage } from "@/components/language-provider";
import type { ResearchContext } from "@/lib/workspace";

type Tool = "stock" | "news" | "market" | "portfolio";
const TOOLS = ["stock", "news", "market", "portfolio"] as const;

function ToolIcon({ type }: { type: Tool }) {
  return (
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {type === "stock" ? <><path d="M4 4v16h16" /><path d="m7 14 4-5 4 3 5-7" /></> : null}
      {type === "news" ? <><rect x="4" y="4" width="16" height="16" rx="2" /><path d="M8 8h8M8 12h3M8 16h8M15 12h1" /></> : null}
      {type === "market" ? <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c4 5 4 13 0 18-4-5-4-13 0-18Z" /></> : null}
      {type === "portfolio" ? <><rect x="3" y="7" width="18" height="14" rx="2" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12a22 22 0 0 0 18 0M12 12v3" /></> : null}
    </svg>
  );
}

export function WorkspaceTools({ activeType, onOpen, launchpad = false }: {
  activeType?: ResearchContext["type"];
  onOpen: (type: Tool) => void;
  launchpad?: boolean;
}) {
  const { t, locale } = useLanguage();
  const labels: Record<Tool, string> = {
    stock: locale === "en" ? "Stocks" : "股票",
    news: t("新闻"),
    market: locale === "en" ? "Market" : "市场",
    portfolio: t("我的持仓"),
  };

  return (
    <nav className={`workspace-tool-shortcuts${launchpad ? " workspace-tool-launchpad" : ""}`} aria-label={t("研究工具")}>
      <div className="workspace-tool-shortcut-row">
        {TOOLS.map(type => (
          <button className="workspace-tool-shortcut" key={type} type="button" title={labels[type]}
            aria-current={activeType === type ? "true" : undefined}
            onClick={() => onOpen(type)}>
            <ToolIcon type={type} /><span>{labels[type]}</span>{launchpad ? <span className="workspace-tool-arrow" aria-hidden="true">↗</span> : null}
          </button>
        ))}
      </div>
    </nav>
  );
}
