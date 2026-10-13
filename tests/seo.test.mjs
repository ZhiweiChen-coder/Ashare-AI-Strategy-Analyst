import assert from "node:assert/strict";
import test from "node:test";
import { landingStructuredData, localizedMetadata, localizedUrl, searchIndexingEnabled, serializeStructuredData, siteOrigin } from "../lib/seo.ts";

function withEnvironment(values, callback) {
  const previous = Object.fromEntries(Object.keys(values).map(key => [key, process.env[key]]));
  try {
    for (const [key, value] of Object.entries(values)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    callback();
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
  }
}

test("locale pages have distinct self canonicals and reciprocal language alternatives", () => {
  withEnvironment({ NEXT_PUBLIC_SITE_URL: undefined, VERCEL_ENV: "production", SEO_NOINDEX: undefined }, () => {
    const en = localizedMetadata({ path: "/landing", language: "en", title: "English", description: "Research" });
    const zh = localizedMetadata({ path: "/landing", language: "zh", title: "中文", description: "研究" });
    assert.equal(en.alternates.canonical, "https://openashare.com/landing?lang=en");
    assert.equal(zh.alternates.canonical, "https://openashare.com/landing?lang=zh");
    assert.deepEqual(en.alternates.languages, zh.alternates.languages);
    assert.equal(en.alternates.languages["x-default"], en.alternates.canonical);
    assert.equal(zh.alternates.languages["zh-CN"], zh.alternates.canonical);
    assert.equal(en.openGraph.url, en.alternates.canonical);
    assert.equal(en.robots.index, true);
  });
});

test("preview builds and explicit indexing opt-out stay out of search", () => {
  for (const environment of ["preview", "development"]) {
    withEnvironment({ VERCEL_ENV: environment, SEO_NOINDEX: undefined }, () => {
      assert.equal(searchIndexingEnabled(), false);
      assert.equal(localizedMetadata({ path: "/landing", language: "en", title: "Test", description: "Test" }).robots.index, false);
    });
  }
  withEnvironment({ VERCEL_ENV: "production", SEO_NOINDEX: "true" }, () => assert.equal(searchIndexingEnabled(), false));
});

test("editorial opt-out is retained in production while links remain followable", () => {
  withEnvironment({ VERCEL_ENV: "production", SEO_NOINDEX: undefined }, () => {
    const article = localizedMetadata({ path: "/journal/ai-chip-cycle", language: "en", title: "Draft", description: "Draft", indexable: false });
    assert.deepEqual(article.robots, { index: false, follow: true });
  });
});

test("canonical origin cannot silently become localhost or insecure HTTP", () => {
  for (const value of ["http://openashare.com", "https://localhost:3000", "https://127.0.0.1", "not a URL"]) {
    withEnvironment({ NEXT_PUBLIC_SITE_URL: value }, () => assert.throws(() => siteOrigin()));
  }
  withEnvironment({ NEXT_PUBLIC_SITE_URL: "https://openashare.com/ignored-path" }, () => {
    assert.equal(siteOrigin(), "https://openashare.com");
    assert.equal(localizedUrl("/landing?lang=zh", "en"), "https://openashare.com/landing?lang=en");
  });
});

test("structured data is script-safe and contains no invented reviews or prices", () => {
  const description = "Research </script><script>alert(1)</script>";
  const data = landingStructuredData("en", description);
  const encoded = serializeStructuredData(data);
  assert.ok(!encoded.includes("<"));
  assert.deepEqual(JSON.parse(encoded), data);
  assert.equal(data["@graph"].find(item => item["@type"] === "WebApplication").description, description);
  assert.ok(!encoded.includes("aggregateRating"));
  assert.ok(!encoded.includes("offers"));
});
