import type { MetadataRoute } from "next";
import { localizedUrl, searchIndexingEnabled } from "@/lib/seo";

export default function sitemap(): MetadataRoute.Sitemap {
  if (!searchIndexingEnabled()) return [];
  // Journal articles remain noindex until their financial claims and citations are reviewed.
  return (["en", "zh"] as const).map(language => ({
    url: localizedUrl("/landing", language),
    alternates: {
      languages: {
        en: localizedUrl("/landing", "en"),
        "zh-CN": localizedUrl("/landing", "zh"),
        "x-default": localizedUrl("/landing", "en"),
      },
    },
  }));
}
