"use client";

import { useLanguage } from "@/components/language-provider";
import { researchProgressLabel, updateToolActivity } from "@/lib/research-activity";
import { ResearchTrace, ResearchTools, ResponseTools, researchToolLabel, type ToolActivity } from "@/components/research-trace";
import { useWorkspacePreferences } from "@/components/workspace-preferences";
import { effectiveResearchMode } from "@/lib/research-availability";
import { decodeEntities } from "@/lib/i18n";
import { ResearchMarkdown } from "@/components/research-markdown";

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";

import { StockPanelLink } from "@/components/stock-panel-link";
import { ResearchChart } from "@/components/research-chart";
import { streamAgent } from "@/lib/api";
import {
  AGENT_LAB_RUN_EVENT,
  compactHeadline,
  contextFromAgentResponse,
  type AgentLabTrace,
  type ResearchContext,
  type WorkspaceSessionSummary,
} from "@/lib/workspace";
import {
  AgentHistoryTurn,
  AgentClarification,
  AgentResponse,
  GlobalNewsItem,
  HotspotItem,
  NewsItem,
  PortfolioAnalysisResponse,
  StockAnalysisResponse,
  WebSearchResult,
} from "@/lib/types";
import type { ChartPoint } from "@/components/candlestick-chart";

type Message = {
  id: string;
  role: "user" | "agent";
  content: string;
  context?: string;
  actions?: string[];
  citations?: string[];
  response?: AgentResponse;
};

export type ChatSession = {
  id: string;
  title: string;
  pinned?: boolean;
  createdAt: number;
  updatedAt: number;
  messages: Message[];
};

const DEFAULT_PROMPTS = ["分析 sh600036", "看看海光信息最近消息", "分析我的持仓并结合世界局势"];

const STORAGE_KEY = "ashare-agent-sessions-v1";

type AgentChatProps = {
  compact?: boolean;
  workspace?: boolean;
  onSessionsChange?: (sessions: WorkspaceSessionSummary[]) => void;
  onCurrentSessionChange?: (sessionId: string | null) => void;
  onContextUpdate?: (context: ResearchContext | null, initial?: boolean, openPanel?: boolean) => void;
  onLabTrace?: (trace: AgentLabTrace) => void;
  onCreditUpdate?: (usage: { charged: number; remaining?: number | null; unlimited?: boolean }) => void;
};
type StreamState = "idle" | "connecting" | "streaming" | "completed" | "error";

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createWelcomeMessage(): Message {
  return {
    id: createId("msg"),
    role: "agent",
    content: "你好，我是 Ashare Agent。可以直接问全球新闻、热点、个股和持仓。",
    actions: DEFAULT_PROMPTS,
  };
}

function createSession(title = "新对话"): ChatSession {
  const now = Date.now();
  return {
    id: createId("session"),
    title,
    createdAt: now,
    updatedAt: now,
    messages: [createWelcomeMessage()],
  };
}

export function AgentChat({
  compact = false,
  workspace = false,
  onSessionsChange,
  onCurrentSessionChange,
  onContextUpdate,
  onLabTrace,
  onCreditUpdate,
}: AgentChatProps) {
  const { t, locale } = useLanguage();
  const { preferences, deepResearchAvailable } = useWorkspacePreferences();
  const prompts = locale === "en" ? ["Research AAPL earnings using SEC filings", "Compare MSFT and AAPL financials", "Latest NVIDIA news"] : ["分析苹果最新 SEC 财报", "对比微软和苹果财务表现", "查看英伟达最近消息"];
  const promptLabels = locale === "en" ? ["Company research", "Compare financials", "News & catalysts"] : ["公司研究", "财务比较", "新闻与催化"];
  const [researchMode, setResearchMode] = useState<"quick" | "deep">(preferences.researchMode);
  useEffect(() => setResearchMode(preferences.researchMode), [preferences.researchMode]);
  const [streamedAnswer, setStreamedAnswer] = useState("");
  const [toolActivity, setToolActivity] = useState<ToolActivity[]>([]);
  const followBottomRef = useRef(true);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>(() => [createSession()]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [streamState, setStreamState] = useState<StreamState>("idle");
  const [currentStageLabel, setCurrentStageLabel] = useState("等待输入");
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historySearch, setHistorySearch] = useState("");
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [clarificationRequest, setClarificationRequest] = useState<{
    clarification: AgentClarification;
    originalQuestion: string;
  } | null>(null);
  const isComposingRef = useRef(false);
  const compactLogRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const askRef = useRef<(question: string, context?: string, requestPrompt?: string) => void>(() => undefined);
  const sessionActionsRef = useRef<{ create: () => void; remove: (id: string) => void; select: (id: string) => void }>({ create: () => undefined, remove: () => undefined, select: () => undefined });
  const requestControllerRef = useRef<AbortController | null>(null);
  const contextSessionRef = useRef<string | undefined>(undefined);
  const lastSubmittedQueryRef = useRef("");

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as ChatSession[];
      if (!Array.isArray(parsed) || !parsed.length) {
        return;
      }
      const normalized = parsed
        .filter((session) => Array.isArray(session.messages) && session.messages.length)
        .map((session) => ({
          ...session,
          pinned: Boolean(session.pinned),
          messages: session.messages.map((message) => ({
            ...message,
            id: message.id || createId("msg"),
          })),
        }));
      if (!normalized.length) {
        return;
      }
      setSessions(normalized);
      setCurrentSessionId(normalized[0].id);
    } catch {
      // Ignore invalid local state and keep a fresh session.
    } finally {
      setSessionsLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      return;
    }
    setCurrentSessionId(sessions[0]?.id ?? null);
  }, [currentSessionId, sessions]);

  useEffect(() => {
    onSessionsChange?.(
      sessions.map(({ id, title, pinned, createdAt, updatedAt }) => ({
        id,
        title,
        pinned,
        createdAt,
        updatedAt,
      })),
    );
  }, [onSessionsChange, sessions]);

  useEffect(() => {
    onCurrentSessionChange?.(currentSessionId);
  }, [currentSessionId, onCurrentSessionChange]);

  useEffect(() => {
    if (!workspace || typeof window === "undefined") {
      return;
    }
    const handleSelectSession = (event: Event) => {
      const customEvent = event as CustomEvent<string>;
      if (customEvent.detail) {
        sessionActionsRef.current.select(customEvent.detail);
      }
    };
    const handleNewSession = () => sessionActionsRef.current.create();
    const handleRenameSession = (event: Event) => {
      const detail = (event as CustomEvent<{ sessionId?: string; title?: string }>).detail;
      const sessionId = detail?.sessionId;
      const title = detail?.title?.trim();
      if (!sessionId || !title) return;
      setSessions((previous) =>
        previous.map((session) =>
          session.id === sessionId
            ? { ...session, title, updatedAt: Date.now() }
            : session,
        ),
      );
    };
    const handleDeleteSession = (event: Event) => {
      const sessionId = (event as CustomEvent<string>).detail;
      if (sessionId) sessionActionsRef.current.remove(sessionId);
    };
    const handleRunPrompt = (event: Event) => {
      const detail = (event as CustomEvent<unknown>).detail;
      if (typeof detail === "string" && detail.trim()) askRef.current(detail);
      else if (detail && typeof detail === "object") {
        const request = detail as { prompt?: unknown; context?: unknown };
        if (typeof request.prompt === "string" && request.prompt.trim()) {
          askRef.current(request.prompt, typeof request.context === "string" ? request.context : undefined);
        }
      }
    };
    window.addEventListener("ashare:select-session", handleSelectSession);
    window.addEventListener("ashare:new-session", handleNewSession);
    window.addEventListener("ashare:rename-session", handleRenameSession);
    window.addEventListener("ashare:delete-session", handleDeleteSession);
    window.addEventListener(AGENT_LAB_RUN_EVENT, handleRunPrompt);
    return () => {
      window.removeEventListener("ashare:select-session", handleSelectSession);
      window.removeEventListener("ashare:new-session", handleNewSession);
      window.removeEventListener("ashare:rename-session", handleRenameSession);
      window.removeEventListener("ashare:delete-session", handleDeleteSession);
      window.removeEventListener(AGENT_LAB_RUN_EVENT, handleRunPrompt);
    };
  }, [workspace]);

  useEffect(() => {
    if (typeof window === "undefined" || !sessionsLoaded) {
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }, [sessions, sessionsLoaded]);

  useEffect(() => () => requestControllerRef.current?.abort(), []);

  const currentSession = useMemo(
    () => sessions.find((session) => session.id === currentSessionId) ?? sessions[0],
    [currentSessionId, sessions],
  );
  const messages = useMemo(() => currentSession?.messages ?? [], [currentSession]);
  const visibleMessages = messages.slice(-40); // cap rendering to last 40 messages to avoid infinite scroll
  // A transition can remain pending while React renders the large response card.
  // Only the transport state should keep the visible "正在研究" indicator on screen.
  const busy = streamState === "connecting" || streamState === "streaming";
  const sortedSessions = useMemo(
    () =>
      [...sessions]
        .filter((session) => {
          const target = `${session.title} ${session.messages.at(-1)?.content ?? ""}`.toLowerCase();
          return target.includes(historySearch.trim().toLowerCase());
        })
        .sort((a, b) => {
          if (Boolean(b.pinned) !== Boolean(a.pinned)) {
            return Number(Boolean(b.pinned)) - Number(Boolean(a.pinned));
          }
          return b.updatedAt - a.updatedAt;
        }),
    [historySearch, sessions],
  );
  const memoryMeta = useMemo(() => findLatestMemoryMeta(messages), [messages]);
  const latestContext = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index--) {
      const response = messages[index].response;
      const context = response ? contextFromAgentResponse(response) : null;
      if (context) return context;
    }
    return null;
  }, [messages]);
  useEffect(() => {
    if (!sessionsLoaded || !currentSessionId || contextSessionRef.current === currentSessionId) return;
    const initial = contextSessionRef.current === undefined;
    contextSessionRef.current = currentSessionId;
    onContextUpdate?.(latestContext, initial);
  }, [sessionsLoaded, currentSessionId, latestContext, onContextUpdate]);

  useEffect(() => {
    if (!compact || !compactLogRef.current) {
      return;
    }
    if (followBottomRef.current) compactLogRef.current.scrollTop = compactLogRef.current.scrollHeight;
  }, [compact, messages, busy, streamedAnswer, toolActivity, currentSessionId]);

  useEffect(() => {
    if (!inputRef.current) {
      return;
    }
    inputRef.current.style.height = "0px";
    inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 160)}px`;
  }, [input]);

  useEffect(() => {
    if (!busy) {
      setCurrentStageLabel(locale === "en" ? "Ready" : "等待输入");
      setActiveTool(null);
    }
  }, [busy, locale]);

  function patchCurrentSession(updater: (session: ChatSession) => ChatSession) {
    setSessions((prev) =>
      prev.map((session) => {
        if (session.id !== currentSession?.id) {
          return session;
        }
        return updater(session);
      }),
    );
  }

  function appendMessage(message: Message) {
    patchCurrentSession((session) => ({
      ...session,
      title: session.title === "新对话" && message.role === "user" ? summarizeTitle(message.content) : session.title,
      updatedAt: Date.now(),
      messages: [...session.messages, message],
    }));
  }

  function appendAgentResponse(response: AgentResponse) {
    const context = contextFromAgentResponse(response);
    if (context) onContextUpdate?.(context, false, context.type === "stock");
    if (response.clarification) {
      setClarificationRequest({
        clarification: response.clarification,
        originalQuestion: lastSubmittedQueryRef.current,
      });
    }
    appendMessage({
      id: createId("msg"),
      role: "agent",
      content: response.summary,
      actions: response.actions,
      citations: response.citations,
      response,
    });
  }

  function ask(question: string, context?: string, requestPrompt?: string) {
    const trimmed = question.trim();
    const attachedContext = context?.trim();
    if (!trimmed || busy || requestControllerRef.current) {
      return;
    }

    const submittedPrompt = requestPrompt?.trim() || trimmed;
    lastSubmittedQueryRef.current = submittedPrompt;
    onLabTrace?.({
      id: createId("lab"),
      phase: "run_started",
      query: submittedPrompt,
      message: "已提交实验 query，等待 Agent 事件流",
      createdAt: 0,
    });

    appendMessage({
      id: createId("msg"),
      role: "user",
      content: trimmed,
      context: attachedContext || undefined,
    });
    setInput("");
    setStreamedAnswer("");
    setToolActivity([]);
    followBottomRef.current = true;
    setCurrentStageLabel(t("正在连接进度流"));
    setActiveTool(null);
    const history = buildAgentHistory(messages);
    void (async () => {
      const controller = new AbortController();
      requestControllerRef.current = controller;
      try {
        setStreamState("connecting");
        setCurrentStageLabel(t("正在请求分析结果"));
        const promptWithContext = attachedContext ? `${submittedPrompt}\n\n${attachedContext}` : submittedPrompt;
        const response = await streamAgent(promptWithContext, history, currentSession?.id ?? undefined, {
          language: locale === "en" ? "en-US" : "zh-CN",
          researchMode: effectiveResearchMode(researchMode, deepResearchAvailable),
          signal: controller.signal,
          onEvent: (event) => {
            if (requestControllerRef.current !== controller) return;
            if (event.type === "message_delta") {
              if (event.provisional !== false) return;
              setStreamState("streaming");
              setStreamedAnswer(previous => event.reset ? (event.message ?? "") : previous + (event.message ?? ""));
            }
            if (event.type === "tool_started" || event.type === "tool_progress") {
              if (event.type === "tool_progress" && event.tool === "manage_watchlist" && event.status === "completed") window.dispatchEvent(new Event("ashare:watchlist-changed"));
              setCurrentStageLabel(event.tool ? researchToolLabel(event.tool, locale) : researchProgressLabel(event.stage, locale));
              setActiveTool(event.tool ? researchToolLabel(event.tool, locale) : null);
              if (event.tool) {
                const tool = event.tool;
                const status = event.type === "tool_progress" ? event.status ?? "running" : "running";
                setToolActivity(previous => updateToolActivity(previous, { tool, status, reasonCode: event.type === "tool_progress" ? event.reasonCode : undefined }));
              }
              onLabTrace?.({
                id: createId("lab"),
                phase: "tool",
                tool: event.tool,
                message: event.message,
                progressPct: event.type === "tool_progress" ? event.progressPct : undefined,
                createdAt: 0,
              });
            }
            if (event.type === "message_completed") {
              const credits = event.response.payload._credits;
              if (credits && typeof credits === "object") {
                onCreditUpdate?.({
                  charged: typeof credits.charged === "number" ? credits.charged : 0,
                  remaining: typeof credits.remaining === "number" ? credits.remaining : null,
                  unlimited: credits.unlimited === true,
                });
              }
              onLabTrace?.({
                id: createId("lab"),
                phase: "result",
                response: event.response,
                message: "最终回答已生成",
                progressPct: 100,
                createdAt: 0,
              });
            }
            if (event.type === "error") {
              setCurrentStageLabel(event.message);
              onLabTrace?.({
                id: createId("lab"),
                phase: "error",
                message: event.message,
                createdAt: 0,
              });
            }
          },
        });
        if (requestControllerRef.current !== controller) return;
        setStreamedAnswer("");
        appendAgentResponse(response);
        setCurrentStageLabel(t("回答已生成"));
        setStreamState("completed");
      } catch (error) {
        if (requestControllerRef.current !== controller) return;
        setStreamedAnswer("");
        setStreamState("error");
        appendMessage({
          id: createId("msg"),
          role: "agent",
          content: controller.signal.aborted ? (locale === "en" ? "Research cancelled." : "研究已取消。") : `${locale === "en" ? "Request failed" : "请求失败"}: ${error instanceof Error ? error.message : "Unknown error"}`,
        });
      } finally {
        window.dispatchEvent(new Event("ashare:watchlist-changed"));
        if (requestControllerRef.current === controller) requestControllerRef.current = null;
      }
    })();
  }

  askRef.current = ask;

  function submitCurrentInput() {
    const value = input.trim();
    if (!value) return;
    if (clarificationRequest) {
      setInput("");
      continueClarifiedQuestion(value);
      return;
    }
    ask(value);
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitCurrentInput();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.nativeEvent.isComposing || isComposingRef.current) {
      return;
    }
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitCurrentInput();
    }
  }

  function clearActiveRun() {
    requestControllerRef.current?.abort();
    requestControllerRef.current = null;
    setStreamState("idle");
    setStreamedAnswer("");
    setToolActivity([]);
    followBottomRef.current = true;
  }

  function onNewChat() {
    clearActiveRun();
    setClarificationRequest(null);
    lastSubmittedQueryRef.current = "";
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setCurrentSessionId(session.id);
    setInput("");
    if (workspace && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("ashare:session-created", { detail: session.id }));
    }
  }

  function onClearChat() {
    clearActiveRun();
    setClarificationRequest(null);
    lastSubmittedQueryRef.current = "";
    patchCurrentSession((session) => ({
      ...session,
      title: "新对话",
      updatedAt: Date.now(),
      messages: [createWelcomeMessage()],
    }));
    setInput("");
  }

  function onSelectSession(sessionId: string) {
    clearActiveRun();
    setClarificationRequest(null);
    lastSubmittedQueryRef.current = "";
    setCurrentSessionId(sessionId);
    setHistoryOpen(false);
  }

  function onDeleteSession(sessionId: string) {
    if (sessionId === currentSession?.id) {
      clearActiveRun();
      setClarificationRequest(null);
      lastSubmittedQueryRef.current = "";
    }
    setSessions((prev) => {
      if (prev.length <= 1) {
        const fresh = createSession();
        setCurrentSessionId(fresh.id);
        if (workspace && typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("ashare:session-created", { detail: fresh.id }));
        }
        return [fresh];
      }
      const next = prev.filter((session) => session.id !== sessionId);
      if (!next.length) {
        const fresh = createSession();
        setCurrentSessionId(fresh.id);
        return [fresh];
      }
      setCurrentSessionId((current) => {
        if (!current || current === sessionId) {
          return next[0].id;
        }
        const stillExists = next.some((session) => session.id === current);
        return stillExists ? current : next[0].id;
      });
      return next;
    });
  }

  function onTogglePinned(sessionId: string) {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              pinned: !session.pinned,
              updatedAt: Date.now(),
            }
          : session,
      ),
    );
  }

  sessionActionsRef.current = { create: onNewChat, remove: onDeleteSession, select: onSelectSession };

  function continueClarifiedQuestion(answer: string) {
    const request = clarificationRequest;
    if (!request) return;
    setClarificationRequest(null);
    setInput("");
    const original = request.originalQuestion.trim();
    const question = request.clarification.question.trim();
    const answerLine = locale === "en" ? `User selected: ${answer}` : `用户选择：${answer}`;
    const clarificationLine = locale === "en" ? `Clarifying question: ${question}` : `澄清问题：${question}`;
    const fullPrompt = [original, clarificationLine, answerLine].filter(Boolean).join("\n\n");
    ask(answer, undefined, fullPrompt);
  }

  function onStartRename(session: ChatSession) {
    setRenamingSessionId(session.id);
    setRenameDraft(session.title === "新对话" ? "" : session.title);
  }

  function onCommitRename(sessionId: string) {
    const nextTitle = renameDraft.trim() || "新对话";
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              title: nextTitle,
              updatedAt: Date.now(),
            }
          : session,
      ),
    );
    setRenamingSessionId(null);
    setRenameDraft("");
  }

  if (compact) {
    const compactMessages = messages.length <= 1 ? [] : visibleMessages.filter(message => message.content !== "你好，我是 Ashare Agent。可以直接问全球新闻、热点、个股和持仓。");

    return (
      <div className={`agent-chat-compact gpt-chat ${compactMessages.length ? "chat-has-messages" : "chat-is-empty"} ${workspace ? "workspace-agent" : ""}`}>
        <div className="gpt-chat-topbar">
          <div className="gpt-chat-heading">
            <div className="gpt-chat-title">{currentSession?.title && currentSession.title !== "新对话" ? currentSession.title : (locale === "en" ? "Research" : "研究")}</div>
            <div className="gpt-chat-subtitle">{locale === "en" ? "From a question to cited evidence" : "从一个问题，到有来源的结论"}</div>
          </div>
          <div className="gpt-topbar-actions">
            {workspace ? null : (
              <button
                className="button ghost gpt-topbar-button"
                onClick={() => setHistoryOpen((open) => !open)}
                type="button"
              >
                {historyOpen ? t("收起历史") : t("历史记录")}
              </button>
            )}
            <button className="button ghost gpt-topbar-button" onClick={onNewChat} type="button">{t("新对话")}</button>
          </div>
        </div>

        <div className="gpt-ai-notice" role="note">
          <span aria-hidden="true">!</span>
          <p>{t("AI 生成内容可能出错或过时，请结合来源核验；不构成投资建议。")}</p>
        </div>

        {historyOpen ? (
          <div className="agent-history-panel">
            <div className="agent-history-head">
              <span className="agent-history-title">{t("历史对话")}</span>
              <span className="agent-history-hint">{t("切换、搜索、置顶、重命名")}</span>
            </div>
            <input
              className="agent-history-search"
              value={historySearch}
              onChange={(event) => setHistorySearch(event.target.value)}
              placeholder={t("搜索历史记录")}
            />
            <div className="agent-history-list">
              {sortedSessions.map((session) => (
                <div
                  key={session.id}
                  className={`agent-history-item ${
                    session.id === currentSession?.id ? "active" : ""
                  }`}
                >
                  <button
                    type="button"
                    className="agent-history-main"
                    onClick={() => onSelectSession(session.id)}
                  >
                    <div className="agent-history-text">
                      <span className="agent-history-name">
                        {session.pinned ? t("置顶 · ") : ""}
                        {session.title === "新对话" ? t("未命名对话") : session.title}
                      </span>
                      <span className="agent-history-meta">
                        {new Date(session.updatedAt).toLocaleString(locale === "en" ? "en-US" : "zh-CN", {
                          month: "numeric",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </button>
                  <div className="agent-history-actions">
                    <button
                      type="button"
                      className="agent-history-action"
                      onClick={() => onTogglePinned(session.id)}
                    >
                      {session.pinned ? t("取消置顶") : t("置顶")}
                    </button>
                    <button
                      type="button"
                      className="agent-history-action"
                      onClick={() => onStartRename(session)}
                    >{t("重命名")}</button>
                    <button
                      type="button"
                      className="agent-history-delete"
                      onClick={() => onDeleteSession(session.id)}
                    >{t("删除")}</button>
                  </div>
                  {renamingSessionId === session.id ? (
                    <div className="agent-history-rename">
                      <input
                        className="agent-history-rename-input"
                        value={renameDraft}
                        onChange={(event) => setRenameDraft(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            onCommitRename(session.id);
                          }
                        }}
                        placeholder={t("输入会话名称")}
                        autoFocus
                      />
                      <button
                        type="button"
                        className="agent-history-action"
                        onClick={() => onCommitRename(session.id)}
                      >{t("保存")}</button>
                    </div>
                  ) : null}
                </div>
              ))}
              {!sortedSessions.length ? <div className="agent-history-empty">{t("暂无历史对话")}</div> : null}
            </div>
          </div>
        ) : null}

        <div className="gpt-chat-log" ref={compactLogRef} onScroll={event => { const el = event.currentTarget; followBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 96; }}>
          <div className="agent-session-surface" key={currentSession?.id ?? "empty"}>
            {memoryMeta ? <MemoryPanel meta={memoryMeta} /> : null}
            {messages.length <= 1 ? (
              <section className="gpt-welcome-card">
                <span className="research-welcome-eyebrow">{locale === "en" ? "YOUR RESEARCH DESK" : "你的研究空间"}</span>
                <h3>{locale === "en" ? "What are you researching?" : "今天，想研究什么？"}</h3>
                <p className="muted">{locale === "en" ? "Stocks, financials and the evidence behind them." : "股票、财务数据，以及观点背后的证据。"}</p>
              </section>
            ) : null}
            <div className="chat-log chat-log-full">
            {compactMessages.map((message) => (
              <div className={`chat-row ${message.role}`} key={message.id}>
                <div className={`chat-avatar ${message.role}`}>{message.role === "user" ? t("你") : "A"}</div>
                <div className={`gpt-bubble ${message.role}`}>
                  {message.role === "agent" && locale === "en" && (message.content.match(/[\u3400-\u9fff]/g)?.length ?? 0) > 16 ? <p className="research-language-notice">Saved response in Chinese. New reports follow your current language setting; saved reports keep their original wording.</p> : null}
                  {message.response ? <ResponseTools response={message.response} /> : null}
                  <MarkdownText content={t(message.content)} />
                  {message.context ? <details className="agent-chart-context"><summary>{locale === "en" ? "Selected chart data" : "所选图表区间数据"}</summary><pre>{message.context}</pre></details> : null}
                  {message.response ? <ResearchTrace response={message.response} showTools={false} /> : null}
                  {message.response ? <PayloadCards response={message.response} workspace={workspace} /> : null}
                  {message.actions?.length && (!message.response || message.response.ui_components === undefined || message.response.ui_components.includes("actions")) ? (
                    <div className="tag-list agent-suggested-actions" style={{ marginTop: 10 }}>
                      {message.actions.slice(0, 3).map((action) => (
                        <button className="tag" key={action} onClick={() => ask(t(action))} type="button">
                          {locale === "en" ? truncate(t(action), 60) : compactActionLabel(action)}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
            {busy ? (
              <div className="chat-row agent">
                <div className="chat-avatar agent">A</div>
                <div className="gpt-bubble agent">
                  <ResearchTools steps={toolActivity} phase={activeTool || currentStageLabel} />
                  {streamedAnswer ? <div className="research-streaming-answer" aria-busy="true"><MarkdownText content={streamedAnswer} /></div> : null}
                </div>
              </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="agent-clarification-shell">
          <ClarificationPrompt
            request={clarificationRequest}
            locale={locale}
            onClose={() => setClarificationRequest(null)}
            onResolve={continueClarifiedQuestion}
          />
        </div>

        <form className="gpt-input-shell" onSubmit={onSubmit}>
          <div className="gpt-input-frame">
            <textarea
              ref={inputRef}
              className="gpt-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              onCompositionStart={() => {
                isComposingRef.current = true;
              }}
              onCompositionEnd={() => {
                isComposingRef.current = false;
              }}
              placeholder={clarificationRequest
                ? (locale === "en" ? "Add a detail to continue…" : "补充信息后自动继续分析…")
                : (locale === "en" ? "Ask about a company, a filing or a market question…" : "输入公司、财报或市场问题…")}
              rows={3}
            />
            <div className="gpt-input-meta">
              <div className="research-mode-switch" role="group" aria-label={locale === "en" ? "Research depth" : "研究深度"}>
                <button type="button" aria-pressed={researchMode === "quick"} onClick={() => setResearchMode("quick")} disabled={busy}>{locale === "en" ? "Quick" : "快速"}</button>
                <button type="button" aria-pressed={researchMode === "deep"} onClick={() => setResearchMode("deep")} disabled={busy || !deepResearchAvailable} title={!deepResearchAvailable ? (locale === "en" ? "Unavailable at the moment" : "暂时不可用") : undefined}>{locale === "en" ? "Deep" : "深入"}</button>
              </div>
              <button className="button ghost gpt-topbar-button research-clear" onClick={onClearChat} type="button" disabled={!currentSession}>{t("清空")}</button>
              {busy
                ? <button className="button gpt-stop-button" type="button" onClick={() => requestControllerRef.current?.abort()}>{locale === "en" ? "Stop" : "停止"}</button>
                : <button className="button" type="submit" disabled={!input.trim()}>{t("发送")}</button>}
            </div>
          </div>
          <p className="research-composer-hint" role={storageError ? "alert" : undefined}>{storageError ? (locale === "en" ? "Browser storage is full or unavailable. Download this report to keep it." : "浏览器存储已满或不可用，请下载报告以保存。") : !deepResearchAvailable ? (locale === "en" ? "Deep research is unavailable at the moment. Quick research is available." : "深入研究暂时不可用，可使用快速研究。") : (locale === "en" ? "Research only · Check dates and sources · Enter to send" : "仅供研究 · 核对数据日期与来源 · Enter 发送")}</p>
        </form>
        {!compactMessages.length ? <div className="research-starters" aria-label={locale === "en" ? "Research suggestions" : "研究建议"}>
          {prompts.map((prompt,index) => <button key={prompt} type="button" title={prompt} onClick={() => {setInput(prompt); inputRef.current?.focus();}}>{promptLabels[index]} <span aria-hidden="true">↗</span></button>)}
        </div> : null}
      </div>
    );
  }

  return (
    <div className="stack">
      <section className="panel section">
        <h1>{t("Agent 对话页")}</h1>
        <p className="muted">{t("当前接入的是后端轻量 Agent，负责意图判断、服务调度和结果整合。")}</p>
      </section>

      <section className="content-grid">
        <div className="panel section">
          <h2>{t("对话")}</h2>
          <div className="gpt-ai-notice" role="note">
            <span aria-hidden="true">!</span>
            <p>{t("AI 生成内容可能出错或过时，请结合来源核验；不构成投资建议。")}</p>
          </div>
          <div className="chat-log">
            {visibleMessages.map((message) => (
              <div className={`bubble ${message.role}`} key={message.id}>
                <strong>{message.role === "user" ? t("你") : "Agent"}</strong>
                {message.response ? <ResponseTools response={message.response} /> : null}
                <MarkdownText content={t(message.content)} />
                {message.context ? <details className="agent-chart-context"><summary>{locale === "en" ? "Selected chart data" : "所选图表区间数据"}</summary><pre>{message.context}</pre></details> : null}
                {message.response ? <ResearchTrace response={message.response} showTools={false} /> : null}
                {message.response ? <PayloadCards response={message.response} workspace={workspace} /> : null}
                {message.actions?.length && (!message.response || message.response.ui_components === undefined || message.response.ui_components.includes("actions")) ? (
                  <div className="tag-list" style={{ marginTop: 12 }}>
                    {message.actions.map((action) => (
                      <button className="tag" key={action} onClick={() => ask(t(action))} type="button">
                        {t(action)}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            {busy ? <div className="bubble agent"><ResearchTools steps={toolActivity} phase={activeTool || currentStageLabel} />{streamedAnswer ? <MarkdownText content={streamedAnswer} /> : null}</div> : null}
          </div>
        </div>

        <div className="panel section">
          <h2>{t("提问")}</h2>
          <form className="stack" onSubmit={onSubmit}>
            <label className="label">{t("你的问题")}<textarea
                className="input"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={onKeyDown}
                onCompositionStart={() => {
                  isComposingRef.current = true;
                }}
                onCompositionEnd={() => {
                  isComposingRef.current = false;
                }}
                placeholder={t("例如：分析我的持仓")}
                rows={4}
              />
            </label>
            <button className="button" type="submit" disabled={busy}>{t("发送给 Agent")}</button>
          </form>
          <div className="stack" style={{ marginTop: 18 }}>
            {prompts.map((prompt) => (
              <button className="button ghost" key={prompt} onClick={() => ask(prompt)} type="button">
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </section>

      <div className="agent-clarification-shell">
        <ClarificationPrompt
          request={clarificationRequest}
          locale={locale}
          onClose={() => setClarificationRequest(null)}
          onResolve={continueClarifiedQuestion}
        />
      </div>
    </div>
  );
}

function ClarificationPrompt({
  request,
  locale,
  onClose,
  onResolve,
}: {
  request: { clarification: AgentClarification; originalQuestion: string } | null;
  locale: "en" | "zh";
  onClose: () => void;
  onResolve: (answer: string) => void;
}) {
  const clarification = request?.clarification;
  if (!request || !clarification) return null;

  return (
    <div className="agent-clarification-row" role="group" aria-label={locale === "en" ? "Clarify your question" : "补充问题意图"}>
      <span className="agent-clarification-prompt" title={clarification.question}>{clarification.question}</span>
      <div className="agent-clarification-options">
        {clarification.options.map((option) => (
          <button key={option} type="button" onClick={() => onResolve(option)} title={option}>
            {option}
          </button>
        ))}
      </div>
      <button
        className="agent-clarification-dismiss"
        type="button"
        onClick={onClose}
        aria-label={locale === "en" ? "Dismiss clarification" : "关闭澄清问题"}
        title={locale === "en" ? "Decide later" : "稍后再说"}
      >
        ×
      </button>
    </div>
  );
}

function MarkdownText({ content }: { content: string }) {
  return <ResearchMarkdown content={decodeEntities(content)} />;
}

function summarizeTitle(input: string) {
  return input.replace(/\s+/g, " ").trim().slice(0, 24) || "新对话";
}

function truncate(text: string, maxLength: number) {
  const normalized = text?.trim() ?? "";
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength).trim()}...` : normalized;
}

function formatIndicatorValue(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "—";
}

function compactActionLabel(action: string) {
  if (action.includes("最新消息")) return "最新消息";
  if (action.includes("同板块")) return "板块对比";
  if (action.includes("完整单股分析")) return "完整分析";
  if (action.includes("全球局势")) return "全球影响";
  return truncate(action.replace(/^继续问[：:]/, "").trim(), 12);
}

function PayloadCards({ response, workspace }: { response: AgentResponse; workspace: boolean }) {
  const { locale } = useLanguage();
  const payload = response.payload;
  const meta = payload._meta;
  const components = response.ui_components ?? [];
  const hasStockAnalysis = Boolean(payload.stock_code && payload.quote);
  // 个股对比：后端在分析多只股票时返回 stocks 数组，逐只渲染股票卡。
  const stocks = Array.isArray(payload.stocks) ? (payload.stocks as unknown as StockAnalysisResponse[]) : [];
  const hasPortfolio = Array.isArray(payload.positions);
  const news = Array.isArray(payload.news) ? (payload.news as NewsItem[]) : [];
  const hotspots = Array.isArray(payload.hotspots) ? (payload.hotspots as HotspotItem[]) : [];
  const globalNews = Array.isArray(payload.global_news) ? (payload.global_news as GlobalNewsItem[]) : [];
  const webResults = Array.isArray(payload.web_results) ? (payload.web_results as WebSearchResult[]) : [];
  const isAgent = response.intent === "pydantic_ai_agent";
  // 当提问聚焦到具体个股（有个股分析或个股消息）时，通用的「全球重点新闻」「热点」
  // 与问题无关，不再铺出来，避免回复跑题变长。宏观提问（无个股焦点）仍正常显示全球新闻。
  // 注意：不能用 web_results 判断——宏观提问也常带联网搜索结果，会误杀全球新闻。
  const isStockFocused = hasStockAnalysis || news.length > 0;
  // In the workspace, stock/news/portfolio detail already lives in the right
  // context pane and the expandable trace. Keep only components the agent
  // explicitly selected instead of duplicating every tool result in the chat.
  const showStock = !workspace && (response.intent === "stock_analysis" || response.intent === "stock_comparison" || isAgent);
  const showNews = !workspace && (response.intent === "news_lookup" || isAgent);
  const showPortfolio = !workspace && (response.intent === "portfolio_analysis" || isAgent);
  const showGlobalNews = !workspace && isAgent && !isStockFocused;
  const showWebResults = !workspace && isAgent;
  const showHotspots = !workspace && isAgent && !isStockFocused;
  // Single-stock charts already live in the workspace's right-side research
  // panel; keep them out of the conversation stream. Comparison cards remain
  // useful inline because the side panel does not replace a side-by-side table.
  const showChart = !workspace && components.includes("chart");
  const showComparison = components.includes("comparison");
  const comparison = payload.financial_comparison;
  const chartStocks = stocks.length > 1
    ? stocks
    : hasStockAnalysis
      ? [payload as unknown as StockAnalysisResponse]
      : [];

  if (workspace && !showChart && !showComparison) return null;

  return (
    <div className="stack" style={{ marginTop: 14 }}>
      {!response.research_steps?.length && meta?.tools_used?.length ? <AgentMetaChips toolsUsed={meta.tools_used} cacheHits={meta.cache_hits ?? []} /> : null}
      {showChart ? chartStocks.map((stock) => {
        const data = lastYearChartPoints(stock.chart_series);
        return data.length >= 2 ? <AgentChartCard key={`chart-${stock.stock_code}`} stock={stock} data={data} /> : null;
      }) : null}
      {showComparison ? <AgentComparisonCard comparison={comparison} stocks={stocks} locale={locale} /> : null}
      {showStock && stocks.length > 1
        ? stocks.map((stock) => <StockAnalysisCard key={stock.stock_code} analysis={stock} />)
        : showStock && hasStockAnalysis
          ? <StockAnalysisCard analysis={payload as unknown as StockAnalysisResponse} />
          : null}
      {showNews && news.length ? <NewsCards news={news} /> : null}
      {showGlobalNews && globalNews.length ? <GlobalNewsCards news={globalNews} /> : null}
      {showWebResults && webResults.length ? <WebResultCards results={webResults} /> : null}
      {showHotspots && hotspots.length ? <HotspotCards hotspots={hotspots} /> : null}
      {showPortfolio && hasPortfolio ? <PortfolioCard analysis={payload as unknown as PortfolioAnalysisResponse} /> : null}
    </div>
  );
}

function lastYearChartPoints(points: ChartPoint[] | undefined): ChartPoint[] {
  if (!Array.isArray(points)) return [];
  const valid = points
    .filter((point) => point && typeof point.date === "string" && Number.isFinite(Date.parse(point.date)))
    .slice()
    .sort((left, right) => left.date.localeCompare(right.date));
  if (valid.length < 2) return [];
  const lastDate = new Date(`${valid.at(-1)!.date.slice(0, 10)}T00:00:00`);
  const yearAgo = new Date(lastDate);
  yearAgo.setFullYear(yearAgo.getFullYear() - 1);
  const filtered = valid.filter((point) => new Date(`${point.date.slice(0, 10)}T00:00:00`) >= yearAgo);
  return filtered.length >= 2 ? filtered : valid.slice(-252);
}

function AgentChartCard({ stock, data }: { stock: StockAnalysisResponse; data: ChartPoint[] }) {
  const { locale } = useLanguage();
  return (
    <section className="agent-payload-card agent-output-chart" aria-label={locale === "en" ? `${stock.stock_name} one-year price chart` : `${stock.stock_name}一年股价图`}>
      <div className="agent-card-head">
        <div>
          <div className="agent-card-kicker">{locale === "en" ? "PRICE CHART · PAST YEAR" : "股价图 · 过去一年"}</div>
          <h3>{stock.stock_name} <span>{stock.stock_code}</span></h3>
        </div>
        <small>{data[0]?.date} — {data.at(-1)?.date}</small>
      </div>
      <ResearchChart data={data} symbol={stock.stock_code} height={250} compact />
    </section>
  );
}

type FinancialComparison = NonNullable<AgentResponse["payload"]["financial_comparison"]>;

function AgentComparisonCard({
  comparison,
  stocks,
  locale,
}: {
  comparison?: FinancialComparison;
  stocks: StockAnalysisResponse[];
  locale: "en" | "zh";
}) {
  const { locale: appLocale } = useLanguage();
  const metricLabels: Record<string, string> = {
    "Revenue": "营业收入",
    "Net income": "净利润",
    "Diluted EPS": "稀释每股收益",
    "Assets": "总资产",
    "Operating cash flow": "经营现金流",
  };
  const comparisonNotes: Record<string, string> = {
    "Metric unavailable for one or more companies.": "至少一家公司缺少该指标。",
    "Reporting currencies or units differ; no direct ranking or conversion.": "报告币种或单位不同，不能直接排序或换算。",
    "Accounting taxonomies differ; no direct ranking.": "会计分类口径不同，不能直接排序。",
    "Reporting periods differ; no direct ranking.": "报告期不同，不能直接排序。",
    "Reporting period metadata unavailable; no direct ranking.": "缺少报告期信息，不能直接排序。",
    "Periods are similar, not necessarily identical; review exact dates.": "报告期接近但不完全相同，请核对具体日期。",
  };
  if (comparison && comparison.companies.length >= 2) {
    const companies = comparison.companies;
    return (
      <section className="agent-payload-card agent-output-comparison">
        <div className="agent-card-kicker">{locale === "en" ? "SIDE-BY-SIDE COMPARISON" : "并列比较"}</div>
        <div className="research-summary-table">
          <table>
            <thead><tr><th>{locale === "en" ? "Metric" : "指标"}</th>{companies.map((company) => <th key={company.code}>{company.name} <small>{company.code}</small></th>)}</tr></thead>
            <tbody>{comparison.metrics.map((metric) => (
              <tr key={metric.metric}>
                <th scope="row">{locale === "zh" ? metricLabels[metric.metric] ?? metric.metric : metric.metric}</th>
                {companies.map((company) => {
                  const fact = metric.values.find((value) => value.code === company.code)?.fact;
                  const value = fact ? `${Number(fact.val).toLocaleString(appLocale === "en" ? "en-US" : "zh-CN")} ${fact.unit}` : (locale === "en" ? "Unavailable" : "暂无数据");
                  const period = fact ? `${fact.start ? `${fact.start} — ` : ""}${fact.end}` : "";
                  return <td key={company.code}>{fact?.url ? <a href={fact.url} target="_blank" rel="noreferrer">{value} ↗</a> : value}{fact ? <small className="agent-comparison-period">{period} · {locale === "en" ? "Filed" : "披露于"} {fact.filed}</small> : null}</td>;
                })}
              </tr>
            ))}{comparison.metrics.filter((metric) => !metric.comparable).map((metric) => (
              <tr className="agent-comparison-detail" key={`${metric.metric}-note`}>
                <td colSpan={companies.length + 1}>{locale === "zh" ? metricLabels[metric.metric] ?? metric.metric : metric.metric}: {locale === "zh" ? comparisonNotes[metric.comparison_note] ?? metric.comparison_note : metric.comparison_note}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>
    );
  }

  const comparedStocks = stocks.filter((stock) => stock?.quote && stock?.stock_code);
  if (comparedStocks.length < 2) return null;
  return (
    <section className="agent-payload-card agent-output-comparison">
      <div className="agent-card-kicker">{locale === "en" ? "MARKET SNAPSHOT" : "行情快照比较"}</div>
      <div className="research-summary-table">
        <table>
          <thead><tr><th>{locale === "en" ? "Measure" : "项目"}</th>{comparedStocks.map((stock) => <th key={stock.stock_code}>{stock.stock_name} <small>{stock.stock_code} · {stock.chart_series?.at(-1)?.date ?? (locale === "en" ? "date unavailable" : "日期未知")}</small></th>)}</tr></thead>
          <tbody>
            <tr><th scope="row">{locale === "en" ? "Last price" : "最新价"}</th>{comparedStocks.map((stock) => <td key={stock.stock_code}>{stock.quote.current_price.toLocaleString(appLocale === "en" ? "en-US" : "zh-CN", { maximumFractionDigits: 4 })} {{ us: "USD", hk: "HKD", cn: "CNY", sh: "CNY", sz: "CNY" }[stock.market] ?? ""}</td>)}</tr>
            <tr><th scope="row">{locale === "en" ? "Daily change" : "当日涨跌"}</th>{comparedStocks.map((stock) => <td key={stock.stock_code}>{stock.quote.change_pct >= 0 ? "+" : ""}{stock.quote.change_pct.toFixed(2)}%</td>)}</tr>
          </tbody>
        </table>
      </div>
      <p className="agent-comparison-note">{locale === "en" ? "Prices use each market's native currency and may be delayed." : "价格保留各市场原生币种，行情可能延迟。"}</p>
    </section>
  );
}

function AgentMetaChips({ toolsUsed, cacheHits }: { toolsUsed: string[]; cacheHits: string[] }) {
  const { t } = useLanguage();
  const cacheSet = new Set(cacheHits);
  return (
    <div className="agent-meta-strip">
      <span className="agent-meta-label">{t("本次调用")}</span>
      <div className="tag-list">
        {toolsUsed.map((tool) => (
          <span className="tag" key={tool}>
            {t(formatToolName(tool))}
            {cacheSet.has(tool) ? t(" · 缓存") : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

function StockAnalysisCard({ analysis }: { analysis: StockAnalysisResponse }) {
  const { t, locale } = useLanguage();
  const technicalNotes = (analysis.technical_commentary ?? []).filter(note => locale !== "en" || !/[\u3400-\u9fff]/.test(note)).slice(0,2);
  const currency = { us: "USD", hk: "HKD", cn: "CNY", sh: "CNY", sz: "CNY" }[analysis.market] ?? "";
  const dataDate = analysis.chart_series?.at(-1)?.date;
  return (
    <div className="agent-payload-card agent-stock-card">
      <div className="agent-card-head">
        <div>
          <div className="agent-card-kicker">{t("股票")}</div>
          <h3>
            {analysis.stock_name} <span>{analysis.stock_code}</span>
          </h3>
        </div>
      </div>
      <div className="agent-card-metrics">
        <div className="agent-card-metric">
          <span>{t("最新价")} {currency}</span>
          <strong>{analysis.quote.current_price.toFixed(2)}</strong>
        </div>
        <div className="agent-card-metric">
          <span>MACD</span>
          <strong>{formatIndicatorValue(analysis.technical_indicators.MACD)}</strong>
        </div>
        <div className="agent-card-metric">
          <span>RSI (14)</span>
          <strong>{formatIndicatorValue(analysis.technical_indicators.RSI)}</strong>
        </div>
      </div>
      <small className="muted">{locale === "en" ? "Historical / delayed" : "历史／延迟行情"} · {dataDate ?? (locale === "en" ? "Data date unavailable" : "数据日期未知")}</small>
      {technicalNotes.length ? (
        <div className="agent-note-list">
          {technicalNotes.map((item) => (
            <span className="agent-note" key={item}>
              {locale === "en" ? item : truncate(item, 40)}
            </span>
          ))}
        </div>
      ) : null}
      <div className="agent-card-actions agent-stock-actions">
        <StockPanelLink stockCode={analysis.stock_code} panel="news" className="button ghost" compactLoading>{t("新闻")}</StockPanelLink>
      </div>
    </div>
  );
}

function GlobalNewsCards({ news }: { news: GlobalNewsItem[] }) {
  const { t, locale } = useLanguage();
  return (
    <div className="agent-payload-card">
      <div className="agent-card-kicker">{t("全球重点新闻")}</div>
      <div className="agent-card-list">
        {news.slice(0, 4).map((item) => (
          <div className="agent-card-row" key={item.id}>
            <div className="agent-card-row-head">
              <strong title={item.title}>{compactHeadline(item.title, 48)}</strong>
              <span className="muted">{item.source}</span>
            </div>
            <p className="muted">{truncate(item.summary, 160)}</p>
            {locale === "en" && /[\u3400-\u9fff]/.test(item.title + item.summary) ? <small className="research-original-language">Original Chinese source</small> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function WebResultCards({ results }: { results: WebSearchResult[] }) {
  const { t } = useLanguage();
  return (
    <div className="agent-payload-card">
      <div className="agent-card-kicker">{t("联网搜索结果")}</div>
      <div className="agent-card-list">
        {results.slice(0, 4).map((item) => (
          <div className="agent-card-row" key={item.id}>
            <div className="agent-card-row-head">
              <a href={item.url} target="_blank" rel="noreferrer" className="agent-card-row-link">
                <strong title={item.title}>{compactHeadline(item.title, 48)}</strong>
              </a>
              <span className="muted">{item.source}</span>
            </div>
            <p className="muted">{truncate(item.snippet, 160)}</p>
            <div className="tag-list">
              <span className="tag">{item.provider}</span>
              {item.published_at ? <span className="tag">{item.published_at}</span> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NewsCards({ news }: { news: NewsItem[] }) {
  const { t, locale } = useLanguage();
  return (
    <div className="agent-payload-card">
      <div className="agent-card-kicker">{t("消息卡片")}</div>
      <div className="agent-card-list">
        {news.slice(0, 3).map((item) => (
          <div className="agent-card-row" key={item.id}>
            <div className="agent-card-row-head">
              <strong title={item.title}>{compactHeadline(item.title, 48)}</strong>
              <span className="muted">{item.source}</span>
            </div>
            <p className="muted">{truncate(item.summary, 160)}</p>
            {locale === "en" && /[\u3400-\u9fff]/.test(item.title + item.summary) ? <small className="research-original-language">Original Chinese source</small> : null}
            <div className="inline-actions agent-card-actions">
              <StockPanelLink stockCode={item.stock_code} panel="news" className="button ghost">{t("查看该股消息")}</StockPanelLink>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function HotspotCards({ hotspots }: { hotspots: HotspotItem[] }) {
  const { t, locale } = useLanguage();
  return (
    <div className="agent-payload-card">
      <div className="agent-card-kicker">{t("热点卡片")}</div>
      <div className="agent-card-list">
        {hotspots.slice(0, 3).map((item) => (
          <div className="agent-card-row" key={item.topic_name}>
            <div className="agent-card-row-head">
              <strong>{locale === "en" && /[\u3400-\u9fff]/.test(t(item.topic_name)) ? "China market theme" : t(item.topic_name)}</strong>
              <span className="muted">{item.related_stocks.length}{t("只相关标的")}</span>
            </div>
            {locale === "en" && /[\u3400-\u9fff]/.test(item.ai_summary || item.reason) ? <details className="research-original-text"><summary>Original Chinese source text</summary><p>{item.ai_summary || item.reason}</p></details> : <p className="muted">{item.ai_summary || item.reason}</p>}
            <div className="tag-list">
              {item.related_stocks.slice(0, 3).map((stock) => (
                <Link
                  href={`/work?symbol=${encodeURIComponent(stock.stock_code)}`}
                  className="tag"
                  key={`${item.topic_name}-${stock.stock_code}`}
                >
                  {stock.stock_name}
                </Link>
              ))}
            </div>
            <div className="inline-actions agent-card-actions">
              {item.related_stocks[0] ? (
                <Link
                  href="/work?context=portfolio"
                  className="button ghost"
                >{t("继续询问持仓")}</Link>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PortfolioCard({ analysis }: { analysis: PortfolioAnalysisResponse }) {
  const { t, locale } = useLanguage();
  return (
    <div className="agent-payload-card">
      <div className="agent-card-kicker">{t("持仓卡片")}</div>
      <div className="agent-card-head">
        <h3>{t("组合表现")}</h3>
        <div className="agent-card-subtitle">{t("把盈亏、收益率和重点持仓收进一张卡片里。")}</div>
      </div>
      <div className="agent-card-metrics">
        <div className="agent-card-metric">
          <span>{t("总盈亏")}</span>
          <strong className={analysis.total_pnl >= 0 ? "signal-up" : "signal-down"}>{analysis.aggregation_available === false ? "—" : `${analysis.total_pnl.toFixed(2)} ${analysis.currency ?? ""}`}</strong>
        </div>
        <div className="agent-card-metric">
          <span>{t("收益率")}</span>
          <strong>{analysis.aggregation_available === false ? "—" : `${analysis.total_pnl_pct.toFixed(2)}%`}</strong>
        </div>
      </div>
      {analysis.aggregation_available === false ? <p className="research-data-gaps">{locale === "en" ? "Mixed currencies: aggregate P&L and return are unavailable without dated FX rates." : "多个币种缺少带日期的汇率，无法汇总盈亏或收益率。"}</p> : null}
      {analysis.positions?.length ? (
        <div className="agent-card-list">
          {analysis.positions.slice(0, 3).map((item) => (
            <div className="agent-card-row" key={`${item.position.id}-${item.position.stock_code}`}>
              <div className="agent-card-row-head">
                <strong>
                  {item.position.stock_name} ({item.position.stock_code})
                </strong>
                <span className="muted">{t("风险")} {t(item.risk_level)}</span>
              </div>
              <p className="muted">{t("盈亏")} {item.pnl.toFixed(2)} {item.currency ?? ""} ({item.pnl_pct.toFixed(2)}%)
              </p>
            </div>
          ))}
        </div>
      ) : null}
      <div className="agent-card-actions inline-actions">
        <Link href="/work?context=portfolio" className="button ghost">{t("继续询问持仓")}</Link>
      </div>
    </div>
  );
}

function formatToolName(tool: string) {
  const names: Record<string, string> = {
    get_sec_company_data: "SEC 财报",
    search_stocks: "股票检索",
    stock_analysis: "技术分析",
    get_stock_analysis: "技术分析",
    stock_news: "个股消息",
    get_stock_news: "个股消息",
    global_news: "全球消息",
    get_global_news: "全球消息",
    hotspots: "热点列表",
    list_hotspots: "热点列表",
    get_hotspot_detail: "热点详情",
    web_search: "联网搜索",
    portfolio_analysis: "持仓分析",
    get_portfolio_analysis: "持仓分析",
  };
  return names[tool] ?? tool;
}

function buildAgentHistory(messages: Message[]): AgentHistoryTurn[] {
  return messages
    .slice(-6)
    .map((message) => ({
      role: message.role,
      content: message.context ? `${message.content}\n\n${message.context}` : message.content,
      intent: message.response?.intent ?? null,
      stock_code: typeof message.response?.payload?.stock_code === "string" ? message.response.payload.stock_code : null,
      stock_name: typeof message.response?.payload?.stock_name === "string" ? message.response.payload.stock_name : null,
    }))
    .filter((item) => item.content.trim());
}

function findLatestMemoryMeta(messages: Message[]) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const meta = messages[index].response?.payload?._meta;
    if (meta?.memory_profile || meta?.heartbeat) {
      return meta;
    }
  }
  return null;
}

function MemoryPanel({
  meta,
}: {
  meta: NonNullable<AgentResponse["payload"]["_meta"]>;
}) {
  const { t, locale } = useLanguage();
  const profile = meta.memory_profile;
  const heartbeat = meta.heartbeat;
  const watchlist: Array<{ code: string; name?: string | null }> = Array.isArray(profile?.watchlist) ? profile.watchlist : [];
  const lastStock = profile?.last_stock_name || profile?.last_stock_code;
  const preferredMarket = t(formatMarketPreference(profile?.preferred_market));
  const activeGoal = typeof profile?.active_goal === "string" && profile.active_goal.trim() ? profile.active_goal.trim() : null;
  const pinnedMemory: string[] = Array.isArray(profile?.pinned_memory)
    ? profile.pinned_memory.filter(Boolean).map((item: unknown) => String(item)).slice(0, 5)
    : [];
  const heartbeatTime = heartbeat?.last_heartbeat_at ? formatHeartbeatTime(heartbeat.last_heartbeat_at, locale) : null;
  const heartbeatSummary = locale === "en" ? null : heartbeat?.summary_text ? formatHeartbeatSummary(heartbeat.summary_text, profile) : null;

  if (!profile && !heartbeat) {
    return null;
  }

  return (
    <details className="memory-panel memory-disclosure">
      <summary><span>{t("记忆")}</span><span>{lastStock || (locale === "en" ? "No saved company" : "暂无标的")} · {preferredMarket}</span></summary>

      <div className="memory-metric-grid">
        <div className="memory-metric">
          <span>{t("偏好市场")}</span>
          <strong>{preferredMarket}</strong>
        </div>
        <div className="memory-metric">
          <span>{t("最近标的")}</span>
          <strong>{lastStock || t("暂无")}</strong>
        </div>
      </div>

      {activeGoal ? (
        <div className="memory-metric" style={{ marginTop: 12 }}>
          <span>{t("当前目标")}</span>
          <strong>{activeGoal}</strong>
          {locale === "en" && /[\u3400-\u9fff]/.test(activeGoal) ? <small>Saved in its original language</small> : null}
        </div>
      ) : null}

      {watchlist.length ? (
        <div className="memory-watchlist">
          {watchlist.slice(0, 5).map((item) => (
            <span className="tag" key={item.code}>
              {item.name || item.code}
            </span>
          ))}
        </div>
      ) : null}

      {pinnedMemory.length ? (
        <div className="memory-watchlist">
          {pinnedMemory.map((item) => (
            <span className="tag" key={String(item)}>
              {String(item)}
            </span>
          ))}
        </div>
      ) : null}

      {heartbeatSummary ? <p className="memory-summary">{heartbeatSummary}</p> : null}
      {heartbeatTime ? <p className="memory-footnote">{t("上次整理 ·")}{heartbeatTime}</p> : null}
    </details>
  );
}

function formatMarketPreference(value?: string | null) {
  if (value === "a_share") return "A股";
  if (value === "hk") return "港股";
  if (value === "us") return "美股";
  return "未形成";
}

function formatHeartbeatTime(value: string, locale: "en" | "zh") {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(locale === "en" ? "en-US" : "zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatHeartbeatSummary(
  raw: string,
  profile?: { preferred_market?: string | null; active_goal?: string | null } | null,
) {
  let text = (raw || "").trim();
  if (!text) return "";

  // 去掉前缀里的 session / 时间戳等技术字段
  text = text.replace(/会话\s+session-[^。]+。?/u, "").trim();

  // 如果有“关注清单：”，说明后面是细节列表，可以省略
  const watchlistIndex = text.indexOf("关注清单：");
  if (watchlistIndex > 0) {
    text = text.slice(0, watchlistIndex).trim();
  }

  const pinnedIndex = text.indexOf("固定记忆：");
  if (pinnedIndex > 0) {
    text = text.slice(0, pinnedIndex).trim();
  }

  // 统一偏好市场文案
  if (profile?.preferred_market === "a_share") {
    text = text.replace(/偏好市场：?a_share/gi, "偏好市场：A股");
  } else if (profile?.preferred_market === "hk") {
    text = text.replace(/偏好市场：?hk/gi, "偏好市场：港股");
  }

  if (profile?.active_goal) {
    text = text.replace(/当前目标：?\s*/g, "当前目标：");
  }

  // 限制长度，避免一整段塞满
  return text.length > 80 ? `${text.slice(0, 80).trim()}…` : text;
}
