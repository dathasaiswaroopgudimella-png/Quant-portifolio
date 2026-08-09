"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";

// Dynamically import 3D scene to avoid SSR issues
const HeroScene3D = dynamic(() => import("@/components/HeroScene3D"), { ssr: false, loading: () => null });
const FragilitySurface3D = dynamic(() => import("@/components/FragilitySurface3D"), { ssr: false, loading: () => null });

/* ─── Animated counter ──────────────────────────────────────────────── */
function Counter({ to, suffix = "", prefix = "" }: { to: number; suffix?: string; prefix?: string }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let start = 0;
        const step = Math.ceil(to / 60);
        const t = setInterval(() => {
          start = Math.min(start + step, to);
          setVal(start);
          if (start >= to) clearInterval(t);
        }, 18);
        obs.disconnect();
      }
    });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [to]);
  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>;
}

/* ─── TypeWriter ─────────────────────────────────────────────────────── */
function TypeWriter({ words }: { words: string[] }) {
  const [idx, setIdx] = useState(0);
  const [sub, setSub] = useState("");
  const [phase, setPhase] = useState<"typing" | "deleting">("typing");

  useEffect(() => {
    const current = words[idx % words.length];
    if (phase === "typing") {
      if (sub === current) {
        const t = setTimeout(() => setPhase("deleting"), 1800);
        return () => clearTimeout(t);
      }
      const t = setTimeout(() => setSub(current.substring(0, sub.length + 1)), 85);
      return () => clearTimeout(t);
    }
    if (sub === "") {
      const t = setTimeout(() => { setIdx(p => (p + 1) % words.length); setPhase("typing"); }, 300);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setSub(sub.substring(0, sub.length - 1)), 40);
    return () => clearTimeout(t);
  }, [sub, phase, idx, words]);

  return (
    <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
      {sub}<span className="animate-pulse">|</span>
    </span>
  );
}

/* ─── 3D Perspective Card with Spotlight Tracking ────────────────────── */
function Card3D({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [spotlight, setSpotlight] = useState({ x: 50, y: 50, opacity: 0 });

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const xPct = ((e.clientX - rect.left) / rect.width) * 100;
    const yPct = ((e.clientY - rect.top) / rect.height) * 100;
    const rotX = ((e.clientY - rect.top) / rect.height - 0.5) * -14;
    const rotY = ((e.clientX - rect.left) / rect.width - 0.5) * 16;
    
    ref.current.style.transform = `perspective(1000px) rotateY(${rotY}deg) rotateX(${rotX}deg) translateZ(8px) scale3d(1.02,1.02,1.02)`;
    setSpotlight({ x: xPct, y: yPct, opacity: 1 });
  };

  const onMouseLeave = () => {
    if (!ref.current) return;
    ref.current.style.transform = "perspective(1000px) rotateY(0deg) rotateX(0deg) translateZ(0px) scale3d(1,1,1)";
    setSpotlight(s => ({ ...s, opacity: 0 }));
  };

  return (
    <div
      ref={ref}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      className={`relative transition-all duration-200 ease-out ${className}`}
      style={{ transformStyle: "preserve-3d", willChange: "transform" }}
    >
      {/* Dynamic Cursor Spotlight Layer */}
      <div
        className="pointer-events-none absolute -inset-px rounded-2xl transition-opacity duration-300 z-20"
        style={{
          opacity: spotlight.opacity,
          background: `radial-gradient(400px circle at ${spotlight.x}% ${spotlight.y}%, rgba(192, 193, 255, 0.15), transparent 80%)`,
        }}
      />
      {children}
    </div>
  );
}

/* ─── Hexagonal Radar (SVG) ─────────────────────────────────────────── */
function HexRadar({ scores }: { scores: number[] }) {
  const labels = ["Soundness", "Greek Fidelity", "Robustness", "Boundary", "Benchmark", "Stability"];
  const N = 6;
  const cx = 120, cy = 120, R = 90;

  const angle = (i: number) => (Math.PI / 2) + (2 * Math.PI * i) / N;
  const pt = (i: number, r: number) => {
    const a = angle(i);
    return [cx + r * Math.cos(a), cy - r * Math.sin(a)];
  };

  const rings = [0.2, 0.4, 0.6, 0.8, 1.0];
  const dataPoints = scores.map((s, i) => pt(i, (s / 100) * R));
  const polyPath = dataPoints.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ") + " Z";

  return (
    <svg viewBox="0 0 240 240" className="w-full h-full">
      {rings.map((r) => {
        const pts = Array.from({ length: N }, (_, i) => pt(i, r * R));
        return (
          <polygon
            key={r}
            points={pts.map(p => p.join(",")).join(" ")}
            fill="none"
            stroke="#2e2c33"
            strokeWidth="1"
          />
        );
      })}
      {Array.from({ length: N }, (_, i) => {
        const [x, y] = pt(i, R);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#2e2c33" strokeWidth="1" />;
      })}
      <polygon points={dataPoints.map(p => p.join(",")).join(" ")} fill="url(#radarFill)" stroke="#c0c1ff" strokeWidth="1.5" />
      <defs>
        <linearGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#c0c1ff" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#4edea3" stopOpacity="0.15" />
        </linearGradient>
      </defs>
      {dataPoints.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3.5" fill="#c0c1ff" />
      ))}
      {Array.from({ length: N }, (_, i) => {
        const [x, y] = pt(i, R + 16);
        return (
          <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
            fill="#908fa0" fontSize="7.5" fontFamily="monospace">
            {labels[i]}
          </text>
        );
      })}
    </svg>
  );
}

/* ─── Main Page ──────────────────────────────────────────────────────── */
export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const demoScores = [88, 91, 76, 94, 83, 89];

  const features = [
    {
      icon: "🧬",
      title: "AST Code Inspection",
      desc: "Real Python AST parsing inspects your model's mathematical structure — detecting local vol, dividend yield, and edge-case guards automatically.",
      color: "#c0c1ff",
    },
    {
      icon: "⚡",
      title: "Adversarial DE Search",
      desc: "SciPy Differential Evolution with normalized relative error targeting finds breaking parameter regimes across Spot × Vol × Rate space.",
      color: "#4edea3",
    },
    {
      icon: "📐",
      title: "Gradient Risk Attribution",
      desc: "Finite-difference partial derivatives (∂Error/∂σ, ∂Error/∂S, ∂Error/∂r) replace static weights with real numerical sensitivity attribution.",
      color: "#ffb95f",
    },
    {
      icon: "🔬",
      title: "QuantLib Benchmark",
      desc: "Every model validated against QuantLib 1.43 Black-Scholes engine with Actual365Fixed day-count alignment and exact Greek computation.",
      color: "#ff7878",
    },
    {
      icon: "📡",
      title: "Live Market Data",
      desc: "Real-time volatility surface calibration from Yahoo Finance with ddof=1 corrected historical volatility and LIVE/DELAYED status tracking.",
      color: "#c0c1ff",
    },
    {
      icon: "🌐",
      title: "3D Fragility Surface",
      desc: "Interactive WebGL topology map of where your model breaks. Drag, rotate, zoom — see the pricing failure landscape in full 3D space.",
      color: "#4edea3",
    },
  ];

  const steps = [
    { n: "01", title: "Submit Your Model", desc: "Paste Python code, describe it in plain English for AI synthesis, upload a file, or pick from pre-configured quantitative models." },
    { n: "02", title: "Adversarial Search", desc: "The engine runs multi-seed differential evolution across 4D parameter space, targeting maximum normalized pricing divergence." },
    { n: "03", title: "Deep Report", desc: "Get a full audit: hexagonal radar, 3D fragility surface, Greek drift table, AST assumption map, and actionable risk boundaries." },
  ];

  return (
    <div className="min-h-screen bg-[#08080d] text-[#e5e1e4] overflow-x-hidden font-sans" style={{ fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>

      {/* ── HERO ─────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">

        {/* Full-screen 3D canvas */}
        <div className="absolute inset-0">
          {mounted && <HeroScene3D />}
        </div>

        {/* Gradient overlays for depth */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#08080d]/30 via-transparent to-[#08080d]" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#08080d]/40 via-transparent to-[#08080d]/40" />
        <div className="absolute bottom-0 left-0 right-0 h-48 bg-gradient-to-t from-[#08080d] to-transparent" />

        {/* Nav */}
        <nav className="absolute top-0 left-0 right-0 flex items-center justify-between px-8 py-5 z-20">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#c0c1ff] to-[#4edea3] flex items-center justify-center text-[#08080d] font-black text-xs">F</div>
            <span className="font-bold text-sm tracking-widest text-[#e5e1e4]">FRAGMENT</span>
          </div>
          <div className="flex items-center gap-6 text-xs font-mono text-[#908fa0]">
            <Link href="/dashboard" className="hover:text-[#c0c1ff] transition-colors">Dashboard</Link>
            <Link href="/editor" className="hover:text-[#4edea3] transition-colors">Editor</Link>
            <Link href="/market" className="hover:text-[#ffb95f] transition-colors">Market</Link>
            <Link href="/validations" className="hover:text-[#e5e1e4] transition-colors">Validations</Link>
            <Link href="/editor" className="px-4 py-2 bg-[#c0c1ff]/10 border border-[#c0c1ff]/30 text-[#c0c1ff] rounded-lg hover:bg-[#c0c1ff]/20 transition-all">
              Launch →
            </Link>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 text-center px-6 max-w-5xl mx-auto" style={{ transform: `translateY(${scrollY * 0.18}px)` }}>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#c0c1ff]/8 border border-[#c0c1ff]/20 rounded-full text-[11px] font-mono text-[#c0c1ff] mb-8 backdrop-blur">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            SR 11-7 Aligned Validation Tooling · QuantLib 1.43 · Three.js WebGL
          </div>

          <h1 className="text-6xl md:text-8xl font-black tracking-tight leading-none mb-6">
            <span className="text-[#e5e1e4]">MODEL</span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] via-[#4edea3] to-[#ffb95f]">RISK</span>
            <br />
            <span className="text-[#e5e1e4] opacity-50">AUDIT</span>
          </h1>

          <p className="text-lg md:text-xl text-[#908fa0] max-w-2xl mx-auto mb-4 leading-relaxed">
            Adversarial validation for quantitative pricing models.
          </p>
          <p className="text-base text-[#606070] max-w-xl mx-auto mb-12">
            <TypeWriter words={[
              "Black-Scholes · Garman-Kohlhagen FX · European Options",
              "Differential Evolution · AST Inspection · QuantLib Benchmark",
              "3D Fragility Surface · Greek Drift · Risk Attribution",
            ]} />
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link href="/editor" className="group px-8 py-3.5 bg-gradient-to-r from-[#c0c1ff] to-[#8889ff] text-[#08080d] font-bold text-sm rounded-xl hover:shadow-[0_0_40px_rgba(192,193,255,0.35)] transition-all duration-300 hover:scale-105">
              <span className="flex items-center gap-2">
                Start Validation
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </span>
            </Link>
            <Link href="/dashboard" className="px-8 py-3.5 bg-white/5 border border-white/10 text-[#e5e1e4] font-semibold text-sm rounded-xl hover:bg-white/10 backdrop-blur transition-all duration-300">
              View Dashboard
            </Link>
          </div>

          {/* Stat bar */}
          <div className="grid grid-cols-3 gap-6 max-w-lg mx-auto">
            {[
              { val: 2, suffix: " Seeded", label: "Real Quant Models" },
              { val: 100, suffix: "%", label: "QuantLib Grounded" },
              { val: 6, suffix: " Axis", label: "Model Risk Radar" },
            ].map((s, i) => (
              <div key={i} className="text-center">
                <div className="text-2xl font-black font-mono text-[#c0c1ff]">
                  <Counter to={s.val} suffix={s.suffix} />
                </div>
                <div className="text-[10px] text-[#606070] font-mono mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2 text-[#606070] text-[10px] font-mono animate-bounce">
          <span>SCROLL</span>
          <div className="w-px h-8 bg-gradient-to-b from-[#606070] to-transparent" />
        </div>
      </section>

      {/* ── 3D SURFACE DEMO ──────────────────────────────────────────── */}
      <section className="relative py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-[11px] font-mono text-[#c0c1ff] tracking-widest mb-3">INTERACTIVE · WEBGL</p>
            <h2 className="text-4xl font-black text-[#e5e1e4] mb-4">
              Adversarial{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
                Fragility Surface
              </span>
            </h2>
            <p className="text-[#908fa0] max-w-xl mx-auto text-sm leading-relaxed">
              The 3D topology of where your pricing model diverges from QuantLib. Peaks are parameter regimes where your model breaks. Drag to rotate.
            </p>
          </div>

          <div className="relative">
            {/* Glow behind */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#c0c1ff]/5 via-[#4edea3]/5 to-[#ffb95f]/5 rounded-3xl blur-3xl" />
            <div className="relative backdrop-blur bg-white/[0.02] border border-white/[0.06] rounded-3xl p-1 shadow-[0_0_80px_rgba(192,193,255,0.08)]">
              <FragilitySurface3D />
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[11px] font-mono text-[#4edea3] tracking-widest mb-3">METHODOLOGY</p>
            <h2 className="text-4xl font-black text-[#e5e1e4]">How It Works</h2>
          </div>

          <div className="relative">
            {/* Connecting line */}
            <div className="absolute left-[28px] top-8 bottom-8 w-px bg-gradient-to-b from-[#c0c1ff]/20 via-[#4edea3]/20 to-[#ffb95f]/20 md:left-1/2" />

            <div className="space-y-12">
              {steps.map((step, i) => (
                <Card3D key={i} className={`flex flex-col md:flex-row items-start gap-8 ${i % 2 === 1 ? "md:flex-row-reverse" : ""}`}>
                  <div className="flex-1">
                    <div className="bg-[#111116] border border-[#2e2c33] rounded-2xl p-6 hover:border-[#c0c1ff]/30 transition-colors duration-300 relative overflow-hidden">
                      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#c0c1ff]/20 to-transparent" />
                      <div className="text-[10px] font-mono text-[#606070] mb-2">{step.n}</div>
                      <h3 className="text-lg font-bold text-[#e5e1e4] mb-2">{step.title}</h3>
                      <p className="text-sm text-[#908fa0] leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#c0c1ff]/20 to-[#4edea3]/10 border border-[#c0c1ff]/20 flex items-center justify-center text-xl font-black text-[#c0c1ff] flex-shrink-0 z-10">
                    {i + 1}
                  </div>
                  <div className="flex-1 hidden md:block" />
                </Card3D>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── FEATURES GRID ────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[11px] font-mono text-[#ffb95f] tracking-widest mb-3">CAPABILITIES</p>
            <h2 className="text-4xl font-black text-[#e5e1e4] mb-4">
              Everything You Need for{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#ffb95f] to-[#ff7878]">
                Model Risk
              </span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, i) => (
              <Card3D key={i}>
                <div className="h-full bg-[#111116] border border-[#2e2c33] rounded-2xl p-6 hover:border-[#c0c1ff]/25 transition-all duration-300 group relative overflow-hidden">
                  {/* Glow on hover */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ background: `radial-gradient(ellipse at 50% 0%, ${f.color}08, transparent 70%)` }} />
                  <div className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ background: `linear-gradient(90deg, transparent, ${f.color}40, transparent)` }} />

                  <div className="text-3xl mb-4">{f.icon}</div>
                  <h3 className="font-bold text-[#e5e1e4] mb-2 text-sm">{f.title}</h3>
                  <p className="text-xs text-[#908fa0] leading-relaxed">{f.desc}</p>

                  <div className="mt-4 w-8 h-0.5 rounded-full" style={{ background: f.color }} />
                </div>
              </Card3D>
            ))}
          </div>
        </div>
      </section>

      {/* ── RADAR DEMO ───────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <p className="text-[11px] font-mono text-[#c0c1ff] tracking-widest mb-3">RISK RADAR</p>
              <h2 className="text-4xl font-black text-[#e5e1e4] mb-6">
                6-Axis Hexagonal{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
                  Risk Score
                </span>
              </h2>
              <p className="text-[#908fa0] text-sm leading-relaxed mb-8">
                Each validation produces a 6-dimensional risk profile covering conceptual soundness, Greek fidelity, parameter robustness, boundary safety, benchmark alignment, and numerical stability.
              </p>
              <div className="space-y-3">
                {["Conceptual Soundness — AST-verified mathematical structure",
                  "Greek Fidelity — Delta/Gamma/Vega drift vs QuantLib",
                  "Parameter Robustness — DE search across 4D space",
                  "Boundary Safety — Short tenor and deep OTM checks",
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-3 text-xs text-[#908fa0]">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#c0c1ff] mt-1.5 flex-shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <Card3D className="flex items-center justify-center">
              <div className="relative w-64 h-64">
                <div className="absolute inset-0 bg-gradient-to-br from-[#c0c1ff]/5 to-[#4edea3]/5 rounded-full blur-2xl" />
                <HexRadar scores={demoScores} />
              </div>
            </Card3D>
          </div>
        </div>
      </section>

      {/* ── UPLOAD MODES ─────────────────────────────────────────────── */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#c0c1ff]/[0.02] to-transparent" />
        <div className="max-w-5xl mx-auto relative">
          <div className="text-center mb-16 font-sans">
            <p className="text-[11px] font-mono text-[#4edea3] tracking-widest mb-3">FOUR WAYS TO SUBMIT</p>
            <h2 className="text-4xl font-black text-[#e5e1e4] mb-4">Any Model. Any Format.</h2>
            <p className="text-[#908fa0] text-sm max-w-lg mx-auto leading-relaxed">
              FRAGMENT accepts code in four ways so no model ever gets rejected at the door.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: "💻", label: "Code Editor", desc: "Paste Python directly into the syntax-highlighted editor with live validation.", color: "#c0c1ff" },
              { icon: "🤖", label: "AI Synthesis", desc: "Describe your model in plain English — OpenRouter GPT synthesizes the Python for you.", color: "#4edea3" },
              { icon: "📤", label: "File Upload", desc: "Upload .py or .txt files. Multi-format parsing handles any code style.", color: "#ffb95f" },
              { icon: "📚", label: "Quant Presets", desc: "Black-Scholes, Garman-Kohlhagen FX, European Options — one-click load.", color: "#ff7878" },
            ].map((m, i) => (
              <Card3D key={i}>
                <div className="bg-[#111116] border border-[#2e2c33] rounded-2xl p-5 text-center hover:border-opacity-60 transition-all duration-300 h-full group relative overflow-hidden font-sans"
                  style={{ "--hover-color": m.color } as React.CSSProperties}>
                  <div className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ background: `linear-gradient(90deg, transparent, ${m.color}50, transparent)` }} />
                  <div className="text-3xl mb-3">{m.icon}</div>
                  <div className="text-xs font-bold text-[#e5e1e4] mb-2">{m.label}</div>
                  <div className="text-[11px] text-[#908fa0] leading-relaxed font-sans">{m.desc}</div>
                </div>
              </Card3D>
            ))}
          </div>

          <div className="text-center mt-10">
            <Link href="/editor" className="inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-[#4edea3] to-[#2bbf88] text-[#08080d] font-bold text-sm rounded-xl hover:shadow-[0_0_40px_rgba(78,222,163,0.3)] transition-all duration-300 hover:scale-105">
              Open Model Editor →
            </Link>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="py-32 px-6 relative overflow-hidden font-sans">
        <div className="absolute inset-0 bg-gradient-to-r from-[#c0c1ff]/[0.04] via-transparent to-[#4edea3]/[0.04]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#c0c1ff]/[0.03] rounded-full blur-3xl" />

        <div className="max-w-3xl mx-auto text-center relative">
          <p className="text-[11px] font-mono text-[#c0c1ff] tracking-widest mb-6">READY TO VALIDATE</p>
          <h2 className="text-5xl md:text-6xl font-black text-[#e5e1e4] mb-6 leading-tight">
            Submit Your Model.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
              Break It First.
            </span>
          </h2>
          <p className="text-[#908fa0] text-base mb-12 max-w-xl mx-auto leading-relaxed font-sans">
            FRAGMENT finds where your model breaks before risk management does. Adversarial search, not unit tests.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/editor" className="group px-10 py-4 bg-gradient-to-r from-[#c0c1ff] to-[#8889ff] text-[#08080d] font-black text-sm rounded-xl hover:shadow-[0_0_60px_rgba(192,193,255,0.4)] transition-all duration-300 hover:scale-105">
              <span className="flex items-center gap-2">
                Start Validation
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </span>
            </Link>
            <Link href="/dashboard" className="px-10 py-4 bg-white/5 border border-white/10 text-[#e5e1e4] font-bold text-sm rounded-xl hover:bg-white/10 backdrop-blur transition-all duration-300">
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────── */}
      <footer className="border-t border-[#2e2c33]/50 py-10 px-6 font-sans">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-[#606070]">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-gradient-to-br from-[#c0c1ff] to-[#4edea3] flex items-center justify-center text-[#08080d] font-black text-[9px]">F</div>
            <span className="font-medium text-[#908fa0]">FRAGMENT — Adversarial Model Risk Validation Platform</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-[#908fa0]">
            <span className="font-mono">QuantLib 1.43</span>
            <span>·</span>
            <span>Next.js 14</span>
            <span>·</span>
            <span>FastAPI</span>
            <span>·</span>
            <span>Three.js WebGL</span>
            <span>·</span>
            <span className="font-mono">SR 11-7 Aligned</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
