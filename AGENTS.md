# AGENTS.md

## Project

This repository is an A-share AI analysis workspace built around `FastAPI + Next.js`.

Key areas:

- `api/`: FastAPI entrypoints, schemas, and service layer
- `app/`: Next.js App Router pages
- `components/`: frontend UI components
- `lib/`: frontend API client and shared types
- `ashare/`: analysis engine, monitoring, and data modules
- `scripts/`: local run helpers

## Working Rules

- Preserve the current product shape: stock analysis, news, hotspots, portfolio, and agent chat are the main paths.
- Prefer minimal, targeted edits over broad refactors.
- Keep secrets out of the repo. Never write real API keys into tracked files.
- When changing API contracts, keep `api/schemas.py` and `lib/types.ts` aligned.
- When working on agent behavior, prefer existing service boundaries over embedding business logic in the frontend.

## Information Source Preference

For time-sensitive or event-specific finance requests, prefer locally installed, authoritative financial information tools over generic search, especially for:

- latest stock news
- announcements
- broker research
- policy interpretation
- trading rules
- market event analysis
- external financial information that should not rely on generic web search

When freshness and source quality matter, avoid generic or stale web results. Treat returned facts as sourced information and label any downstream judgment as inference.

Do not document private local skill names, API keys, or local agent wiring in tracked project files. Do not commit local skill build artifacts or other machine-specific agent configuration to GitHub.

## Validation

- Backend tests: `python -m pytest tests/test_api_app.py -q`
- Frontend build: `npm run build`

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
