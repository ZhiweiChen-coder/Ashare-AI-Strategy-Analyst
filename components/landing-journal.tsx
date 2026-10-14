import Link from "next/link";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import styles from "@/app/landing.module.css";

export function LandingJournal({ language }: { language: LandingLanguage }) {
  const copy = landingCopy[language];

  return (
    <div className={styles.journalGrid}>
      {copy.articles.map((item) => (
        <Link
          key={item.slug || item.title}
          href={`/journal/${item.slug}?lang=${language}`}
          className={styles.journalCard}
        >
          <div className={styles.journalMeta}>
            <span>{item.concept || copy.concept}</span>
            <span className={styles.journalMetaDivider} aria-hidden="true">·</span>
            <span>{item.category}</span>
          </div>
          <h3>{item.title}</h3>
          <span className={styles.journalLink}>
            {copy.explore}
            <span aria-hidden="true">→</span>
          </span>
        </Link>
      ))}
    </div>
  );
}
