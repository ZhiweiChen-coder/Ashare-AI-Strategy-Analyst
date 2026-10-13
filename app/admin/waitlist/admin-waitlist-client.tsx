"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { User } from "@supabase/supabase-js";

import { useLanguage } from "@/components/language-provider";
import { SupabaseAuthPanel, type SupabaseAuthSnapshot } from "@/components/supabase-auth-panel";
import type { WaitlistApplication, WaitlistApplicationStatus } from "@/lib/types";
import { createClient } from "@/utils/supabase/client";

import styles from "./admin-waitlist.module.css";

const statusLabels: Record<WaitlistApplicationStatus, { en: string; zh: string }> = {
  submitted: { en: "Submitted", zh: "待审核" },
  reviewing: { en: "Under review", zh: "审核中" },
  invited: { en: "Invited", zh: "已邀请" },
  declined: { en: "Declined", zh: "暂不邀请" },
};

const experienceLabels: Record<WaitlistApplication["investment_experience"], { en: string; zh: string }> = {
  beginner: { en: "Just getting started", zh: "刚开始投资" },
  one_to_three_years: { en: "1–3 years", zh: "1–3 年" },
  three_to_five_years: { en: "3–5 years", zh: "3–5 年" },
  five_plus_years: { en: "5+ years", zh: "5 年以上" },
};

const storedLabels: Record<string, { en: string; zh: string }> = {
  美股: { en: "US stocks", zh: "美股" },
  内地股票: { en: "Mainland China stocks", zh: "内地股票" },
  香港股票: { en: "Hong Kong stocks", zh: "香港股票" },
  个股研究: { en: "Company research", zh: "个股研究" },
  市场与热点跟踪: { en: "Markets and themes", zh: "市场与热点跟踪" },
  持仓复盘: { en: "Portfolio review", zh: "持仓复盘" },
  建立研究工作流: { en: "Build a research workflow", zh: "建立研究工作流" },
};

function readableError(error: unknown, en: boolean) {
  const message = error instanceof Error ? error.message : en ? "Could not load applications." : "暂时无法读取申请记录。";
  if (message.includes("waitlist_applications") || message.includes("admin_users")) {
    return en ? "The waitlist admin is not configured. Apply the Supabase 0004 migration first." : "等待名单后台尚未配置完成，请先执行 Supabase 的 0004 数据库迁移。";
  }
  return message;
}

function formatDate(value: string, en: boolean) {
  return new Intl.DateTimeFormat(en ? "en-US" : "zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function AdminWaitlistClient() {
  const { locale } = useLanguage();
  const en = locale === "en";
  const [user, setUser] = useState<User | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
  const [applications, setApplications] = useState<WaitlistApplication[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadAdminData = useCallback(async (nextUser: User) => {
    setIsChecking(true);
    setError("");
    try {
      const supabase = createClient();
      const { data: adminRecord, error: roleError } = await supabase
        .from("admin_users")
        .select("user_id")
        .eq("user_id", nextUser.id)
        .maybeSingle();
      if (roleError) throw roleError;
      if (!adminRecord) {
        setIsAdmin(false);
        setApplications([]);
        return;
      }
      setIsAdmin(true);
      const { data, error: applicationsError } = await supabase
        .from("waitlist_applications")
        .select("*")
        .order("created_at", { ascending: false });
      if (applicationsError) throw applicationsError;
      setApplications((data ?? []) as WaitlistApplication[]);
    } catch (loadError) {
      setIsAdmin(false);
      setError(readableError(loadError, en));
    } finally {
      setIsChecking(false);
    }
  }, [en]);

  useEffect(() => {
    if (user) {
      void loadAdminData(user);
    } else {
      setIsAdmin(null);
      setApplications([]);
    }
  }, [loadAdminData, user]);

  const handleAuthChange = useCallback((snapshot: SupabaseAuthSnapshot) => {
    setUser(snapshot.user);
    setAuthError(snapshot.error);
  }, []);

  const stats = useMemo(() => ({
    total: applications.length,
    submitted: applications.filter((item) => item.status === "submitted").length,
    invited: applications.filter((item) => item.status === "invited").length,
  }), [applications]);

  async function updateStatus(application: WaitlistApplication, status: WaitlistApplicationStatus) {
    setUpdatingId(application.id);
    setError("");
    setMessage("");
    try {
      if (status === "invited") {
        const response = await fetch("/api/admin/waitlist/invite", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ applicationId: application.id, language: locale }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(typeof payload?.error === "string" ? payload.error : en ? "Could not send the invitation email." : "邀请邮件发送失败。");
        }
        setApplications((items) => items.map((item) => item.id === application.id ? payload.application as WaitlistApplication : item));
        setMessage(en ? `Invitation sent to ${application.email}.` : payload.message ?? `邀请邮件已发送至 ${application.email}。`);
        return;
      }

      const supabase = createClient();
      const { data, error: updateError } = await supabase
        .from("waitlist_applications")
        .update({ status })
        .eq("id", application.id)
        .select("*")
        .single();
      if (updateError) throw updateError;
      setApplications((items) => items.map((item) => item.id === application.id ? data as WaitlistApplication : item));
    } catch (updateError) {
      setError(readableError(updateError, en));
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <a className={styles.brand} href={`/landing?lang=${locale}`} aria-label={en ? "Open the OpenAshare home page" : "前往 OpenAshare 首页"}>
          <img src="/favicon.svg" alt="" width="32" height="32" />
          <span>OpenAshare <small>ADMIN</small></span>
        </a>
        <SupabaseAuthPanel placement="header" onAuthChange={handleAuthChange} />
      </header>

      <section className={styles.content} aria-labelledby="admin-title">
        <div className={styles.heading}>
          <p>PRIVATE OPERATIONS</p>
          <h1 id="admin-title">{en ? "Waitlist administration" : "等待名单管理"}</h1>
          <span>{en ? "Authorized administrators can review applications and update their status here." : "此页面仅供已授权管理员查看与更新申请状态。"}</span>
        </div>

        {!user ? <div className={styles.notice}>{en ? "Sign in with an administrator account." : "请使用管理员账号登录。"}</div> : null}
        {authError ? <div className={styles.error}>{authError}</div> : null}
        {isChecking ? <div className={styles.notice}>{en ? "Checking administrator access…" : "正在验证管理员权限…"}</div> : null}
        {user && isAdmin === false && !isChecking ? <div className={styles.denied}>{en ? "This account does not have admin access. No application data was loaded." : "当前账号没有后台访问权限。申请数据未被加载。"}</div> : null}
        {error ? <div className={styles.error}>{error}</div> : null}
        {message ? <div className={styles.success}>{message}</div> : null}

        {isAdmin ? (
          <>
            <div className={styles.stats}>
              <div><strong>{stats.total}</strong><span>{en ? "All applications" : "全部申请"}</span></div>
              <div><strong>{stats.submitted}</strong><span>{en ? "Submitted" : "待审核"}</span></div>
              <div><strong>{stats.invited}</strong><span>{en ? "Invited" : "已邀请"}</span></div>
            </div>
            <div className={styles.list}>
              {applications.length === 0 ? <div className={styles.notice}>{en ? "There are no waitlist applications yet." : "还没有等待名单申请。"}</div> : applications.map((application) => (
                <article className={styles.application} key={application.id}>
                  <div className={styles.applicationTop}>
                    <div>
                      <strong>{application.email}</strong>
                      <span>{formatDate(application.created_at, en)}</span>
                    </div>
                    <select value={application.status} disabled={updatingId === application.id} onChange={(event) => void updateStatus(application, event.target.value as WaitlistApplicationStatus)} aria-label={en ? `Update application status for ${application.email}` : `更新 ${application.email} 的申请状态`}>
                      {Object.entries(statusLabels).map(([value, labels]) => <option key={value} value={value}>{labels[en ? "en" : "zh"]}</option>)}
                    </select>
                  </div>
                  <dl>
                    <div><dt>{en ? "Experience" : "经历"}</dt><dd>{experienceLabels[application.investment_experience][en ? "en" : "zh"]}</dd></div>
                    <div><dt>{en ? "Markets" : "市场"}</dt><dd>{application.focus_markets.map((item) => storedLabels[item]?.[en ? "en" : "zh"] ?? item).join(en ? ", " : "、") || (en ? "Not provided" : "未填写")}</dd></div>
                    <div><dt>{en ? "Goals" : "目标"}</dt><dd>{application.research_goals.map((item) => storedLabels[item]?.[en ? "en" : "zh"] ?? item).join(en ? ", " : "、") || (en ? "Not provided" : "未填写")}</dd></div>
                  </dl>
                  {application.note ? <p className={styles.note}>{application.note}</p> : null}
                </article>
              ))}
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
