import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
import { LandingHeader } from "@/components/landing-header";
import { SignalRibbon } from "@/components/signal-ribbon";
import { LandingWorkflows } from "@/components/landing-workflows";
import { LandingJournal } from "@/components/landing-journal";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import { landingStructuredData, localizedMetadata, serializeStructuredData } from "@/lib/seo";
import styles from "@/app/landing.module.css";

type Props = { searchParams: Promise<{ lang?: string | string[] }> };
async function getLanguage(searchParams: Props["searchParams"]): Promise<LandingLanguage> {
  const { lang } = await searchParams;
  const requested = Array.isArray(lang) ? lang[0] : lang;
  if (requested === "en" || requested === "zh") return requested;
  return (await cookies()).get("openashare-language")?.value === "zh" ? "zh" : "en";
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const language = await getLanguage(searchParams);
  const copy = landingCopy[language];
  return localizedMetadata({ path: "/landing", language, title: copy.title, description: copy.description });
}

export default async function LandingPage({ searchParams }: Props) {
  const language = await getLanguage(searchParams);
  const copy = landingCopy[language];
  return (
    <div className={styles.page} lang={language === "zh" ? "zh-CN" : "en"}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: serializeStructuredData(landingStructuredData(language, copy.description)) }} />
      <LandingHeader language={language}/>
      <main id="content">
        <section className={`${styles.hero} ${styles.wrap}`} aria-labelledby="hero-title">
          <span className={styles.eyebrow}>{copy.eyebrow}</span>
          <h1 id="hero-title">{copy.headline}<span>{copy.accent}</span></h1>
          <p className={styles.heroSub}>{copy.support}</p>
          <div className={styles.heroActions}>
            <Link className={styles.primary} href={`/work?lang=${language}`}>{copy.primary}<span aria-hidden="true">↗</span></Link>
            <a className={styles.textButton} href="#demo">{copy.secondary}<span aria-hidden="true">↓</span></a>
          </div>
          <SignalRibbon language={language}/>
        </section>
        <section className={`${styles.experienceSection} ${styles.wrap}`} id="experience" aria-labelledby="experience-title">
          <div className={styles.experienceSummary}>
            <h2 id="experience-title">{copy.experienceTitle}</h2>
          </div>
          <LandingWorkflows language={language}/>
        </section>
        <section className={`${styles.journal} ${styles.wrap}`} id="journal" aria-label={copy.journal}>
          <div className={styles.sectionHeader}>
            <div className={styles.journalHeading}>
              <h2 className={styles.sectionLabel}>{copy.journalLabel}</h2>
              <span className={styles.sectionMeta}>{copy.journalMeta}</span>
            </div>
            <svg className={styles.journalDiagram} viewBox="0 0 96 56" aria-hidden="true">
              <path className={styles.journalDiagramLine} d="M17 28H40 M49 26L73 13 M49 30L73 43" />
              <circle className={styles.journalDiagramSource} cx="12" cy="28" r="5" />
              <circle className={styles.journalDiagramNode} cx="45" cy="28" r="6" />
              <circle className={styles.journalDiagramNode} cx="79" cy="10" r="5" />
              <circle className={styles.journalDiagramNode} cx="79" cy="46" r="5" />
            </svg>
          </div>
          <LandingJournal language={language}/>
        </section>
        <section className={`${styles.approach} ${styles.wrap}`} id="approach" aria-labelledby="approach-title">
          <div className={styles.sectionHeader}><span className={styles.sectionLabel}>{copy.approachLabel}</span><span className={styles.sectionMeta}>{copy.approachMeta}</span></div>
          <h2 className={styles.approachTitle} id="approach-title">{copy.approachTitle}</h2>
          <div className={styles.accordion}>{copy.principles.map((item,index) => <details key={item.title}><summary><span className={styles.number}>0{index + 1}</span><span>{item.title}</span><span className={styles.plus} aria-hidden="true">+</span></summary><p>{item.body}</p></details>)}</div>
        </section>
        <section className={styles.closing}>
          <span className={styles.eyebrow}>{copy.closingLabel}</span>
          <h2>{copy.closingTitle}<span>{copy.closingAccent}</span></h2>
          <Link className={styles.primary} href={`/waitlist?lang=${language}`}>{copy.beta}<span aria-hidden="true">↗</span></Link>
          <p>{copy.markets}</p>
        </section>
      </main>
      <footer className={`${styles.footer} ${styles.wrap}`}>
        <Link href={`/landing?lang=${language}`} className={styles.footerBrand}>OpenAshare</Link>
        <div><a href="#experience">{copy.experience}</a><a href="https://github.com/ZhiweiChen-coder/OpenAshare" target="_blank" rel="noopener noreferrer">GitHub ↗</a><span>{copy.footer}</span></div>
      </footer>
    </div>
  );
}
