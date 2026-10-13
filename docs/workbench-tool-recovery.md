# Workbench tool recovery and layout

Company coordination reuses a matching, unambiguous, verified identity from the current run. A later empty or unrelated search cannot replace that identity. Newly requested companies still need their own verification. Compound retrieval consumes its own search response rather than the latest result from a shared list, so concurrent searches cannot change its target.

Identity search can fall back to SEC mappings if the primary lookup fails. Failed lookup records are excluded from name and SEC identity reads. Existing provider-call, token, source-read and cancellation limits remain in force; this change adds no paid retry policy.

Research steps have an optional `reason_code` aligned between the API and frontend. Empty successful reads display No match or No results, dependency blocks display Needs identity, and source-read limits remain distinct from provider failures. Cached failures retain their failure status. Streaming progress merges repeated updates for the same tool; saved reports retain their attempt history and identify earlier attempts followed by later completion. Actual source gaps remain visible.

Desktop sidebars have draggable and keyboard-accessible separators. Panel widths are saved in browser preferences after dragging ends, bounded to keep the conversation usable, and reset with a double-click. Compact layouts use overlays without resize handles. The empty research panel offers the same stock, news, market and portfolio launchers as the left sidebar.

News cards show their source material without sentiment or numeric impact badges. Backend metadata is preserved for compatibility.

Offline regression coverage includes parallel identity completion, identity reuse after an empty search, preventing cross-company reuse, fallback verification, failed-cache status, empty news, streaming status recovery and panel sizing. Live provider research and model quality still require separate evaluation; these checks do not claim universal source availability.
