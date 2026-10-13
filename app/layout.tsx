import type { Metadata } from "next";
import { Suspense } from "react";
import { cookies, headers } from "next/headers";
import { siteOrigin } from "@/lib/seo";
import { isPublicBetaRuntime } from "@/lib/research-availability";
import { LanguageProvider } from "@/components/language-provider";
import { WorkspacePreferencesProvider } from "@/components/workspace-preferences";

import { AppShell, AppShellProvider } from "@/components/app-shell";
import "./tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteOrigin()),
  title: "OpenAshare",
  description: "AI-powered stock analysis, news and portfolio workstation.",
  // Public marketing pages opt in explicitly; personal workspace pages stay out of search.
  robots: { index: false, follow: true },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const requestedLanguage = (await headers()).get("x-openashare-page-language");
  const language = requestedLanguage === "en" || requestedLanguage === "zh"
    ? requestedLanguage
    : (await cookies()).get("openashare-language")?.value === "zh" ? "zh" : "en";
  return (
    <html lang={language === "en" ? "en" : "zh-CN"} suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="shell">
          <div className="frame">
            <Suspense fallback={null}>
              <LanguageProvider initialLanguage={language}>
              <WorkspacePreferencesProvider initialDeepResearchAvailable={!isPublicBetaRuntime(process.env)}>
              <AppShellProvider>
                <AppShell>{children}</AppShell>
              </AppShellProvider>
              </WorkspacePreferencesProvider>
              </LanguageProvider>
            </Suspense>
          </div>
        </div>
      </body>
    </html>
  );
}
