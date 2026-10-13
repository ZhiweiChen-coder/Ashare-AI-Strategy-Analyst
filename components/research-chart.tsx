"use client";

import { useLanguage } from "@/components/language-provider";

import { useCallback, useMemo, useRef, useState } from "react";
import type { IChartApi, Logical } from "lightweight-charts";

import { CandlestickChart, type ChartPoint } from "@/components/candlestick-chart";
import { ChartTimeline } from "@/components/chart-timeline";
import { chartSegment, clampChartWindow, orderedChartBars, presetChartWindow, type ChartWindow, type ChartSegment } from "@/lib/chart-window";
export type { ChartSegment } from "@/lib/chart-window";
export type ChartAnnotation = { id: string; startDate: string; endDate: string; note: string };

type IndicatorKey = "MA20" | "MA60" | "MACD" | "RSI" | "KDJ";
type DrawMode = "pointer" | "select" | "trend" | "horizontal";
type Point = { x: number; y: number };

type ResearchChartProps = {
  data: ChartPoint[];
  symbol?: string;
  height?: number;
  compact?: boolean;
  sourceIndicators?: Record<string, number | null | undefined>;
  fill?: boolean;
  periodSelection?: {
    selected: ChartSegment | null;
    onSelect: (segment: ChartSegment | null) => void;
    onAnnotate: (segment: ChartSegment) => void;
  };
  annotations?: ChartAnnotation[];
  onAnnotationSelect?: (annotation: ChartAnnotation, segment: ChartSegment) => void;
};

type IndicatorSeries = {
  values: Array<number | null>;
  signal?: Array<number | null>;
  histogram?: Array<number | null>;
};

const INDICATOR_LABELS: Record<IndicatorKey, string> = {
  MA20: "MA20",
  MA60: "MA60",
  MACD: "MACD",
  RSI: "RSI",
  KDJ: "KDJ",
};

const INDICATOR_COLORS: Record<IndicatorKey, string> = {
  MA20: "#0f8a7b",
  MA60: "#c25b3a",
  MACD: "#7257a5",
  RSI: "#2677a8",
  KDJ: "#b47a20",
};

function finiteValues(values: Array<number | null>) {
  return values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
}

function movingAverage(values: number[], period: number) {
  return values.map((_, index) => {
    if (index < period - 1) return null;
    const window = values.slice(index - period + 1, index + 1);
    return window.reduce((sum, value) => sum + value, 0) / period;
  });
}

function exponentialAverage(values: number[], period: number) {
  const result: Array<number | null> = [];
  const multiplier = 2 / (period + 1);
  let previous: number | null = null;
  values.forEach((value, index) => {
    previous = previous === null || index === 0 ? value : (value - previous) * multiplier + previous;
    result.push(previous);
  });
  return result;
}

function calculateIndicators(data: ChartPoint[]): Record<IndicatorKey, IndicatorSeries> {
  const closes = data.map((point) => point.close ?? 0);
  const highs = data.map((point) => point.high ?? point.close ?? 0);
  const lows = data.map((point) => point.low ?? point.close ?? 0);
  const ma20 = movingAverage(closes, 20);
  const ma60 = movingAverage(closes, 60);
  const fast = exponentialAverage(closes, 12);
  const slow = exponentialAverage(closes, 26);
  const macd = fast.map((value, index) => (value ?? 0) - (slow[index] ?? 0));
  const signal = exponentialAverage(macd, 9);
  let averageGain = 0, averageChange = 0;
  const rsi = closes.map((close, index) => {
    if (index === 0) return null;
    const change = close - closes[index - 1];
    averageGain = index === 1 ? Math.max(change, 0) : (13 * averageGain + Math.max(change, 0)) / 14;
    averageChange = index === 1 ? Math.abs(change) : (13 * averageChange + Math.abs(change)) / 14;
    return averageChange === 0 ? 50 : (averageGain / averageChange) * 100;
  });
  const k: Array<number | null> = [];
  const d: Array<number | null> = [];
  const j: Array<number | null> = [];
  let previousK = 50;
  let previousD = 50;
  closes.forEach((_, index) => {
    if (index < 8) {
      k.push(null);
      d.push(null);
      j.push(null);
      return;
    }
    const high = Math.max(...highs.slice(index - 8, index + 1));
    const low = Math.min(...lows.slice(index - 8, index + 1));
    const rsv = high === low ? 50 : ((closes[index] - low) / (high - low)) * 100;
    previousK = index === 8 ? rsv : (2 * previousK + rsv) / 3;
    previousD = index === 8 ? previousK : (2 * previousD + previousK) / 3;
    k.push(previousK);
    d.push(previousD);
    j.push(3 * previousK - 2 * previousD);
  });
  return {
    MA20: { values: ma20 },
    MA60: { values: ma60 },
    MACD: { values: macd, signal, histogram: macd.map((value, index) => 2 * (value - (signal[index] ?? 0))) },
    RSI: { values: rsi },
    KDJ: { values: k, signal: d, histogram: j },
  } satisfies Record<IndicatorKey, IndicatorSeries>;
}

function pathFor(values: Array<number | null>) {
  const points = values
    .map((value, index) => ({ value, index }))
    .filter((point): point is { value: number; index: number } => typeof point.value === "number" && Number.isFinite(point.value));
  if (points.length < 2) return "";
  const numbers = points.map((point) => point.value);
  const min = Math.min(...numbers);
  const max = Math.max(...numbers);
  const range = max - min || 1;
  const denominator = Math.max(values.length - 1, 1);
  return points
    .map((point) => `${(point.index / denominator) * 100},${96 - ((point.value - min) / range) * 82}`)
    .join(" ");
}

function latestValue(values: Array<number | null>) {
  const valuesOnly = finiteValues(values);
  return valuesOnly.at(-1);
}

function formatValue(value: number | undefined) {
  return value === undefined ? "—" : value.toFixed(2);
}

function IndicatorPane({ indicator, series, sourceIndicators }: { indicator: IndicatorKey; series: IndicatorSeries; sourceIndicators?: ResearchChartProps["sourceIndicators"] }) {
  const { t } = useLanguage();
  const latest = sourceIndicators?.[indicator === "KDJ" ? "K" : indicator] ?? latestValue(indicator === "MACD" ? series.histogram ?? [] : series.values);
  const secondary = latestValue(series.signal ?? []);
  const tertiary = latestValue(series.histogram ?? []);
  return (
    <div className="research-indicator-pane">
      <div className="research-indicator-head">
        <span style={{ color: INDICATOR_COLORS[indicator] }}>{INDICATOR_LABELS[indicator]}</span>
        <div>
          <strong>{formatValue(latest)}</strong>
          {indicator === "MACD" ? <small>DIF {formatValue(sourceIndicators?.DIF ?? latestValue(series.values))} · DEA {formatValue(sourceIndicators?.DEA ?? secondary)}</small> : secondary !== undefined ? <small>{t("信号")} {formatValue(secondary)}</small> : null}
          {indicator === "KDJ" && tertiary !== undefined ? <small>J {formatValue(tertiary)}</small> : null}
        </div>
      </div>
      <svg className="research-indicator-spark" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        {series.histogram?.map((value, index) => {
          if (value === null) return null;
          const normalized = Math.max(4, Math.min(96, 50 - value * 28));
          return <line key={`${indicator}-bar-${index}`} x1={(index / Math.max(series.values.length - 1, 1)) * 100} x2={(index / Math.max(series.values.length - 1, 1)) * 100} y1="50" y2={normalized} />;
        })}
        <polyline points={pathFor(series.values)} style={{ stroke: INDICATOR_COLORS[indicator] }} />
        {series.signal ? <polyline className="secondary" points={pathFor(series.signal)} /> : null}
      </svg>
    </div>
  );
}

export function ResearchChart({ data, symbol = "", height = 420, compact = false, sourceIndicators, fill = false, periodSelection, annotations = [], onAnnotationSelect }: ResearchChartProps) {
  const { t, locale } = useLanguage();
  const [selectedIndicators, setSelectedIndicators] = useState<IndicatorKey[]>(["MA20", "MACD"]);
  const [drawMode, setDrawMode] = useState<DrawMode>(periodSelection ? "select" : "pointer");
  const [drawings, setDrawings] = useState<Array<{ mode: "trend" | "horizontal"; start: Point; end: Point }>>([]);
  const [pendingPoint, setPendingPoint] = useState<Point | null>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const chartApiRef = useRef<IChartApi | null>(null);
  const cleanupViewportRef = useRef<(() => void) | null>(null);
  const selectionDragRef = useRef<{ x: number; index: number } | null>(null);
  const [draft, setDraft] = useState<ChartWindow | null>(null);
  const bars = useMemo(() => orderedChartBars(data), [data]);
  const [viewport, setViewport] = useState({ range: presetChartWindow(bars, null), width: 0, height: 0, origin: 0, barSpacing: 1 });
  const selectedSegment = periodSelection?.selected ?? null;
  // Compute from the full series so older visible periods retain MA warm-up bars.
  const indicators = useMemo(() => calculateIndicators(bars), [bars]);
  const visible = clampChartWindow(viewport.range, bars.length);
  const fromIndex = Math.floor(visible.from), toIndex = Math.ceil(visible.to);
  const activePreset = ([null, 1, 3, 6, 12] as const).find(months => {
    const preset = presetChartWindow(bars, months);
    return Math.abs(preset.from - visible.from) < 1 && Math.abs(preset.to - visible.to) < 1;
  });
  const handleChartReady = useCallback((chart: IChartApi | null) => {
    cleanupViewportRef.current?.(); cleanupViewportRef.current = null;
    chartApiRef.current = chart;
    if (!chart) return;
    const scale = chart.timeScale();
    const update = () => {
      const range = scale.getVisibleLogicalRange();
      const origin = scale.logicalToCoordinate(0 as Logical) ?? 0;
      const barSpacing = (scale.logicalToCoordinate(1 as Logical) ?? origin + 1) - origin;
      if (range) setViewport({ range, width: scale.width(), height: chart.paneSize().height, origin, barSpacing });
    };
    scale.subscribeVisibleLogicalRangeChange(update);
    scale.subscribeSizeChange(update);
    scale.setVisibleLogicalRange(presetChartWindow(bars, null));
    update();
    cleanupViewportRef.current = () => { scale.unsubscribeVisibleLogicalRangeChange(update); scale.unsubscribeSizeChange(update); };
  }, [bars]);
  function changeWindow(range: ChartWindow) { chartApiRef.current?.timeScale().setVisibleLogicalRange(clampChartWindow(range, bars.length)); }
  function indexAt(event: React.PointerEvent<HTMLElement>) {
    const x = event.clientX - event.currentTarget.getBoundingClientRect().left;
    return chartApiRef.current?.timeScale().coordinateToLogical(x) ?? null;
  }
  function startSelection(event: React.PointerEvent<HTMLDivElement>) {
    if (!periodSelection || event.button !== 0) return;
    const index = indexAt(event);
    if (index === null) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    selectionDragRef.current = { x: event.clientX, index };
    setDraft({ from: index, to: index });
  }
  function dragSelection(event: React.PointerEvent<HTMLDivElement>) {
    const saved = selectionDragRef.current, index = indexAt(event);
    if (saved && index !== null) setDraft({ from: Math.min(saved.index, index), to: Math.max(saved.index, index) });
  }
  function finishSelection(event: React.PointerEvent<HTMLDivElement>) {
    const saved = selectionDragRef.current, index = indexAt(event);
    if (saved && index !== null) periodSelection?.onSelect(chartSegment(bars, saved.index, index, locale, Math.abs(saved.x - event.clientX) < 6));
    selectionDragRef.current = null; setDraft(null);
  }
  function bandFor(range: ChartWindow | null) {
    if (!range || !viewport.width) return null;
    const a = viewport.origin + range.from * viewport.barSpacing, b = viewport.origin + range.to * viewport.barSpacing;
    const left = Math.max(0, Math.min(a, b) - 3), right = Math.min(viewport.width, Math.max(a, b) + 3);
    return right > left ? { left, width: right - left, height: viewport.height } : null;
  }
  const selectionBand = bandFor(draft ?? (selectedSegment ? { from: bars.findIndex(point => point.date === selectedSegment.startDate), to: bars.findIndex(point => point.date === selectedSegment.endDate) } : null));

  function toggleIndicator(indicator: IndicatorKey) {
    setSelectedIndicators((current) => current.includes(indicator) ? current.filter((item) => item !== indicator) : [...current, indicator]);
  }

  function handleDraw(event: React.PointerEvent<SVGSVGElement>) {
    if (drawMode === "pointer" || drawMode === "select" || !stageRef.current) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const point = {
      x: Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)),
      y: Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height)),
    };
    if (drawMode === "horizontal") {
      setDrawings((current) => [...current, { mode: "horizontal", start: { x: 0, y: point.y }, end: { x: 1, y: point.y } }]);
      return;
    }
    if (pendingPoint) {
      setDrawings((current) => [...current, { mode: "trend", start: pendingPoint, end: point }]);
      setPendingPoint(null);
    } else {
      setPendingPoint(point);
    }
  }

  return (
    <div className={`research-chart ${compact ? "research-chart--compact" : ""} ${fill ? "research-chart--fill" : ""}`}>
      {!compact ? (
        <div className="research-chart-toolbar">
          <div className="research-chart-tool-group">
            <span className="research-chart-toolbar-label">{t("指标")}</span>
            {(Object.keys(INDICATOR_LABELS) as IndicatorKey[]).map((indicator) => (
              <button type="button" key={indicator} className={`research-chart-tool ${selectedIndicators.includes(indicator) ? "active" : ""}`} onClick={() => toggleIndicator(indicator)}>
                {INDICATOR_LABELS[indicator]}
              </button>
            ))}
          </div>
          <div className="research-chart-tool-group">
            <span className="research-chart-toolbar-label">{t("画线")}</span>
            {(periodSelection ? ["select", "pointer", "trend", "horizontal"] as DrawMode[] : ["pointer", "trend", "horizontal"] as DrawMode[]).map((mode) => (
              <button type="button" key={mode} className={`research-chart-tool ${drawMode === mode ? "active" : ""}`} aria-pressed={drawMode === mode} onClick={() => { setDrawMode(mode); setPendingPoint(null); }}>
                {mode === "select" ? (locale === "en" ? "Select period" : "选择区间") : mode === "pointer" ? (locale === "en" ? "Pan" : "平移") : mode === "trend" ? t("趋势线") : t("水平线")}
              </button>
            ))}
            <button type="button" className="research-chart-tool muted" onClick={() => { setDrawings([]); setPendingPoint(null); }}>{t("清除")}</button>
          </div>
        </div>
      ) : null}
      <div className={`research-chart-stage ${drawMode !== "pointer" && !compact ? "drawing" : ""}`} ref={stageRef} style={fill ? undefined : { height }}>
        <CandlestickChart data={bars} height={height} symbol={symbol} compact={compact} fill={fill} onReady={handleChartReady} />
        {selectionBand ? <div className="research-chart-selection-band" style={selectionBand} /> : null}
        {periodSelection && drawMode === "select" ? <div className="research-chart-select-surface" tabIndex={0} role="group" aria-label={locale === "en" ? "Select a chart period. Click a month or drag across dates. Press Enter to select the visible period." : "选择图表区间。点击选择月份，拖动选择时间段，按回车选择可见区间。"} style={{ width: viewport.width, height: viewport.height }} onPointerDown={startSelection} onPointerMove={dragSelection} onPointerUp={finishSelection} onPointerCancel={() => { selectionDragRef.current = null; setDraft(null); }} onKeyDown={event => { if (event.key === "Enter") { event.preventDefault(); periodSelection.onSelect(chartSegment(bars, visible.from, visible.to, locale)); } }} /> : null}
        {periodSelection && !selectedSegment && !draft ? <span className="research-chart-select-hint">{locale === "en" ? "Click a month · drag to select a period" : "点击选择月份 · 拖动选择时间段"}</span> : null}
        {selectedSegment && !draft ? <div className="research-chart-selection-actions" role="status"><span>{selectedSegment.startDate} — {selectedSegment.endDate}<small>{selectedSegment.points.length} {locale === "en" ? "trading sessions" : "个交易日"}</small></span><button type="button" className="research-chart-tool active" onClick={() => periodSelection?.onAnnotate(selectedSegment)}>{locale === "en" ? "Annotate" : "标注"}</button><button type="button" className="research-chart-tool" aria-label={locale === "en" ? "Clear selected period" : "清除选区"} onClick={() => periodSelection?.onSelect(null)}>×</button></div> : null}
        {annotations.map(annotation => {
          const from = bars.findIndex(point => point.date >= annotation.startDate), to = bars.findLastIndex(point => point.date <= annotation.endDate);
          const band = from >= 0 && to >= from ? bandFor({ from, to }) : null;
          if (!band) return null;
          return <button key={annotation.id} className="research-chart-note-marker" style={{ left: Math.min(viewport.width - 26, band.left + band.width / 2) }} title={annotation.note} aria-label={`${locale === "en" ? "Open annotation" : "查看标注"}: ${annotation.startDate} — ${annotation.endDate}`} onClick={() => { const segment = chartSegment(bars, from, to, locale); if (segment) onAnnotationSelect?.(annotation, segment); }}>✎</button>;
        })}
        {!compact ? (
          <svg className={`research-chart-draw-layer ${drawMode === "trend" || drawMode === "horizontal" ? "is-active" : ""}`} style={periodSelection ? { width: viewport.width, height: viewport.height } : undefined} viewBox="0 0 100 100" preserveAspectRatio="none" onPointerDown={handleDraw} aria-label={t("图表画线区域")}>
            {drawings.map((drawing, index) => <line key={`drawing-${index}`} x1={drawing.start.x * 100} y1={drawing.start.y * 100} x2={drawing.end.x * 100} y2={drawing.end.y * 100} className={drawing.mode === "horizontal" ? "horizontal" : "trend"} />)}
            {pendingPoint ? <line x1={pendingPoint.x * 100} y1={pendingPoint.y * 100} x2={pendingPoint.x * 100 + 12} y2={pendingPoint.y * 100 - 4} className="pending" /> : null}
          </svg>
        ) : null}
      </div>
      {periodSelection && bars.length ? <div className="research-chart-navigation"><ChartTimeline data={bars} window={visible} onChange={changeWindow} /><div className="research-chart-range-presets" role="group" aria-label={locale === "en" ? "Quick date ranges" : "快捷时间范围"}>{([1, 3, 6, 12, null] as const).map(months => <button type="button" key={months ?? "all"} aria-pressed={activePreset === months} onClick={() => changeWindow(presetChartWindow(bars, months))}>{locale === "en" ? months === null ? "All" : months === 12 ? "1Y" : `${months}M` : months === null ? "全部" : months === 12 ? "1年" : `${months}月`}</button>)}</div></div> : null}
      {!compact && selectedIndicators.length ? (
        <div className="research-indicator-grid">
          {selectedIndicators.map((indicator) => <IndicatorPane indicator={indicator} series={{ values: indicators[indicator].values.slice(fromIndex, toIndex + 1), signal: "signal" in indicators[indicator] ? indicators[indicator].signal?.slice(fromIndex, toIndex + 1) : undefined, histogram: "histogram" in indicators[indicator] ? indicators[indicator].histogram?.slice(fromIndex, toIndex + 1) : undefined }} sourceIndicators={toIndex >= bars.length - 1 ? sourceIndicators : undefined} key={indicator} />)}
        </div>
      ) : null}
      {!compact && drawMode === "trend" && pendingPoint ? <p className="research-chart-hint">{t("已选择起点，再点击一次完成趋势线。")}</p> : null}
    </div>
  );
}
