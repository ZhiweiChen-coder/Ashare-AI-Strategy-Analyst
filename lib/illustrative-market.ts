/** Fixed brand artwork. These values are not security prices or market data. */
export type IllustrativeCandle = { u: number; open: number; close: number; high: number; low: number };

const trend = [
  -.98, -.85, -.88, -.60, -.37, -.45, -.04, .34, .19, .52, .76, 1.02,
];

export function illustrativeSpine(u: number) {
  const position = Math.max(0, Math.min(1, u)) * (trend.length - 1);
  const i = Math.min(trend.length - 2, Math.floor(position));
  const t = position - i;
  const p0 = trend[Math.max(0, i - 1)], p1 = trend[i], p2 = trend[i + 1], p3 = trend[Math.min(trend.length - 1, i + 2)];
  return .5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t);
}

function createStudy(count: number): IllustrativeCandle[] {
  let seed = 41729;
  const random = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  let previous = illustrativeSpine(0) - .035;
  return Array.from({ length: count }, (_, i) => {
    const u = i / (count - 1);
    const open = previous + (random() - .5) * .028;
    const close = illustrativeSpine(u) + (random() - .5) * .075;
    previous = close;
    return { u, open, close, high: Math.max(open, close) + .035 + random() * .065, low: Math.min(open, close) - .035 - random() * .065 };
  });
}

export const illustrativeStudies = { desktop: createStudy(121), mobile: createStudy(43) };
export const studyX = (u: number) => 36 + u * 1228;
export const studyY = (y: number) => 150 - y * (300 / 3.4);

/** A single shallow fold keeps the ribbon continuous at every point. */
export const ribbonHalfWidth = (u: number) => .026 + .105 * Math.sin(Math.PI * u) ** .8;
export const ribbonFold = (u: number) => -.5 + u * 1.15;
