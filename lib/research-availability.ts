export type ResearchMode = "quick" | "deep";
type RuntimeEnvironment = Readonly<Record<string, string | undefined>>;

export function isPublicBetaRuntime(environment: RuntimeEnvironment): boolean {
  return environment.VERCEL === "1" || environment.OPENASHARE_PUBLIC_BETA === "true";
}

export function effectiveResearchMode(mode: ResearchMode, deepAvailable: boolean): ResearchMode {
  return mode === "deep" && deepAvailable ? "deep" : "quick";
}

export function deepResearchUnavailableMessage(language: string): string {
  return language === "zh-CN"
    ? "深入研究暂时不可用，请使用快速研究。"
    : "Deep research is unavailable at the moment. Please use Quick research.";
}

export function blockedDeepResearch(body: string, environment: RuntimeEnvironment): { code: string; detail: string } | null {
  if (!isPublicBetaRuntime(environment)) return null;
  try {
    const payload = JSON.parse(body);
    return payload?.research_mode === "deep"
      ? { code: "deep_research_unavailable", detail: deepResearchUnavailableMessage(payload.language) }
      : null;
  } catch {
    // Malformed requests remain subject to normal backend validation.
    return null;
  }
}
