import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function Home({ searchParams }: { searchParams: Promise<{ lang?: string | string[] }> }) {
  const { lang } = await searchParams;
  const requested = Array.isArray(lang) ? lang[0] : lang;
  const saved = (await cookies()).get("openashare-language")?.value;
  const language = requested === "zh" || requested === "en" ? requested : saved === "zh" ? "zh" : "en";
  redirect(`/landing?lang=${language}`);
}
