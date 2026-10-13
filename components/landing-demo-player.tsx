"use client";

import { useEffect, useId, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import styles from "@/app/landing.module.css";

type DemoMedia = { src: string; poster: string; duration: number };

function timestamp(seconds: number) {
  const value = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
}

function PlaybackIcon({ playing, ended }: { playing: boolean; ended: boolean }) {
  return <svg viewBox="0 0 24 24" aria-hidden="true">
    {ended ? <path d="M5 8a8 8 0 1 1-1 8M5 3v5H0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      : playing ? <><rect x="6" y="4" width="4" height="16" rx="1.3" /><rect x="14" y="4" width="4" height="16" rx="1.3" /></>
        : <path d="M8.5 4.9C7.1 4 5.4 5 5.4 6.6v10.8c0 1.6 1.7 2.6 3.1 1.7l8.8-5.4c1.3-.8 1.3-2.6 0-3.4Z" />}
  </svg>;
}

export function LandingDemoPlayer({ media, label, language }: { media: DemoMedia; label: string; language: LandingLanguage }) {
  const copy = landingCopy[language];
  const player = useRef<HTMLVideoElement>(null);
  const frame = useRef<HTMLDivElement>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const keyboardFocus = useRef(false);
  const optionsPanel = useRef<HTMLDivElement>(null);
  const moreButton = useRef<HTMLButtonElement>(null);
  const optionsId = useId();
  const [playing, setPlaying] = useState(false);
  const [ended, setEnded] = useState(false);
  const [visible, setVisible] = useState(true);
  const [muted, setMuted] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const [duration, setDuration] = useState(media.duration);
  const [rate, setRate] = useState(1);
  const [fullscreen, setFullscreen] = useState(false);
  const [error, setError] = useState(false);
  const [fullscreenError, setFullscreenError] = useState(false);
  const [optionsOpen, setOptionsOpen] = useState(false);

  function clearHideTimer() {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    hideTimer.current = null;
  }

  function revealControls() {
    clearHideTimer();
    setVisible(true);
    if (player.current && !player.current.paused && !keyboardFocus.current && !optionsPanel.current) {
      hideTimer.current = setTimeout(() => { if (!optionsPanel.current) setVisible(false); }, 2200);
    }
  }

  useEffect(() => {
    const video = player.current;
    const onFullscreen = () => setFullscreen(document.fullscreenElement === frame.current);
    document.addEventListener("fullscreenchange", onFullscreen);
    return () => {
      document.removeEventListener("fullscreenchange", onFullscreen);
      if (hideTimer.current) clearTimeout(hideTimer.current);
      video?.pause();
    };
  }, []);

  useEffect(() => {
    if (optionsOpen) optionsPanel.current?.querySelector("select")?.focus();
  }, [optionsOpen]);

  async function togglePlayback() {
    const video = player.current;
    if (!video) return;
    if (!video.paused) {
      video.pause();
      return;
    }
    if (video.ended) video.currentTime = 0;
    setError(false);
    try {
      await video.play();
    } catch (reason) {
      if (player.current === video && !(reason instanceof DOMException && reason.name === "AbortError")) setError(true);
    }
  }

  function seek(seconds: number) {
    const video = player.current;
    if (!video || video.readyState < 1) return;
    video.currentTime = Math.min(duration, Math.max(0, seconds));
    setElapsed(video.currentTime);
    setEnded(false);
    revealControls();
  }

  function toggleMute() {
    if (player.current) player.current.muted = !player.current.muted;
  }

  async function toggleFullscreen() {
    setFullscreenError(false);
    try {
      if (document.fullscreenElement === frame.current) await document.exitFullscreen();
      else if (frame.current?.requestFullscreen) await frame.current.requestFullscreen();
      else {
        const video = player.current as (HTMLVideoElement & { webkitEnterFullscreen?: () => void }) | null;
        if (video?.webkitEnterFullscreen) video.webkitEnterFullscreen();
        else setFullscreenError(true);
      }
    } catch {
      setFullscreenError(true);
    }
    revealControls();
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape" && optionsOpen) {
      event.preventDefault();
      setOptionsOpen(false);
      moreButton.current?.focus();
      return;
    }
    if ((event.target as HTMLElement).closest("button, input, select, a")) return;
    if ([" ", "k", "K"].includes(event.key)) { event.preventDefault(); void togglePlayback(); }
    else if (event.key === "ArrowRight" || event.key === "ArrowLeft") { event.preventDefault(); seek(elapsed + (event.key === "ArrowRight" ? 5 : -5)); }
    else if (event.key.toLowerCase() === "m") { event.preventDefault(); toggleMute(); }
    else if (event.key.toLowerCase() === "f") { event.preventDefault(); void toggleFullscreen(); }
  }

  const playbackLabel = ended ? copy.replayVideo : playing ? copy.pauseVideo : copy.playVideo;
  const controlsVisible = !playing || visible;
  const progress = duration > 0 ? Math.min(100, elapsed / duration * 100) : 0;

  return <>
    <div
      ref={frame}
      className={styles.demoPlayer}
      role="group"
      aria-label={`${label} · ${copy.videoPlayer}`}
      tabIndex={0}
      data-controls={controlsVisible ? "visible" : "hidden"}
      data-playing={playing}
      onKeyDown={onKeyDown}
      onPointerMove={revealControls}
      onPointerDown={event => { keyboardFocus.current = false; if (optionsPanel.current && !optionsPanel.current.contains(event.target as Node) && !moreButton.current?.contains(event.target as Node)) setOptionsOpen(false); revealControls(); }}
      onPointerLeave={() => { if (player.current && !player.current.paused && !keyboardFocus.current && !optionsPanel.current) { clearHideTimer(); setVisible(false); } }}
      onFocusCapture={event => { if ((event.target as HTMLElement).matches(":focus-visible")) { keyboardFocus.current = true; clearHideTimer(); setVisible(true); } }}
      onBlurCapture={event => { if (!event.currentTarget.contains(event.relatedTarget)) { keyboardFocus.current = false; setOptionsOpen(false); revealControls(); } }}
    >
      <video
        ref={player}
        className={styles.workflowDemoVideo}
        src={media.src}
        poster={media.poster}
        muted
        playsInline
        preload="metadata"
        aria-label={label}
        onLoadedMetadata={event => { const value = event.currentTarget.duration; if (Number.isFinite(value)) setDuration(value); }}
        onTimeUpdate={event => setElapsed(event.currentTarget.currentTime)}
        onPlay={() => { setPlaying(true); setEnded(false); revealControls(); }}
        onPause={() => { setPlaying(false); clearHideTimer(); setVisible(true); }}
        onEnded={() => { setEnded(true); setPlaying(false); clearHideTimer(); setVisible(true); }}
        onVolumeChange={event => setMuted(event.currentTarget.muted)}
        onError={() => setError(true)}
      />
      <button type="button" className={styles.demoSurface} aria-label={playbackLabel} onClick={() => void togglePlayback()}>
        <span className={styles.demoCenterControl}><PlaybackIcon playing={playing} ended={ended} /></span>
      </button>
      <div className={styles.demoControls}>
        <button type="button" className={styles.demoControlButton} aria-label={playbackLabel} title={playbackLabel} onClick={() => void togglePlayback()}><PlaybackIcon playing={playing} ended={ended} /></button>
        <span className={styles.demoTime} aria-hidden="true">{timestamp(elapsed)} <span>| {timestamp(duration)}</span></span>
        <input
          type="range"
          className={styles.demoSeek}
          aria-label={copy.videoTimeline}
          aria-valuetext={`${timestamp(elapsed)} / ${timestamp(duration)}`}
          min={0}
          max={duration}
          step={0.1}
          value={elapsed}
          style={{ "--video-progress": `${progress}%` } as CSSProperties}
          onChange={event => seek(Number(event.target.value))}
        />
        <button type="button" className={`${styles.demoControlButton} ${styles.demoMuteControl}`} aria-label={muted ? copy.unmuteVideo : copy.muteVideo} title={muted ? copy.unmuteVideo : copy.muteVideo} onClick={toggleMute}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4Z" />{muted ? <path d="m3 3 18 18" /> : <><path d="M15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14" /></>}</svg>
        </button>
        <button type="button" className={`${styles.demoControlButton} ${styles.demoFullscreenControl}`} aria-label={fullscreen ? copy.exitVideoFullscreen : copy.videoFullscreen} title={fullscreen ? copy.exitVideoFullscreen : copy.videoFullscreen} onClick={() => void toggleFullscreen()}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{fullscreen ? <path d="M14 3v7h7m-7 0 7-7M10 21v-7H3m7 0-7 7" /> : <path d="M14 3h7v7m0-7-7 7M10 21H3v-7m0 7 7-7" />}</svg>
        </button>
        <button ref={moreButton} type="button" className={`${styles.demoControlButton} ${styles.demoMoreControl}`} aria-label={copy.videoMore} title={copy.videoMore} aria-haspopup="dialog" aria-expanded={optionsOpen} aria-controls={optionsId} onClick={() => { clearHideTimer(); setVisible(true); setOptionsOpen(value => !value); }}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" /></svg>
        </button>
      </div>
      {optionsOpen ? <div ref={optionsPanel} id={optionsId} className={styles.demoOptions} role="dialog" aria-label={copy.videoOptions}>
        <label><span>{copy.videoSpeed}</span><select aria-label={copy.videoSpeed} value={rate} onChange={event => { const next = Number(event.target.value); if (player.current) player.current.playbackRate = next; setRate(next); }}>
          {[0.5, 1, 1.5, 2].map(speed => <option value={speed} key={speed}>{speed}×</option>)}
        </select></label>
      </div> : null}
    </div>
    {error || fullscreenError ? <p className={styles.workflowMediaError} role="status">{error ? copy.videoUnavailable : copy.videoFullscreenUnavailable} <a href={media.src} target="_blank" rel="noopener noreferrer">{copy.openVideo} ↗</a></p> : null}
  </>;
}
