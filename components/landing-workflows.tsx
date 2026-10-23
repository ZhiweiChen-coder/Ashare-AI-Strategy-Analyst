"use client";

import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import { LandingDemoPlayer } from "@/components/landing-demo-player";
import styles from "@/app/landing.module.css";

const demoMedia = {
  src: "/marketing/openashare-30s-product.mp4",
  poster: "/marketing/openashare-30s-product.jpg",
  duration: 30,
};

export function LandingWorkflows({ language }: { language: LandingLanguage }) {
  const copy = landingCopy[language];
  const item = copy.workflowDemo;

  return <div className={styles.workflowShowcase} id="demo">
    <div className={styles.workflowContent}>
      <figure className={styles.workflowDemo} aria-label={item.label}>
        <LandingDemoPlayer media={demoMedia} label={item.label} language={language} />
      </figure>
      <div className={styles.workflowCopy}>
        <div><h3>{item.title}</h3></div>
        <p>{item.description}</p>
      </div>
    </div>
  </div>;
}
