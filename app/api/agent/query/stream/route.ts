import { NextResponse } from "next/server";
import { blockedDeepResearch } from "@/lib/research-availability";

const BACKEND =
  process.env.BACKEND_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

// Public beta is Quick-only; local Deep still uses its existing backend deadline.
export const maxDuration = 300;

function agentTimeoutFor(body: string) {
  try {
    return JSON.parse(body)?.research_mode === "deep" ? 560_000 : 190_000;
  } catch {
    return 190_000;
  }
}

export async function POST(request: Request) {
  const backendUrl = `${BACKEND.replace(/\/$/, "")}/api/agent/query/stream`;
  const body = await request.text();
  const blocked = blockedDeepResearch(body, process.env);
  if (blocked) return NextResponse.json(blocked, { status: 503 });
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), agentTimeoutFor(body));
  const abort = () => controller.abort();
  if (request.signal.aborted) abort();
  else request.signal.addEventListener("abort", abort, { once: true });
  const cleanup = () => {
    clearTimeout(timeoutId);
    request.signal.removeEventListener("abort", abort);
  };
  const headers = new Headers(request.headers);
  headers.set("Content-Type", "application/json");
  headers.set("Accept", "text/event-stream");
  headers.delete("host");
  headers.delete("content-length");

  try {
    const res = await fetch(backendUrl, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok || !res.body) {
      const text = await res.text();
      cleanup();
      return NextResponse.json({ detail: text || "Agent stream unavailable" }, { status: res.status || 502 });
    }
    const reader = res.body.getReader();
    const stream = new ReadableStream<Uint8Array>({
      async pull(target) {
        try {
          const { done, value } = await reader.read();
          if (done) { cleanup(); target.close(); }
          else target.enqueue(value);
        } catch (error) { cleanup(); target.error(error); }
      },
      async cancel() {
        abort();
        cleanup();
        await reader.cancel().catch(() => undefined);
      },
    });
    return new Response(stream, {
      status: res.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    cleanup();
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ detail: `Agent stream failed: ${message}` }, { status: 502 });
  }
}
