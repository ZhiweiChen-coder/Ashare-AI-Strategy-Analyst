# Signal landing page

The landing page adapts the semantic HTML and CSS composition supplied in `OpenAshare_V3_Signal_Design_Package.zip` and the candlestick grammar from the V4 package. The approved ascending ribbon remains as a soft foundation for the illustrative candles, with teal/clay light and a full-width research desk demo. The workspace's warm white palette and sans-serif typography remain consistent.

- `/` redirects to `/landing` on the same origin, carrying a valid `lang=en` or `lang=zh` query and falling back to the language cookie.
- Workspace, waitlist and return-home links use relative paths. GitHub links intentionally open the public repository.
- The hero combines the approved ascending ribbon with the V4 candlestick study. Deterministic illustrative candles share the ribbon's curve and gentle displacement, with teal/clay pigment and a soft ambient glow. Desktop uses 121 candles; mobile uses 43, with complete SVG artwork in the server HTML. The visual has no floating signal or news markers; the demo entry remains below the artwork. The visible caption identifies the artwork as illustrative and not live data. A pause control and reduced-motion fallback are provided; rendering suspends when offscreen or when the browser tab is hidden. Geometry, materials, the renderer and event listeners are disposed on navigation. Pixel ratio is capped and the candle bodies use instanced rendering.
- The hero demo links lead to the product video. Three accessible workflow tabs sit directly below it and reveal matching example views and research guidance. The video uses sample data and is labelled as not live market data.
- Homepage and workspace brand marks use the same SVG asset. The primary homepage links enter `/work`, and the workspace brand link returns to `/landing`, preserving the active language and origin.
- Journal cards open research-idea dialogs, rather than implying that reports have already been published. Native dialogs support Escape, keyboard focus containment and return focus to the initiating button.
- English and Chinese page copy and metadata are provided. The layout supports narrow mobile, tablet and desktop widths.

The page continues to use Next.js server-rendered HTML and a CSS module. Client JavaScript supports navigation, decorative rendering, journal dialogs and the workflow tabs. Landing-page viewing does not issue market-data or model requests.
