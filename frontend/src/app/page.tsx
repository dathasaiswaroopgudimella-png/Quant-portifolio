"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import FragilitySurface3D from "@/components/FragilitySurface3D";

/* ─── SVG Icon library ──────────────────────────────────────────────── */
const Icons = {
  Shield: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7l-9-5z" /></svg>,
  Code: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg>,
  Zap: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>,
  BarChart: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="20" x2="12" y2="10" /><line x1="18" y1="20" x2="18" y2="4" /><line x1="6" y1="20" x2="6" y2="16" /></svg>,
  Arrow: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>,
  ChevronDown: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>,
  Activity: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>,
  Check: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>,
  X: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>,
  Target: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" /></svg>,
  Database: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /></svg>,
  GitBranch: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><line x1="6" y1="3" x2="6" y2="15" /><circle cx="18" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M18 9a9 9 0 0 1-9 9" /></svg>,
  Eye: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>,
  Clock: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>,
  TrendingUp: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" /></svg>,
  Box3D: (p: any) => <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></svg>,
};

/* ─── Animated counter ──────────────────────────────────────────────── */
function Counter({ to, suffix = "", prefix = "" }: { to: number; suffix?: string; prefix?: string }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let start = 0;
        const step = Math.ceil(to / 50);
        const t = setInterval(() => {
          start = Math.min(start + step, to);
          setVal(start);
          if (start >= to) clearInterval(t);
        }, 20);
        obs.disconnect();
      }
    });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [to]);
  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>;
}

/* ─── Typewriter ──────────────────────────────────────────────────── */
function TypeWriter({ words }: { words: string[] }) {
  const [idx, setIdx] = useState(0);
  const [sub, setSub] = useState("");
  const [phase, setPhase] = useState<"typing" | "pause" | "deleting" | "gap">("typing");

  useEffect(() => {
    const current = words[idx % words.length];
    let delay = 90;

    if (phase === "typing") {
      if (sub === current) {
        delay = 1800;
        const t = setTimeout(() => setPhase("deleting"), delay);
        return () => clearTimeout(t);
      }
      const t = setTimeout(() => setSub(current.substring(0, sub.length + 1)), delay);
      return () => clearTimeout(t);
    }

    if (phase === "deleting") {
      delay = 45;
      if (sub === "") {
        const t = setTimeout(() => {
          setIdx(prev => (prev + 1) % words.length);
          setPhase("typing");
        }, 300);
        return () => clearTimeout(t);
      }
      const t = setTimeout(() => setSub(sub.substring(0, sub.length - 1)), delay);
      return () => clearTimeout(t);
    }
  }, [sub, phase, idx, words]);

  return (
    <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
      {sub}<span className="animate-pulse text-[#c0c1ff]">|</span>
    </span>
  );
}

/* ─── Step card ────────────────────────────────────────────────────── */
function Step({ num, title, desc, icon, accent }: { num: string; title: string; desc: string; icon: React.ReactNode; accent: string }) {
  return (
    <div className="flex gap-5 group">
      <div className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center border transition-colors" style={{ borderColor: `${accent}30`, backgroundColor: `${accent}08` }}>
        <div style={{ color: accent }}>{icon}</div>
      </div>
      <div>
        <div className="text-[10px] font-mono uppercase tracking-widest mb-1" style={{ color: accent }}>Step {num}</div>
        <h3 className="font-bold text-[#e5e1e4] mb-1.5">{title}</h3>
        <p className="text-sm text-[#908fa0] leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

/* ─── Landing page ──────────────────────────────────────────────────── */
export default function LandingPage() {
  const [activeSection, setActiveSection] = useState("hero");
  const sections = ["hero", "surface3d", "problem", "how", "engines", "architecture", "stack", "cta"];

  useEffect(() => {
    const handler = () => {
      for (const id of sections) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 120 && rect.bottom >= 120) { setActiveSection(id); break; }
        }
      }
    };
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const navLinks = [
    { id: "surface3d", label: "3D Fragility Mesh" },
    { id: "problem", label: "The Problem" },
    { id: "how", label: "How It Works" },
    { id: "engines", label: "Engines" },
    { id: "architecture", label: "Architecture" },
    { id: "stack", label: "Tech Stack" },
  ];

  return (
    <div className="bg-[#0e0e10] text-[#e5e1e4] font-sans overflow-x-hidden -mt-14">

      {/* ── STICKY NAV ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#2e2c33]/60 backdrop-blur-xl bg-[#0e0e10]/80">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <button onClick={() => scrollTo("hero")} className="flex items-center gap-2 font-mono font-bold text-sm tracking-wider">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#c0c1ff] to-[#8083ff] flex items-center justify-center font-bold text-[#1000a9] text-sm shadow-lg shadow-[#c0c1ff]/20">
              F
            </div>
            <span className="text-[#c0c1ff]">FRAGMENT</span>
          </button>

          <div className="hidden md:flex items-center gap-6">
            {navLinks.map(l => (
              <button
                key={l.id}
                onClick={() => scrollTo(l.id)}
                className={`text-xs font-mono transition-colors ${activeSection === l.id ? "text-[#c0c1ff]" : "text-[#908fa0] hover:text-[#e5e1e4]"}`}
              >
                {l.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-xs font-mono text-[#908fa0] hover:text-[#e5e1e4] transition-colors px-3 py-1.5">
              Dashboard
            </Link>
            <Link href="/editor" className="text-xs font-mono font-bold px-4 py-1.5 rounded bg-[#c0c1ff] text-[#1000a9] hover:bg-[#8083ff] transition-colors shadow shadow-[#c0c1ff]/20">
              Open Sandbox →
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section id="hero" className="relative min-h-screen flex flex-col items-center justify-center pt-24 pb-16 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#464554_1px,transparent_1px),linear-gradient(to_bottom,#464554_1px,transparent_1px)] bg-[size:48px_48px] opacity-[0.06] pointer-events-none" />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-[radial-gradient(ellipse,rgba(192,193,255,0.10)_0%,transparent_70%)] pointer-events-none" />

        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#1a1820] border border-[#c0c1ff]/20 text-[#c0c1ff] text-xs font-mono shadow-lg">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            QuantLib 1.43 Ground Truth &bull; SR 11-7 Aligned Validation Tooling &bull; SciPy DE Search
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.06]">
            Your Financial Models<br />
            Silently <TypeWriter words={["Break.", "Fail.", "Diverge.", "Lie.", "Drift."]} />
          </h1>

          <p className="text-lg md:text-xl text-[#c7c4d7] max-w-3xl mx-auto leading-relaxed font-light">
            <strong className="text-[#e5e1e4] font-semibold">FRAGMENT</strong> is an{" "}
            <em>adversarial model risk validation platform</em> for quantitative finance. It finds the{" "}
            <strong className="text-[#c0c1ff]">minimal realistic market parameter perturbation</strong> that causes your model to diverge from QuantLib analytical ground truth.
          </p>

          <div className="flex flex-wrap justify-center gap-10 py-7 border-y border-[#2e2c33]">
            {[
              { value: <Counter to={35} suffix=" Iterations" />, label: "SciPy DE global search depth", color: "#4edea3" },
              { value: <Counter to={49} />, label: "7x7 fragility surface points evaluated", color: "#c0c1ff" },
              { value: <Counter to={5} />, label: "AST-derived mathematical assumptions", color: "#ffb95f" },
              { value: "100%", label: "Deterministic quant engine execution", color: "#e5e1e4" },
            ].map((s, i) => (
              <div key={i} className="text-center">
                <p className="text-3xl font-bold font-mono" style={{ color: s.color }}>{s.value}</p>
                <p className="text-xs text-[#908fa0] mt-1 max-w-[130px] mx-auto leading-tight">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/editor" className="group flex items-center gap-2.5 px-8 py-3.5 rounded-lg bg-[#c0c1ff] text-[#1000a9] font-bold hover:bg-[#8083ff] transition-all shadow-xl shadow-[#c0c1ff]/25 text-sm">
              <Icons.Code className="w-4 h-4" />
              Open Model Sandbox Editor
              <Icons.Arrow className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <button onClick={() => scrollTo("surface3d")} className="flex items-center gap-2 px-8 py-3.5 rounded-lg border border-[#2e2c33] text-[#c7c4d7] hover:bg-[#161519] hover:text-[#e5e1e4] transition-colors text-sm font-medium">
              <Icons.Box3D className="w-4 h-4 text-[#c0c1ff]" />
              Explore 3D Fragility Surface
              <Icons.ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        <button onClick={() => scrollTo("surface3d")} className="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce text-[#908fa0] hover:text-[#c0c1ff] transition-colors">
          <Icons.ChevronDown className="w-6 h-6" />
        </button>
      </section>

      {/* ── 3D WEBGL FRAGILITY SURFACE DEMO ── */}
      <section id="surface3d" className="py-20 px-6 border-t border-[#2e2c33] bg-[#0b0b0d]">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="text-center max-w-2xl mx-auto">
            <p className="text-xs font-mono uppercase tracking-widest text-[#c0c1ff] mb-2">Spatial Interactive Visualization</p>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-[#e5e1e4]">
              3D WebGL Option Failure Topology
            </h2>
            <p className="text-xs text-[#908fa0] mt-2">
              Physical WebGL deforming mesh visualizes pricing divergence ($Z$-axis height) across Spot ($X$) and Volatility ($Y$).
            </p>
          </div>

          <FragilitySurface3D />
        </div>
      </section>

      {/* ── THE PROBLEM ── */}
      <section id="problem" className="py-28 px-6 border-t border-[#2e2c33]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-[#c0c1ff] mb-3">Why We Built This</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-5">
              The Invisible Risk Inside<br />
              <span className="text-[#ffb4ab]">Every Quant Pricing Model</span>
            </h2>
            <p className="text-[#908fa0] max-w-2xl mx-auto leading-relaxed">
              Every pricing model hides a set of mathematical assumptions in its code. These assumptions hold under normal market conditions — but during regime shifts, models break down silently.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {[
              {
                icon: <Icons.Eye className="w-6 h-6" />,
                color: "#ffb4ab",
                title: "Silent Model Drift",
                problem: "A Black-Scholes model assumes constant volatility. Under high-vol regimes, pricing error diverges silently without raising runtime exceptions.",
                bullet: "The code executes. The output misprices derivatives."
              },
              {
                icon: <Icons.Clock className="w-6 h-6" />,
                color: "#ffb95f",
                title: "Stress Testing is Backwards",
                problem: "Traditional stress tests evaluate known historical crises. FRAGMENT's adversarial optimizer discovers unknown breaking combinations.",
                bullet: "Find worst-case parameter points algorithmically."
              },
              {
                icon: <Icons.Shield className="w-6 h-6" />,
                color: "#ff7878",
                title: "Independent Ground Truth",
                problem: "SR 11-7 guidelines require independent model validation. FRAGMENT compares user Python models against C++ QuantLib 1.43 ground truth.",
                bullet: "Objective benchmark validation."
              }
            ].map((c, i) => (
              <div key={i} className="rounded-xl border p-6 space-y-4 hover:border-opacity-60 transition-all"
                style={{ borderColor: `${c.color}20`, backgroundColor: `${c.color}05` }}>
                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${c.color}12`, color: c.color }}>
                  {c.icon}
                </div>
                <h3 className="font-bold text-[#e5e1e4]">{c.title}</h3>
                <p className="text-sm text-[#908fa0] leading-relaxed">{c.problem}</p>
                <div className="flex items-start gap-2 pt-2 border-t border-[#2e2c33]">
                  <Icons.X className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" style={{ color: c.color }} />
                  <p className="text-xs font-mono italic" style={{ color: c.color }}>{c.bullet}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-[#161519] border border-[#ffb4ab]/15 rounded-2xl p-8 md:p-12 text-center">
            <p className="text-2xl md:text-3xl font-light text-[#c7c4d7] leading-relaxed max-w-3xl mx-auto">
              "We discovered our Black-Scholes model had a <strong className="text-[#ffb4ab]">$2.14 mispricing error</strong> at 
              a volatility of 38% — a regime we were actively trading in. 
              Nobody had ever tested it above 25%."
            </p>
            <p className="text-sm text-[#908fa0] mt-4 font-mono">— The scenario FRAGMENT was built to detect</p>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how" className="py-28 px-6 border-t border-[#2e2c33] bg-[#0b0b0d]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-[#4edea3] mb-3">The Solution</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-5">
              Inputs &rarr; Engines &rarr; Outputs<br />
              <span className="text-[#4edea3]">In One Deterministic Pipeline</span>
            </h2>
            <p className="text-[#908fa0] max-w-2xl mx-auto leading-relaxed">
              You paste your Python pricing model. FRAGMENT evaluates it against AST security rules, QuantLib 1.43 ground truth, and SciPy Differential Evolution.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-10 bg-[#161519] border border-[#2e2c33] rounded-2xl p-8 md:p-10">
            <div className="space-y-8">
              <Step num="01" title="Paste Your Python Pricing Model" icon={<Icons.Code className="w-5 h-5" />} accent="#c0c1ff"
                desc="You write or paste any Black-Scholes pricing function in Python. The sandbox accepts standard math/scipy." />
              <Step num="02" title="AST Security Analysis & Dynamic Assumption Extraction" icon={<Icons.Shield className="w-5 h-5" />} accent="#4edea3"
                desc="FRAGMENT parses your Abstract Syntax Tree. It detects local volatility skew, variable rate parameters, and enforces AST security rules." />
              <Step num="03" title="QuantLib 1.43 Ground Truth Pricing" icon={<Icons.Target className="w-5 h-5" />} accent="#ffb95f"
                desc="Your function's output is compared against QuantLib 1.43's analytical Black-Scholes engine with exact fractional day maturity precision." />
            </div>
            <div className="space-y-8">
              <Step num="04" title="SciPy Adversarial Parameter Search" icon={<Icons.Zap className="w-5 h-5" />} accent="#ff7878"
                desc="SciPy's Differential Evolution optimizer searches parameter space using normalized relative error to find exact breaking parameter regimes." />
              <Step num="05" title="Fragility Surface & 3D WebGL Topology" icon={<Icons.BarChart className="w-5 h-5" />} accent="#c0c1ff"
                desc="A 7x7 parameter grid and 3D WebGL canvas map pricing error across the Spot x Volatility parameter space." />
              <Step num="06" title="Executive SR 11-7 Aligned Report" icon={<Icons.GitBranch className="w-5 h-5" />} accent="#4edea3"
                desc="Synthesizes an executive summary citing breaking parameters, numerical gradient risk attributions, and actionable operational guidance." />
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section id="cta" className="py-28 px-6 border-t border-[#2e2c33] bg-[#0b0b0d]">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight">
            Validate Your Model's<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
              Breaking Point Today
            </span>
          </h2>

          <p className="text-[#908fa0] text-lg max-w-xl mx-auto leading-relaxed">
            Paste your Python pricing model. Get back a calibrated Fragility Index, breaking market parameters, Greek drifts, and actionable operational guidance.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/editor" className="group flex items-center gap-3 px-10 py-4 rounded-xl bg-[#c0c1ff] text-[#1000a9] font-bold text-base hover:bg-[#8083ff] transition-all shadow-2xl shadow-[#c0c1ff]/25">
              <Icons.Code className="w-5 h-5" />
              Open Model Sandbox Editor
              <Icons.Arrow className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link href="/dashboard" className="flex items-center gap-3 px-10 py-4 rounded-xl border border-[#2e2c33] text-[#c7c4d7] hover:bg-[#161519] hover:border-[#464554] transition-colors text-base font-medium">
              <Icons.BarChart className="w-5 h-5" />
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-[#2e2c33] py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-[#c0c1ff] flex items-center justify-center">
              <Icons.Target className="w-3 h-3 text-[#1000a9]" />
            </div>
            <span className="font-mono font-bold text-sm text-[#c0c1ff]">FRAGMENT</span>
            <span className="text-xs text-[#464554] font-mono ml-2">Adversarial Quantitative Model Risk Platform</span>
          </div>
          <div className="flex items-center gap-6 text-xs font-mono text-[#464554]">
            <span>QuantLib 1.43</span>
            <span>&bull;</span>
            <span>SR 11-7 Aligned Tooling</span>
            <span>&bull;</span>
            <span>SciPy Differential Evolution</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
