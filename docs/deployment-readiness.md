# Coordinated release checklist

The production architecture is Next.js on Vercel, FastAPI on the Oracle VM, and Supabase for hosted authentication and workspace storage. A frontend deployment alone does not release the new research tools. This checklist prepares a release; it does not publish it.

## Build the release revision

Review the full working tree, including new backend modules, frontend components and the six web demo files in `public/marketing/`. Include every required source file in the release revision. Do not include `.env`, `.venv`, `output/`, local databases or raw screen recordings. `.vercelignore` keeps local artifacts out of CLI uploads; `.gitignore` controls Git-based deployments independently. Keep `reports/`: the archived report route reads its HTML at runtime.

Use Node 22 and Python 3.12. Run:

```bash
node --version
python --version
python -m pytest tests/test_api_app.py -q
node --experimental-strip-types --test tests/seo.test.mjs
python -m pytest tests/test_research_availability.py -q
node --experimental-strip-types --test tests/research-availability.test.mjs
npm run build
```

A production build must include the canonical origin `NEXT_PUBLIC_SITE_URL=https://openashare.com`. Omission uses that same default. Keep it pointed at production in preview builds too. Production must not set `SEO_NOINDEX=true`; preview builds automatically opt out of indexing.

## Validate hosted dependencies before release

- Confirm the Vercel project is `open-ashare`, with the intended production domains. The package pins Node 22, overriding a different project default.
- Compare environment **names and destinations** with [the frontend template](../deploy/.env.frontend.example) and [the backend template](../deploy/oracle/.env.backend.example). Set model, news and SEC credentials only in the backend runtime. Never export secrets into release reports.
- Verify the schema effects of all five checked-in Supabase migrations. If they were applied through the SQL editor, the migration-history list can be empty even while tables and RPCs exist. Compare required columns, RLS policies, indexes and functions before deciding that a migration is missing; do not blindly replay migrations just because history is empty.
- Confirm the hosted Supabase project matches both frontend and backend settings and that unauthenticated private API requests are rejected. An HTTP 200 from `/healthz` proves only that the server responds.
- The current public-beta release is **Quick-only**. Vercel agent routes use `maxDuration=300`; the Quick proxy deadline remains 190 seconds and the backend deadline 180 seconds. Verify the project uses a runtime configuration that supports this; 300 seconds is the documented Fluid Compute maximum on Hobby. Do not upgrade a plan automatically.
- Deep support remains unverified and is suspended across the public-beta UI, Next proxy and authenticated Oracle backend. Set `OPENASHARE_PUBLIC_BETA=true` on the Oracle runtime and on any hosted frontend outside Vercel; Vercel is detected automatically. `SUPABASE_REQUIRE_AUTH=true` also identifies the hosted backend and keeps Deep suspended. Users see “Deep research is unavailable at the moment.” Requests for Deep return 503 before credit reservation or model execution. Local development without hosted auth or the public-beta flag retains Deep.
- Re-enabling Deep requires a reviewed release after validating the actual request path. Apex/www browser traffic currently goes directly to Oracle; previews use the Next proxy. Confirm Oracle's current revision, dependencies, Nginx timeouts, CORS, streaming, cancellation and a bounded 540-second workflow. For a proxied Deep path, verify the Vercel plan supports a 600-second function duration and update the route configuration. No unknown runtime support should be treated as confirmed.
- Review the Journal's specific financial, clinical and supply-chain claims against primary sources before publishing those articles as reviewed research. They remain `noindex, follow` and are excluded from the sitemap until that review. Canonicals and language alternatives are already prepared.

## Release the backend first

Back up the backend code revision and persistent `data/` separately. Preserve the runtime `.env`; do not overwrite it with example values. Record the current systemd and Nginx configuration for rollback.

Deploy the reviewed revision using the existing Oracle access workflow. Install `requirements_api.txt` in the Python 3.12 environment, check the quoted identifying SEC User-Agent, keep `SUPABASE_REQUIRE_AUTH=true`, bind Uvicorn to loopback, and use one worker on a small VM. Apply [the Nginx configuration](../deploy/oracle/openashare-nginx.conf) with its 600-second idle timeout, run `nginx -t`, reload Nginx and restart the backend service. The idle timeout is the interval between reads, not a total research budget.

Verify public health, authenticated tools, English and Chinese requests, watchlist persistence, cancellation, and SSE streaming with the current frontend contract. Begin with read-only/data-only requests. Any model smoke test must have an explicit small request and spending allowance; do not run an unbounded research batch as a deployment check.

For this beta, `GET /api/agent/capabilities` is a public metadata endpoint and must return `quick_available=true`, `deep_available=false`. It contains no user or billing data. After sign-in, verify a Deep POST to both query endpoints returns 503 without reserving credits or starting a run. Unauthenticated query requests must still return 401. See the [Oracle upgrade and verification steps](../deploy/oracle/README.md#upgrading-an-existing-vm).

## Stage the exact production frontend build

Link the CLI to the existing Vercel project, using its normal secure authentication flow. Check `vercel --version` and its current command help before executing. Do not create a second project.

Stage a **production-configured deployment without moving public domains**:

```bash
vercel deploy --prod --skip-domain
```

Use deployment protection to inspect that build. Validate:

- Root redirects to the local `/landing` path with the requested language; marketing links open the same deployment's `/work` and `/waitlist` paths.
- English and Chinese render meaningful HTML before JavaScript, have the correct HTML `lang`, self-canonicals and reciprocal `hreflang` links.
- `/robots.txt`, `/sitemap.xml` and `/opengraph-image` return 200; the sitemap contains only both localized landing pages. Preview-target builds instead prohibit indexing.
- `/work`, account/admin and archived report pages remain noindex. `noindex` is an SEO instruction, not an access-control mechanism.
- All three demo videos load and play; posters, mobile layout, keyboard access and reduced-motion behavior work.
- Sign-in, private workspace reads, watchlist updates, one bounded research run, cancellation, saved results, cited sources and streaming complete on the staged production build.
- Deep is disabled in the composer and account settings, including when browser storage remembers Deep. The unavailable notice is localized; Quick remains selectable. Deep POSTs to the Next proxy return 503 without contacting the backend.
- Measure mobile performance on the staged build. Local dev timings are not Core Web Vitals or production field measurements.

Record the deployment URL, frontend revision, backend revision and verification result. Promote **that same verified production build** when release is authorized:

```bash
vercel promote <verified-deployment-url>
```

Do not promote a preview-target build as a substitute for testing production environment variables. Configure `www.openashare.com` to redirect to the apex domain when domain changes are authorized; current canonical links already use the apex.

## Post-release and rollback

Check apex and www behavior, public health, language metadata, videos and one bounded authenticated workflow. Submit `https://openashare.com/sitemap.xml` in Google Search Console, request indexing for both landing variants, and inspect canonical selection. Search Console verification/access and actual rankings are outside the local audit.

Keep the previous Vercel production deployment available for rollback. If a release fails, roll back the frontend using the verified previous deployment. Restore the backend revision and runtime configuration independently; preserve persistent data and do not reverse database migrations blindly.

## References

- [Vercel staging and promotion](https://vercel.com/docs/deployments/promoting-a-deployment)
- [Vercel function duration limits](https://vercel.com/docs/functions/configuring-functions/duration)
- [Vercel Node versions](https://vercel.com/docs/functions/runtimes/node-js/node-js-versions)
- [Google localized versions](https://developers.google.com/search/docs/specialty/international/localized-versions)
- [Google video indexing guidance](https://developers.google.com/search/docs/appearance/video)

Metadata and structured data help discovery; they do not guarantee rankings or rich results. No ratings, pricing, fabricated authorship or video upload dates are added.
