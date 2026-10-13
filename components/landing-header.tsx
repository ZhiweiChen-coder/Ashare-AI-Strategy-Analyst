"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import styles from "@/app/landing.module.css";

export function LandingHeader({ language, sectionBase = "" }: { language: LandingLanguage; sectionBase?: string }) {
  const copy = landingCopy[language];
  const sectionHref = (section: string) => `${sectionBase}#${section}`;
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setOpen(false); menuRef.current?.focus(); }
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);
  return (
    <header className={styles.header}>
      <a className={styles.skip} href="#content">{copy.skip}</a>
      <nav className={`${styles.wrap} ${styles.nav}`} aria-label={language === "en" ? "Main navigation" : "主导航"}>
        <Link href={`/landing?lang=${language}`} className={styles.brand}>
          <Image src="/favicon.svg" width={34} height={34} alt="" priority />
          OpenAshare
        </Link>
        <div className={styles.navLinks} id="landing-navigation" data-open={open}>
          <a href={sectionHref("experience")} onClick={() => setOpen(false)}>{copy.experience}</a>
          <a href={sectionHref("journal")} onClick={() => setOpen(false)}>{copy.journal}</a>
          <a href={sectionHref("approach")} onClick={() => setOpen(false)}>{copy.approach}</a>
          <a href="https://github.com/ZhiweiChen-coder/OpenAshare" target="_blank" rel="noopener noreferrer">GitHub <span aria-hidden="true">↗</span></a>
          <Link className={styles.mobileBeta} href={`/waitlist?lang=${language}`}>{copy.beta} <span aria-hidden="true">↗</span></Link>
        </div>
        <div className={styles.navRight}>
          <Link className={styles.language} href={`/landing?lang=${language === "en" ? "zh" : "en"}`} aria-label={language === "en" ? "切换为中文" : "Switch to English"} hrefLang={language === "en" ? "zh" : "en"}>{language === "en" ? "中文" : "EN"}</Link>
          <Link className={styles.navBeta} href={`/waitlist?lang=${language}`}>{copy.beta} <span aria-hidden="true">↗</span></Link>
          <button ref={menuRef} className={styles.menuButton} type="button" aria-label={open ? copy.close : copy.menu} aria-expanded={open} aria-controls="landing-navigation" onClick={() => setOpen(!open)}>
            {open ? <span aria-hidden="true">×</span> : <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M3 6h14M3 14h14" fill="none" stroke="currentColor" strokeWidth="1.5" /></svg>}
          </button>
        </div>
      </nav>
    </header>
  );
}
