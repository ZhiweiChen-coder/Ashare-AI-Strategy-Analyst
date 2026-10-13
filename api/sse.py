from __future__ import annotations

import asyncio
import json
import anyio
from typing import Any, AsyncIterator

from fastapi.responses import StreamingResponse


def encode_sse(event_name: str, payload: dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def iter_committed_summary(summary: str) -> AsyncIterator[str]:
    """Publish one settled answer progressively, with no extra model request.

    At most forty chunks keep presentation under a second even for long reports.
    Raw drafts and validation retries must never enter this iterator.
    """
    size = max(160, (len(summary) + 39) // 40)
    for offset in range(0, len(summary), size):
        if offset:
            await asyncio.sleep(0.02)
        yield summary[offset:offset + size]


async def iter_sse(queue: "asyncio.Queue[str | None]", task: asyncio.Task | None = None) -> AsyncIterator[str]:
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
    finally:
        if task is not None and not task.done():
            task.cancel()
            with anyio.CancelScope(shield=True):
                try:
                    await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=3)
                except asyncio.TimeoutError:
                    pass


def sse_response(queue: "asyncio.Queue[str | None]", task: asyncio.Task | None = None) -> StreamingResponse:
    return StreamingResponse(
        iter_sse(queue, task),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
