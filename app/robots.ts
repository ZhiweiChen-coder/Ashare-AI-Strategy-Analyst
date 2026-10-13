import type { MetadataRoute } from "next";
import { searchIndexingEnabled, siteOrigin } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  if (!searchIndexingEnabled()) return { rules: { userAgent: "*", disallow: "/" } };
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/admin/", "/auth/"] },
    sitemap: `${siteOrigin()}/sitemap.xml`,
  };
}
