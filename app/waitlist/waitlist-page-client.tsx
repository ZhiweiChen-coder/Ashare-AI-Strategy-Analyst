"use client";

import { useCallback, useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";

import { SupabaseAuthPanel, type SupabaseAuthSnapshot } from "@/components/supabase-auth-panel";
import { useLanguage } from "@/components/language-provider";
import type { InvestmentExperience, WaitlistApplication } from "@/lib/types";
import { createClient } from "@/utils/supabase/client";

import styles from "./waitlist.module.css";

const experienceOptions: Array<{ value: InvestmentExperience; en: string; zh: string }> = [
  { value: "beginner", en: "Just getting started", zh: "刚开始投资" },
  { value: "one_to_three_years", en: "1–3 years", zh: "1–3 年" },
  { value: "three_to_five_years", en: "3–5 years", zh: "3–5 年" },
  { value: "five_plus_years", en: "5+ years", zh: "5 年以上" },
];

const marketOptions = ["美股", "内地股票", "香港股票"];
const goalOptions = ["个股研究", "市场与热点跟踪", "持仓复盘", "建立研究工作流"];
const optionLabels: Record<string, { en: string; zh: string }> = {
  "美股": { en: "US stocks", zh: "美股" },
  "内地股票": { en: "Mainland China stocks", zh: "内地股票" },
  "香港股票": { en: "Hong Kong stocks", zh: "香港股票" },
  "个股研究": { en: "Company research", zh: "个股研究" },
  "市场与热点跟踪": { en: "Markets and themes", zh: "市场与热点跟踪" },
  "持仓复盘": { en: "Portfolio review", zh: "持仓复盘" },
  "建立研究工作流": { en: "Build a research workflow", zh: "建立研究工作流" },
};

function toggleValue(values: string[], value: string) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function readableError(error: unknown, en: boolean) {
  const message = error instanceof Error ? error.message : en ? "Could not submit the application. Please try again." : "暂时无法提交申请，请稍后重试。";
  if (message.includes("waitlist_applications")) {
    return en ? "The waitlist is not configured. Ask an administrator to apply the latest Supabase migration." : "等待名单尚未配置完成，请管理员先执行最新的 Supabase 数据库迁移。";
  }
  return message;
}

export function WaitlistPageClient() {
  const { locale } = useLanguage();
  const en = locale === "en";
  const [user, setUser] = useState<User | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [application, setApplication] = useState<WaitlistApplication | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [experience, setExperience] = useState<InvestmentExperience>("beginner");
  const [markets, setMarkets] = useState<string[]>([]);
  const [goals, setGoals] = useState<string[]>([]);
  const [note, setNote] = useState("");

  const loadApplication = useCallback(async (nextUser: User) => {
    setIsLoading(true);
    setError("");
    try {
      const supabase = createClient();
      const { data, error: queryError } = await supabase
        .from("waitlist_applications")
        .select("*")
        .eq("user_id", nextUser.id)
        .maybeSingle();
      if (queryError) throw queryError;
      const nextApplication = (data ?? null) as WaitlistApplication | null;
      setApplication(nextApplication);
      if (nextApplication) {
        setExperience(nextApplication.investment_experience);
        setMarkets(nextApplication.focus_markets);
        setGoals(nextApplication.research_goals);
        setNote(nextApplication.note);
      }
    } catch (loadError) {
      setError(readableError(loadError, en));
    } finally {
      setIsLoading(false);
    }
  }, [en]);

  useEffect(() => {
    if (user) {
      void loadApplication(user);
    } else {
      setApplication(null);
      setMessage("");
    }
  }, [loadApplication, user]);

  const handleAuthChange = useCallback((snapshot: SupabaseAuthSnapshot) => {
    setUser(snapshot.user);
    setAuthError(snapshot.error);
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    if (markets.length === 0) {
      setError(en ? "Select at least one market." : "请至少选择一个关注市场。");
      return;
    }
    if (goals.length === 0) {
      setError(en ? "Select at least one research goal." : "请至少选择一个研究目标。");
      return;
    }

    setIsSubmitting(true);
    setMessage("");
    setError("");
    try {
      const supabase = createClient();
      const { data, error: upsertError } = await supabase
        .from("waitlist_applications")
        .upsert(
          {
            user_id: user.id,
            email: user.email ?? "",
            investment_experience: experience,
            focus_markets: markets,
            research_goals: goals,
            note: note.trim(),
          },
          { onConflict: "user_id" },
        )
        .select("*")
        .single();
      if (upsertError) throw upsertError;
      setApplication(data as WaitlistApplication);
      setMessage(en ? "You are on the waitlist. We will contact you at your sign-in email when invitations open." : "已加入等待名单。开放邀请时，我们会通过登录邮箱联系你。");
    } catch (submitError) {
      setError(readableError(submitError, en));
    } finally {
      setIsSubmitting(false);
    }
  }

  const isLocked = application !== null && application.status !== "submitted";

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <a className={styles.brand} href={`/landing?lang=${locale}`} aria-label={en ? "Open the OpenAshare home page" : "前往 OpenAshare 首页"}>
          <img src="/favicon.svg" alt="" width="36" height="36" />
          <span>OpenAshare<small>AI RESEARCH DESK</small></span>
        </a>
        <SupabaseAuthPanel placement="header" onAuthChange={handleAuthChange} />
      </header>

      <section className={styles.content} aria-labelledby="waitlist-title">
        <div className={styles.intro}>
          <p>OPENAShare CLOUD BETA</p>
          <h1 id="waitlist-title">{en ? "Join the waitlist" : "申请加入等待名单"}</h1>
          <p>{en ? "Tell us how you research so we can invite testers at the right pace." : "用一分钟告诉我们你的研究习惯，帮助我们按合适的节奏邀请测试用户。"}</p>
          <ul>
            <li>{en ? "We collect only what is needed for product invitations and research." : "只收集用于产品邀请与研究的必要信息"}</li>
            <li>{en ? "Your application will not be used to provide stock recommendations." : "不会据此提供个股买卖建议"}</li>
            <li>{en ? "You can update your application before it is reviewed." : "提交后可在审核前更新资料"}</li>
          </ul>
        </div>

        <div className={styles.panel}>
          {!user ? (
            <div className={styles.signInState}>
              <strong>{en ? "Sign in to complete your application." : "请先登录，再填写申请。"}</strong>
              <p>{en ? "We will use your sign-in email as the contact address." : "登录邮箱会作为申请的联系邮箱，不需要重复填写。"}</p>
              {authError ? <p className={styles.error}>{authError}</p> : null}
            </div>
          ) : isLoading ? (
            <p className={styles.loading}>{en ? "Loading your application…" : "正在读取你的申请…"}</p>
          ) : (
            <form onSubmit={submit}>
              <div className={styles.emailRow}>
                <span>{en ? "Contact email" : "联系邮箱"}</span>
                <strong>{user.email ?? (en ? "Current account" : "当前登录账户")}</strong>
              </div>

              <fieldset disabled={isLocked || isSubmitting}>
                <legend>{en ? "Your investing experience" : "你的投资经历"}</legend>
                <div className={styles.optionGrid}>
                  {experienceOptions.map((option) => (
                    <label className={styles.option} key={option.value}>
                      <input type="radio" name="experience" value={option.value} checked={experience === option.value} onChange={() => setExperience(option.value)} />
                      <span>{en ? option.en : option.zh}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset disabled={isLocked || isSubmitting}>
                <legend>{en ? "Which markets do you follow?" : "你主要关注哪些市场？"}<small>{en ? "Select all that apply" : "可多选"}</small></legend>
                <div className={styles.optionGrid}>
                  {marketOptions.map((option) => (
                    <label className={styles.option} key={option}>
                      <input type="checkbox" checked={markets.includes(option)} onChange={() => setMarkets((items) => toggleValue(items, option))} />
                      <span>{optionLabels[option]?.[en ? "en" : "zh"] ?? option}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset disabled={isLocked || isSubmitting}>
                <legend>{en ? "What would you most like to solve?" : "你最希望先解决什么？"}<small>{en ? "Select all that apply" : "可多选"}</small></legend>
                <div className={styles.optionGrid}>
                  {goalOptions.map((option) => (
                    <label className={styles.option} key={option}>
                      <input type="checkbox" checked={goals.includes(option)} onChange={() => setGoals((items) => toggleValue(items, option))} />
                      <span>{optionLabels[option]?.[en ? "en" : "zh"] ?? option}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <label className={styles.noteLabel}>
                <span>{en ? "Anything else we should know?" : "还有什么希望我们了解？"}<small>{en ? "Optional · up to 600 characters" : "选填，最多 600 字"}</small></span>
                <textarea value={note} onChange={(event) => setNote(event.target.value.slice(0, 600))} rows={4} disabled={isLocked || isSubmitting} placeholder={en ? "For example, how you organize research today or what you want an agent to help with." : "例如：你现在如何整理研究资料，或期待 Agent 帮上什么忙。"} />
              </label>

              {isLocked ? <p className={styles.status}>{en ? application.status === "invited" ? "Your invitation has been sent. Check your inbox and spam folder." : `Your application is ${application.status === "reviewing" ? "under review" : "being processed"} and cannot be edited right now.` : application.status === "invited" ? "邀请邮件已发送，请查收邮箱；如未收到，请检查垃圾邮件。" : `你的申请正在${application.status === "reviewing" ? "审核" : "处理"}，暂时不能修改。`}</p> : null}
              {error ? <p className={styles.error}>{error}</p> : null}
              {message ? <p className={styles.success}>{message}</p> : null}
              <button className={styles.submit} type="submit" disabled={isLocked || isSubmitting}>{isSubmitting ? en ? "Submitting…" : "提交中…" : application ? en ? "Update application" : "更新申请" : en ? "Submit application" : "提交申请"}</button>
            </form>
          )}
        </div>
      </section>
    </main>
  );
}
