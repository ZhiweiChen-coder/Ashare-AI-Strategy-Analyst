import type { Metadata } from "next";

import { WaitlistPageClient } from "./waitlist-page-client";

export const metadata: Metadata = {
  title: "Join the beta | OpenAshare",
  description: "Request access to the OpenAshare cloud beta.",
};

export default function WaitlistPage() {
  return <WaitlistPageClient />;
}
