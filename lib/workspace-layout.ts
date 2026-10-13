export const panelDefaults = { left: 248, right: 380 };
export const panelLimits = { left: { min: 180, max: 400 }, right: { min: 280, max: 820 } };

export function panelWidth(value: unknown, side: "left" | "right") {
  return typeof value === "number" && Number.isFinite(value) ? Math.max(panelLimits[side].min, Math.min(panelLimits[side].max, value)) : panelDefaults[side];
}

export function fitWorkspacePanels(preferred: { left: number; right: number }, width: number, leftOpen: boolean, rightOpen: boolean) {
  let left = leftOpen ? panelWidth(preferred.left, "left") : 0;
  let right = rightOpen ? panelWidth(preferred.right, "right") : 0;
  const minLeft = leftOpen ? panelLimits.left.min : 0, minRight = rightOpen ? panelLimits.right.min : 0;
  const budget = Math.max(minLeft + minRight, (width || 1280) - 360);
  if (left + right > budget) {
    const extra = Math.max(0, budget - minLeft - minRight);
    const requestedExtra = left + right - minLeft - minRight;
    const fraction = requestedExtra ? extra / requestedExtra : 0;
    left = minLeft + (left - minLeft) * fraction;
    right = minRight + (right - minRight) * fraction;
  }
  return { left: Math.floor(left), right: Math.floor(right) };
}
