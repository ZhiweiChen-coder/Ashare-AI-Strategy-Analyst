import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../lib/api.ts', import.meta.url), 'utf8');
let compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const authStub = 'data:text/javascript,' + encodeURIComponent('export function createClient() { throw new Error("Unexpected auth client in offline stream test"); }');
compiled = compiled.replace(/from "@\/utils\/supabase\/client"/, `from ${JSON.stringify(authStub)}`);
const { streamAgent } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const frame = (event, payload) => `event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`;

for (const intent of ['pydantic_ai_agent', 'error']) {
  test(`only the canonical ${intent === 'error' ? 'partial result' : 'answer'} reaches the displayed stream`, async () => {
    const summary = '## Source-backed facts\n\n核验后保留的版本 [1](https://example.org/filing_(annual)).';
    const final = { intent, summary, actions: [], citations: [], payload: {} };
    const wire = frame('progress', { stage: 'check_facts', message: '正在核对事实与来源', meta: {} })
      + frame('token', { meta: { delta: 'Rejected draft with unsupported facts', provisional: true, reset: true } })
      + frame('token', { meta: { delta: 'Unmarked legacy draft', reset: true } })
      + frame('token', { meta: { delta: summary.slice(0, 30), provisional: false } })
      + frame('token', { meta: { delta: summary.slice(30), provisional: false } })
      + frame('result', { payload: final }) + frame('done', {});
    const bytes = new TextEncoder().encode(wire);
    const previousFetch = globalThis.fetch;
    let calls = 0, visible = '';
    const events = [];
    globalThis.fetch = async () => {
      calls += 1;
      return new Response(new ReadableStream({
        start(controller) {
          // Split SSE frames and UTF-8 characters across transport chunks.
          for (let i = 0; i < bytes.length; i += 7) controller.enqueue(bytes.slice(i, i + 7));
          controller.close();
        },
      }), { status: 200 });
    };
    try {
      const result = await streamAgent('Offline NVIDIA brief fixture', [], undefined, { onEvent(event) {
        events.push(event);
        if (event.type === 'tool_started') {
          assert.equal(event.stage, 'check_facts');
          assert.equal(visible, '');
        }
        if (event.type === 'message_delta') {
          assert.equal(event.provisional, false);
          assert.equal(event.reset, false);
          visible += event.message;
          assert.ok(summary.startsWith(visible), 'Visible text cannot be replaced by a later draft');
        }
      } });
      assert.equal(calls, 1);
      assert.equal(visible, result.summary);
      assert.deepEqual(result, final);
      assert.equal(events.filter(event => event.type === 'message_delta').length, 2);
      assert.doesNotMatch(JSON.stringify(events), /Rejected draft|legacy draft/);
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
}
