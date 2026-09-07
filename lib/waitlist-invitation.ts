const RESEND_ENDPOINT = "https://api.resend.com/emails";

type SendWaitlistInvitationInput = {
  to: string;
  siteUrl: string;
};

type SendWaitlistInvitationResult = {
  id: string | null;
};

function getRequiredEnv(name: string) {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export async function sendWaitlistInvitation({ to, siteUrl }: SendWaitlistInvitationInput): Promise<SendWaitlistInvitationResult> {
  const apiKey = getRequiredEnv("RESEND_API_KEY");
  const from = getRequiredEnv("RESEND_FROM_EMAIL");
  const fromName = process.env.RESEND_FROM_NAME?.trim() || "OpenAshare";
  const loginUrl = `${siteUrl.replace(/\/$/, "")}/work`;
  const safeLoginUrl = escapeHtml(loginUrl);

  const response = await fetch(RESEND_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: `${fromName} <${from}>`,
      to: [to],
      subject: "你已获邀加入 OpenAshare 云端 Beta",
      text: [
        "你好，",
        "",
        "你已获邀加入 OpenAshare 云端 Beta。请打开以下链接进入研究工作台，并使用这个邮箱登录或注册：",
        loginUrl,
        "",
        "如果你还没有账号，请先点击“注册”；如果已经注册，直接登录即可。",
        "",
        "OpenAshare 团队",
      ].join("\n"),
      html: `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #25221f; line-height: 1.7; max-width: 560px;">
          <h2 style="margin-bottom: 16px;">你已获邀加入 OpenAshare 云端 Beta</h2>
          <p>你好，</p>
          <p>你已获邀加入 OpenAshare 云端 Beta。请打开以下链接进入研究工作台，并使用这个邮箱登录或注册：</p>
          <p><a href="${safeLoginUrl}" style="display: inline-block; padding: 10px 18px; background: #171613; color: #fff; text-decoration: none; border-radius: 6px;">打开 OpenAshare</a></p>
          <p style="color: #6e6961; font-size: 14px;">如果按钮无法打开，请复制此链接：${safeLoginUrl}</p>
          <p>如果你还没有账号，请先点击“注册”；如果已经注册，直接登录即可。</p>
          <p>OpenAshare 团队</p>
        </div>
      `,
    }),
    cache: "no-store",
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload?.message === "string" ? payload.message : `Email provider returned ${response.status}`;
    throw new Error(message);
  }

  return { id: typeof payload?.id === "string" ? payload.id : null };
}
