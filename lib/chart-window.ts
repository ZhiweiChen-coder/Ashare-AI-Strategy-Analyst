export type ChartBar = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume?: number | null;
};
export type ChartWindow = { from: number; to: number };
export type ChartSegment = { key: string; label: string; startDate: string; endDate: string; points: ChartBar[] };

// The navigator and selection must use the same ordered bars as the renderer.
export function orderedChartBars(data: ChartBar[]) {
  const dates = new Map<string, ChartBar>();
  for (const point of data) {
    const date = point.date.slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(date)) || new Date(date).toISOString().slice(0, 10) !== date) continue;
    if (![point.open, point.high, point.low, point.close].every(value => typeof value === "number" && Number.isFinite(value))) continue;
    dates.set(date, { ...point, date });
  }
  return [...dates.values()].sort((a, b) => a.date.localeCompare(b.date));
}

export function clampChartWindow(range: ChartWindow, count: number): ChartWindow {
  if (count < 2) return { from: 0, to: 1 };
  const max = count - 1;
  const minSpan = Math.min(4, max);
  const from = Math.max(0, Math.min(max - minSpan, range.from));
  return { from, to: Math.max(from + minSpan, Math.min(max, range.to)) };
}

export function moveChartWindow(range: ChartWindow, delta: number, count: number): ChartWindow {
  const span = range.to - range.from;
  const from = Math.max(0, Math.min(Math.max(0, count - 1 - span), range.from + delta));
  return clampChartWindow({ from, to: from + span }, count);
}

export function presetChartWindow(data: ChartBar[], months: number | null): ChartWindow {
  if (months === null || !data.length) return clampChartWindow({ from: 0, to: data.length - 1 }, data.length);
  const [year, month] = data.at(-1)!.date.split("-").map(Number);
  const cutoff = new Date(Date.UTC(year, month - months, 1)).toISOString().slice(0, 10);
  const from = Math.max(0, data.findIndex(point => point.date >= cutoff));
  return clampChartWindow({ from, to: data.length - 1 }, data.length);
}

export function chartSegment(data: ChartBar[], firstIndex: number, lastIndex: number, locale: "en" | "zh", wholeMonth = false): ChartSegment | null {
  if (!data.length) return null;
  const clamp = (value: number) => Math.max(0, Math.min(data.length - 1, Math.round(value)));
  let from = clamp(Math.min(firstIndex, lastIndex)), to = clamp(Math.max(firstIndex, lastIndex));
  if (wholeMonth) {
    const month = data[from].date.slice(0, 7);
    from = data.findIndex(point => point.date.startsWith(month));
    to = data.findLastIndex(point => point.date.startsWith(month));
  }
  const points = data.slice(from, to + 1);
  const startDate = points[0].date, endDate = points.at(-1)!.date;
  const format = (date: string) => new Date(`${date}T00:00:00Z`).toLocaleDateString(locale === "en" ? "en-US" : "zh-CN", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
  return { key: `${startDate}:${endDate}`, label: startDate === endDate ? format(startDate) : `${format(startDate)} — ${format(endDate)}`, startDate, endDate, points };
}

export function sampleChartBars(data: ChartBar[], max = 80): ChartBar[] {
  const limit = Math.max(4, max);
  if (data.length <= limit) return data;
  let high = 0, low = 0;
  data.forEach((point, index) => { if (point.high! > data[high].high!) high = index; if (point.low! < data[low].low!) low = index; });
  const indices = new Set([0, data.length - 1, high, low]);
  for (let i = 1; i <= limit - 4; i++) indices.add(Math.round(i / (limit - 3) * (data.length - 1)));
  return [...indices].sort((a, b) => a - b).map(index => data[index]);
}
