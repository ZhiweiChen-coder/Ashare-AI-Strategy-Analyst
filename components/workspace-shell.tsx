"use client";

import { useLanguage } from "@/components/language-provider";

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import Image from "next/image";
import { useSearchParams } from "next/navigation";

import { AgentChat } from "@/components/agent-chat";
import { AgentLabBar } from "@/components/agent-lab-bar";
import { CandlestickChart, type ChartPoint } from "@/components/candlestick-chart";
import { ResearchChart, type ChartAnnotation, type ChartSegment } from "@/components/research-chart";
import {
  getGlobalNews,
  getCreditBalance,
  getHotspotDetail,
  getMarketRegime,
  getPortfolioAnalysis,
  getStockAnalysis,
  getStockNews,
  getWorkspaceBootstrap,
  getWorkspaceWatchlist,
  initializeWorkspaceWatchlist,
  updateWorkspaceWatchlist,
  searchStocks,
} from "@/lib/api";
import type {
  GlobalNewsItem,
  HotspotDetailResponse,
  MarketRegimeResponse,
  NewsItem,
  PortfolioAnalysisResponse,
  StockAnalysisResponse,
  CreditBalanceResponse,
} from "@/lib/types";
import {
  AGENT_LAB_RUN_EVENT,
  contextFromStock,
  compactHeadline,
  type AgentLabTrace,
  type ResearchContext,
  type WorkspaceSessionSummary,
} from "@/lib/workspace";
import { SupabaseAuthPanel, type SupabaseAuthSnapshot } from "@/components/supabase-auth-panel";
import { WorkspaceSettings, useWorkspacePreferences } from "@/components/workspace-preferences";
import { WorkspaceTools } from "@/components/workspace-tools";
import { WorkspacePanelResizer } from "@/components/workspace-panel-resizer";
import { fitWorkspacePanels, panelLimits } from "@/lib/workspace-layout";
import { formatQuantity } from "@/lib/i18n";
import { sampleChartBars, orderedChartBars, presetChartWindow, clampChartWindow } from "@/lib/chart-window";
import type { IChartApi } from "lightweight-charts";

type WatchItem = {
  code: string;
  name: string;
};

type WorkspaceProject = {
  id: string;
  name: string;
  createdAt: number;
};

type SessionContextMenu = {
  sessionId: string;
  x: number;
  y: number;
  renaming: boolean;
};

type ProjectContextMenu = {
  projectId: string;
  x: number;
  y: number;
  renaming: boolean;
};

const WATCHLIST_STORAGE_KEY = "ashare-workspace-watchlist-v3";
const PROJECTS_STORAGE_KEY = "ashare-workspace-projects-v1";
const SESSION_PROJECTS_STORAGE_KEY = "ashare-workspace-session-projects-v1";

const DEFAULT_WATCHLIST: WatchItem[] = [
  { code: "US.AAPL", name: "Apple" },
  { code: "US.NVDA", name: "NVIDIA" },
  { code: "US.MSFT", name: "Microsoft" },
  { code: "sh000001", name: "上证指数" },
  { code: "sz399001", name: "深证成指" },
  { code: "HK.HSI", name: "恒生指数" },
  { code: "sh000300", name: "沪深300" },
];

function readWatchlistCache(): WatchItem[] {
  try {
    const stored = window.localStorage.getItem(WATCHLIST_STORAGE_KEY);
    const parsed = stored ? JSON.parse(stored) : null;
    if (Array.isArray(parsed) && parsed.every(item => typeof item?.code === "string" && typeof item?.name === "string")) return parsed;
  } catch { /* An invalid browser cache must not block server recovery. */ }
  return DEFAULT_WATCHLIST;
}

export function WorkspaceShell({ labMode = false }: { labMode?: boolean }) {
  const { t, locale } = useLanguage();
  const { preferences, updatePreferences } = useWorkspacePreferences();
  const searchParams = useSearchParams();
  const [watchlist, setWatchlist] = useState<WatchItem[]>(DEFAULT_WATCHLIST);
  const [watchlistLoaded, setWatchlistLoaded] = useState(false);
  const [watchlistBusy, setWatchlistBusy] = useState(false);
  const [watchlistInput, setWatchlistInput] = useState("");
  const [watchlistError, setWatchlistError] = useState("");
  const [sessions, setSessions] = useState<WorkspaceSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [projects, setProjects] = useState<WorkspaceProject[]>([]);
  const [sessionProjects, setSessionProjects] = useState<Record<string, string>>({});
  const [projectsLoaded, setProjectsLoaded] = useState(false);
  const [activeProjectId, setActiveProjectId] = useState<string>("all");
  const [projectComposerOpen, setProjectComposerOpen] = useState(false);
  const [projectDraft, setProjectDraft] = useState("");
  const [sessionMenu, setSessionMenu] = useState<SessionContextMenu | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [projectMenu, setProjectMenu] = useState<ProjectContextMenu | null>(null);
  const [projectRenameDraft, setProjectRenameDraft] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [activeContext, setActiveContext] = useState<ResearchContext | null>(null);
  const [pinnedContext, setPinnedContext] = useState<ResearchContext | null>(null);
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [compactViewport, setCompactViewport] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);
  const [gridWidth, setGridWidth] = useState(0);
  const [draftPanelSizes, setDraftPanelSizes] = useState<{ left: number; right: number } | null>(null);
  const panelSizes = fitWorkspacePanels(draftPanelSizes ?? { left: preferences.leftPanelWidth, right: preferences.rightPanelWidth }, gridWidth, leftPanelOpen, rightPanelOpen);
  useEffect(() => {
    const grid = gridRef.current;
    if (!grid) return;
    const observer = new ResizeObserver(() => setGridWidth(grid.clientWidth));
    observer.observe(grid); return () => observer.disconnect();
  }, []);
  function resizePanel(side: "left" | "right", width: number, commit = false) {
    if (commit) { updatePreferences(side === "left" ? { leftPanelWidth: width } : { rightPanelWidth: width }); setDraftPanelSizes(null); }
    else setDraftPanelSizes(current => ({ left: current?.left ?? panelSizes.left, right: current?.right ?? panelSizes.right, [side]: width }));
  }
  const closeResearchContext = useCallback(() => {
    setRightPanelOpen(false);
    if (!compactViewport) updatePreferences({showResearchPanel: false});
    document.querySelector<HTMLButtonElement>('button[aria-controls="research-drawer"]')?.focus();
  }, [compactViewport, updatePreferences]);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const closeSettings = useCallback(() => setSettingsOpen(false), []);
  const accountMenuRef = useRef<HTMLDivElement>(null);
  const sessionMenuRef = useRef<HTMLDivElement>(null);
  const projectMenuRef = useRef<HTMLDivElement>(null);
  const [labTraces, setLabTraces] = useState<AgentLabTrace[]>([]);
  useEffect(() => {
    const viewport = window.matchMedia("(max-width: 900px)");
    const applyViewport = () => {
      setCompactViewport(viewport.matches);
      setLeftPanelOpen(!viewport.matches);
      setRightPanelOpen(!viewport.matches);
    };
    applyViewport();
    viewport.addEventListener("change", applyViewport);
    return () => viewport.removeEventListener("change", applyViewport);
  }, []);
  useEffect(() => {
    setRightPanelOpen(!compactViewport && preferences.showResearchPanel);
  }, [compactViewport, preferences.showResearchPanel]);
  const [cloudStatus, setCloudStatus] = useState<"local" | "syncing" | "connected" | "error">("local");
  const [cloudError, setCloudError] = useState("");
  const [creditBalance, setCreditBalance] = useState<CreditBalanceResponse | null>(null);

  const refreshCreditBalance = useCallback(async () => {
    try {
      setCreditBalance(await getCreditBalance());
    } catch {
      setCreditBalance(null);
    }
  }, []);

  const refreshWatchlist = useCallback(async () => {
    try {
      const saved = await getWorkspaceWatchlist();
      const canonical = saved.initialized ? saved : await initializeWorkspaceWatchlist(readWatchlistCache());
      setWatchlist(canonical.items);
      setWatchlistLoaded(true);
      setWatchlistError("");
    } catch {
      setWatchlistError(locale === "en" ? "Watchlist sync unavailable. Your saved list is preserved." : "自选股同步暂不可用，已保存的列表仍保留。");
    }
  }, [locale]);

  useEffect(() => {
    let cancelled = false;
    const existing = readWatchlistCache();
    setWatchlist(existing);
    void (async () => {
      try {
        const saved = await getWorkspaceWatchlist();
        const canonical = saved.initialized ? saved : await initializeWorkspaceWatchlist(existing);
        if (!cancelled) { setWatchlist(canonical.items); setWatchlistLoaded(true); setWatchlistError(""); }
      } catch {
        if (!cancelled) setWatchlistError("Watchlist sync unavailable. Your saved list is preserved.");
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!watchlistLoaded) return;
    try { window.localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist)); }
    catch { /* The backend remains the source of truth when browser storage is full. */ }
  }, [watchlist, watchlistLoaded]);

  useEffect(() => {
    const refresh = () => { void refreshWatchlist(); };
    window.addEventListener("ashare:watchlist-changed", refresh);
    window.addEventListener("focus", refresh);
    return () => { window.removeEventListener("ashare:watchlist-changed", refresh); window.removeEventListener("focus", refresh); };
  }, [refreshWatchlist]);

  useEffect(() => {
    try {
      const storedProjects = window.localStorage.getItem(PROJECTS_STORAGE_KEY);
      const storedAssignments = window.localStorage.getItem(SESSION_PROJECTS_STORAGE_KEY);
      if (storedProjects) {
        const parsed = JSON.parse(storedProjects) as WorkspaceProject[];
        if (Array.isArray(parsed) && parsed.every((project) => project?.id && project?.name)) {
          setProjects(parsed);
        }
      }
      if (storedAssignments) {
        const parsed = JSON.parse(storedAssignments) as Record<string, string>;
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          setSessionProjects(parsed);
        }
      }
    } catch {
      // Project grouping is an enhancement; invalid local state should not block chats.
    } finally {
      setProjectsLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!projectsLoaded) return;
    window.localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  }, [projects, projectsLoaded]);

  useEffect(() => {
    if (!projectsLoaded) return;
    window.localStorage.setItem(SESSION_PROJECTS_STORAGE_KEY, JSON.stringify(sessionProjects));
  }, [projectsLoaded, sessionProjects]);

  useEffect(() => {
    if (!accountMenuOpen) return;

    function closeOnOutsidePointer(event: PointerEvent) {
      if (!accountMenuRef.current?.contains(event.target as Node)) {
        setAccountMenuOpen(false);
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setAccountMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", closeOnOutsidePointer);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [accountMenuOpen]);

  useEffect(() => {
    if (!sessionMenu) return;

    function closeSessionMenu(event: PointerEvent) {
      if (!sessionMenuRef.current?.contains(event.target as Node)) {
        setSessionMenu(null);
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setSessionMenu(null);
    }

    document.addEventListener("pointerdown", closeSessionMenu);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeSessionMenu);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [sessionMenu]);

  useEffect(() => {
    if (!projectMenu) return;

    function closeProjectMenu(event: PointerEvent) {
      if (!projectMenuRef.current?.contains(event.target as Node)) {
        setProjectMenu(null);
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setProjectMenu(null);
    }

    document.addEventListener("pointerdown", closeProjectMenu);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeProjectMenu);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [projectMenu]);

  useEffect(() => {
    function assignNewSession(event: Event) {
      const sessionId = (event as CustomEvent<string>).detail;
      if (!sessionId || activeProjectId === "all" || activeProjectId === "unassigned") return;
      setSessionProjects((current) => ({ ...current, [sessionId]: activeProjectId }));
    }

    window.addEventListener("ashare:session-created", assignNewSession);
    return () => window.removeEventListener("ashare:session-created", assignNewSession);
  }, [activeProjectId]);

  const handleSupabaseAuth = useCallback(async (snapshot: SupabaseAuthSnapshot) => {
    if (!snapshot.session?.access_token) {
      setCloudStatus("local");
      setCloudError(snapshot.error ?? "");
      void refreshCreditBalance();
      void refreshWatchlist();
      return;
    }
    setCloudStatus("syncing");
    setCloudError("");
    try {
      const bootstrap = await getWorkspaceBootstrap(snapshot.session.access_token);
      void bootstrap;
      await refreshWatchlist();
      setCloudStatus("connected");
      await refreshCreditBalance();
    } catch (syncError) {
      setCloudStatus("error");
      setCloudError(syncError instanceof Error ? syncError.message : t("Supabase 工作台同步失败"));
    }
  }, [refreshCreditBalance, refreshWatchlist, t]);

  useEffect(() => {
    void refreshCreditBalance();
  }, [refreshCreditBalance]);

  useEffect(() => {
    const symbol = searchParams.get("symbol");
    const context = searchParams.get("context");
    if (symbol) {
      const existing = watchlist.find((item) => item.code.toLowerCase() === symbol.toLowerCase());
      openStock(existing?.code ?? symbol, existing?.name);
    } else if (context === "portfolio" || context === "market" || context === "news") {
      setActiveContext({ type: context, title: (locale === "en" ? { portfolio: "My portfolio", market: "Market pulse", news: "Global news" } : { portfolio: "我的持仓", market: "市场脉搏", news: "全球新闻" })[context], payload: {}, updatedAt: new Date().toISOString() });
      setRightPanelOpen(true);
    }
    // URL state is an initial deep-link, not a live source of truth.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const sortedSessions = useMemo(
    () =>
      [...sessions].sort((a, b) => {
        if (Boolean(b.pinned) !== Boolean(a.pinned)) return Number(Boolean(b.pinned)) - Number(Boolean(a.pinned));
        return b.updatedAt - a.updatedAt;
      }),
    [sessions],
  );

  const visibleSessions = useMemo(() => {
    if (!projects.length || activeProjectId === "all") return sortedSessions;
    if (activeProjectId === "unassigned") return sortedSessions.filter((session) => !sessionProjects[session.id]);
    return sortedSessions.filter((session) => sessionProjects[session.id] === activeProjectId);
  }, [activeProjectId, projects.length, sessionProjects, sortedSessions]);

  function openStock(code: string, name?: string) {
    if (pinnedContext) return;
    const normalized = normalizeSymbol(code);
    setSelectedSymbol(normalized);
    setActiveContext(contextFromStock(normalized, name));
    setRightPanelOpen(true);
    if (!compactViewport) updatePreferences({showResearchPanel: true});
    if (compactViewport) setLeftPanelOpen(false);
  }

  async function addWatchItem(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = watchlistInput.trim();
    if (!value || watchlistBusy || !watchlistLoaded) return;
    setWatchlistError("");
    let code = normalizeSymbol(value);
    let name = value;
    try {
      const matches = await searchStocks(value);
      const exact = matches.filter(item => item.name.toLowerCase() === value.toLowerCase() || item.code.toUpperCase() === value.toUpperCase() || item.code.toUpperCase() === `US.${value.toUpperCase()}`);
      const target = exact[0] ?? (matches.length === 1 ? matches[0] : null);
      if (!target) { setWatchlistError(locale === "en" ? "Use a ticker to identify the company precisely." : "请提供股票代码，以准确识别公司。"); return; }
      code = target.code;
      name = target.name;
    } catch { setWatchlistError(locale === "en" ? "Company search unavailable. Please try again." : "股票搜索暂不可用，请重试。"); return; }
    if (watchlist.some((item) => item.code.toLowerCase() === code.toLowerCase())) {
      openStock(code);
      setWatchlistInput("");
      return;
    }
    setWatchlistBusy(true);
    try {
      const saved = await updateWorkspaceWatchlist("add", code);
      setWatchlist(saved.items);
      setWatchlistInput("");
      openStock(code, name);
    } catch (error) { setWatchlistError(error instanceof Error ? error.message : t("自选股保存失败")); }
    finally { setWatchlistBusy(false); }
  }

  async function removeWatchItem(code: string) {
    if (watchlistBusy) return;
    setWatchlistBusy(true);
    setWatchlistError("");
    try { setWatchlist((await updateWorkspaceWatchlist("remove", code)).items); }
    catch (error) { setWatchlistError(error instanceof Error ? error.message : t("自选股保存失败")); }
    finally { setWatchlistBusy(false); }
  }

  async function toggleWatchItem(code: string) {
    if (watchlistBusy || !watchlistLoaded) return;
    setWatchlistBusy(true);
    setWatchlistError("");
    try {
      const action = watchlist.some(item => item.code.toUpperCase() === code.toUpperCase()) ? "remove" : "add";
      setWatchlist((await updateWorkspaceWatchlist(action, code)).items);
    } catch (error) { setWatchlistError(error instanceof Error ? error.message : t("自选股保存失败")); }
    finally { setWatchlistBusy(false); }
  }

  function selectSession(sessionId: string) {
    setActiveSessionId(sessionId);
    window.dispatchEvent(new CustomEvent("ashare:select-session", { detail: sessionId }));
  }

  function createSession() {
    window.dispatchEvent(new Event("ashare:new-session"));
  }

  const handleSessionsChange = useCallback((nextSessions: WorkspaceSessionSummary[]) => {
    setSessions(nextSessions);
    setSessionProjects((current) => {
      const liveIds = new Set(nextSessions.map((session) => session.id));
      const nextEntries = Object.entries(current).filter(([sessionId]) => liveIds.has(sessionId));
      if (nextEntries.length === Object.keys(current).length) return current;
      return Object.fromEntries(nextEntries);
    });
  }, []);

  function createProject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = projectDraft.trim();
    if (!name) return;
    const project: WorkspaceProject = {
      id: `project-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      name: name.slice(0, 48),
      createdAt: Date.now(),
    };
    setProjects((current) => [project, ...current]);
    setActiveProjectId(project.id);
    setProjectDraft("");
    setProjectComposerOpen(false);
  }

  function openProjectMenu(event: React.MouseEvent<HTMLButtonElement>, project: WorkspaceProject) {
    event.preventDefault();
    const menuWidth = 210;
    const menuHeight = 150;
    setProjectRenameDraft(project.name);
    setProjectMenu({
      projectId: project.id,
      x: Math.max(12, Math.min(event.clientX, window.innerWidth - menuWidth)),
      y: Math.max(12, Math.min(event.clientY, window.innerHeight - menuHeight)),
      renaming: false,
    });
  }

  function renameProject(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!projectMenu || !projectRenameDraft.trim()) return;
    const name = projectRenameDraft.trim().slice(0, 48);
    setProjects((current) => current.map((project) => (
      project.id === projectMenu.projectId ? { ...project, name } : project
    )));
    setProjectMenu(null);
  }

  function deleteProject(projectId: string) {
    setProjects((current) => current.filter((project) => project.id !== projectId));
    setSessionProjects((current) => {
      const next = { ...current };
      for (const [sessionId, assignedProjectId] of Object.entries(next)) {
        if (assignedProjectId === projectId) delete next[sessionId];
      }
      return next;
    });
    if (activeProjectId === projectId) setActiveProjectId("all");
    setProjectMenu(null);
  }

  function openSessionMenu(event: React.MouseEvent<HTMLButtonElement>, session: WorkspaceSessionSummary) {
    event.preventDefault();
    const menuWidth = 224;
    const menuHeight = 272;
    setRenameDraft(session.title === "新对话" ? "" : session.title);
    setSessionMenu({
      sessionId: session.id,
      x: Math.max(12, Math.min(event.clientX, window.innerWidth - menuWidth)),
      y: Math.max(12, Math.min(event.clientY, window.innerHeight - menuHeight)),
      renaming: false,
    });
  }

  function renameSession(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sessionMenu || !renameDraft.trim()) return;
    window.dispatchEvent(new CustomEvent("ashare:rename-session", {
      detail: { sessionId: sessionMenu.sessionId, title: renameDraft.trim().slice(0, 80) },
    }));
    setSessionMenu(null);
  }

  function moveSessionToProject(sessionId: string, projectId: string | null) {
    setSessionProjects((current) => {
      if (!projectId) {
        const next = { ...current };
        delete next[sessionId];
        return next;
      }
      return { ...current, [sessionId]: projectId };
    });
    setSessionMenu(null);
  }

  function deleteSession(sessionId: string) {
    window.dispatchEvent(new CustomEvent("ashare:delete-session", { detail: sessionId }));
    setSessionMenu(null);
  }

  function projectSessionCount(projectId: string) {
    return sessions.filter((session) => sessionProjects[session.id] === projectId).length;
  }

  const handleContextUpdate = useCallback((context: ResearchContext | null, initial = false, openPanel = false) => {
    if (pinnedContext) return;
    // An explicit stock/tool link takes precedence over the initial saved chat.
    if (initial && (searchParams.get("symbol") || searchParams.get("context"))) return;
    setActiveContext(context);
    setSelectedSymbol(context?.type === "stock" ? context.entityId ?? null : null);
    if (openPanel && context?.type === "stock") {
      setRightPanelOpen(true);
      if (!compactViewport) updatePreferences({ showResearchPanel: true });
      if (compactViewport) setLeftPanelOpen(false);
    }
  }, [compactViewport, pinnedContext, searchParams, updatePreferences]);

  function handleLabTrace(trace: AgentLabTrace) {
    setLabTraces((current) => [...current, trace].slice(-30));
  }

  function openResearchTool(type: "stock" | "news" | "portfolio" | "market") {
    if (type === "stock") {
      setPinnedContext(null);
      const normalized = selectedSymbol ? normalizeSymbol(selectedSymbol) : null;
      const watchName = normalized
        ? watchlist.find(item => item.code.toUpperCase() === normalized.toUpperCase())?.name
        : undefined;
      const displayName = watchName && !isUnknownStockName(watchName) ? watchName : undefined;
      setSelectedSymbol(normalized);
      setActiveContext(normalized
        ? contextFromStock(normalized, displayName)
        : { type: "stock", title: locale === "en" ? "Stock research" : "股票研究", payload: {}, updatedAt: new Date().toISOString() });
      setRightPanelOpen(true);
      if (!compactViewport) updatePreferences({showResearchPanel: true});
      if (compactViewport) setLeftPanelOpen(false);
      return;
    }
    setPinnedContext(null);
    setActiveContext({ type, title: (locale === "en" ? { news: "News and catalysts", portfolio: "My portfolio", market: "Market overview" } : { news: "新闻与催化", portfolio: "我的持仓", market: "市场概览" })[type], payload: {}, updatedAt: new Date().toISOString() });
    setRightPanelOpen(true);
    if (!compactViewport) updatePreferences({showResearchPanel: true});
    if (compactViewport) setLeftPanelOpen(false);
  }

  return (
    <main className={`workspace-page workspace-v2 ${labMode ? "workspace-page--lab" : ""}`}>
      <header className="workspace-header" inert={settingsOpen}>
        <div className="workspace-header-leading">
          <button className="workspace-icon-button workspace-sidebar-toggle" type="button" aria-expanded={leftPanelOpen} aria-controls="research-sidebar" aria-label={leftPanelOpen ? t("隐藏列表") : t("显示列表")} title={leftPanelOpen ? t("隐藏列表") : t("显示列表")} onClick={() => { setLeftPanelOpen((open) => !open); if (compactViewport) setRightPanelOpen(false); }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M9 4v16"/></svg>
          </button>
          <a
            className="workspace-brand-lockup"
            href={`/landing?lang=${locale}`}
            aria-label={t("返回 OpenAshare 首页")}
          >
            <span className="workspace-brand-mark">
              <Image src="/favicon.svg" alt="OpenAshare" width={44} height={44} priority />
            </span>
            <div>
              <strong>OpenAshare</strong>
              <span>{t("研究工作台")}</span>
            </div>
          </a>
        </div>
        <div className="workspace-header-status">
          <button className="workspace-icon-button" type="button" aria-expanded={rightPanelOpen} aria-controls="research-drawer" onClick={() => { const open = !rightPanelOpen; setRightPanelOpen(open); if (compactViewport) setLeftPanelOpen(false); else updatePreferences({showResearchPanel: open}); }}>
            {rightPanelOpen ? (locale === "en" ? "Hide panel" : "隐藏面板") : (locale === "en" ? "Show panel" : "显示面板")}
          </button>
        </div>
      </header>

      {labMode ? <AgentLabBar traces={labTraces} onClear={() => setLabTraces([])} /> : null}

      <div ref={gridRef} inert={settingsOpen} style={{ "--workspace-left-width": `${panelSizes.left}px`, "--workspace-right-width": `${panelSizes.right}px` } as CSSProperties} className={`workspace-grid ${leftPanelOpen ? "left-open" : "left-closed"} ${rightPanelOpen ? "right-open" : "right-closed"}`}>
        {leftPanelOpen ? (
          <aside id="research-sidebar" className="workspace-left-panel" aria-label={t("自选股和会话")}>
            <div className="workspace-panel-heading">
              <div>
                <span className="workspace-kicker">{t("研究工作台")}</span>
                <h1>{t("我的研究")}</h1>
              </div>
              <button className="workspace-round-button" type="button" onClick={createSession} aria-label={t("新建对话")}>
                +
              </button>
            </div>

            <WorkspaceTools activeType={activeContext?.type} onOpen={openResearchTool} />

            <form className="workspace-watch-search" onSubmit={addWatchItem}>
              <span aria-hidden="true">⌕</span>
              <input
                disabled={watchlistBusy || !watchlistLoaded}
                value={watchlistInput}
                onChange={(event) => setWatchlistInput(event.target.value)}
                placeholder={t("添加股票或代码")}
                aria-label={t("添加股票或代码")}
              />
            </form>
            {watchlistError ? <p className="workspace-empty-copy" role="alert">{watchlistError}</p> : null}

            <section className="workspace-list-section">
              <div className="workspace-section-heading">
                <span>{t("自选股")}</span>
                <span className="workspace-count">{watchlist.length}</span>
              </div>
              <div className="workspace-watchlist">
                {watchlist.map((item) => (
                  <div className={`workspace-watch-item ${selectedSymbol === item.code ? "active" : ""}`} key={item.code}>
                    <button type="button" onClick={() => openStock(item.code, item.name)}
                      aria-current={selectedSymbol === item.code ? "true" : undefined}
                      title={`${t(isUnknownStockName(item.name) ? item.code : item.name)} · ${item.code.toUpperCase()}`}>
                      <span className="workspace-watch-symbol">{item.code.toUpperCase()}</span>
                      <span className="workspace-watch-name">{t(isUnknownStockName(item.name) ? item.code : item.name)}</span>
                    </button>
                    <button
                      type="button"
                      className="workspace-remove-button"
                      disabled={watchlistBusy || !watchlistLoaded}
                      onClick={() => removeWatchItem(item.code)}
                      aria-label={`${locale === "en" ? "Remove" : "移除"} ${t(isUnknownStockName(item.name) ? item.code : item.name)}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </section>

            <section className="workspace-list-section workspace-project-section">
              <div className="workspace-section-heading workspace-project-heading">
                <span>{t("项目")}</span>
                <button
                  type="button"
                  className="workspace-project-add"
                  aria-label={t("建立项目")}
                  aria-expanded={projectComposerOpen}
                  onClick={() => setProjectComposerOpen((open) => !open)}
                >
                  +
                </button>
              </div>
              {projectComposerOpen ? (
                <form className="workspace-project-composer" onSubmit={createProject}>
                  <input
                    value={projectDraft}
                    onChange={(event) => setProjectDraft(event.target.value)}
                    placeholder={t("例如：新能源产业链")}
                    aria-label={t("项目名称")}
                    autoFocus
                  />
                  <button type="submit">{t("建立")}</button>
                </form>
              ) : null}
              {projects.length > 0 ? <div className="workspace-project-list" aria-label={t("项目筛选")}>
                <button
                  className={`workspace-project-item ${activeProjectId === "all" ? "active" : ""}`}
                  type="button"
                  onClick={() => setActiveProjectId("all")}
                >
                  <span>{t("全部对话")}</span>
                  <b>{sessions.length}</b>
                </button>
                <button
                  className={`workspace-project-item ${activeProjectId === "unassigned" ? "active" : ""}`}
                  type="button"
                  onClick={() => setActiveProjectId("unassigned")}
                >
                  <span>{t("未归类")}</span>
                  <b>{sessions.filter((session) => !sessionProjects[session.id]).length}</b>
                </button>
                {projects.map((project) => (
                  <button
                    className={`workspace-project-item ${activeProjectId === project.id ? "active" : ""}`}
                    type="button"
                    key={project.id}
                    onClick={() => setActiveProjectId(project.id)}
                    onContextMenu={(event) => openProjectMenu(event, project)}
                    title={project.name}
                  >
                    <span>{project.name}</span>
                    <b>{projectSessionCount(project.id)}</b>
                  </button>
                ))}
              </div> : null}
            </section>

            <section className="workspace-list-section workspace-conversation-section">
              <div className="workspace-section-heading">
                <span>{!projects.length || activeProjectId === "all" ? t("最近会话") : activeProjectId === "unassigned" ? t("未归类对话") : t("项目对话")}</span>
                <span className="workspace-count">{visibleSessions.length}</span>
              </div>
              <div className="workspace-session-list">
                {visibleSessions.map((session) => (
                  <button
                    className={`workspace-session-item ${activeSessionId === session.id ? "active" : ""}`}
                    type="button"
                    key={session.id}
                    onClick={() => selectSession(session.id)}
                    onContextMenu={(event) => openSessionMenu(event, session)}
                  >
                    <span className="workspace-session-title">{session.pinned ? "✦ " : ""}{session.title === "新对话" ? t("未命名对话") : session.title}</span>
                    <span className="workspace-session-time">{formatRelativeTime(session.updatedAt, locale)}</span>
                  </button>
                ))}
                {!visibleSessions.length ? <p className="workspace-empty-copy">{t(!projects.length || activeProjectId === "all" ? "暂无历史对话" : "这个项目还没有对话。点击右键可移动已有对话，或新建一个。")}</p> : null}
              </div>
            </section>

            <div className="workspace-left-footer">
              <div className="workspace-account-menu" ref={accountMenuRef}>
                {accountMenuOpen ? (
                  <div className="workspace-account-popover" role="dialog" aria-label={t("账户菜单")}>
                    <div className="workspace-account-popover-head">
                      <span className="workspace-avatar workspace-avatar--large">P</span>
                      <div className="workspace-account-copy">
                        <strong>Peter</strong>
                        <span>{t("个人研究空间")}</span>
                      </div>
                    </div>
                    <button type="button" className="workspace-account-settings" onClick={() => { setAccountMenuOpen(false); setSettingsOpen(true); }}>{locale === "en" ? "Settings" : "设置"}<span aria-hidden="true">↗</span></button>
                    <SupabaseAuthPanel placement="profile" onAuthChange={handleSupabaseAuth} />
                    <p className="workspace-account-status">{cloudStatus === "connected" ? t("云端已连接") : cloudStatus === "syncing" ? t("同步中") : cloudStatus === "error" ? t("云端同步未完成") : t("本地模式")}</p>
                    {cloudError ? <p className="workspace-account-status">{t("使用本地记录")}</p> : null}
                    <p className="workspace-account-status">{creditBalance?.unlimited ? t("本地模式 · Credits 不限") : `${creditBalance?.balance ?? "—"} Credits`}</p>
                  </div>
                ) : null}
                <button
                  type="button"
                  className={`workspace-account-trigger ${accountMenuOpen ? "open" : ""}`}
                  aria-expanded={accountMenuOpen}
                  aria-haspopup="dialog"
                  onClick={() => setAccountMenuOpen((open) => !open)}
                >
                  <span className="workspace-account-card">
                    <span className="workspace-avatar">P</span>
                    <span className="workspace-account-copy">
                      <strong>Peter</strong>
                      <span>{t("个人研究空间")}</span>
                    </span>
                  </span>
                  <span className="workspace-account-menu-icon" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </span>
                </button>
              </div>
            </div>
          </aside>
        ) : null}

        <section className="workspace-chat-panel" aria-label={t("Agent 对话")} inert={compactViewport && (leftPanelOpen || rightPanelOpen)}>
          <AgentChat
            compact
            workspace
            onSessionsChange={handleSessionsChange}
            onCurrentSessionChange={setActiveSessionId}
            onContextUpdate={handleContextUpdate}
            onLabTrace={labMode ? handleLabTrace : undefined}
            onCreditUpdate={(usage) => {
              if (usage.remaining == null || usage.unlimited) return;
              setCreditBalance((current) => current ? {
                ...current,
                balance: usage.remaining ?? current.balance,
                lifetime_used: current.lifetime_used + usage.charged,
              } : current);
            }}
          />
        </section>

        {rightPanelOpen ? (
          <aside id="research-drawer" className="workspace-right-panel" aria-label={t("研究上下文")}>
            <ResearchContextPanel
              context={activeContext}
              pinned={Boolean(pinnedContext)}
              onTogglePin={() => setPinnedContext((current) => (current ? null : activeContext))}
              onSelectStock={openStock}
              onClose={closeResearchContext}
              onOpenTool={openResearchTool}
              watchlist={watchlist}
              watchlistBusy={watchlistBusy || !watchlistLoaded}
              watchlistError={watchlistError}
              onToggleWatch={toggleWatchItem}
            />
          </aside>
        ) : null}
        {!compactViewport && leftPanelOpen ? <WorkspacePanelResizer side="left" width={panelSizes.left} max={Math.min(panelLimits.left.max, Math.max(panelLimits.left.min, gridWidth - panelSizes.right - 360))} onResize={width => resizePanel("left", width)} onCommit={width => resizePanel("left", width, true)} /> : null}
        {!compactViewport && rightPanelOpen ? <WorkspacePanelResizer side="right" width={panelSizes.right} max={Math.min(panelLimits.right.max, Math.max(panelLimits.right.min, gridWidth - panelSizes.left - 360))} onResize={width => resizePanel("right", width)} onCommit={width => resizePanel("right", width, true)} /> : null}
      </div>

      {settingsOpen ? <WorkspaceSettings onClose={closeSettings} /> : null}

      {sessionMenu ? (
        <div
          className="workspace-session-menu"
          ref={sessionMenuRef}
          role="menu"
          aria-label={t("对话操作")}
          style={{ left: sessionMenu.x, top: sessionMenu.y }}
        >
          {sessionMenu.renaming ? (
            <form className="workspace-session-rename" onSubmit={renameSession}>
              <label htmlFor="workspace-session-rename-input">{t("对话名称")}</label>
              <input
                id="workspace-session-rename-input"
                value={renameDraft}
                onChange={(event) => setRenameDraft(event.target.value)}
                placeholder={t("输入新名称")}
                autoFocus
              />
              <div>
                <button type="button" onClick={() => setSessionMenu(null)}>{t("取消")}</button>
                <button type="submit">{t("保存")}</button>
              </div>
            </form>
          ) : (
            <>
              <button
                type="button"
                role="menuitem"
                onClick={() => setSessionMenu((current) => current ? { ...current, renaming: true } : current)}
              >{t("重命名对话")}</button>
              <div className="workspace-session-menu-group">
                <span>{t("移动到项目")}</span>
                <button type="button" role="menuitem" onClick={() => moveSessionToProject(sessionMenu.sessionId, null)}>{t("未归类")}</button>
                {projects.map((project) => (
                  <button
                    type="button"
                    role="menuitem"
                    key={project.id}
                    onClick={() => moveSessionToProject(sessionMenu.sessionId, project.id)}
                  >
                    {project.name}
                  </button>
                ))}
                {!projects.length ? <em>{t("先建立一个项目")}</em> : null}
              </div>
              <button
                type="button"
                role="menuitem"
                className="workspace-session-menu-delete"
                onClick={() => deleteSession(sessionMenu.sessionId)}
              >{t("删除对话")}</button>
            </>
          )}
        </div>
      ) : null}

      {projectMenu ? (
        <div
          className="workspace-project-menu"
          ref={projectMenuRef}
          role="menu"
          aria-label={t("项目操作")}
          style={{ left: projectMenu.x, top: projectMenu.y }}
        >
          {projectMenu.renaming ? (
            <form className="workspace-session-rename" onSubmit={renameProject}>
              <label htmlFor="workspace-project-rename-input">{t("项目名称")}</label>
              <input
                id="workspace-project-rename-input"
                value={projectRenameDraft}
                onChange={(event) => setProjectRenameDraft(event.target.value)}
                placeholder={t("输入项目名称")}
                autoFocus
              />
              <div>
                <button type="button" onClick={() => setProjectMenu(null)}>{t("取消")}</button>
                <button type="submit">{t("保存")}</button>
              </div>
            </form>
          ) : (
            <>
              <button
                type="button"
                role="menuitem"
                onClick={() => setProjectMenu((current) => current ? { ...current, renaming: true } : current)}
              >{t("重命名项目")}</button>
              <button
                type="button"
                role="menuitem"
                className="workspace-session-menu-delete"
                onClick={() => deleteProject(projectMenu.projectId)}
              >{t("删除项目")}</button>
              <p>{t("项目内对话将保留到“未归类”。")}</p>
            </>
          )}
        </div>
      ) : null}
    </main>
  );
}

function ResearchContextPanel({
  context,
  pinned,
  onTogglePin,
  onSelectStock,
  onClose,
  onOpenTool,
  watchlist, watchlistBusy, watchlistError, onToggleWatch,
}: {
  context: ResearchContext | null;
  pinned: boolean;
  onTogglePin: () => void;
  onSelectStock: (code: string, name?: string) => void;
  watchlist: WatchItem[];
  watchlistBusy: boolean;
  watchlistError: string;
  onToggleWatch: (code: string) => Promise<void>;
  onClose: () => void;
  onOpenTool: (type: "stock" | "news" | "portfolio" | "market") => void;
}) {
  const { t, locale } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [stock, setStock] = useState<StockAnalysisResponse | null>(null);
  const [resolvedStockName, setResolvedStockName] = useState<string | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [hotspot, setHotspot] = useState<HotspotDetailResponse | null>(null);
  const [market, setMarket] = useState<MarketRegimeResponse | null>(null);
  const [globalNews, setGlobalNews] = useState<GlobalNewsItem[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioAnalysisResponse | null>(null);
  const [error, setError] = useState("");
  const { preferences, updatePreferences } = useWorkspacePreferences();
  const marketScope = preferences.market;
  const hasGeneralMarketFeed = globalNews.some(item => item.raw_payload?.general_feed_available === true);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      const inToolMenu = event.target instanceof Element && event.target.closest('.workspace-tool-shortcuts, [role="menu"]');
      if (event.key === "Escape" && !event.defaultPrevented && !inToolMenu && !document.querySelector('[aria-modal="true"]')) {
        onClose();
      }
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    setError("");
    setStock(null);
    setResolvedStockName(null);
    setNews([]);
    setHotspot(null);
    setMarket(null);
    setGlobalNews([]);
    setPortfolio(null);

    if (!context || (context.type === "stock" && !context.entityId)) {
      setLoading(false);
      return;
    }

    setLoading(true);
    const load = async () => {
      try {
        if (context.type === "stock" && context.entityId) {
          const requestedSymbol = context.entityId;
          const payloadStock = payloadToStock(context.payload);
          let searchResults: Awaited<ReturnType<typeof searchStocks>> = [];
          try {
            searchResults = await searchStocks(requestedSymbol);
          } catch {
            // A temporary search outage should not block a request that already has a code.
          }
          const exactMatch = searchResults.find((item) =>
            item.match_type !== "code_validation" &&
            !isUnknownStockName(item.name) &&
            (item.code.toLowerCase() === requestedSymbol.toLowerCase() ||
              item.name.trim().toLowerCase() === requestedSymbol.trim().toLowerCase()),
          );
          const stockCode = exactMatch?.code ?? payloadStock?.stock_code ?? requestedSymbol;
          const payloadName = payloadStock?.stock_name;
          const stockName = exactMatch?.name ?? (payloadName && !isUnknownStockName(payloadName) ? payloadName : undefined);
          if (stockName && stockName !== stockCode) setResolvedStockName(stockName);
          const [analysis, relatedNews] = await Promise.all([
            getStockAnalysis(stockCode, { includeAi: false, language: locale === "en" ? "en-US" : "zh-CN" }),
            getStockNews(stockCode),
          ]);
          if (!cancelled) {
            setStock(analysis);
            setResolvedStockName(isUnknownStockName(analysis.stock_name) ? null : analysis.stock_name);
            setNews(relatedNews);
          }
        } else if (context.type === "topic" && context.entityId) {
          const detail = await getHotspotDetail(context.entityId);
          if (!cancelled) setHotspot(detail);
        } else if (context.type === "news") {
          const items = marketScope === "hk" ? [] : await getGlobalNews(marketScope === "us" ? "us" : "global");
          if (!cancelled) setGlobalNews(items);
        } else if (context.type === "portfolio") {
          const analysis = await getPortfolioAnalysis({language: locale === "en" ? "en-US" : "zh-CN"});
          if (!cancelled) setPortfolio(analysis ?? null);
        } else {
          for (let attempt = 0; attempt < 16 && !cancelled; attempt++) {
            const regime = await getMarketRegime({market: marketScope, language: locale === "en" ? "en-US" : "zh-CN"});
            if (cancelled) return;
            setMarket(regime);
            setLoading(false);
            if (!regime.is_loading) break;
            if (attempt === 15) throw new Error(locale === "en" ? "Data retrieval is taking longer than expected. Retry when the provider is available." : "数据获取耗时较长，请稍后重试。");
            await new Promise(resolve => setTimeout(resolve, 1500));
          }
        }
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : locale === "en" ? "Research data is temporarily unavailable." : "研究数据暂时不可用");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [context, locale, marketScope, reload]);

  const contextStock = context?.type === "stock" ? payloadToStock(context.payload) : null;
  const contextStockCode = stock?.stock_code ?? contextStock?.stock_code ?? context?.entityId;
  const analysisName = stock?.stock_name && stock.stock_name !== stock.stock_code && !isUnknownStockName(stock.stock_name)
    ? stock.stock_name
    : undefined;
  const watchlistName = watchlist.find(item => item.code.toUpperCase() === contextStockCode?.toUpperCase())?.name;
  const contextStockName = analysisName ?? (watchlistName && !isUnknownStockName(watchlistName) ? watchlistName : undefined)
    ?? (resolvedStockName && !isUnknownStockName(resolvedStockName) ? resolvedStockName : undefined);
  const contextTitle = context?.type === "stock"
    ? contextStockCode
      ? contextStockName && contextStockName !== contextStockCode
        ? `${contextStockName} · ${contextStockCode}`
        : contextStockCode
      : locale === "en" ? "Stock research" : "股票研究"
    : context?.title ?? (locale === "en" ? "Research tools" : "研究工具");
  const newsCoverageMessage = marketScope === "hk"
    ? (locale === "en" ? "Hong Kong news coverage is unavailable with the current provider." : "当前数据源暂不支持港股新闻。")
    : marketScope === "us"
      ? hasGeneralMarketFeed
        ? (locale === "en" ? "General market headlines plus selected-company news. Company links require a direct source mention." : "综合市场新闻与所选公司新闻。只有来源原文明确提及公司时才建立关联。")
        : (locale === "en" ? "Company headlines only; wider market coverage depends on provider availability." : "当前仅有公司新闻；综合市场覆盖取决于数据源是否可用。")
      : globalNews.length
        ? (locale === "en" ? "China-provider headlines, shown in the source's original language." : "中国资讯提供方的原文新闻。")
        : "";

  return (
    <div className={`research-context-panel ${context?.type === "stock" ? "stock-research-panel" : ""}`}>
      <div className="research-context-head">
        <div>
          <span className="workspace-kicker">Live context</span>
          <h2>{t(contextTitle)}</h2>
        </div>
        <div className="research-drawer-actions"><button
          type="button"
          className={`workspace-context-action ${pinned ? "active" : ""}`}
          onClick={onTogglePin}
          aria-label={pinned ? t("取消固定研究上下文") : t("固定当前研究上下文")}
          aria-pressed={pinned}
          disabled={!context}
        >
          {pinned ? "◆" : "◇"}
        </button>
        <button type="button" className="workspace-context-action" aria-label={locale === "en" ? "Close context" : "关闭资料"} onClick={onClose}>×</button></div>
      </div>

      {context ? <div className="research-tool-picker"><select aria-label={t("研究工具")} value={context?.type === "topic" ? "topic" : context?.type ?? ""} onChange={e => onOpenTool(e.target.value as "stock" | "news" | "portfolio" | "market")}>
        <option value="" disabled>{locale === "en" ? "Choose a research tool" : "选择研究工具"}</option>
        {context?.type === "topic" ? <option value="topic" disabled>{locale === "en" ? "Current context" : "当前资料"}</option> : null}
        {(["stock","news","portfolio","market"] as const).map(type => <option key={type} value={type}>{t({stock:"股票",news:"新闻与催化",portfolio:"我的持仓",market:"市场概览"}[type])}</option>)}
      </select>
      {context?.type === "market" || context?.type === "news" ? <select aria-label={locale === "en" ? "Market" : "市场"} value={marketScope} onChange={e => updatePreferences({market: e.target.value as typeof marketScope})}>
        <option value="us">{locale === "en" ? "United States" : "美股"}</option><option value="a_share">{locale === "en" ? "China A-shares" : "A股"}</option><option value="hk">{locale === "en" ? "Hong Kong" : "港股"}</option>
      </select> : null}</div> : null}

      {!context ? <EmptyResearchContext onOpen={onOpenTool} /> : null}
      {loading ? <ContextLoading /> : null}
      {error ? <div className="research-error" role="alert">{error}<button type="button" onClick={() => setReload(v => v+1)}>{locale === "en" ? "Retry" : "重试"}</button></div> : null}
      {!loading && !error && context?.type === "stock" && !context.entityId ? (
        <div className="research-empty-state"><h3>{locale === "en" ? "Choose a stock to research" : "选择一只股票开始研究"}</h3><p>{locale === "en" ? "Select a saved stock or search for a ticker in the left panel." : "请从左侧自选股中选择，或搜索代码后添加。"}</p></div>
      ) : null}
      {!loading && !error && context?.type === "stock" && context.entityId ? (
        <StockContext analysis={stock} news={news} fallback={payloadToStock(context.payload)} displayName={contextStockName ?? undefined} onSelectStock={onSelectStock} watched={watchlist.some(item => item.code.toUpperCase() === contextStockCode?.toUpperCase())} watchlistBusy={watchlistBusy} watchlistError={watchlistError} onToggleWatch={onToggleWatch} />
      ) : null}
      {!loading && !error && context?.type === "topic" ? <TopicContext detail={hotspot} /> : null}
      {!loading && !error && context?.type === "market" ? <MarketContext market={market} /> : null}
      {!loading && !error && context?.type === "portfolio" ? <PortfolioContext portfolio={portfolio} /> : null}
      {!loading && !error && context?.type === "news" ? (
        <div className="research-context-content">
          {newsCoverageMessage ? <p className="research-coverage">{newsCoverageMessage}</p> : null}
          {globalNews.length ? globalNews.map(item => (
            <article key={item.id} className="research-news-item">
              <SourceHeadline title={item.title} url={item.url} />
              <span>{item.source} · {item.published_at}</span>
              {marketScope === "us" ? <small>{item.related_symbols.length
                ? `${locale === "en" ? "Source mentions" : "原文提及"}: ${item.related_symbols.join(", ")}`
                : (locale === "en" ? "Market-wide headline" : "市场综合新闻")}</small> : null}
              <p>{item.summary}</p>
            </article>
          )) : <p>{locale === "en" ? "No news available from the current provider." : "当前数据源暂无新闻。"}</p>}
        </div>
      ) : null}
    </div>
  );
}

function StockContext({
  analysis,
  news,
  fallback,
  displayName,
  onSelectStock,
  watched, watchlistBusy, watchlistError, onToggleWatch,
}: {
  analysis: StockAnalysisResponse | null;
  news: NewsItem[];
  fallback: StockAnalysisResponse | null;
  displayName?: string;
  onSelectStock: (code: string, name?: string) => void;
  watched: boolean;
  watchlistBusy: boolean;
  watchlistError: string;
  onToggleWatch: (code: string) => Promise<void>;
}) {
  const { t, locale } = useLanguage();
  const [chartExpanded, setChartExpanded] = useState(false);
  const [range, setRange] = useState("1Y");
  const [selectedSegment, setSelectedSegment] = useState<ChartSegment | null>(null);
  const [annotationPrompt, setAnnotationPrompt] = useState("");
  const [annotationOpen, setAnnotationOpen] = useState(false);
  const [annotations, setAnnotations] = useState<ChartAnnotation[]>([]);
  const [annotationId, setAnnotationId] = useState<string | null>(null);
  const [annotationError, setAnnotationError] = useState("");
  const [chartType, setChartType] = useState<"candles" | "line">("candles");
  const chartDialogRef = useRef<HTMLDivElement>(null);
  const expandButtonRef = useRef<HTMLButtonElement>(null);
  const data = analysis ?? fallback;
  const fullSeries = useMemo(() => orderedChartBars(data?.chart_series ?? []), [data?.chart_series]);
  const previewCleanupRef = useRef<(() => void) | null>(null);
  const [previewDates, setPreviewDates] = useState<{ from: string; to: string } | null>(null);
  const handlePreviewChartReady = useCallback((chart: IChartApi | null) => {
    previewCleanupRef.current?.(); previewCleanupRef.current = null;
    if (!chart || !fullSeries.length) return;
    const scale = chart.timeScale();
    const update = () => {
      const current = scale.getVisibleLogicalRange();
      if (!current) return;
      const visible = clampChartWindow(current, fullSeries.length);
      setPreviewDates({ from: fullSeries[Math.floor(visible.from)]?.date ?? fullSeries[0].date, to: fullSeries[Math.min(fullSeries.length - 1, Math.ceil(visible.to))]?.date ?? fullSeries.at(-1)!.date });
    };
    scale.subscribeVisibleLogicalRangeChange(update);
    scale.setVisibleLogicalRange(presetChartWindow(fullSeries, ({ "1M": 1, "3M": 3, "6M": 6, "1Y": 12 } as Record<string, number>)[range] ?? null));
    update();
    previewCleanupRef.current = () => scale.unsubscribeVisibleLogicalRangeChange(update);
  }, [fullSeries, range]);
  const annotationStorageKey = `openashare.chart.annotations.v1.${data?.stock_code ?? ""}`;
  useEffect(() => {
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(annotationStorageKey) ?? "[]");
      setAnnotations(Array.isArray(saved) ? saved.filter((item): item is ChartAnnotation => item && typeof item.id === "string" && typeof item.startDate === "string" && typeof item.endDate === "string" && typeof item.note === "string").slice(-50) : []);
      setAnnotationError("");
    } catch { setAnnotations([]); }
  }, [annotationStorageKey]);
  useEffect(() => {
    if (!chartExpanded) return;
    const dialog = chartDialogRef.current;
    const trigger = expandButtonRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog?.querySelector<HTMLButtonElement>("button")?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopImmediatePropagation();
        setChartExpanded(false);
      }
      if (event.key === "Tab" && dialog) {
        const elements = Array.from(dialog.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input, select, textarea, [tabindex="0"]'));
        const first = elements[0], last = elements.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener("keydown", handleKey, true);
    return () => { document.removeEventListener("keydown", handleKey, true); document.body.style.overflow = previousOverflow; trigger?.focus(); };
  }, [chartExpanded]);
  if (!data) return <div className="research-empty-state">{t("等待股票研究结果…")}</div>;
  const stockCode = data.stock_code;
  const direction = data.quote.change_pct >= 0 ? "up" : "down";
  const currency = data.market === "us" ? "USD" : data.market === "hk" ? "HKD" : "CNY";
  const series = fullSeries;
  const asOf = String(data.metadata?.data_as_of ?? series.at(-1)?.date ?? (locale === "en" ? "Date unknown" : "日期未知"));
  const chartData = filterChartRange(series, range);
  const chartName = displayName ?? data.stock_name;

  function showExpandedChart() {
    setSelectedSegment(null);
    setAnnotationOpen(false);
    setChartExpanded(true);
  }

  function annotateSegment(segment: ChartSegment) {
    setSelectedSegment(segment);
    setAnnotationId(null);
    setAnnotationError("");
    setAnnotationPrompt(locale === "en"
      ? `Please explain the main drivers of ${chartName} (${stockCode}) during ${segment.label} (${segment.startDate} to ${segment.endDate}), including relevant company news, filings, earnings or market catalysts.`
      : `请帮我分析 ${chartName}（${stockCode}）在 ${segment.label}（${segment.startDate} 至 ${segment.endDate}）这段时间的主要涨跌原因，并结合期间相关的新闻、公告、财报或市场催化因素。`);
    setAnnotationOpen(true);
  }

  function saveAnnotation() {
    if (!selectedSegment || !annotationPrompt.trim()) return;
    const note: ChartAnnotation = { id: annotationId ?? crypto.randomUUID(), startDate: selectedSegment.startDate, endDate: selectedSegment.endDate, note: annotationPrompt.trim().slice(0, 2000) };
    const next = [...annotations.filter(item => item.id !== note.id), note].slice(-50);
    try {
      localStorage.setItem(annotationStorageKey, JSON.stringify(next));
      setAnnotations(next); setAnnotationOpen(false); setAnnotationError("");
    } catch { setAnnotationError(locale === "en" ? "This browser could not save the annotation. Your text is still here." : "浏览器无法保存标注，输入的内容仍保留在这里。"); }
  }

  function deleteAnnotation() {
    if (!annotationId) return;
    const next = annotations.filter(item => item.id !== annotationId);
    try { localStorage.setItem(annotationStorageKey, JSON.stringify(next)); setAnnotations(next); setAnnotationOpen(false); }
    catch { setAnnotationError(locale === "en" ? "This browser could not remove the annotation." : "浏览器无法移除这条标注。"); }
  }

  function sendSegmentQuestion() {
    if (!selectedSegment || !annotationPrompt.trim()) return;
    const context = buildChartSegmentContext(chartName, stockCode, selectedSegment, locale);
    window.dispatchEvent(new CustomEvent(AGENT_LAB_RUN_EVENT, {
      detail: { prompt: annotationPrompt.trim(), context },
    }));
    setAnnotationOpen(false);
    setChartExpanded(false);
  }
  const metrics = [
    [locale === "en" ? "Volume · shares" : "成交量 · 股", formatQuantity(data.quote.volume, locale)],
    [t("振幅"), `${data.quote.amplitude_pct.toFixed(2)}%`],
    ["MA20", formatIndicatorValue(data.technical_indicators.MA20)],
    ["MACD", formatIndicatorValue(data.technical_indicators.MACD)],
    ["RSI (14)", formatIndicatorValue(data.technical_indicators.RSI)],
    ["MA60", formatIndicatorValue(data.technical_indicators.MA60)],
  ];
  if (data.market !== "us") metrics[0][0] = locale === "en" ? "Volume · source units" : "成交量 · 来源单位";
  return (
    <div className="research-context-content stock-research-content">
      <div className="stock-quote-header">
        <div className="research-quote-row">
          <div><span className="research-label">{t("最新价")} · {currency}</span><strong className="research-price">{data.quote.current_price.toFixed(2)}</strong></div>
          <div className={`research-change ${direction}`}>{data.quote.change_pct >= 0 ? "+" : ""}{data.quote.change_pct.toFixed(2)}%</div>
        </div>
        <div className="stock-quote-caption"><button type="button" className="stock-watch-button" disabled={watchlistBusy} aria-pressed={watched} aria-label={watched ? (locale === "en" ? "Remove from watchlist" : "移出自选股") : (locale === "en" ? "Add to watchlist" : "加入自选股")} onClick={() => { void onToggleWatch(data.stock_code); }}><span aria-hidden="true">{watched ? "★" : "☆"}</span>{watched ? (locale === "en" ? "Watching" : "已关注") : (locale === "en" ? "Watch" : "关注")}</button><span>{locale === "en" ? "Delayed daily data" : "延迟日线"} · {asOf}</span></div>
        {watchlistError ? <p className="stock-watch-error" role="alert">{watchlistError}</p> : null}
      </div>
      {series.length ? <section className="stock-chart-surface" aria-label={locale === "en" ? "Price chart" : "价格图表"}>
        <div className="stock-chart-toolbar">
          <div className="stock-chart-ranges" role="group" aria-label={locale === "en" ? "Chart date range" : "图表时间范围"}>{["1M", "3M", "6M", "1Y", "ALL"].map(value => <button type="button" key={value} aria-pressed={range === value} onClick={() => setRange(value)}>{locale === "en" ? (value === "ALL" ? "All" : value) : ({ "1M": "1月", "3M": "3月", "6M": "6月", "1Y": "1年", "ALL": "全部" }[value])}</button>)}</div>
          <div className="stock-chart-view"><select aria-label={locale === "en" ? "Chart type" : "图表类型"} value={chartType} onChange={event => setChartType(event.target.value as typeof chartType)}><option value="candles">{locale === "en" ? "Candles" : "K线"}</option><option value="line">{locale === "en" ? "Line" : "折线"}</option></select><button ref={expandButtonRef} type="button" aria-label={t("展开 K 线")} title={t("展开 K 线")} onClick={showExpandedChart}>↗</button></div>
        </div>
        <CandlestickChart data={series} height={260} surface chartType={chartType} onReady={handlePreviewChartReady} />
        <div className="stock-chart-caption"><span>{previewDates?.from ?? chartData[0]?.date.slice(0, 10)} — {previewDates?.to ?? chartData.at(-1)?.date.slice(0, 10)}</span><span>{currency} · {locale === "en" ? "Daily" : "日线"}</span></div>
      </section> : <p className="research-muted">{locale === "en" ? "Price history unavailable." : "历史价格暂不可用。"}</p>}
      {chartExpanded && series.length ? createPortal(<div className="research-chart-overlay" role="dialog" aria-modal="true" aria-label={`${chartName} · ${t("K 线")}`} onClick={event => { if (event.target === event.currentTarget) setChartExpanded(false); }}>
        <div ref={chartDialogRef} className="research-chart-dialog">
          <div className="research-chart-dialog-head">
            <div><span className="workspace-kicker">{locale === "en" ? "Price history" : "历史价格"}</span><h3>{chartName === data.stock_code ? data.stock_code : `${chartName} · ${data.stock_code}`}<small className="research-chart-available-history">{series[0]?.date} — {series.at(-1)?.date} · {locale === "en" ? "available daily history" : "可用日线历史"}</small></h3></div>
            <button type="button" className="workspace-context-action" onClick={() => setChartExpanded(false)} aria-label={t("关闭 K 线图")}>×</button>
          </div>
          <ResearchChart
            data={series}
            height={600}
            fill
            symbol={data.stock_code}
            sourceIndicators={data.technical_indicators}
            periodSelection={{ selected: selectedSegment, onSelect: segment => { setSelectedSegment(segment); setAnnotationOpen(false); }, onAnnotate: annotateSegment }}
            annotations={annotations}
            onAnnotationSelect={(annotation, segment) => { setSelectedSegment(segment); setAnnotationId(annotation.id); setAnnotationPrompt(annotation.note); setAnnotationOpen(true); setAnnotationError(""); }}
          />
          {annotationOpen && selectedSegment ? <form className="research-chart-annotation" onSubmit={event => { event.preventDefault(); sendSegmentQuestion(); }}>
            <header><strong>{locale === "en" ? "Period annotation" : "区间标注"}</strong><button type="button" className="workspace-context-action" aria-label={locale === "en" ? "Close annotation" : "关闭标注"} onClick={() => setAnnotationOpen(false)}>×</button></header>
            <p>{selectedSegment.startDate} — {selectedSegment.endDate}</p>
            <label htmlFor="research-chart-question">{locale === "en" ? "Your note or research question" : "记录你的观察或研究问题"}</label>
            <textarea autoFocus id="research-chart-question" value={annotationPrompt} onChange={event => setAnnotationPrompt(event.target.value)} rows={6} maxLength={2000} />
            <small>{locale === "en" ? "Saved notes stay in this browser. Ask the agent to research this period with the selected price data." : "保存的标注保留在本浏览器中。向 Agent 提问时，会同时附上选中区间的价格数据。"}</small>
            {annotationError ? <p role="alert">{annotationError}</p> : null}
            <div>{annotationId ? <button type="button" className="research-chart-tool muted" onClick={deleteAnnotation}>{locale === "en" ? "Delete note" : "删除标注"}</button> : null}<button type="button" className="research-chart-tool" disabled={!annotationPrompt.trim()} onClick={saveAnnotation}>{locale === "en" ? "Save note" : "保存标注"}</button><button type="submit" className="research-chart-tool active" disabled={!annotationPrompt.trim()}>{locale === "en" ? "Ask agent" : "询问 Agent"}</button></div>
          </form> : null}
        </div>
      </div>, document.body) : null}
      <dl className="stock-metrics">{metrics.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      {!!data.technical_commentary?.length && <section className="stock-observations"><h3>{t("技术观察")}</h3>{data.technical_commentary.slice(0, 2).map(item => <p key={item}>{item}</p>)}</section>}
      <section className="stock-news"><h3>{locale === "en" ? "News & market context" : "新闻与市场背景"}</h3>{news.slice(0, 3).map(item => <article className="research-news-item" key={item.id}><SourceHeadline title={item.title} url={item.url}/><span>{item.source} · {item.published_at.slice(0, 10)}</span>{item.relation_type !== "direct" ? <small>{locale === "en" ? "Market context · company link unconfirmed" : "市场背景 · 公司关联未确认"}</small> : null}</article>)}{!news.length ? <p className="research-muted">{t("暂无相关新闻")}</p> : null}</section>
      <details className="stock-data-disclosure"><summary>{locale === "en" ? "Data & sources" : "数据与来源"}<span>{String(data.metadata?.source ?? "—")}</span></summary><div className="stock-source-meta"><span>{locale === "en" ? "Data date" : "数据日期"}: {asOf}</span><span>{locale === "en" ? "Retrieved" : "获取时间"}: {String(data.metadata?.generated_at ?? "—")}</span><p>{locale === "en" ? "Historical / delayed prices. Retrieval time is not the exchange quote time. Indicators describe the full available daily series." : "历史／延迟价格；获取时间并非交易所报价时间。指标使用完整的可用日线数据。"}</p></div>{series.length ? <table className="stock-data-table"><caption>{locale === "en" ? "Latest available trading days" : "最近可用交易日"}</caption><thead><tr><th>{locale === "en" ? "Date" : "日期"}</th><th>{locale === "en" ? "Close" : "收盘"} · {currency}</th><th>{locale === "en" ? "Volume" : "成交量"}</th></tr></thead><tbody>{series.slice(-5).reverse().map(point => <tr key={point.date}><td>{point.date.slice(0, 10)}</td><td>{point.close?.toFixed(2) ?? "—"}</td><td>{point.volume == null ? "—" : formatQuantity(point.volume, locale)}</td></tr>)}</tbody></table> : null}</details>
      <button className="stock-refresh" type="button" onClick={() => onSelectStock(data.stock_code, data.stock_name)}>{locale === "en" ? "Refresh data" : "刷新数据"}<span aria-hidden="true">↻</span></button>
    </div>
  );
}

function TopicContext({ detail }: { detail: HotspotDetailResponse | null }) {
  const { t, locale } = useLanguage();
  if (!detail) return <div className="research-empty-state">{t("等待热点研究结果…")}</div>;
  return (
    <div className="research-context-content">
      <div className="research-topic-score">
        <span>{t("热度")}</span>
        <strong>{detail.topic.heat_score.toFixed(0)}</strong>
        <span className={`research-trend ${detail.topic.trend_direction}`}>{detail.topic.trend_direction}</span>
      </div>
      <p className="research-coverage">{locale === "en" ? "Mainland China theme · activity derived from news and market monitoring; not a forecast." : "A 股热点 · 基于新闻与市场监测的活跃度，并非预测。"}</p>
      <OriginalText text={detail.topic.ai_summary || detail.topic.reason}/>
      <ContextSection title={t("相关标的")}>
        {detail.topic.related_stocks.slice(0, 6).map((stock) => (
          <div className="research-stock-row" key={stock.stock_code}>
            <span><strong>{stock.stock_name}</strong><small>{stock.stock_code}</small></span>
            <OriginalText text={stock.reason}/>
          </div>
        ))}
      </ContextSection>
      <ContextSection title={t("相关消息")}>
        {detail.related_news.slice(0, 3).map((item) => <article className="research-news-item" key={item.id}><SourceHeadline title={item.title} url={item.url}/><span>{item.source} · {item.published_at}</span></article>)}
      </ContextSection>
    </div>
  );
}

function MarketContext({ market }: { market: MarketRegimeResponse | null }) {
  const { t, locale } = useLanguage();
  if (!market) return <div className="research-empty-state">{t("等待市场数据…")}</div>;
  if (market.is_loading) return <div className="research-empty-state" aria-busy="true">{t("市场数据加载中…")}</div>;
  return (
    <div className="research-context-content">
      <p className="research-coverage">{market.market === "us" ? (locale === "en" ? "US market · SPY, QQQ and DIA are ETF proxies for major equity indices, not index quotes." : "美股 · SPY、QQQ、DIA 是主要指数的 ETF 代理，并非指数报价。") : market.market === "hk" ? (locale === "en" ? "Hong Kong · Hang Seng coverage only." : "港股 · 当前仅覆盖恒生指数。") : (locale === "en" ? "China A-shares · four mainland indices." : "A股 · 四个内地指数。")}</p>
      {market.status !== "unavailable" ? <div className="research-regime-card">
        <span>{locale === "en" ? "Retrieved basket trend" : "所获取标的的趋势"}{market.status === "partial" ? (locale === "en" ? " · partial coverage" : " · 覆盖不完整") : ""}</span>
        <strong>{market.regime === "risk_on" ? (locale === "en" ? "Positive trend" : "趋势偏强") : market.regime === "risk_off" ? (locale === "en" ? "Weaker trend" : "趋势偏弱") : (locale === "en" ? "Mixed trend" : "趋势分化")}</strong>
        <small>{locale === "en" ? "Basket score" : "标的组合评分"} {market.score.toFixed(0)} / 100 · {market.action_bias}</small>
      </div> : null}
      <p className="research-summary">{market.summary || market.position_guidance}</p>
      <p className="research-freshness">{locale === "en" ? "Historical / delayed daily data. Retrieval time is not market quote time." : "历史／延迟日线。获取时间不等于行情时间。"}</p>
      <ContextSection title={market.market === "us" ? (locale === "en" ? "Index ETF proxies" : "指数 ETF 代理") : t("主要指数")}>
        {market.indices.slice(0, 5).map((index) => (
          <div className="research-market-instrument" key={index.stock_code}><div className="research-index-row"><span>{t(index.stock_name)}</span><strong className={index.change_pct >= 0 ? "up" : "down"}>{index.change_pct >= 0 ? "+" : ""}{index.change_pct.toFixed(2)}%</strong></div><small>{index.current_price.toFixed(2)} {index.currency} · {index.data_as_of ?? (locale === "en" ? "Date unknown" : "日期未知")} · {index.provider ?? (locale === "en" ? "Provider unknown" : "来源未知")}</small></div>
        ))}
      </ContextSection>
      {market.notes.map(note => <p key={note} className="research-note">{note}</p>)}
      {!!market.data_gaps?.length && <div className="research-data-gaps"><strong>{locale === "en" ? "Data gaps" : "数据缺口"}</strong>{market.data_gaps.map(gap => <p key={gap}>{gap}</p>)}</div>}
      <p className="research-freshness">{locale === "en" ? "Retrieved" : "获取时间"}: {market.updated_at ?? "—"}</p>
    </div>
  );
}

function PortfolioContext({ portfolio }: { portfolio: PortfolioAnalysisResponse | null }) {
  const { t, locale } = useLanguage();
  if (!portfolio) return <div className="research-empty-state">{t("等待持仓数据…")}</div>;
  if (!portfolio.positions.length) return <div className="research-empty-state">{locale === "en" ? "No positions yet. Add holdings before requesting a portfolio review." : "暂无持仓，添加持仓后可查看组合分析。"}</div>;
  return (
    <div className="research-context-content">
      <div className="research-metric-grid portfolio-metrics">
        <ResearchMetric label={t("总市值")} value={portfolio.aggregation_available === false ? "—" : `${portfolio.total_market_value.toFixed(2)} ${portfolio.currency ?? ""}`} />
        <ResearchMetric label={t("总盈亏")} value={portfolio.aggregation_available === false ? "—" : `${portfolio.total_pnl.toFixed(2)} ${portfolio.currency ?? ""}`} tone={portfolio.total_pnl >= 0 ? "up" : "down"} />
        <ResearchMetric label={t("收益率")} value={portfolio.aggregation_available === false ? "—" : `${portfolio.total_pnl_pct.toFixed(2)}%`} />
        <ResearchMetric label={t("技术风险")} value={t(portfolio.technical_risk)} />
      </div>
      <p className="research-coverage">{locale === "en" ? "Historical / delayed prices. Cost prices are assumed to use each instrument's trading currency. Technical signals do not cover all portfolio risks." : "历史／延迟行情。成本价默认使用各标的交易币种。技术指标并不覆盖全部组合风险。"}</p>
      {portfolio.aggregation_available === false ? <p className="research-data-gaps">{locale === "en" ? "Mixed currencies: totals are unavailable without dated FX rates. Values remain in their original currencies." : "持仓包含多个币种；缺少带日期的汇率，无法汇总。各标的保留原币种。"}</p> : null}
      <ContextSection title={t("组合提示")}>
        {portfolio.rebalance_suggestions.slice(0, 5).map((item) => <OriginalText key={item} text={item}/>)}
      </ContextSection>
      <ContextSection title={t("重点持仓")}>
        {portfolio.positions.slice(0, 6).map((item) => <div className="research-market-instrument" key={item.position.stock_code}><div className="research-index-row"><span>{item.position.stock_name} · {item.position.stock_code}</span><strong className={item.pnl >= 0 ? "up" : "down"}>{item.pnl_pct >= 0 ? "+" : ""}{item.pnl_pct.toFixed(2)}%</strong></div><small>{item.current_price.toFixed(2)} {item.currency ?? ""} · {item.data_as_of ?? (locale === "en" ? "Date unknown" : "日期未知")}</small></div>)}
      </ContextSection>
    </div>
  );
}

function ContextSection({ title, children }: { title: string; children: React.ReactNode }) {

  return <section className="research-context-section"><div className="research-section-title">{title}</div>{children}</section>;
}

function OriginalText({ text }: {text: string}) {
  const {locale} = useLanguage();
  return locale === "en" && /[\u3400-\u9fff]/.test(text)
    ? <details className="research-original-text"><summary>Original Chinese source text</summary><p>{text}</p></details>
    : <p className="research-note">{text}</p>;
}

function SourceHeadline({ title, url }: {title: string; url?: string | null}) {
  const {locale} = useLanguage();
  const safeUrl = url && /^https?:\/\//i.test(url) ? url : null;
  return <><strong title={title}>{safeUrl ? <a href={safeUrl} target="_blank" rel="noopener noreferrer">{compactHeadline(title,100)}</a> : compactHeadline(title,100)}</strong>{locale === "en" && /[\u3400-\u9fff]/.test(title) ? <small className="research-original-language">Original Chinese source</small> : null}</>;
}

function ResearchMetric({ label, value, tone }: { label: string; value: string; tone?: "up" | "down" }) {

  return <div className="research-metric"><span>{label}</span><strong className={tone ?? ""}>{value}</strong></div>;
}

function EmptyResearchContext({ onOpen }: { onOpen: (type: "stock" | "news" | "portfolio" | "market") => void }) {
  const { locale } = useLanguage();
  return <div className="research-empty-state research-empty-state--welcome"><h3>{locale === "en" ? "Open a research tool" : "打开一个研究工具"}</h3><p>{locale === "en" ? "Charts, news and your portfolio, alongside the conversation." : "在对话旁查看图表、新闻和持仓。"}</p><WorkspaceTools onOpen={onOpen} launchpad /></div>;
}

function ContextLoading() {
  const { t } = useLanguage();
  return <div className="research-loading"><span /><span /><span /><p>{t("正在整理研究上下文")}</p></div>;
}

function payloadToStock(payload: Record<string, unknown>): StockAnalysisResponse | null {
  if (!payload.quote || typeof payload.stock_code !== "string") return null;
  return payload as unknown as StockAnalysisResponse;
}

function normalizeSymbol(value: string) {
  const trimmed = value.trim();
  if (/^us\./i.test(trimmed)) return trimmed.toUpperCase();
  if (/^(sh|sz)\d{6}$/i.test(trimmed)) return trimmed.toLowerCase();
  if (/^6\d{5}$/.test(trimmed)) return `sh${trimmed}`;
  if (/^\d{6}$/.test(trimmed)) return `sz${trimmed}`;
  return trimmed;
}

function isUnknownStockName(value: string) {
  return /^未知股票(?:\s*[（(]|$)/.test(value.trim()) || /^unknown stock(?:\s*[(]|$)/i.test(value.trim());
}

function filterChartRange(series: ChartPoint[], range: string) {
  if (range === "ALL" || !series.length) return series;
  const monthCount = ({ "1M": 1, "3M": 3, "6M": 6, "1Y": 12 } as Record<string, number>)[range] ?? 12;
  const [year, month] = (series.at(-1)?.date.slice(0, 7) ?? "").split("-").map(Number);
  if (!year || !month) return series;
  const cutoff = new Date(Date.UTC(year, month - monthCount, 1)).toISOString().slice(0, 10);
  return series.filter(point => point.date.slice(0, 10) >= cutoff);
}

function buildChartSegmentContext(company: string, symbol: string, segment: ChartSegment, locale: "en" | "zh") {
  const valid = segment.points.filter(point => typeof point.close === "number" && Number.isFinite(point.close));
  const first = valid[0];
  const last = valid.at(-1);
  const highPoint = segment.points.reduce<ChartPoint | null>((best, point) =>
    point.high != null && (!best || best.high == null || point.high > best.high) ? point : best, null);
  const lowPoint = segment.points.reduce<ChartPoint | null>((best, point) =>
    point.low != null && (!best || best.low == null || point.low < best.low) ? point : best, null);
  const returnPct = first && last && first.close !== 0 ? ((last.close! / first.close!) - 1) * 100 : null;
  const volume = segment.points.reduce((sum, point) => sum + (point.volume ?? 0), 0);
  const number = (value: number | null | undefined) => value == null ? "—" : value.toFixed(2);
  const volumeText = formatQuantity(volume, locale);
  const suppliedBars = sampleChartBars(segment.points);
  const bars = suppliedBars.map(point =>
    `${point.date.slice(0, 10)}, ${number(point.open)}, ${number(point.high)}, ${number(point.low)}, ${number(point.close)}, ${point.volume == null ? "—" : Math.round(point.volume)}`,
  );
  const summary = locale === "en"
    ? `First close ${number(first?.close)}; last close ${number(last?.close)}; segment return ${returnPct == null ? "unavailable" : `${returnPct >= 0 ? "+" : ""}${returnPct.toFixed(2)}%`}; high ${number(highPoint?.high)} on ${highPoint?.date.slice(0, 10) ?? "—"}; low ${number(lowPoint?.low)} on ${lowPoint?.date.slice(0, 10) ?? "—"}; total reported volume ${volumeText}.`
    : `首个收盘价 ${number(first?.close)}；末个收盘价 ${number(last?.close)}；区间涨跌幅 ${returnPct == null ? "不可用" : `${returnPct >= 0 ? "+" : ""}${returnPct.toFixed(2)}%`}；最高价 ${number(highPoint?.high)}（${highPoint?.date.slice(0, 10) ?? "—"}）；最低价 ${number(lowPoint?.low)}（${lowPoint?.date.slice(0, 10) ?? "—"}）；区间成交量 ${volumeText}。`;
  const header = locale === "en"
    ? `Selected chart period: ${company} (${symbol}), ${segment.label} (${segment.startDate} to ${segment.endDate}).`
    : `用户选中的图表区间：${company}（${symbol}），${segment.label}（${segment.startDate} 至 ${segment.endDate}）。`;
  const dataLabel = locale === "en" ? "Daily OHLCV (date, open, high, low, close, volume):" : "每日 OHLCV 数据（日期、开盘、最高、最低、收盘、成交量）：";
  const coverage = suppliedBars.length < segment.points.length
    ? locale === "en" ? `Price details are sampled: ${suppliedBars.length} of ${segment.points.length} sessions, including the endpoints and high/low. Summary statistics use the full selected period. Samples are not consecutive bars; retrieve exact data before explaining unsampled daily moves.` : `价格明细为抽样：${segment.points.length} 个交易日中展示 ${suppliedBars.length} 个，保留起止点及最高／最低点。汇总统计使用完整选区。抽样之间不是连续 K 线；解释未展示的单日变化前请获取精确数据。`
    : "";
  const instruction = locale === "en"
    ? "Use these supplied bars as the selected-period price evidence. To explain why it moved, look for dated company news, filings, earnings, guidance, sector or market catalysts during this period. Cite sources and distinguish evidence from inference; OHLCV alone does not prove causation."
    : "请把这些日线作为用户选中区间的价格证据。解释涨跌原因时，检索该期间有日期依据的公司新闻、公告、财报、指引、行业或市场催化；引用来源，并区分事实证据与推断。仅凭 OHLCV 不能证明因果关系。";
  return [header, summary, coverage, dataLabel, ...bars, instruction].filter(Boolean).join("\n");
}

function formatIndicatorValue(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "—";
}

function formatRelativeTime(timestamp: number, locale: "zh" | "en" = "zh") {
  const diff = Math.max(0, Date.now() - timestamp);
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return locale === "en" ? "Just now" : "刚刚";
  if (minutes < 60) return locale === "en" ? `${minutes}m ago` : `${minutes}分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return locale === "en" ? `${hours}h ago` : `${hours}小时前`;
  return locale === "en" ? `${Math.floor(hours / 24)}d ago` : `${Math.floor(hours / 24)}天前`;
}
