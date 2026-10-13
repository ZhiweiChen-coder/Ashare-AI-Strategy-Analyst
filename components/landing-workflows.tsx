"use client";

import { useId, useState, type KeyboardEvent } from "react";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import { LandingDemoPlayer } from "@/components/landing-demo-player";
import styles from "@/app/landing.module.css";

const demoMedia = [
  { src: "/marketing/demo-stock-questions.mp4?v=656aab7e3a8f", poster: "/marketing/demo-stock-questions.jpg?v=4d186819a884", duration: 22.566667 },
  { src: "/marketing/demo-chart-research.mp4?v=72d63aac1c7b", poster: "/marketing/demo-chart-research.jpg?v=2ecc5ef4161e", duration: 26.65 },
  { src: "/marketing/demo-deep-research.mp4?v=ff2f37d1480e", poster: "/marketing/demo-deep-research.jpg?v=25df169a7df0", duration: 95.883333 },
];

export function LandingWorkflows({ language }: { language: LandingLanguage }) {
  const copy = landingCopy[language];
  const [active, setActive] = useState(0);
  const id = useId().replace(/:/g, "");
  const item = copy.workflowItems[active];
  const media = demoMedia[active];
  const panelId = `${id}-panel`;

  function selectDemo(index: number) {
    if (active === index) return;
    setActive(index);
  }

  function onTabKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0
      : event.key === "End" ? copy.workflowItems.length - 1
      : (active + (event.key === "ArrowRight" ? 1 : -1) + copy.workflowItems.length) % copy.workflowItems.length;
    selectDemo(next);
    event.currentTarget.querySelectorAll<HTMLButtonElement>("[role=tab]")[next]?.focus();
  }

  return <div className={styles.workflowShowcase} id="demo">
    <div className={styles.workflowTabs} role="tablist" aria-label={copy.workflowTabsLabel} aria-orientation="horizontal" onKeyDown={onTabKeyDown}>
      {copy.workflowItems.map((workflow, index) => <button
        key={workflow.label}
        className={styles.workflowTab}
        id={`${id}-tab-${index}`}
        type="button"
        role="tab"
        aria-selected={active === index}
        aria-controls={panelId}
        tabIndex={active === index ? 0 : -1}
        onClick={() => selectDemo(index)}
      >
        <span className={styles.workflowTabNumber}>0{index + 1}</span>
        <span>{workflow.label}</span>
        <span className={styles.workflowTabArrow} aria-hidden="true">↗</span>
      </button>)}
    </div>
    <div className={styles.workflowContent} role="tabpanel" id={panelId} aria-labelledby={`${id}-tab-${active}`} tabIndex={0}>
      <figure className={styles.workflowDemo} aria-label={item.label}>
        <LandingDemoPlayer key={media.src} media={media} label={item.label} language={language} />
      </figure>
      <div className={styles.workflowCopy}>
        <div><span className={styles.workflowPreviewLabel}>{item.preview}</span><h3>{item.title}</h3></div>
        <p>{item.description}</p>
      </div>
    </div>
  </div>;
}
