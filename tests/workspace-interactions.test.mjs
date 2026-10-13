import assert from "node:assert/strict";
import test from "node:test";
import { researchProgressLabel, researchWorkLabel, toolActivityOutcome, updateToolActivity } from "../lib/research-activity.ts";
import { fitWorkspacePanels, panelWidth } from "../lib/workspace-layout.ts";

test("duplicate stream progress does not create extra tool rows", () => {
  let steps = [];
  for (const status of ["running", "running", "completed", "completed"]) steps = updateToolActivity(steps, { tool: "search_stocks", status });
  assert.equal(steps.length, 1); assert.equal(steps[0].status, "completed");
});
test("empty successful results keep their reason on redundant completion", () => {
  let steps = updateToolActivity([], { tool: "get_stock_news", status: "completed", reasonCode: "no_results" });
  steps = updateToolActivity(steps, { tool: "get_stock_news", status: "completed" });
  assert.equal(toolActivityOutcome(steps[0], "en").label, "No results");
});
test("retry completion clears stale failure and records recovery", () => {
  let steps = updateToolActivity([], { tool: "search_stocks", status: "unavailable", reasonCode: "provider_error" });
  steps = updateToolActivity(steps, { tool: "search_stocks", status: "running" });
  steps = updateToolActivity(steps, { tool: "search_stocks", status: "completed" });
  assert.equal(toolActivityOutcome(steps[0], "en").label, "Done after retry");
  assert.equal(steps[0].reasonCode, undefined);
});
test("saved earlier attempts distinguish later success from continuing failures", () => {
  const failed = { tool: "research_company", status: "unavailable" };
  assert.equal(toolActivityOutcome(failed, "en", true).label, "Retried");
  assert.equal(toolActivityOutcome(failed, "en", false).label, "Unavailable");
  assert.match(toolActivityOutcome(failed, "en", true).detail, /later call/);
});
test("identity prerequisites and unavailable sources are not shown as provider outages", () => {
  assert.equal(toolActivityOutcome({tool:"research_company",status:"unavailable",reasonCode:"identity_required"}, "en").label, "Needs identity");
  assert.equal(toolActivityOutcome({tool:"web_search",status:"unavailable",reasonCode:"provider_error"}, "zh").label, "来源不可用");
});
test("fact checking is a localized progress phase rather than a writing claim", () => {
  assert.equal(researchProgressLabel('check_facts', 'en'), 'Checking facts and sources');
  assert.equal(researchProgressLabel('check_facts', 'zh'), '核对事实与来源');
  assert.equal(researchProgressLabel('publish_answer', 'en'), 'Presenting the answer');
  assert.doesNotMatch(researchProgressLabel('check_facts', 'en'), /checked|Writing/);
});
test("work duration carries seconds into minutes and hides unavailable timings", () => {
  assert.equal(researchWorkLabel(59.7, 'en'), 'Worked for 1m 0s');
  assert.equal(researchWorkLabel(78, 'zh'), '用时 1 分 18 秒');
  for (const value of [undefined, null, '78', NaN, Infinity, -1]) assert.equal(researchWorkLabel(value, 'en'), undefined);
});
test("remembered panel sizes cannot crowd out the conversation", () => {
  for (const width of [901, 1024, 1280, 1710]) {
    const fit = fitWorkspacePanels({left:400,right:820}, width, true, true);
    assert.ok(fit.left >= 180 && fit.right >= 280);
    assert.ok(width - fit.left - fit.right >= 360);
  }
});
test("closed panels release space and single-panel resizing uses available width", () => {
  assert.deepEqual(fitWorkspacePanels({left:248,right:380}, 1280, false, false), {left:0,right:0});
  assert.deepEqual(fitWorkspacePanels({left:248,right:820}, 1280, false, true), {left:0,right:820});
});
test("invalid stored widths fall back to finite bounded values", () => {
  assert.equal(panelWidth(NaN,"left"),248); assert.equal(panelWidth("wide","right"),380);
  assert.equal(panelWidth(-5,"left"),180); assert.equal(panelWidth(Infinity,"right"),380);
});
