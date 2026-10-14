"use client";

import { useEffect, useId, useRef, useState, type CSSProperties } from "react";
import { landingCopy, type LandingLanguage } from "@/lib/landing-copy";
import { illustrativeSpine, illustrativeStudies, ribbonFold, ribbonHalfWidth, studyX, studyY, type IllustrativeCandle } from "@/lib/illustrative-market";
import styles from "@/app/landing.module.css";

function StaticStudy({ candles, mobile, id }: { candles: IllustrativeCandle[]; mobile?: boolean; id: string }) {
  const points = Array.from({ length: 181 }, (_, i) => {
    const u = i / 180, y = illustrativeSpine(u), width = ribbonHalfWidth(u) * Math.cos(ribbonFold(u));
    return { x: studyX(u), y: studyY(y), top: studyY(y + width), bottom: studyY(y - width) };
  });
  const path = (key: "y" | "top" | "bottom") => points.map((point, i) => `${i ? "L" : "M"}${point.x.toFixed(2)} ${point[key].toFixed(2)}`).join(" ");
  const band = `${path("top")} ${[...points].reverse().map(point => `L${point.x.toFixed(2)} ${point.bottom.toFixed(2)}`).join(" ")} Z`;
  const bodyWidth = 1228 / (candles.length - 1) * .43;
  return <svg className={`${styles.ribbonFallback} ${mobile ? styles.signalMobile : styles.signalDesktop}`} viewBox="0 0 1300 300" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <linearGradient id={id}><stop stopColor="#668f83" stopOpacity=".16"/><stop offset=".4" stopColor="#bed2c5" stopOpacity=".38"/><stop offset=".72" stopColor="#c07a62" stopOpacity=".22"/><stop offset="1" stopColor="#a7c8bb" stopOpacity=".2"/></linearGradient>
      <filter id={`${id}-halo`} x="-10%" y="-50%" width="120%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
    </defs>
    <path d={path("y")} fill="none" stroke={`url(#${id})`} strokeWidth="28" filter={`url(#${id}-halo)`}/>
    <path d={band} fill={`url(#${id})`}/>
    <path d={path("top")} fill="none" stroke="#779f91" strokeWidth=".65" opacity=".3"/>
    <path d={path("y")} fill="none" stroke="#4e776a" strokeWidth="1" strokeLinecap="round" opacity=".45"/>
    {candles.map((bar, i) => <g key={i} className={styles.signalCandle} style={{ "--candle-delay": `${i / candles.length * .8}s`, "--candle-opacity": (.5 + .42 * Math.sin(Math.PI * bar.u) ** .3).toFixed(4) } as CSSProperties} fill={bar.close >= bar.open ? "#527e70" : "#bd674e"} stroke={bar.close >= bar.open ? "#527e70" : "#bd674e"}>
      <line x1={studyX(bar.u)} x2={studyX(bar.u)} y1={studyY(bar.high)} y2={studyY(bar.low)} strokeWidth="1.35"/>
      <rect x={studyX(bar.u) - bodyWidth / 2} y={studyY(Math.max(bar.open, bar.close))} width={bodyWidth} height={Math.max(2.2, Math.abs(studyY(bar.open) - studyY(bar.close)))} rx=".4" stroke="none"/>
    </g>)}
  </svg>;
}

export function SignalRibbon({ language }: { language: LandingLanguage }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{ sync: () => void } | null>(null);
  const pausedRef = useRef(false);
  const [paused, setPaused] = useState(false);
  const [reduced, setReduced] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const id = useId().replace(/:/g, "");
  const copy = landingCopy[language];

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    let disposed = false;
    let cleanupScene: (() => void) | undefined;
    const updatePreference = () => { setReduced(media.matches); sceneRef.current?.sync(); };
    updatePreference();
    media.addEventListener("change", updatePreference);
    // The complete deterministic candle study is already in the server HTML.
    void import("three").then(THREE => {
      if (disposed) return;
      let renderer: InstanceType<typeof THREE.WebGLRenderer>;
      try { renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true }); }
      catch { setUnavailable(true); return; }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      renderer.domElement.setAttribute("aria-hidden", "true");
      host.appendChild(renderer.domElement);
      const scene = new THREE.Scene();
      const camera = new THREE.OrthographicCamera(-5.9, 5.9, 1.7, -1.7, .1, 100);
      camera.position.set(0, 0, 10);
      const xWorld = (u: number) => studyX(u) / 1300 * 11.8 - 5.9;
      const segments = 180, across = 8;
      const positions = new Float32Array((segments + 1) * (across + 1) * 3);
      const uvs = new Float32Array((segments + 1) * (across + 1) * 2);
      const indices: number[] = [];
      for (let i = 0; i <= segments; i++) for (let j = 0; j <= across; j++) {
        const vertex = i * (across + 1) + j;
        uvs[vertex * 2] = i / segments; uvs[vertex * 2 + 1] = j / across;
        if (i < segments && j < across) { const next = vertex + across + 1; indices.push(vertex, next, vertex + 1, next, next + 1, vertex + 1); }
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute("uv", new THREE.BufferAttribute(uvs, 2)); geometry.setIndex(indices);
      const material = new THREE.ShaderMaterial({
        side: THREE.DoubleSide, transparent: true, depthWrite: false,
        uniforms: { uTime: { value: 0 } },
        vertexShader: `varying vec2 vUv; varying vec3 vNormal;
          void main() { vUv = uv; vNormal = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
        fragmentShader: `uniform float uTime; varying vec2 vUv; varying vec3 vNormal;
          void main() {
            vec3 teal = vec3(.31,.49,.42), clay = vec3(.73,.39,.28), paper = vec3(.984,.976,.957);
            float facing = abs(dot(normalize(vNormal), normalize(vec3(.1,.7,1.0))));
            float head = fract(uTime*.035+.1);
            float light = exp(-pow((vUv.x-head)/.075,2.0));
            float warmth = .65*exp(-pow((vUv.x-.72)/.2,2.0));
            vec3 pigment = mix(teal,clay,warmth);
            vec3 color = mix(pigment,paper,.36+facing*.12+vUv.y*.12+light*.16);
            float edge = smoothstep(0.0,.06,vUv.y)*smoothstep(0.0,.06,1.0-vUv.y);
            gl_FragColor = vec4(color,(.24+.10*(1.0-facing)+light*.08)*edge);
          }`,
      });
      const ribbon = new THREE.Mesh(geometry, material);
      ribbon.frustumCulled = false; ribbon.renderOrder = 1; scene.add(ribbon);
      const positionAttribute = geometry.getAttribute("position") as InstanceType<typeof THREE.BufferAttribute>;
      // The halo follows the curve, so illumination stays attached to the silk.
      const haloGeometry = geometry.clone();
      const haloPositions = haloGeometry.getAttribute("position") as InstanceType<typeof THREE.BufferAttribute>;
      const haloMaterial = new THREE.ShaderMaterial({
        transparent: true, depthWrite: false, depthTest: false, side: THREE.DoubleSide,
        uniforms: material.uniforms,
        vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
        fragmentShader: `uniform float uTime; varying vec2 vUv;
          void main() {
            float warmth = .65*exp(-pow((vUv.x-.72)/.2,2.0));
            vec3 color = mix(vec3(.31,.49,.42),vec3(.73,.39,.28),warmth);
            float light = exp(-pow((vUv.x-fract(uTime*.035+.1))/.12,2.0));
            float soft = exp(-pow((vUv.y-.5)*4.6,2.0));
            float ends = smoothstep(0.0,.12,vUv.x)*smoothstep(0.0,.12,1.0-vUv.x);
            gl_FragColor = vec4(color,soft*ends*(.045+light*.04));
          }`,
      });
      const halo = new THREE.Mesh(haloGeometry, haloMaterial);
      halo.frustumCulled = false; halo.renderOrder = 0; scene.add(halo);
      const spineGeometry = new THREE.BufferGeometry();
      spineGeometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array((segments + 1) * 3), 3));
      const spinePositionAttribute = spineGeometry.getAttribute("position") as InstanceType<typeof THREE.BufferAttribute>;
      const spineMaterial = new THREE.LineBasicMaterial({ color: 0x4e776a, transparent: true, opacity: .44, depthTest: false });
      const spine = new THREE.Line(spineGeometry, spineMaterial);
      spine.frustumCulled = false; spine.renderOrder = 1.5; scene.add(spine);
      const uniforms = { uReveal: { value: 0 }, uTime: { value: 0 } };
      const fragmentShader = `uniform float uTime; varying float vUp; varying float vAlpha;
        void main() { vec3 color = mix(vec3(.73,.39,.28),vec3(.31,.49,.42),vUp); gl_FragColor = vec4(color,vAlpha); }`;
      const vertex = (instanced: boolean) => `attribute float aProgress; attribute float aUp; uniform float uReveal;
        varying float vUp; varying float vAlpha;
        void main() {
          vUp = aUp; float fade = .42+.48*pow(max(0.0,sin(aProgress*3.14159265)),.3);
          vAlpha = fade*smoothstep(aProgress*.8,aProgress*.8+.2,uReveal);
          gl_Position = projectionMatrix*modelViewMatrix*${instanced ? "instanceMatrix*" : ""}vec4(position,1.0);
        }`;
      const candleMaterial = new THREE.ShaderMaterial({ uniforms, vertexShader: vertex(true), fragmentShader, transparent: true, depthWrite: false, depthTest: false });
      const wickMaterial = new THREE.ShaderMaterial({ uniforms, vertexShader: vertex(false), fragmentShader, transparent: true, depthWrite: false, depthTest: false });
      const lanes = [illustrativeStudies.desktop, illustrativeStudies.mobile].map(candles => {
        const bodyGeometry = new THREE.PlaneGeometry(xWorld(1) - xWorld(0), 1);
        bodyGeometry.setAttribute("aProgress", new THREE.InstancedBufferAttribute(new Float32Array(candles.map(bar => bar.u)), 1));
        bodyGeometry.setAttribute("aUp", new THREE.InstancedBufferAttribute(new Float32Array(candles.map(bar => Number(bar.close >= bar.open))), 1));
        const bodies = new THREE.InstancedMesh(bodyGeometry, candleMaterial, candles.length);
        bodies.instanceMatrix.setUsage(THREE.DynamicDrawUsage); bodies.frustumCulled = false; bodies.renderOrder = 3;
        const wickGeometry = new THREE.BufferGeometry();
        wickGeometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(candles.length * 6), 3));
        wickGeometry.setAttribute("aProgress", new THREE.BufferAttribute(new Float32Array(candles.flatMap(bar => [bar.u, bar.u])), 1));
        wickGeometry.setAttribute("aUp", new THREE.BufferAttribute(new Float32Array(candles.flatMap(bar => [Number(bar.close >= bar.open), Number(bar.close >= bar.open)])), 1));
        const wicks = new THREE.LineSegments(wickGeometry, wickMaterial); wicks.frustumCulled = false; wicks.renderOrder = 2;
        const group = new THREE.Group(); group.add(wicks, bodies); scene.add(group);
        return { candles, group, bodies, bodyGeometry, wickGeometry };
      });
      const transform = new THREE.Object3D();
      let lane = lanes[0], elapsed = 0, scroll = 0, targetScroll = 0, frame = 0, lastTick = 0, intersecting = true, lost = false;
      const displacement = (u: number) => media.matches ? 0
        : (.022 * Math.sin(u * 5.4 - elapsed * .36)
          + .008 * Math.sin(u * 9.2 + elapsed * .24)) * Math.sin(u * Math.PI)
          - scroll * .03 * u * u;
      const draw = () => {
        for (let i = 0; i <= segments; i++) {
          const u = i / segments, center = illustrativeSpine(u) + displacement(u);
          const twist = ribbonFold(u) + .08 * Math.sin(u * 4.2 - elapsed * .18), width = ribbonHalfWidth(u);
          for (let j = 0; j <= across; j++) {
            const side = j / across * 2 - 1;
            positionAttribute.setXYZ(i * (across + 1) + j, xWorld(u), center + side * width * Math.cos(twist), side * width * Math.sin(twist));
            haloPositions.setXYZ(i * (across + 1) + j, xWorld(u), center + side * width * 4.2, -.1);
          }
          spinePositionAttribute.setXYZ(i, xWorld(u), center, .52);
        }
        positionAttribute.needsUpdate = true; geometry.computeVertexNormals();
        haloPositions.needsUpdate = true;
        spinePositionAttribute.needsUpdate = true;
        material.uniforms.uTime.value = elapsed;
        uniforms.uReveal.value = 1; // The shared CSS reveal unfolds every layer together.
        uniforms.uTime.value = elapsed;
        const wickPositions = lane.wickGeometry.getAttribute("position") as InstanceType<typeof THREE.BufferAttribute>;
        lane.candles.forEach((bar, i) => {
          const delta = displacement(bar.u), height = Math.max(.025, Math.abs(bar.close - bar.open));
          transform.position.set(xWorld(bar.u), (bar.open + bar.close) / 2 + delta, .8);
          transform.scale.set(.43 / (lane.candles.length - 1), height, 1); transform.updateMatrix();
          lane.bodies.setMatrixAt(i, transform.matrix);
          wickPositions.setXYZ(i * 2, xWorld(bar.u), bar.high + delta, .7);
          wickPositions.setXYZ(i * 2 + 1, xWorld(bar.u), bar.low + delta, .7);
        });
        lane.bodies.instanceMatrix.needsUpdate = true; wickPositions.needsUpdate = true;
        renderer.render(scene, camera);
      };
      const active = () => !disposed && !lost && intersecting && !document.hidden && !media.matches && !pausedRef.current;
      const tick = (now: number) => {
        frame = 0;
        if (!active()) return;
        if (!lastTick || now - lastTick >= 1000 / 30) { elapsed += lastTick ? Math.min(.07, (now - lastTick) / 1000) : 0; lastTick = now; scroll += (targetScroll - scroll) * .09; draw(); }
        frame = requestAnimationFrame(tick);
      };
      const sync = () => {
        cancelAnimationFrame(frame); frame = 0; lastTick = 0;
        const running = active(); host.dataset.motion = media.matches ? "reduced" : pausedRef.current ? "paused" : running ? "running" : "suspended";
        if (intersecting && !document.hidden && !lost) draw();
        if (running) frame = requestAnimationFrame(tick);
      };
      const measureScroll = () => {
        const hero = host.closest("section")?.getBoundingClientRect();
        if (hero) targetScroll = Math.max(0, Math.min(1, (84 - hero.top) / Math.max(1, hero.height * .85)));
      };
      const resize = () => {
        const rect = host.getBoundingClientRect();
        if (!rect.width || !rect.height || lost) return;
        lane = lanes[rect.width <= 720 ? 1 : 0]; lanes.forEach(item => { item.group.visible = item === lane; });
        renderer.setSize(rect.width, rect.height); measureScroll(); draw();
      };
      const sizing = new ResizeObserver(resize); sizing.observe(host);
      const visibility = new IntersectionObserver(entries => { intersecting = entries[0]?.isIntersecting ?? false; sync(); }, { threshold: 0 }); visibility.observe(host);
      const contextLost = (event: Event) => { event.preventDefault(); lost = true; cancelAnimationFrame(frame); delete host.dataset.renderer; host.dataset.motion = "fallback"; setUnavailable(true); };
      sceneRef.current = { sync };
      renderer.domElement.addEventListener("webglcontextlost", contextLost);
      document.addEventListener("visibilitychange", sync); window.addEventListener("scroll", measureScroll, { passive: true });
      resize(); host.dataset.renderer = "webgl"; sync();
      cleanupScene = () => {
        cancelAnimationFrame(frame); sizing.disconnect(); visibility.disconnect();
        document.removeEventListener("visibilitychange", sync); window.removeEventListener("scroll", measureScroll);
        renderer.domElement.removeEventListener("webglcontextlost", contextLost);
        geometry.dispose(); haloGeometry.dispose(); haloMaterial.dispose(); spineGeometry.dispose(); material.dispose(); spineMaterial.dispose(); candleMaterial.dispose(); wickMaterial.dispose();
        lanes.forEach(item => { item.bodyGeometry.dispose(); item.wickGeometry.dispose(); });
        renderer.dispose(); renderer.domElement.remove(); sceneRef.current = null; delete host.dataset.renderer; delete host.dataset.motion;
      };
    }).catch(() => { if (!disposed) setUnavailable(true); });
    return () => { disposed = true; media.removeEventListener("change", updatePreference); cleanupScene?.(); };
  }, []);

  function toggleMotion() { pausedRef.current = !paused; setPaused(!paused); sceneRef.current?.sync(); }

  return <figure className={styles.ribbonScene} aria-label={copy.studyDescription}>
    <div className={styles.ribbonVisual}>
      <div className={styles.ribbonArt} ref={hostRef} aria-hidden="true" data-motion={reduced ? "reduced" : unavailable ? "fallback" : paused ? "paused" : "running"}>
        <div className={styles.ribbonGlow}/>
        <StaticStudy candles={illustrativeStudies.desktop} id={`${id}-desktop`}/>
        <StaticStudy candles={illustrativeStudies.mobile} id={`${id}-mobile`} mobile/>
      </div>
    </div>
    <figcaption className={styles.ribbonTools}>
      <a href="#demo" className={styles.ribbonScroll}>{copy.watchDemo}<span aria-hidden="true">↓</span></a>
      <button type="button" className={styles.motionButton} onClick={toggleMotion} aria-pressed={paused || reduced || unavailable} disabled={reduced || unavailable}>{reduced || unavailable ? copy.staticMotion : paused ? copy.playMotion : copy.pauseMotion}</button>
    </figcaption>
  </figure>;
}
