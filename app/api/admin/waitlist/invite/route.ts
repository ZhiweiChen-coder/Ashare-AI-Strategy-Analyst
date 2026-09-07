import { NextResponse } from "next/server";

import { sendWaitlistInvitation } from "@/lib/waitlist-invitation";
import { createClient } from "@/utils/supabase/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type InviteRequest = { applicationId?: unknown };

function errorResponse(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

export async function POST(request: Request) {
  let body: InviteRequest;
  try {
    body = await request.json() as InviteRequest;
  } catch {
    return errorResponse("请求格式无效。", 400);
  }

  const applicationId = typeof body.applicationId === "string" ? body.applicationId.trim() : "";
  if (!applicationId) return errorResponse("缺少申请记录 ID。", 400);

  let supabase;
  try {
    supabase = await createClient();
  } catch {
    return errorResponse("Supabase 尚未配置。", 503);
  }

  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData.user) return errorResponse("请先登录管理员账号。", 401);

  const { data: adminRecord, error: adminError } = await supabase
    .from("admin_users")
    .select("user_id")
    .eq("user_id", userData.user.id)
    .maybeSingle();
  if (adminError) return errorResponse("无法验证管理员权限。", 503);
  if (!adminRecord) return errorResponse("当前账号没有后台访问权限。", 403);

  const { data: application, error: applicationError } = await supabase
    .from("waitlist_applications")
    .select("id, email, status, invitation_sent_at")
    .eq("id", applicationId)
    .maybeSingle();
  if (applicationError) return errorResponse("无法读取申请记录。", 500);
  if (!application) return errorResponse("申请记录不存在。", 404);

  if (application.invitation_sent_at) {
    return NextResponse.json({ alreadySent: true, application, message: "邀请邮件已经发送过。" });
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim() || new URL(request.url).origin;
  let emailId: string | null = null;
  try {
    ({ id: emailId } = await sendWaitlistInvitation({ to: application.email, siteUrl }));
  } catch (sendError) {
    const message = sendError instanceof Error ? sendError.message : "邮件发送失败。";
    if (message === "Missing RESEND_API_KEY" || message === "Missing RESEND_FROM_EMAIL") {
      return errorResponse("邮件服务尚未配置，请设置 RESEND_API_KEY 和 RESEND_FROM_EMAIL。", 503);
    }
    return errorResponse(`邀请邮件发送失败：${message}`, 502);
  }

  const sentAt = new Date().toISOString();
  const { data: updatedApplication, error: updateError } = await supabase
    .from("waitlist_applications")
    .update({ status: "invited", invitation_sent_at: sentAt, invitation_email_id: emailId })
    .eq("id", application.id)
    .select("*")
    .single();
  if (updateError) {
    return errorResponse("邮件已发送，但申请状态记录失败，请不要重复操作，并联系管理员检查数据库。", 500);
  }

  return NextResponse.json({
    alreadySent: false,
    application: updatedApplication,
    message: `邀请邮件已发送至 ${application.email}。`,
  });
}
