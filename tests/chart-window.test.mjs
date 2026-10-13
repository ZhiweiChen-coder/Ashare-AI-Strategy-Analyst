import assert from "node:assert/strict";
import test from "node:test";
import { chartSegment, clampChartWindow, moveChartWindow, orderedChartBars, presetChartWindow, sampleChartBars } from "../lib/chart-window.ts";

const bar = (date, close = 10) => ({ date, open: close, high: close + 1, low: close - 1, close, volume: 100 });
const data = ["2026-07-31", "2026-08-03", "2026-08-04", "2026-08-31", "2026-09-01", "2026-09-30", "2026-10-01"].map(date => bar(date));

test("selection across months retains exact trading dates and evidence bars", () => {
  const result = chartSegment(data, 1, 5, "en");
  assert.equal(result.startDate, "2026-08-03"); assert.equal(result.endDate, "2026-09-30");
  assert.deepEqual(result.points, data.slice(1, 6));
});
test("right-to-left selection has the same chronological evidence", () => {
  assert.deepEqual(chartSegment(data, 5, 1, "en"), chartSegment(data, 1, 5, "en"));
});
test("a click selects the calendar month without inventing weekend bars", () => {
  const result = chartSegment(data, 2, 2, "zh", true);
  assert.equal(result.startDate, "2026-08-03"); assert.equal(result.endDate, "2026-08-31"); assert.equal(result.points.length, 3);
});
test("out-of-chart endpoints are bounded by actual data", () => {
  assert.deepEqual(chartSegment(data, -99, 999, "en").points, data);
  assert.equal(chartSegment([], 0, 1, "en"), null);
});
test("renderer index normalization drops missing, invalid and duplicate bars", () => {
  const result = orderedChartBars([bar("2026-08-04"), bar("2026-08-03"), bar("2026-08-04", 20), bar("2026-02-30"), bar("invalid"), bar("2026-08-05", NaN), { ...bar("2026-08-06"), open: null }]);
  assert.deepEqual(result.map(item => item.date), ["2026-08-03", "2026-08-04"]); assert.equal(result[1].close, 20);
});
test("navigator preserves span at either data boundary", () => {
  assert.deepEqual(moveChartWindow({ from: 20, to: 40 }, -100, 100), { from: 0, to: 20 });
  assert.deepEqual(moveChartWindow({ from: 20, to: 40 }, 100, 100), { from: 79, to: 99 });
});
test("crossing timeline handles retains a valid minimum window", () => {
  assert.deepEqual(clampChartWindow({ from: 50, to: 10 }, 100), { from: 50, to: 54 });
  assert.ok(clampChartWindow({ from: 999, to: 999 }, 100).to <= 99);
});
test("date presets anchor to the data date, not the current clock", () => {
  assert.deepEqual(presetChartWindow(data, 1), { from: 2, to: 6 });
  assert.deepEqual(presetChartWindow(data, null), { from: 0, to: 6 });
});
test("large research selections bound model context and retain endpoints and extremes", () => {
  const large = Array.from({ length: 1200 }, (_, index) => ({ ...bar(String(index)), high: index === 571 ? 1000 : 11, low: index === 817 ? -5 : 9 }));
  const result = sampleChartBars(large);
  assert.ok(result.length <= 80); assert.equal(result[0], large[0]); assert.equal(result.at(-1), large.at(-1));
  assert.ok(result.includes(large[571])); assert.ok(result.includes(large[817]));
  assert.equal(sampleChartBars(data), data);
});
