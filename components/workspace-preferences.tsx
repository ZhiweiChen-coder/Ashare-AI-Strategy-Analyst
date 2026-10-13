"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useLanguage } from "@/components/language-provider";
import { panelDefaults, panelWidth } from "@/lib/workspace-layout";
import { getAgentResearchCapabilities } from "@/lib/api";
import { effectiveResearchMode } from "@/lib/research-availability";
import { usePathname } from "next/navigation";

type Preferences = { market: "us" | "a_share" | "hk"; researchMode: "quick" | "deep"; readingSize: "standard" | "large"; showResearchPanel: boolean; leftPanelWidth: number; rightPanelWidth: number };
const defaults: Preferences = { market: "us", researchMode: "quick", readingSize: "standard", showResearchPanel: true, leftPanelWidth: panelDefaults.left, rightPanelWidth: panelDefaults.right };
const storageKey = "openashare-preferences-v1";
const PreferencesContext = createContext<{ preferences: Preferences; updatePreferences: (patch: Partial<Preferences>) => void; deepResearchAvailable: boolean } | null>(null);

export function WorkspacePreferencesProvider({ children, initialDeepResearchAvailable = true }: { children: React.ReactNode; initialDeepResearchAvailable?: boolean }) {
  const pathname = usePathname();
  const [deepResearchAvailable, setDeepResearchAvailable] = useState(initialDeepResearchAvailable);
  const [preferences, setPreferences] = useState(defaults);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    // The public beta stays suspended even if an older backend advertises Deep.
    if (!initialDeepResearchAvailable || pathname === "/landing" || pathname === "/" || pathname.startsWith("/journal/")) return;
    let active = true;
    void getAgentResearchCapabilities().then(capabilities => {
      if (active) setDeepResearchAvailable(capabilities.deep_available === true);
    }).catch(() => { /* Local development retains its existing mode if an older backend lacks this endpoint. */ });
    return () => { active = false; };
  }, [initialDeepResearchAvailable, pathname]);
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
      const market = saved.market ?? localStorage.getItem("openashare-market");
      setPreferences({
        market: ["us", "a_share", "hk"].includes(market) ? market : defaults.market,
        researchMode: saved.researchMode === "deep" ? "deep" : "quick",
        readingSize: saved.readingSize === "large" ? "large" : "standard",
        showResearchPanel: saved.showResearchPanel !== false,
        leftPanelWidth: panelWidth(saved.leftPanelWidth, "left"),
        rightPanelWidth: panelWidth(saved.rightPanelWidth, "right"),
      });
    } catch { /* Keep defaults when browser storage is unavailable. */ }
    setReady(true);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.readingSize = preferences.readingSize;
    if (ready) {
      try { localStorage.setItem(storageKey, JSON.stringify(preferences)); } catch { /* Retain preferences for this visit. */ }
    }
  }, [preferences, ready]);
  const updatePreferences = useCallback((patch: Partial<Preferences>) => setPreferences(current => ({ ...current, ...patch, ...(patch.researchMode ? { researchMode: effectiveResearchMode(patch.researchMode, deepResearchAvailable) } : {}) })), [deepResearchAvailable]);
  const effectivePreferences = { ...preferences, researchMode: effectiveResearchMode(preferences.researchMode, deepResearchAvailable) };
  return <PreferencesContext.Provider value={{ preferences: effectivePreferences, updatePreferences, deepResearchAvailable }}>{children}</PreferencesContext.Provider>;
}

export function useWorkspacePreferences() {
  const value = useContext(PreferencesContext);
  if (!value) throw new Error("WorkspacePreferencesProvider is required");
  return value;
}

export function WorkspaceSettings({ onClose }: { onClose: () => void }) {
  const { locale, setLocale } = useLanguage();
  const { preferences, updatePreferences, deepResearchAvailable } = useWorkspacePreferences();
  const panelRef = useRef<HTMLDivElement>(null);
  const en = locale === "en";
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    panel?.querySelector<HTMLElement>("button")?.focus();
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); onClose(); }
      if (event.key !== "Tab" || !panel) return;
      const focusable = Array.from(panel.querySelectorAll<HTMLElement>("button, select, [tabindex='0']"));
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); if (previous?.isConnected) previous.focus(); else document.querySelector<HTMLButtonElement>(".workspace-account-trigger")?.focus(); };
  }, [onClose]);
  return <div className="workspace-settings-backdrop" onClick={onClose}>
    <div className="workspace-settings" ref={panelRef} role="dialog" aria-modal="true" aria-labelledby="workspace-settings-title" onClick={event => event.stopPropagation()}>
      <header><div><span>{en ? "YOUR WORKSPACE" : "你的工作空间"}</span><h2 id="workspace-settings-title">{en ? "Settings" : "设置"}</h2></div><button type="button" className="workspace-icon-button" aria-label={en ? "Close settings" : "关闭设置"} onClick={onClose}>✕</button></header>
      <div className="workspace-setting-row"><label htmlFor="preference-language">{en ? "Language" : "语言"}<small>{en ? "Menus and new research reports" : "菜单与新生成的研究报告"}</small></label><select id="preference-language" value={locale} onChange={e => setLocale(e.target.value as "en" | "zh")}><option value="en">English</option><option value="zh">简体中文</option></select></div>
      <div className="workspace-setting-row"><label htmlFor="preference-market">{en ? "Default market" : "默认市场"}<small>{en ? "Market pulse and news coverage" : "市场脉搏与新闻范围"}</small></label><select id="preference-market" value={preferences.market} onChange={e => updatePreferences({market: e.target.value as Preferences["market"]})}><option value="us">{en ? "United States" : "美股"}</option><option value="a_share">{en ? "Mainland China" : "A股"}</option><option value="hk">{en ? "Hong Kong" : "港股"}</option></select></div>
      <div className="workspace-setting-row"><label htmlFor="preference-depth">{en ? "Research depth" : "研究深度"}<small>{deepResearchAvailable ? (en ? "Quick answers promptly; Deep spends longer checking sources" : "快速模式直接回答；深入模式会花更多时间检索和核验来源") : (en ? "Deep research is unavailable at the moment." : "深入研究暂时不可用。")}</small></label><select id="preference-depth" value={preferences.researchMode} onChange={e => updatePreferences({researchMode: e.target.value as Preferences["researchMode"]})}><option value="quick">{en ? "Quick" : "快速"}</option><option value="deep" disabled={!deepResearchAvailable}>{deepResearchAvailable ? (en ? "Deep" : "深入") : (en ? "Deep — Unavailable at the moment" : "深入 — 暂时不可用")}</option></select></div>
      <div className="workspace-setting-row"><label htmlFor="preference-reading">{en ? "Reading size" : "阅读字号"}<small>{en ? "Research answers and sources" : "研究回答与来源"}</small></label><select id="preference-reading" value={preferences.readingSize} onChange={e => updatePreferences({readingSize: e.target.value as Preferences["readingSize"]})}><option value="standard">{en ? "Standard" : "标准"}</option><option value="large">{en ? "Larger" : "较大"}</option></select></div>
      <div className="workspace-setting-row"><label htmlFor="preference-panel">{en ? "Chart & research panel" : "图表与研究面板"}<small>{en ? "Stock details beside your chat on desktop" : "桌面端在对话旁显示股票资料"}</small></label><select id="preference-panel" value={preferences.showResearchPanel ? "show" : "hide"} onChange={e => updatePreferences({showResearchPanel: e.target.value === "show"})}><option value="show">{en ? "Show" : "显示"}</option><option value="hide">{en ? "Hide" : "隐藏"}</option></select></div>
      <footer>{en ? "Saved automatically in this browser. Existing reports keep their original language." : "自动保存在此浏览器。已有报告保留原来的语言。"}</footer>
    </div>
  </div>;
}
