"use client";

import { useMemo, useRef } from "react";
import { useLanguage } from "@/components/language-provider";
import { clampChartWindow, moveChartWindow, type ChartBar, type ChartWindow } from "@/lib/chart-window";

export function ChartTimeline({ data, window: visible, onChange }: { data: ChartBar[]; window: ChartWindow; onChange: (range: ChartWindow) => void }) {
  const { locale } = useLanguage();
  const trackRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ x: number; range: ChartWindow; mode: "from" | "to" | "move"; width: number } | null>(null);
  const count = data.length;
  const max = Math.max(1, count - 1);
  const range = clampChartWindow(visible, count);
  const path = useMemo(() => {
    const prices = data.map(point => point.close!);
    const low = Math.min(...prices), spread = Math.max(...prices) - low || 1;
    return prices.map((value, index) => `${index / Math.max(1, prices.length - 1) * 1000},${44 - (value - low) / spread * 34}`).join(" ");
  }, [data]);
  const months = useMemo(() => data.flatMap((point, index) => index === 0 || point.date.slice(0, 7) !== data[index - 1].date.slice(0, 7) ? [{ index, date: point.date }] : []), [data]);
  const ticks = months.filter(({ date }, index) => index === 0 || index === months.length - 1 || (months.length > 24 ? ["01", "07"].includes(date.slice(5, 7)) : months.length > 14 ? index % 3 === 0 : true));
  const start = data[Math.max(0, Math.round(range.from))]?.date;
  const end = data[Math.min(count - 1, Math.round(range.to))]?.date;

  function begin(event: React.PointerEvent<HTMLElement>, mode: "from" | "to" | "move") {
    if (count < 2 || event.button !== 0 || !trackRef.current) return;
    event.preventDefault(); event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, range, mode, width: trackRef.current.getBoundingClientRect().width };
  }
  function drag(event: React.PointerEvent<HTMLElement>) {
    const saved = dragRef.current;
    if (!saved) return;
    const delta = (event.clientX - saved.x) / Math.max(1, saved.width) * max;
    if (saved.mode === "move") onChange(moveChartWindow(saved.range, delta, count));
    else if (saved.mode === "from") onChange(clampChartWindow({ from: Math.min(saved.range.to - Math.min(4, max), saved.range.from + delta), to: saved.range.to }, count));
    else onChange(clampChartWindow({ from: saved.range.from, to: saved.range.to + delta }, count));
  }
  function finish() { dragRef.current = null; }
  function keyboard(event: React.KeyboardEvent<HTMLElement>, mode: "from" | "to" | "move") {
    const step = event.shiftKey ? 10 : 1;
    const delta = event.key === "ArrowLeft" ? -step : event.key === "ArrowRight" ? step : 0;
    if (!delta && event.key !== "Home" && event.key !== "End") return;
    event.preventDefault();
    if (mode === "move") onChange(moveChartWindow(range, event.key === "Home" ? -max : event.key === "End" ? max : delta, count));
    else if (mode === "from") onChange(clampChartWindow({ from: Math.min(range.to - Math.min(4, max), event.key === "Home" ? 0 : event.key === "End" ? range.to - Math.min(4, max) : range.from + delta), to: range.to }, count));
    else onChange(clampChartWindow({ from: range.from, to: event.key === "Home" ? range.from + Math.min(4, max) : event.key === "End" ? max : range.to + delta }, count));
  }
  const pointerEvents = { onPointerMove: drag, onPointerUp: finish, onPointerCancel: finish, onLostPointerCapture: finish };
  return (
    <section className="chart-timeline" aria-label={locale === "en" ? "Chart timeline" : "图表时间轴"}>
      <div className="chart-timeline-meta"><span>{start} — {end}</span><span>{locale === "en" ? "Drag edges to zoom · drag the window to move" : "拖动两端缩放 · 拖动中间平移"}</span></div>
      <div className="chart-timeline-track" ref={trackRef}>
        <svg viewBox="0 0 1000 50" preserveAspectRatio="none" aria-hidden="true"><polygon points={`0,50 ${path} 1000,50`} /><polyline points={path} /></svg>
        <div className="chart-timeline-shade" style={{ left: 0, width: `${range.from / max * 100}%` }} />
        <div className="chart-timeline-shade" style={{ right: 0, width: `${(1 - range.to / max) * 100}%` }} />
        <div className="chart-timeline-window" role="button" tabIndex={count > 1 ? 0 : -1} aria-label={locale === "en" ? "Move visible period" : "移动可见时间区间"} style={{ left: `${range.from / max * 100}%`, width: `${(range.to - range.from) / max * 100}%` }} onPointerDown={event => begin(event, "move")} onKeyDown={event => keyboard(event, "move")} {...pointerEvents} />
        {(["from", "to"] as const).map(edge => <div key={edge} className="chart-timeline-handle" role="slider" tabIndex={count > 1 ? 0 : -1} aria-label={locale === "en" ? (edge === "from" ? "Visible period start" : "Visible period end") : (edge === "from" ? "可见区间起点" : "可见区间终点")} aria-valuemin={0} aria-valuemax={max} aria-valuenow={Math.round(range[edge])} aria-valuetext={edge === "from" ? start : end} style={{ left: `${range[edge] / max * 100}%` }} onPointerDown={event => begin(event, edge)} onKeyDown={event => keyboard(event, edge)} {...pointerEvents}><span /></div>)}
      </div>
      <div className="chart-timeline-months" aria-hidden="true">{ticks.map(({ index, date }, i) => <span key={date} style={{ left: `${index / max * 100}%` }} className={i % 2 ? "alternate" : ""}>{new Date(`${date}T00:00:00Z`).toLocaleDateString(locale === "en" ? "en-US" : "zh-CN", { month: "short", ...(months.length > 24 || i === 0 || date.slice(5, 7) === "01" ? { year: "2-digit" as const } : {}), timeZone: "UTC" })}</span>)}</div>
    </section>
  );
}
