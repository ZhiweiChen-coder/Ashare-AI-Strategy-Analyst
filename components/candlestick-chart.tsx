"use client";

import { useEffect, useRef } from "react";
import { createChart, CandlestickSeries, LineSeries, type IChartApi } from "lightweight-charts";

export type ChartPoint = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume?: number | null;
};

type CandlestickChartProps = {
  data: ChartPoint[];
  height?: number;
  symbol?: string;
  compact?: boolean;
  surface?: boolean;
  chartType?: "candles" | "line";
  fill?: boolean;
  onReady?: (chart: IChartApi | null) => void;
};

function toChartTime(dateStr: string): string {
  const d = dateStr.slice(0, 10);
  return d; // YYYY-MM-DD
}

export function CandlestickChart({ data, height = 400, symbol = "", compact = false, surface = false, chartType = "candles", fill = false, onReady }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);


  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    // 跟随全局行情方向色（受 <html data-market-color> 切换），
    // 回退到当前国际惯例色值，保证读取失败时表现不变。
    const rootStyle = getComputedStyle(document.documentElement);
    const upColor = rootStyle.getPropertyValue("--color-up").trim() || "#0d9488";
    const downColor = rootStyle.getPropertyValue("--color-down").trim() || "#c25b3a";

    const chart = createChart(containerRef.current, {
      layout: { background: { color: surface ? "#f2efe8" : "#ffffff" }, textColor: surface ? "#807c74" : "#0d0d0d", fontSize: surface ? 10 : 12 },
      grid: {
        vertLines: { color: compact ? "rgba(0,0,0,0.025)" : "rgba(0,0,0,0.06)" },
        horzLines: { color: compact ? "rgba(0,0,0,0.035)" : "rgba(0,0,0,0.06)" },
      },
      width: containerRef.current.clientWidth,
      height: fill ? containerRef.current.clientHeight || height : height,
      timeScale: {
        borderColor: compact ? "transparent" : "rgba(0,0,0,0.08)",
        timeVisible: false,
        secondsVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
        // A large offset leaves most of a short series empty on full-size charts.
        rightOffset: surface ? 1 : compact ? 8 : 2,
        barSpacing: 8,
        minBarSpacing: .1,
      },
      rightPriceScale: { borderColor: compact ? "transparent" : "rgba(0,0,0,0.08)", visible: !compact },
      handleScroll: {
        mouseWheel: false,
        pressedMouseMove: true,
      },
      handleScale: {
        axisPressedMouseMove: {
          time: true,
          price: true,
        },
        mouseWheel: false,
        pinch: true,
      },
    });

    const validData = data.filter(p => p.open != null && p.high != null && p.low != null && p.close != null);
    if (chartType === "line") {
      const series = chart.addSeries(LineSeries, { color: upColor, lineWidth: 2 });
      series.setData(validData.map(p => ({ time: toChartTime(p.date), value: p.close! })));
    } else {
      const series = chart.addSeries(CandlestickSeries, { upColor, downColor, borderVisible: false, wickUpColor: upColor, wickDownColor: downColor });
      series.setData(validData.map(p => ({ time: toChartTime(p.date), open: p.open!, high: p.high!, low: p.low!, close: p.close! })));
    }

    chart.timeScale().fitContent();

    chartRef.current = chart;
    onReady?.(chart);

    const onResize = () => {
      if (containerRef.current && chartRef.current) chartRef.current.applyOptions({ width: containerRef.current.clientWidth, ...(fill ? { height: containerRef.current.clientHeight } : {}) });
    };
    const observer = new ResizeObserver(onResize);
    observer.observe(containerRef.current);
    window.addEventListener("resize", onResize);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", onResize);
      onReady?.(null);
      chart.remove();
      chartRef.current = null;
    };
  }, [compact, data, height, surface, chartType, fill, onReady]);

  return (
    <div className={`candlestick-wrap${fill ? " candlestick-wrap--fill" : ""}`} style={{ width: "100%", ...(fill ? { height: "100%", minHeight: 0 } : { minHeight: height }) }}>
      {symbol ? <div className="chart-symbol">{symbol}</div> : null}
      <div ref={containerRef} style={fill ? { height: "100%" } : undefined} />
    </div>
  );
}
