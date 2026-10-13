import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const source = await readFile(new URL('../components/research-markdown.tsx', import.meta.url), 'utf8');
let compiled = ts.transpileModule(source, { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext } }).outputText;
compiled = compiled.replace(/from "([^"]+)"/g, (_, name) => `from ${JSON.stringify(import.meta.resolve(name))}`);
const { ResearchMarkdown } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const render = content => renderToStaticMarkup(React.createElement(ResearchMarkdown, { content }));

test('years, numbered prose and dashes stay inside the paragraph', () => {
  const html = render('The filing was dated 2026. Revenue remains uncertain - source coverage is partial.');
  assert.match(html, /dated 2026\. Revenue/);
  assert.doesNotMatch(html, /<ol|<ul/);
});
test('headings, nested lists, GFM tables and inline formatting render normally', () => {
  const html = render('## **Facts**\n\n- Filing\n  - **Dated** source\n\n| Metric | Value |\n| --- | --- |\n| Status | Partial |');
  assert.match(html, /<h2><strong>Facts<\/strong><\/h2>/);
  assert.equal((html.match(/<ul>/g) ?? []).length, 2);
  assert.match(html, /research-summary-table/);
  assert.match(html, /<td>Partial<\/td>/);
});
test('links containing parentheses work and source HTML cannot execute', () => {
  const html = render('[Source](https://example.org/results_(annual))\n\n<script>alert(1)</script>\n\n[bad](javascript:alert)');
  assert.match(html, /href="https:\/\/example.org\/results_\(annual\)"/);
  assert.match(html, /noopener noreferrer/);
  assert.doesNotMatch(html, /<script|href="javascript:/);
});
