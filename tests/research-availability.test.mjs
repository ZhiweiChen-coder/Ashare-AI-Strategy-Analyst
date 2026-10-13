import assert from "node:assert/strict";
import test from "node:test";
import { blockedDeepResearch, effectiveResearchMode, isPublicBetaRuntime } from "../lib/research-availability.ts";

test("public deployments block Deep while local production keeps it available", () => {
  const body = JSON.stringify({ query: "Research NVIDIA", research_mode: "deep", language: "en-US" });
  for (const environment of [{ VERCEL: "1" }, { OPENASHARE_PUBLIC_BETA: "true" }]) {
    assert.equal(isPublicBetaRuntime(environment), true);
    assert.equal(blockedDeepResearch(body, environment)?.code, "deep_research_unavailable");
    assert.match(blockedDeepResearch(body, environment)?.detail, /unavailable at the moment/);
  }
  assert.equal(blockedDeepResearch(body, { NODE_ENV: "production" }), null);
});

test("Quick and default-mode requests still reach normal validation", () => {
  for (const body of [{ query: "Hello" }, { query: "Hello", research_mode: "quick" }]) {
    assert.equal(blockedDeepResearch(JSON.stringify(body), { VERCEL: "1" }), null);
  }
  assert.equal(blockedDeepResearch("not JSON", { VERCEL: "1" }), null);
});

test("Chinese clients receive an understandable unavailable response", () => {
  const blocked = blockedDeepResearch(JSON.stringify({ research_mode: "deep", language: "zh-CN" }), { VERCEL: "1" });
  assert.match(blocked.detail, /暂时不可用/);
});

test("a remembered Deep preference cannot select a suspended mode", () => {
  assert.equal(effectiveResearchMode("deep", false), "quick");
  assert.equal(effectiveResearchMode("deep", true), "deep");
  assert.equal(effectiveResearchMode("quick", true), "quick");
});
