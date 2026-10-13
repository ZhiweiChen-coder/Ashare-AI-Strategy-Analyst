import { ImageResponse } from "next/og";

export const alt = "OpenAshare — AI stock research desk for US, China and Hong Kong equities";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", width: "100%", height: "100%", padding: "60px 76px", background: "#faf9f6", color: "#151715", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 32, fontWeight: 700 }}>OpenAshare</span>
        <span style={{ color: "#168f82", fontSize: 19, letterSpacing: 3 }}>AI STOCK RESEARCH</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", fontSize: 86, fontWeight: 700, letterSpacing: -4, lineHeight: 1.12 }}>
        <span>See the signal.</span>
        <span style={{ color: "#bb5734" }}>Find the story.</span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", paddingTop: 24, borderTop: "1px solid #dddcd5", color: "#5e635d", fontSize: 23 }}>
        <span>Charts · News · Cited research</span>
        <span>US · China · Hong Kong</span>
      </div>
    </div>,
    size,
  );
}
