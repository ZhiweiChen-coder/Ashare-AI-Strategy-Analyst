"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useLanguage } from "@/components/language-provider";

export default function AppLoading() {
  const { locale } = useLanguage();
  const pathname = usePathname();
  const requested = useSearchParams().get("lang");
  const english = requested === "en" || (requested !== "zh" && locale === "en");
  if (pathname === "/" || pathname === "/landing") return null;
  return (
    <>
      <section className="panel section loading-hero">
        <div className="section-kicker">{english ? "Switching view" : "正在切换页面"}</div>
        <h1>{english ? "Loading your page" : "正在加载页面"}</h1>
        <p className="muted">{english ? "Preparing your workspace…" : "请稍后，正在准备数据和组件。"}</p>
      </section>

      <section className="panel section loading-progress-panel">
        <div className="loading-skeleton-grid" aria-hidden="true">
          <div className="loading-skeleton-card">
            <div className="loading-skeleton-bar loading-skeleton-bar-sm" />
            <div className="loading-skeleton-bar" />
            <div className="loading-skeleton-bar loading-skeleton-bar-faded" />
          </div>
          <div className="loading-skeleton-card">
            <div className="loading-skeleton-bar loading-skeleton-bar-sm" />
            <div className="loading-skeleton-bar" />
            <div className="loading-skeleton-bar loading-skeleton-bar-faded" />
          </div>
          <div className="loading-skeleton-card">
            <div className="loading-skeleton-bar loading-skeleton-bar-sm" />
            <div className="loading-skeleton-bar" />
            <div className="loading-skeleton-bar loading-skeleton-bar-faded" />
          </div>
        </div>
      </section>
    </>
  );
}
