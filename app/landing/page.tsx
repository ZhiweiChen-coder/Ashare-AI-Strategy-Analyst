import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
import { LandingHeader } from "@/components/landing-header";
import { SignalRibbon } from "@/components/signal-ribbon";
import { LandingWorkflows } from "@/components/landing-workflows";
import { LandingJournal } from "@/components/landing-journal";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import { landingDetails } from "@/lib/landing-details";
import { landingStructuredData, localizedMetadata, serializeStructuredData } from "@/lib/seo";
import styles from "@/app/landing.module.css";
import content from "@/app/landing-content.module.css";

const repository = "https://github.com/ZhiweiChen-coder/OpenAshare";
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
  const detail = landingDetails[language];
  const workHref = `/work?lang=${language}`;
  const structuredData = landingStructuredData(language, copy.description);
  const faqData = { "@context": "https://schema.org", "@type": "FAQPage", inLanguage: language === "zh" ? "zh-CN" : "en", mainEntity: detail.faqs.map(item => ({ "@type": "Question", name: item.title, acceptedAnswer: { "@type": "Answer", text: item.body } })) };
  return <div className={styles.page} lang={language === "zh" ? "zh-CN" : "en"}>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: serializeStructuredData([structuredData, faqData]) }} />
    <LandingHeader language={language}/>
    <main id="content">
      <section className={`${content.hero} ${styles.wrap}`} aria-labelledby="hero-title">
        <div className={content.heroCopy}>
          <p className={content.beta}>{detail.beta}</p>
          <h1 id="hero-title">{copy.headline}</h1>
          <p className={content.support}>{copy.support}</p>
          <div className={content.actions}><Link className={styles.primary} href={workHref}>{copy.primary}</Link><a className={styles.textButton} href="#demo">{copy.secondary}<span aria-hidden="true">↓</span></a></div>
          <p className={content.trust}>{detail.trust}</p>
        </div>
        <SignalRibbon language={language}/>
      </section>
      <section className={`${content.section} ${styles.wrap}`} id="experience" aria-labelledby="experience-title">
        <div className={content.sectionHeading}><h2 id="experience-title">{copy.experienceTitle}</h2><span>{language === "en" ? "Recorded in the research desk" : "来自研究工作台的实际录屏"}</span></div>
        <LandingWorkflows language={language}/>
      </section>
      <section className={content.openSource} id="open-source" aria-labelledby="source-title">
        <div className={`${styles.wrap} ${content.sourceGrid}`}>
          <div><span className={content.license}>MIT / Open source</span><h2 id="source-title">{detail.sourceTitle}</h2><p>{detail.sourceBody}</p><a className={content.sourceLink} href={repository} target="_blank" rel="noopener noreferrer">{detail.sourceLink} ↗</a></div>
          <div className={content.quickstart}><h3>{detail.setupTitle}</h3><ol>{detail.setupSteps.map(step => <li key={step}>{step}</li>)}</ol><a href={`${repository}#run-locally`} target="_blank" rel="noopener noreferrer">{detail.setupLink} ↗</a></div>
        </div>
      </section>
      <section className={`${content.section} ${styles.wrap}`} id="faq" aria-labelledby="faq-title">
        <div className={content.sectionHeading}><h2 id="faq-title">{detail.faqTitle}</h2></div>
        <div className={content.faq}>{detail.faqs.map((item, index) => <details key={item.title} id={index === 5 ? "data-handling" : undefined}><summary>{item.title}<span aria-hidden="true">+</span></summary><p>{item.body}</p></details>)}</div>
      </section>
      <section className={`${content.section} ${styles.wrap}`} id="journal" aria-labelledby="journal-title"><div className={content.sectionHeading}><h2 id="journal-title">{detail.journal}</h2></div><LandingJournal language={language}/></section>
      <section className={`${content.closing} ${styles.wrap}`}><div><h2>{detail.closing}</h2><p>{detail.closingBody}</p></div><Link className={styles.primary} href={workHref}>{copy.primary}</Link></section>
    </main>
    <footer className={content.footer}><div className={styles.wrap}><div className={content.footerTop}><Link href={`/landing?lang=${language}`} className={styles.footerBrand}>OpenAshare</Link><div><a href="#data-handling">{detail.data}</a><a href={`${repository}/issues`} target="_blank" rel="noopener noreferrer">{detail.contact} ↗</a><a href={repository} target="_blank" rel="noopener noreferrer">GitHub ↗</a><Link href={`/landing?lang=${language === "en" ? "zh" : "en"}`}>{language === "en" ? "中文" : "English"}</Link></div></div><p>{detail.risk}</p><p>{detail.credits}</p><a href="https://github.com/ZhiweiChen-coder" target="_blank" rel="noopener noreferrer">{detail.maintainer} ↗</a></div></footer>
  </div>;
}
