import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const source = await readFile(new URL('../components/research-trace.tsx', import.meta.url), 'utf8');
let compiled = ts.transpileModule(source, { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext } }).outputText;
compiled = compiled.replace(/from "([^"]+)"/g, (_, name) => {
  let url;
  if (name === '@/components/language-provider') url = 'data:text/javascript,' + encodeURIComponent('export const useLanguage = () => ({locale: "en"});');
  else if (name === '@/lib/research-export') url = 'data:text/javascript,' + encodeURIComponent('export function researchExport() { throw new Error("Export is outside this display test"); }');
  else if (name === '@/lib/research-activity') url = new URL('../lib/research-activity.ts', import.meta.url).href;
  else url = import.meta.resolve(name);
  return `from ${JSON.stringify(url)}`;
});
export const { ResearchTools, ResponseTools } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
export const fixtureSteps = [
  { tool: 'search_stocks', status: 'completed' },
  { tool: 'get_sec_company_data', status: 'completed' },
  { tool: 'get_stock_news', status: 'completed' },
];

test('checking is a collapsed, accessible progress control with tool details', () => {
  const html = renderToStaticMarkup(React.createElement(ResearchTools, { steps: fixtureSteps, phase: 'Checking facts and sources' }));
  assert.match(html, /<details class="research-tool-activity">/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /Checking facts and sources/);
  assert.match(html, /Retrieve SEC filings and facts/);
  assert.doesNotMatch(html, /<details[^>]*\bopen\b|Writing|checked before saving/);
});
test('progress remains visible before the first tool without presenting an answer', () => {
  const html = renderToStaticMarkup(React.createElement(ResearchTools, { steps: [], phase: 'Preparing research' }));
  assert.match(html, /Preparing research/);
  assert.doesNotMatch(html, /markdown-body|research-streaming-answer/);
});
test('completed tool history has the same disclosure layout and no busy indicator', () => {
  const html = renderToStaticMarkup(React.createElement(ResponseTools, { response: { research_steps: fixtureSteps } }));
  assert.match(html, /Tools used/);
  assert.match(html, /<details class="research-tool-activity">/);
  assert.doesNotMatch(html, /research-stream-dot|Checking facts|aria-live/);
});
test('saved work duration stays with the collapsed tool history', () => {
  const response = JSON.parse(JSON.stringify({ research_steps: fixtureSteps, payload: { _meta: { latency_seconds: 78.2 } } }));
  const html = renderToStaticMarkup(React.createElement(ResponseTools, { response }));
  assert.match(html, /Worked for 1m 18s/);
  assert.match(html, /3 tools/);
  assert.doesNotMatch(html, /<details[^>]*\bopen\b|research-stream-dot/);
});
test('very fast replies show an honest duration without an empty tool disclosure', () => {
  const html = renderToStaticMarkup(React.createElement(ResponseTools, { response: { payload: { _meta: { latency_seconds: 0.15 } } } }));
  assert.match(html, /Worked for &lt;1s/);
  assert.doesNotMatch(html, /<details/);
});
