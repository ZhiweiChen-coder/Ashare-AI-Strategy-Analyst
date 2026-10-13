"use client";

import { useLanguage } from "@/components/language-provider";

export default function ChartsLoading() {
  const { locale } = useLanguage();
  const en = locale === "en";
  return (
    <>
      <section className="panel section loading-hero">
        <div className="section-kicker">Charts</div>
        <h1>{en ? "Loading charts" : "K 线页加载中"}</h1>
        <p className="muted">{en ? "Preparing stock search and chart modules." : "页面已切换，正在初始化搜索与图表模块。"}</p>
      </section>

      <section className="panel section">
        <h2>{en ? "Chart workspace" : "图表模块"}</h2>
        <div className="loading-progress-track" aria-hidden="true">
          <span />
        </div>
        <p className="muted">{en ? "The price chart and indicator snapshot will load after you select a stock." : "选择股票后会继续加载对应 K 线与指标快照。"}</p>
      </section>
    </>
  );
}
