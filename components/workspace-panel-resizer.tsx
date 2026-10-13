"use client";

import { useEffect, useRef } from "react";
import { useLanguage } from "@/components/language-provider";
import { panelDefaults, panelLimits } from "@/lib/workspace-layout";

export function WorkspacePanelResizer({ side, width, max, onResize, onCommit }: { side: "left" | "right"; width: number; max: number; onResize: (width: number) => void; onCommit: (width: number) => void }) {
  const { locale } = useLanguage();
  const dragRef = useRef<{ x: number; initial: number; value: number; cursor: string; userSelect: string } | null>(null);
  const min = panelLimits[side].min;
  const label = locale === "en" ? (side === "left" ? "Resize watchlist sidebar" : "Resize research panel") : (side === "left" ? "调整左侧列表宽度" : "调整研究面板宽度");
  function restore() {
    const saved = dragRef.current;
    if (saved) { document.body.style.cursor = saved.cursor; document.body.style.userSelect = saved.userSelect; dragRef.current = null; }
  }
  useEffect(() => () => { const saved = dragRef.current; if (saved) { document.body.style.cursor = saved.cursor; document.body.style.userSelect = saved.userSelect; } }, []);
  function begin(event: React.PointerEvent<HTMLDivElement>) {
    if (event.button !== 0) return;
    event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, initial: width, value: width, cursor: document.body.style.cursor, userSelect: document.body.style.userSelect };
    document.body.style.cursor = "col-resize"; document.body.style.userSelect = "none";
  }
  function move(event: React.PointerEvent<HTMLDivElement>) {
    const saved = dragRef.current;
    if (!saved) return;
    const next = Math.max(min, Math.min(max, saved.initial + (event.clientX - saved.x) * (side === "right" ? -1 : 1)));
    saved.value = next; onResize(next);
  }
  function finish(cancel = false) { const saved = dragRef.current; if (!saved) return; onCommit(cancel ? saved.initial : saved.value); restore(); }
  return <div className={`workspace-panel-resizer workspace-panel-resizer--${side}`} role="separator" aria-orientation="vertical" aria-label={label} aria-valuemin={min} aria-valuemax={Math.round(max)} aria-valuenow={Math.round(width)} tabIndex={0} title={`${label} · ${locale === "en" ? "double-click to reset" : "双击恢复默认"}`} onPointerDown={begin} onPointerMove={move} onPointerUp={() => finish()} onPointerCancel={() => finish(true)} onLostPointerCapture={() => finish(true)} onDoubleClick={() => onCommit(panelDefaults[side])} onKeyDown={event => {
    const delta = event.key === "ArrowLeft" ? -1 : event.key === "ArrowRight" ? 1 : 0;
    if (!delta && event.key !== "Home" && event.key !== "End") return;
    event.preventDefault();
    onCommit(event.key === "Home" ? min : event.key === "End" ? max : Math.max(min, Math.min(max, width + delta * (event.shiftKey ? 20 : 5) * (side === "right" ? -1 : 1))));
  }} />;
}
