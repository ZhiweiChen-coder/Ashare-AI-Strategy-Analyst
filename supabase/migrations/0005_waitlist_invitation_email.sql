-- Track whether the administrator invitation email has been sent.
-- Run after 0004_waitlist_admin.sql.

alter table public.waitlist_applications
  add column if not exists invitation_sent_at timestamptz,
  add column if not exists invitation_email_id text;

notify pgrst, 'reload schema';
