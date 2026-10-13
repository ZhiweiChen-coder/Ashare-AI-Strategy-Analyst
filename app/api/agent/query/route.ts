import { NextResponse } from "next/server";
import { blockedDeepResearch } from "@/lib/research-availability";

/**
 * Server-side proxy for POST /api/agent/query.
 * - Browser calls same-origin Next → no CORS / no "Failed to fetch" to 127.0.0.1:8000.
 * - Next does one long fetch to FastAPI with explicit timeout (avoids dev rewrite ECONNRESET).
 */
const BACKEND =
  process.env.BACKEND_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

// Public beta is Quick-only; local Next.js does not enforce this platform limit.
export const maxDuration = 300;

function agentTimeoutFor(body: string) {
  try {
    return JSON.parse(body)?.research_mode === "deep" ? 560_000 : 190_000;
  } catch {
    return 190_000;
  }
}

export async function POST(request: Request) {
  const backendUrl = `${BACKEND.replace(/\/$/, "")}/api/agent/query`;
  let body: string;
  try {
    body = await request.text();
  } catch {
    return NextResponse.json(
      { intent: "error", summary: "Invalid request body.", actions: [], citations: [], payload: {} },
      { status: 400 },
    );
  }

  const blocked = blockedDeepResearch(body, process.env);
  if (blocked) return NextResponse.json(blocked, { status: 503 });

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), agentTimeoutFor(body));
  const headers = new Headers(request.headers);
  headers.set("Content-Type", "application/json");
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
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    const isAbort = e instanceof Error && e.name === "AbortError";
    return NextResponse.json(
      {
        intent: "error",
        summary: isAbort
          ? "The research connection timed out. The report may be incomplete; check available sources before starting another request."
          : `Proxy error: ${msg}. Check BACKEND_BASE_URL and that uvicorn is running.`,
        actions: [
          "Run ./scripts/run_api.sh and retry.",
          "If the API is already running, ask a lighter question or open the stock page for full analysis.",
        ],
        citations: [],
        payload: {},
      },
      { status: 200 },
    );
  } finally {
    clearTimeout(timeoutId);
  }
}
