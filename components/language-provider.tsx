"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { translateLabel, type Language } from "@/lib/i18n";

const LanguageContext = createContext<{ locale: Language; setLocale: (locale: Language) => void } | null>(null);

export function LanguageProvider({ children, initialLanguage }: { children: React.ReactNode; initialLanguage: Language }) {
  const params = useSearchParams();
  const [locale, setLocale] = useState<Language>(initialLanguage);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const explicit = params.get("lang");
    let stored: string | null = null;
    try { stored = localStorage.getItem("openashare-language"); } catch { /* Storage can be disabled. */ }
    const candidate = explicit ?? stored ?? initialLanguage;
    if (candidate === "en" || candidate === "zh") setLocale(candidate);
    setReady(true);
  }, [params, initialLanguage]);
  useEffect(() => {
    if (!ready) return;
    document.documentElement.lang = locale === "en" ? "en" : "zh-CN";
    document.cookie = `openashare-language=${locale};path=/;max-age=31536000;SameSite=Lax`;
    try { localStorage.setItem("openashare-language", locale); } catch { /* Retain the in-memory preference. */ }
  }, [locale, ready]);
  const changeLanguage = useCallback((next: Language) => {
    setLocale(next);
    const url = new URL(window.location.href);
    url.searchParams.set("lang", next);
    window.history.replaceState(null, "", url);
  }, []);
  return <LanguageContext.Provider value={{ locale, setLocale: changeLanguage }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("LanguageProvider is required");
  const t = useCallback((text: string) => translateLabel(text, context.locale), [context.locale]);
  return { ...context, t };
}

export function LanguageSwitcher() {
  const { locale, setLocale } = useLanguage();
  return <div className="workspace-language-switch" role="group" aria-label={locale === "en" ? "Interface language" : "界面语言"}>
    <button type="button" aria-pressed={locale === "zh"} onClick={() => setLocale("zh")}>中文</button>
    <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>EN</button>
  </div>;
}
