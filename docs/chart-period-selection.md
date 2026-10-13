# Expanded chart research

Expanded charts start with all available daily history. Date presets change the visible time scale while retaining the complete series in both the sidebar and expanded chart. Native panning is bounded by the first and last available bars, and the sidebar date caption follows the actual visible interval.

The stock chart opens in an edge-to-edge viewport, preserving the workspace palette. The chart resizes with its available height rather than using a fixed 600px canvas. Escape closes it and returns focus to the expand button.

The bottom overview contains a draggable visible window and two resize handles. Arrow keys move a focused handle or window; Shift moves ten sessions, and Home/End move to the available boundaries. Date presets sit beside the timeline, below the main chart. All navigation changes the chart's time scale while retaining the complete available history.

In Select period mode, clicking a candle selects its calendar month. Dragging across candles selects the actual trading sessions between the endpoints, including intervals spanning months. The selection highlight uses the renderer's coordinate mapping and remains aligned after zooming, panning or resizing. Pan mode retains native chart navigation. Enter on the selection surface selects the visible period.

The Annotate action opens a note or question editor. Saved notes are local to this browser and stock; they can be reopened from a chart marker, edited or deleted. Asking the agent uses the existing research event with the selected dates, supplied OHLCV bars, a price summary and an instruction to retrieve dated sources rather than infer price causation from candles alone. Saving a note makes no model request.

Bars with missing OHLC values, non-finite prices or invalid dates are excluded consistently from rendering and selection; duplicate dates are consolidated and bars are sorted. Indicator history is calculated before slicing the visible interval, retaining warm-up data. Research attachments contain at most 80 OHLCV bars, preserving endpoints and price extremes; larger selections explicitly disclose sampling and retain full-period summary statistics.

Selection and navigator boundary checks: `node --experimental-strip-types --test tests/chart-window.test.mjs` (Node 22). Repository validation remains the backend API tests and the frontend build.
