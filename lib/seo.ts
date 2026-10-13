import type { Metadata } from "next";

export type SiteLanguage = "en" | "zh";

export function siteOrigin(): string {
  const url = new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://openashare.com");
  if (url.protocol !== "https:" || ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) {
    throw new Error("NEXT_PUBLIC_SITE_URL must be the public HTTPS site origin.");
  }
  return url.origin;
}

export function localizedUrl(path: string, language: SiteLanguage): string {
  const url = new URL(path, siteOrigin());
  url.searchParams.set("lang", language);
  return url.toString();
}

export function searchIndexingEnabled(): boolean {
  return process.env.SEO_NOINDEX !== "true"
    && !["preview", "development"].includes(process.env.VERCEL_ENV || "");
}

export function localizedMetadata({ path, language, title, description, indexable = true }: {
  path: string;
  language: SiteLanguage;
  title: string;
  description: string;
  indexable?: boolean;
}): Metadata {
  const canonical = localizedUrl(path, language);
  const index = indexable && searchIndexingEnabled();
  const image = { url: `${siteOrigin()}/opengraph-image`, width: 1200, height: 630, alt: "OpenAshare — AI stock research desk" };
  return {
    title,
    description,
    alternates: {
      canonical,
      languages: {
        en: localizedUrl(path, "en"),
        "zh-CN": localizedUrl(path, "zh"),
        "x-default": localizedUrl(path, "en"),
      },
    },
    robots: { index, follow: true },
    openGraph: {
      type: "website", siteName: "OpenAshare", url: canonical, title, description,
      locale: language === "zh" ? "zh_CN" : "en_US",
      alternateLocale: language === "zh" ? "en_US" : "zh_CN",
      images: [image],
    },
    twitter: { card: "summary_large_image", title, description, images: [image.url] },
  };
}

export function landingStructuredData(language: SiteLanguage, description: string) {
  const origin = siteOrigin();
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization", "@id": `${origin}/#organization`, name: "OpenAshare",
        url: origin, logo: `${origin}/logo.png`,
        sameAs: ["https://github.com/ZhiweiChen-coder/OpenAshare"],
      },
      {
        "@type": "WebSite", "@id": `${origin}/#website`, name: "OpenAshare", url: origin,
        inLanguage: ["en", "zh-CN"], publisher: { "@id": `${origin}/#organization` },
      },
      {
        "@type": "WebApplication", "@id": `${origin}/#application`, name: "OpenAshare",
        applicationCategory: "FinanceApplication", operatingSystem: "Web",
        url: localizedUrl("/landing", language), description,
        inLanguage: language === "zh" ? "zh-CN" : "en",
        publisher: { "@id": `${origin}/#organization` },
      },
    ],
  };
}

export function serializeStructuredData(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
