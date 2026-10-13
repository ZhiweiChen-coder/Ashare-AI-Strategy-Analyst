/** Fixed brand artwork. These values are not security prices or market data. */
export type IllustrativeCandle = { u: number; open: number; close: number; high: number; low: number };

const trend = [
  -.94, -.86, -.91, -.80, -.84, -.78, -.82, -.72, -.75, -.62, -.57, -.62,
  -.43, -.34, -.40, -.20, -.12, -.19, -.03, .08, .04, .22, .38, .46,
  .38, .24, .31, .23, .43, .58, .66, .61, .75, .92, .87, 1.04,
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
