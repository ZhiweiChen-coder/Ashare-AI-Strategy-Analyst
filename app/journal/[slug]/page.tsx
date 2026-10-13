import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cookies } from "next/headers";
import { LandingHeader } from "@/components/landing-header";
import { getJournalArticle } from "@/lib/journal-data";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import { localizedMetadata } from "@/lib/seo";
import styles from "@/app/journal/journal.module.css";
import landingStyles from "@/app/landing.module.css";

type Props = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ lang?: string | string[] }>;
};

async function getLanguage(searchParams: Props["searchParams"]): Promise<LandingLanguage> {
  const { lang } = await searchParams;
  const requested = Array.isArray(lang) ? lang[0] : lang;
  if (requested === "en" || requested === "zh") return requested;
  return (await cookies()).get("openashare-language")?.value === "zh" ? "zh" : "en";
}

export async function generateStaticParams() {
  return [
    { slug: "biotech-headline" },
    { slug: "ai-chip-cycle" },
  ];
}

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  const language = await getLanguage(searchParams);
  const article = getJournalArticle(slug, language);

  if (!article) {
    return { title: "Journal Article Not Found — OpenAshare" };
  }

  return localizedMetadata({
    path: `/journal/${slug}`,
    language,
    title: `${article.title} — OpenAshare Journal`,
    description: article.description,
    indexable: false,
  });
}

export default async function JournalArticlePage({ params, searchParams }: Props) {
  const { slug } = await params;
  const language = await getLanguage(searchParams);
  const article = getJournalArticle(slug, language);

  if (!article) {
    notFound();
  }

  const copy = landingCopy[language];
  const isBiotech = article.slug === "biotech-headline";
  const diagramSteps = language === "zh"
    ? isBiotech
      ? ["临床或监管信息", "公司预期变化", "供应链线索"]
      : ["AI 算力投入", "芯片与基础设施", "供应链线索"]
    : isBiotech
      ? ["Clinical or regulatory signal", "Company outlook", "Supply chain signals"]
      : ["AI investment", "Chip infrastructure", "Supplier signals"];

  return (
    <div className={styles.page} lang={language === "zh" ? "zh-CN" : "en"}>
      <LandingHeader language={language} sectionBase={`/landing?lang=${language}`} />

      <main className={`${styles.main} ${styles.wrap}`} id="content">
        <nav aria-label="Breadcrumb">
          <Link
            href={`/landing?lang=${language}#journal`}
            className={styles.breadcrumb}
          >
            ← {language === "zh" ? "返回研究日志" : "Back to The Journal"}
          </Link>
        </nav>

        <article className={styles.article}>
          <header className={styles.articleHero}>
            <div className={styles.metaRow}>
              <span className={styles.conceptBadge}>
                {article.number} / {article.concept}
              </span>
              <span className={styles.categoryTag}>{article.category}</span>
              <span className={styles.dateTag}>
                {article.date} · {article.readTime}
              </span>
            </div>
            <h1 className={styles.title}>{article.title}</h1>
            <p className={styles.abstract}>{article.description}</p>
            <figure className={styles.diagram} aria-label={language === "zh" ? "研究路径示意图" : "Illustrative research path"}>
              <div className={styles.diagramSteps}>
                {diagramSteps.map((step, index) => (
                  <div className={styles.diagramStep} key={step}>
                    <span className={styles.diagramIndex}>0{index + 1}</span>
                    <span className={styles.diagramNode} aria-hidden="true" />
                    <span className={styles.diagramLabel}>{step}</span>
                  </div>
                ))}
              </div>
              <figcaption className={styles.diagramCaption}>
                {language === "zh" ? "研究路径示意 · 需结合原始来源核验" : "Illustrative research path · verify against primary sources"}
              </figcaption>
            </figure>
          </header>

          <section className={styles.coreQuestionBox} aria-label="Core Question">
            <span className={styles.coreKicker}>
              {language === "zh"
                ? "值得深入追问的核心问题"
                : "THE QUESTION WORTH PURSUING"}
            </span>
            <p className={styles.coreQuestionText}>{article.coreQuestion}</p>
            {article.keyQuestions && article.keyQuestions.length > 0 && (
              <ul className={styles.coreList}>
                {article.keyQuestions.map((q, idx) => (
                  <li key={idx}>
                    <span className={styles.coreNum}>0{idx + 1}</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {article.keyFindings && article.keyFindings.length > 0 && (
            <section className={styles.findingsSection} aria-label="Key Observations">
              <span className={styles.sectionKicker}>
                {language === "zh"
                  ? "核心发现与观察"
                  : "KEY OBSERVATIONS & FINDINGS"}
              </span>
              <div className={styles.findingsGrid}>
                {article.keyFindings.map((finding, idx) => (
                  <div key={idx} className={styles.findingCard}>
                    <h3>{finding.title}</h3>
                    <p>{finding.desc}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {article.sections && article.sections.length > 0 && (
            <section className={styles.sectionsList}>
              {article.sections.map((sec) => (
                <div key={sec.id} className={styles.sectionBlock}>
                  <span className={styles.sectionPill}>
                    {sec.number} / {sec.tag}
                  </span>
                  <h2>{sec.heading}</h2>
                  <p className={styles.sectionLead}>{sec.lead}</p>
                  <div className={styles.paragraphs}>
                    {sec.paragraphs.map((p, pIdx) => (
                      <p key={pIdx}>{p}</p>
                    ))}
                  </div>
                  {sec.callout && (
                    <aside className={styles.callout}>
                      <span className={styles.calloutTitle}>{sec.callout.title}</span>
                      <p>{sec.callout.content}</p>
                    </aside>
                  )}
                </div>
              ))}
            </section>
          )}

          {article.checklist && article.checklist.length > 0 && (
            <section className={styles.checklistSection} aria-label="Analyst Checklist">
              <span className={styles.sectionKicker}>
                {language === "zh" ? "实操清单" : "CHECKLIST"}
              </span>
              <h2>
                {language === "zh"
                  ? "研究工作台核查清单"
                  : "Analyst Verification Checklist"}
              </h2>
              <div className={styles.checklistGrid}>
                {article.checklist.map((item) => (
                  <div key={item.step} className={styles.checklistCard}>
                    <div className={styles.checklistHeader}>
                      <span className={styles.checklistStep}>{item.step}</span>
                      <h3>{item.title}</h3>
                    </div>
                    <p>{item.action}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {article.references && article.references.length > 0 && (
            <section className={styles.referencesSection} aria-label="Primary Sources">
              <span className={styles.sectionKicker}>
                {language === "zh" ? "一手依据" : "SOURCES"}
              </span>
              <h2>
                {language === "zh"
                  ? "原始文献与官方披露依据"
                  : "Primary Sources & Authoritative References"}
              </h2>
              <div className={styles.refGrid}>
                {article.references.map((ref, idx) => (
                  <a
                    key={idx}
                    href={ref.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.refCard}
                  >
                    <div className={styles.refMeta}>
                      <span className={styles.refSource}>{ref.source}</span>
                      <span className={styles.refType}>{ref.type}</span>
                    </div>
                    <h3 className={styles.refTitle}>
                      {ref.title} <span aria-hidden="true">↗</span>
                    </h3>
                    <p className={styles.refCitation}>{ref.citation}</p>
                  </a>
                ))}
              </div>
            </section>
          )}

          <div className={styles.actionBanner}>
            <div className={styles.actionText}>
              <h3>
                {article.actionLabel ||
                  (language === "zh"
                    ? "在研究工作台中深入探索"
                    : "Explore in Research Desk")}
              </h3>
              <p>
                {language === "zh"
                  ? "在 OpenAshare 中调取行情、公告、研报与供应链数据，进行交互式推演。"
                  : "Bring charts, filings, research and supply chain telemetry together in your own research session."}
              </p>
            </div>
            <Link
              href={`/work?lang=${language}&q=${encodeURIComponent(article.actionPrompt)}`}
              className={styles.actionButton}
            >
              {language === "zh" ? "进入工作台研究此课题" : "Open in Research Desk"}{" "}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <p className={styles.disclaimer}>{article.note}</p>
        </article>
      </main>

      <footer className={`${landingStyles.footer} ${styles.wrap}`}>
        <Link href={`/landing?lang=${language}`} className={landingStyles.footerBrand}>
          OpenAshare
        </Link>
        <div>
          <Link href={`/landing?lang=${language}#journal`}>{copy.journal}</Link>
          <a
            href="https://github.com/ZhiweiChen-coder/OpenAshare"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub ↗
          </a>
          <span>{copy.footer}</span>
        </div>
      </footer>
    </div>
  );
}
