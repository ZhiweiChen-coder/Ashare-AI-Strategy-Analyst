import { type NextRequest, NextResponse } from "next/server";

import { updateSession } from "@/utils/supabase/middleware";

export async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  if (path === "/" || path === "/landing" || path.startsWith("/journal/")) {
    const requested = request.nextUrl.searchParams.get("lang");
    const language = requested === "en" || requested === "zh"
      ? requested : request.cookies.get("openashare-language")?.value === "zh" ? "zh" : "en";
    if (path === "/") {
      // Redirect before rendering/streaming so crawlers receive an HTTP redirect.
      // Use the incoming origin to keep local and staging navigation on that site.
      const destination = new URL("/landing", request.url);
      destination.searchParams.set("lang", language);
      return NextResponse.redirect(destination);
    }
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("x-openashare-page-language", language);
    // Public pages need no auth refresh; language must also be correct before hydration.
    return NextResponse.next({ request: { headers: requestHeaders } });
  }
  return updateSession(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|opengraph-image|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|mp4|webm|mov|woff|woff2|ttf)$).*)",
  ],
};
