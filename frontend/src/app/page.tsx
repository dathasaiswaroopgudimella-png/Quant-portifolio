"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

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
  const sections = ["hero", "problem", "how", "engines", "architecture", "stack", "cta"];

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
      <section id="hero" className="relative min-h-screen flex flex-col items-center justify-center pt-24 pb-20 px-6 overflow-hidden">
        {/* Background grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#464554_1px,transparent_1px),linear-gradient(to_bottom,#464554_1px,transparent_1px)] bg-[size:48px_48px] opacity-[0.06] pointer-events-none" />
        {/* Glow blobs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-[radial-gradient(ellipse,rgba(192,193,255,0.10)_0%,transparent_70%)] pointer-events-none" />
        <div className="absolute bottom-1/4 right-0 w-[400px] h-[400px] bg-[radial-gradient(ellipse,rgba(78,222,163,0.07)_0%,transparent_70%)] pointer-events-none" />

        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#1a1820] border border-[#c0c1ff]/20 text-[#c0c1ff] text-xs font-mono shadow-lg">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            QuantLib 1.43 Ground Truth Engine · SR 11-7 Compliant · Production Ready
          </div>

          {/* Headline */}
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.06]">
            Your Financial Models<br />
            Silently <TypeWriter words={["Break.", "Fail.", "Diverge.", "Lie.", "Drift."]} />
          </h1>

          {/* Sub */}
          <p className="text-lg md:text-xl text-[#c7c4d7] max-w-3xl mx-auto leading-relaxed font-light">
            <strong className="text-[#e5e1e4] font-semibold">FRAGMENT</strong> is the world's first{" "}
            <em>adversarial model risk validation platform</em> for quantitative finance. It doesn't ask{" "}
            <em>"What if 2008 happens?"</em> — it finds the{" "}
            <strong className="text-[#c0c1ff]">exact smallest market shift</strong> that silently breaks your specific model, right now.
          </p>

          {/* Stats */}
          <div className="flex flex-wrap justify-center gap-10 py-7 border-y border-[#2e2c33]">
            {[
              { value: <Counter to={10} suffix="ms" />, label: "Adversarial search per iteration", color: "#4edea3" },
              { value: <Counter to={49} />, label: "Fragility surface data points per run", color: "#c0c1ff" },
              { value: <Counter to={5} />, label: "Core mathematical assumptions extracted", color: "#ffb95f" },
              { value: "100%", label: "Deterministic — no AI guessing", color: "#e5e1e4" },
            ].map((s, i) => (
              <div key={i} className="text-center">
                <p className="text-3xl font-bold font-mono" style={{ color: s.color }}>{s.value}</p>
                <p className="text-xs text-[#908fa0] mt-1 max-w-[130px] mx-auto leading-tight">{s.label}</p>
              </div>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/editor" className="group flex items-center gap-2.5 px-8 py-3.5 rounded-lg bg-[#c0c1ff] text-[#1000a9] font-bold hover:bg-[#8083ff] transition-all shadow-xl shadow-[#c0c1ff]/25 text-sm">
              <Icons.Code className="w-4 h-4" />
              Open Model Sandbox Editor
              <Icons.Arrow className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <button onClick={() => scrollTo("problem")} className="flex items-center gap-2 px-8 py-3.5 rounded-lg border border-[#2e2c33] text-[#c7c4d7] hover:bg-[#161519] hover:text-[#e5e1e4] transition-colors text-sm font-medium">
              See How It Works
              <Icons.ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        <button onClick={() => scrollTo("problem")} className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce text-[#908fa0] hover:text-[#c0c1ff] transition-colors">
          <Icons.ChevronDown className="w-6 h-6" />
        </button>
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
              Every pricing model hides a set of mathematical assumptions in its code. These assumptions are correct on the day they're written — but markets change, and nobody checks whether the model still holds. Until it doesn't.
            </p>
          </div>

          {/* Three problem cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {[
              {
                icon: <Icons.Eye className="w-6 h-6" />,
                color: "#ffb4ab",
                title: "Silent Model Drift",
                problem: "A Black-Scholes model written in 2019 assumes a normal volatility regime. By 2024, implied vol has doubled. Nobody re-validated the model. It now misprices options by $4.20 per contract.",
                bullet: "The model looks fine. The model is not fine."
              },
              {
                icon: <Icons.Clock className="w-6 h-6" />,
                color: "#ffb95f",
                title: "Stress Testing is Backwards",
                problem: "Traditional stress tests ask 'What happens if 2008 repeats?' — that's a known scenario. The real danger is unknown scenarios. The market shifts nobody thought of. The combination of parameters nobody tested.",
                bullet: "You can't stress-test what you can't imagine."
              },
              {
                icon: <Icons.Shield className="w-6 h-6" />,
                color: "#ff7878",
                title: "No Regulatory Ground Truth",
                problem: "The Federal Reserve's SR 11-7 mandates model risk management — but most firms have no independent pricing engine to compare against. Their validators are checking their models against their own models.",
                bullet: "Circular validation is not validation."
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

          {/* The moment of realization */}
          <div className="bg-[#161519] border border-[#ffb4ab]/15 rounded-2xl p-8 md:p-12 text-center">
            <p className="text-2xl md:text-3xl font-light text-[#c7c4d7] leading-relaxed max-w-3xl mx-auto">
              "We discovered our Black-Scholes model had a <strong className="text-[#ffb4ab]">$2.14 mispricing error</strong> at 
              a volatility of 38% — a regime we were actively trading in. 
              Nobody had ever tested it above 25%."
            </p>
            <p className="text-sm text-[#908fa0] mt-4 font-mono">— The scenario FRAGMENT was built to prevent</p>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how" className="py-28 px-6 border-t border-[#2e2c33] bg-[#0b0b0d]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-[#4edea3] mb-3">The Solution</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-5">
              Inputs → Engines → Outputs<br />
              <span className="text-[#4edea3]">In One Deterministic Pipeline</span>
            </h2>
            <p className="text-[#908fa0] max-w-2xl mx-auto leading-relaxed">
              You paste your Python pricing model. FRAGMENT runs it through four precision engines and returns a complete fragility report — all in under 30 seconds.
            </p>
          </div>

          {/* Input → Process → Output visual */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {/* INPUT */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-7 h-7 rounded-full bg-[#c0c1ff]/10 border border-[#c0c1ff]/30 flex items-center justify-center text-[#c0c1ff] text-xs font-mono font-bold">1</div>
                <h3 className="font-bold text-[#e5e1e4] uppercase tracking-wider text-sm">Your Inputs</h3>
              </div>
              {[
                { label: "Python Pricing Function", value: "def black_scholes_call(S,K,T,r,σ)", icon: <Icons.Code className="w-4 h-4" /> },
                { label: "Market Parameters", value: "Spot=$150, Strike=$155, T=0.5y, r=5%, σ=22%", icon: <Icons.BarChart className="w-4 h-4" /> },
                { label: "Live Market Data (Optional)", value: "Auto-fetched from Yahoo Finance for AAPL/SPY etc.", icon: <Icons.TrendingUp className="w-4 h-4" /> },
              ].map((item, i) => (
                <div key={i} className="flex gap-3 p-3 bg-[#161519] border border-[#2e2c33] rounded-lg">
                  <div className="text-[#c0c1ff] mt-0.5">{item.icon}</div>
                  <div>
                    <p className="text-[10px] text-[#908fa0] uppercase tracking-wider font-mono">{item.label}</p>
                    <p className="text-xs font-mono text-[#c7c4d7] mt-0.5">{item.value}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* PROCESS */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-7 h-7 rounded-full bg-[#4edea3]/10 border border-[#4edea3]/30 flex items-center justify-center text-[#4edea3] text-xs font-mono font-bold">2</div>
                <h3 className="font-bold text-[#e5e1e4] uppercase tracking-wider text-sm">FRAGMENT Engines</h3>
              </div>
              {[
                { label: "AST Security Sandbox", desc: "Validates your code is safe before execution. Blocks os/subprocess/network calls.", color: "#c0c1ff" },
                { label: "QuantLib Pricer", desc: "Prices your option using the industry standard analytical engine as ground truth.", color: "#4edea3" },
                { label: "SciPy Adversarial Search", desc: "Finds the exact market parameters (spot, vol, rate) that maximize error vs QuantLib.", color: "#ffb95f" },
                { label: "Fragility Scorer", desc: "Produces a 0–100 Fragility Index and a 7×7 surface map of where the model breaks.", color: "#ff7878" },
              ].map((item, i) => (
                <div key={i} className="flex gap-3 p-3 bg-[#161519] border border-[#2e2c33] rounded-lg">
                  <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <div>
                    <p className="text-xs font-semibold font-mono" style={{ color: item.color }}>{item.label}</p>
                    <p className="text-xs text-[#908fa0] mt-0.5 leading-snug">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* OUTPUT */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-7 h-7 rounded-full bg-[#ffb95f]/10 border border-[#ffb95f]/30 flex items-center justify-center text-[#ffb95f] text-xs font-mono font-bold">3</div>
                <h3 className="font-bold text-[#e5e1e4] uppercase tracking-wider text-sm">Your Outputs</h3>
              </div>
              {[
                { label: "Fragility Index Score", value: "e.g. 72/100 — CRITICAL", color: "#ff7878", icon: "⚠" },
                { label: "Breaking Market Params", value: "S=$131.5, σ=49.2%, error=$3.41 (+18.2%)", color: "#ffb95f", icon: "🎯" },
                { label: "5 Greeks (ΔΓΘVρ)", value: "Delta=0.52, Gamma=0.018, Vega=0.38...", color: "#c0c1ff", icon: "Δ" },
                { label: "7×7 Fragility Surface", value: "Visual heatmap of error across vol/spot grid", color: "#4edea3", icon: "▦" },
                { label: "SR 11-7 Compliance Report", value: "AI-summarised executive brief for regulators", color: "#908fa0", icon: "📋" },
              ].map((item, i) => (
                <div key={i} className="flex gap-3 p-3 bg-[#161519] border border-[#2e2c33] rounded-lg">
                  <span className="text-base flex-shrink-0">{item.icon}</span>
                  <div>
                    <p className="text-[10px] text-[#908fa0] uppercase tracking-wider font-mono">{item.label}</p>
                    <p className="text-xs font-mono mt-0.5" style={{ color: item.color }}>{item.value}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Step by step */}
          <div className="grid md:grid-cols-2 gap-10 bg-[#161519] border border-[#2e2c33] rounded-2xl p-8 md:p-10">
            <div className="space-y-8">
              <Step num="01" title="Paste Your Python Pricing Model" icon={<Icons.Code className="w-5 h-5" />} accent="#c0c1ff"
                desc="You write or paste any Black-Scholes pricing function in Python. The sandbox accepts standard math/scipy — no black boxes, no compiled code." />
              <Step num="02" title="AST Security Analysis" icon={<Icons.Shield className="w-5 h-5" />} accent="#4edea3"
                desc="Before any execution, FRAGMENT parses your Abstract Syntax Tree. It detects and blocks all dangerous operations — os, subprocess, network, file access. Completely isolated." />
              <Step num="03" title="QuantLib Ground Truth Pricing" icon={<Icons.Target className="w-5 h-5" />} accent="#ffb95f"
                desc="Your function's output is compared against QuantLib 1.43's analytical Black-Scholes engine — the same library used by global investment banks as the industry reference." />
            </div>
            <div className="space-y-8">
              <Step num="04" title="SciPy Adversarial Parameter Search" icon={<Icons.Zap className="w-5 h-5" />} accent="#ff7878"
                desc="SciPy's Differential Evolution optimizer searches over spot price (±30%), volatility (0.5×–2.5×), and risk-free rate bounds to find the minimal perturbation that maximizes pricing error." />
              <Step num="05" title="Fragility Surface Generation" icon={<Icons.BarChart className="w-5 h-5" />} accent="#c0c1ff"
                desc="A 7×7 parameter grid is computed to map exactly where your model diverges. This becomes a heatmap showing which market regimes are safe and which are dangerous." />
              <Step num="06" title="AI-Synthesized Executive Report" icon={<Icons.GitBranch className="w-5 h-5" />} accent="#4edea3"
                desc="OpenRouter synthesizes a regulatory-quality executive summary in plain English, citing the exact breaking parameters, fragility score, and SR 11-7 compliance assessment." />
            </div>
          </div>
        </div>
      </section>

      {/* ── ENGINES ── */}
      <section id="engines" className="py-28 px-6 border-t border-[#2e2c33]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-[#c0c1ff] mb-3">Core Engines</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-5">
              Four Precision Engines.<br />
              <span className="text-[#c0c1ff]">One Unbreakable Pipeline.</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                title: "AST Security Sandbox",
                badge: "Security Layer",
                color: "#4edea3",
                description: "Before your code ever runs, FRAGMENT's Abstract Syntax Tree parser performs static analysis — it walks the entire parse tree of your Python function and identifies all import statements, function calls, and attribute accesses.",
                points: [
                  "Blocks os, sys, subprocess, socket, eval, exec",
                  "Whitelist: only math, scipy.stats, numpy allowed",
                  "5-second execution timeout enforced via threading",
                  "Zero network or filesystem access possible",
                ],
                code: `# What FRAGMENT sees in your code:
parse_and_validate_model_code(user_code)
# → checks for dangerous AST nodes
# → raises ASTSecurityError if found
# → compiles into isolated exec() scope`
              },
              {
                title: "QuantLib 1.43 Analytical Pricer",
                badge: "Ground Truth Engine",
                color: "#c0c1ff",
                description: "QuantLib is the open-source gold standard for quantitative finance, used by JPMorgan, Goldman, and the ECB. FRAGMENT uses it as an independent oracle to price the same option contract using exact analytical Black-Scholes with full Greeks computation.",
                points: [
                  "Exact Black-Scholes analytical pricing (not numeric)",
                  "Delta, Gamma, Vega, Theta, Rho computed analytically",
                  "European Call & Put options",
                  "Acts as SR 11-7 independent validation model",
                ],
                code: `# QuantLib computes the "truth":
ql_result = QuantLibPricer.price_european_option(
  spot=150.0, strike=155.0, maturity=0.5,
  risk_free_rate=0.05, volatility=0.22
)
# → price=7.42, delta=0.48, gamma=0.023...`
              },
              {
                title: "SciPy Differential Evolution",
                badge: "Adversarial Optimizer",
                color: "#ffb95f",
                description: "The core innovation. Instead of testing pre-defined scenarios, FRAGMENT runs SciPy's Differential Evolution — a global, non-convex optimization algorithm — over a 3-dimensional parameter space to find the market conditions that maximize the gap between your model and QuantLib.",
                points: [
                  "Global non-convex search — not gradient descent",
                  "15 iterations × 8-member population per run",
                  "Searches spot ±30%, vol 0.5×–2.5×, rate ±5%",
                  "Finds the exact 'breaking point' — not a scenario",
                ],
                code: `# SciPy finds the worst case:
result = differential_evolution(
  objective, bounds=[(0.7,1.3),(0.5,2.5),(r-0.03,r+0.05)],
  maxiter=15, popsize=8, seed=42
)
# → Breaking: spot=$131.5, vol=49.2%, error=$3.41`
              },
              {
                title: "Fragility Scorer + Surface Map",
                badge: "Risk Quantification",
                color: "#ff7878",
                description: "The final output is a normalized Fragility Index from 0 to 100, computed from the ratio of adversarial error to base price. Additionally, a 7×7 grid maps pricing error across the entire spot/volatility parameter space.",
                points: [
                  "Fragility Index: 0–100 (ROBUST / VULNERABLE / FRAGILE / CRITICAL)",
                  "7×7 surface: 49 pricing evaluations across vol × spot grid",
                  "Risk attribution identifies which parameter drives instability",
                  "SR 11-7 conceptual soundness: PASS / WARNING / FAIL",
                ],
                code: `# Fragility calculation:
fragility_score = (adversarial_error / base_price) * sensitivity
# → 0–30: ROBUST, 30–60: VULNERABLE
# → 60–80: FRAGILE, 80+: CRITICAL
# → surface[7][7] = error at each vol×spot`
              }
            ].map((engine, i) => (
              <div key={i} className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-7 space-y-5 hover:border-opacity-60 transition-all group"
                style={{ '--accent': engine.color } as any}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-[10px] font-mono uppercase tracking-widest mb-1 px-2 py-0.5 rounded inline-block"
                      style={{ color: engine.color, backgroundColor: `${engine.color}12`, border: `1px solid ${engine.color}25` }}>
                      {engine.badge}
                    </div>
                    <h3 className="text-lg font-bold text-[#e5e1e4] mt-2">{engine.title}</h3>
                  </div>
                </div>
                <p className="text-sm text-[#908fa0] leading-relaxed">{engine.description}</p>
                <ul className="space-y-2">
                  {engine.points.map((pt, j) => (
                    <li key={j} className="flex items-start gap-2.5 text-xs text-[#c7c4d7]">
                      <Icons.Check className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" style={{ color: engine.color }} />
                      {pt}
                    </li>
                  ))}
                </ul>
                <div className="font-mono text-[11px] text-[#908fa0] bg-[#0e0e10] border border-[#2e2c33] rounded-lg p-3 leading-relaxed whitespace-pre-wrap">
                  {engine.code}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── ARCHITECTURE ── */}
      <section id="architecture" className="py-28 px-6 border-t border-[#2e2c33] bg-[#0b0b0d]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-[#c0c1ff] mb-3">System Architecture</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-5">
              Full-Stack Quant Platform<br />
              <span className="text-[#c0c1ff]">Built Production-Ready</span>
            </h2>
          </div>

          {/* Architecture diagram (text-based but clean) */}
          <div className="grid md:grid-cols-3 gap-4 mb-12">
            {/* Frontend */}
            <div className="bg-[#161519] border border-[#c0c1ff]/20 rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#c0c1ff]" />
                <h3 className="font-bold text-[#c0c1ff] text-sm font-mono">FRONTEND</h3>
              </div>
              <p className="text-[10px] font-mono text-[#908fa0] uppercase tracking-wider">Next.js 14 · TypeScript · TailwindCSS</p>
              <div className="space-y-2 text-xs font-mono text-[#c7c4d7]">
                {[
                  "/ — Landing Page (this page)",
                  "/dashboard — Model Registry",
                  "/editor — Code Sandbox + Validator",
                  "/validations — All Fragility Reports",
                  "/market — Live Market Data Monitor",
                ].map(r => <div key={r} className="pl-2 border-l border-[#c0c1ff]/20">{r}</div>)}
              </div>
            </div>

            {/* Backend */}
            <div className="bg-[#161519] border border-[#4edea3]/20 rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#4edea3]" />
                <h3 className="font-bold text-[#4edea3] text-sm font-mono">BACKEND API</h3>
              </div>
              <p className="text-[10px] font-mono text-[#908fa0] uppercase tracking-wider">FastAPI · Python 3.12 · Uvicorn ASGI</p>
              <div className="space-y-2 text-xs font-mono text-[#c7c4d7]">
                {[
                  "POST /api/v1/models/upload",
                  "POST /api/v1/validations",
                  "GET  /api/v1/validations/{id}",
                  "GET  /api/v1/market-data/{ticker}",
                  "GET  /api/v1/models/{id}/assumptions",
                ].map(r => <div key={r} className="pl-2 border-l border-[#4edea3]/20">{r}</div>)}
              </div>
            </div>

            {/* Engines */}
            <div className="bg-[#161519] border border-[#ffb95f]/20 rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#ffb95f]" />
                <h3 className="font-bold text-[#ffb95f] text-sm font-mono">ENGINE LAYER</h3>
              </div>
              <p className="text-[10px] font-mono text-[#908fa0] uppercase tracking-wider">QuantLib · SciPy · NumPy · SQLAlchemy</p>
              <div className="space-y-2 text-xs font-mono text-[#c7c4d7]">
                {[
                  "sandbox.py — AST + exec isolation",
                  "quantlib_pricer.py — Analytical BS",
                  "adversarial_engine.py — DiffEvo",
                  "fragility_scorer.py — 0–100 index",
                  "expectations.py — SR 11-7 suite",
                ].map(r => <div key={r} className="pl-2 border-l border-[#ffb95f]/20">{r}</div>)}
              </div>
            </div>
          </div>

          {/* Data Flow */}
          <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-8">
            <h3 className="font-bold text-sm uppercase font-mono text-[#908fa0] mb-6 tracking-wider">End-to-End Data Flow</h3>
            <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
              {[
                { label: "User Code + Params", color: "#c0c1ff" },
                { arrow: true },
                { label: "AST Validation", color: "#4edea3" },
                { arrow: true },
                { label: "QuantLib Baseline", color: "#4edea3" },
                { arrow: true },
                { label: "SciPy Adversarial Search", color: "#ffb95f" },
                { arrow: true },
                { label: "Fragility Surface 7×7", color: "#ff7878" },
                { arrow: true },
                { label: "PostgreSQL Persistence", color: "#908fa0" },
                { arrow: true },
                { label: "AI Executive Report", color: "#c0c1ff" },
                { arrow: true },
                { label: "Dashboard UI", color: "#4edea3" },
              ].map((item, i) => (
                item.arrow
                  ? <span key={i} className="text-[#464554] text-lg">→</span>
                  : <span key={i} className="px-2.5 py-1 rounded-lg border" style={{ color: item.color!, borderColor: `${item.color}30`, backgroundColor: `${item.color}08` }}>
                    {item.label}
                  </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── TECH STACK ── */}
      <section id="stack" className="py-28 px-6 border-t border-[#2e2c33]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-[#c0c1ff] mb-3">Technology Stack</p>
            <h2 className="text-4xl font-bold tracking-tight mb-5">
              Best-in-Class Libraries.<br />
              <span className="text-[#4edea3]">Zero Compromises.</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              {
                name: "QuantLib 1.43",
                role: "Ground Truth Pricing Engine",
                desc: "The industry's reference implementation for derivatives pricing. Used by JPMorgan, Goldman Sachs, and the ECB. We price every option analytically to produce the ground truth.",
                link: "https://www.quantlib.org",
                color: "#c0c1ff",
                tag: "CORE",
              },
              {
                name: "SciPy Optimize",
                role: "Non-Convex Adversarial Search",
                desc: "differential_evolution() — a global optimization algorithm that doesn't need gradients. Finds the true global worst-case, not a local minimum. The adversarial engine's backbone.",
                link: "https://scipy.org",
                color: "#ffb95f",
                tag: "CORE",
              },
              {
                name: "yfinance",
                role: "Real-Time Market Data",
                desc: "No-API-key market data provider. Fetches live spot prices, option chains, and historical OHLCV data for computing 21-day rolling realized volatility.",
                link: "https://github.com/ranaroussi/yfinance",
                color: "#4edea3",
                tag: "DATA",
              },
              {
                name: "FastAPI + Uvicorn",
                role: "Async Backend API",
                desc: "Modern Python ASGI framework with automatic OpenAPI docs. Handles async database sessions, validation pipelines, and streaming computation results.",
                link: "https://fastapi.tiangolo.com",
                color: "#c0c1ff",
                tag: "BACKEND",
              },
              {
                name: "Next.js 14",
                role: "React Frontend Framework",
                desc: "App Router, server components, and optimized bundling for the interactive sandbox, dashboard, and validation report viewer.",
                link: "https://nextjs.org",
                color: "#4edea3",
                tag: "FRONTEND",
              },
              {
                name: "OpenRouter AI",
                role: "Executive Report Synthesis",
                desc: "Routes LLM calls to synthesize plain-English regulatory summaries. Only invoked on validation completion — not for any model pricing computation (which is 100% deterministic).",
                link: "https://openrouter.ai",
                color: "#ffb95f",
                tag: "AI",
              },
              {
                name: "SQLAlchemy + SQLite",
                role: "Model + Validation Persistence",
                desc: "Async ORM persisting financial models, assumption extractions, validation runs, fragility surfaces, and full reports. Supports PostgreSQL for production.",
                link: "https://sqlalchemy.org",
                color: "#908fa0",
                tag: "DATA",
              },
              {
                name: "Python AST Module",
                role: "Static Security Analysis",
                desc: "The stdlib ast module builds a parse tree of user-submitted Python code before execution. FRAGMENT traverses this tree to block any dangerous node types at the syntax level.",
                link: "https://docs.python.org/3/library/ast.html",
                color: "#ff7878",
                tag: "SECURITY",
              },
              {
                name: "NumPy",
                role: "Numerical Grid Computing",
                desc: "Generates the spot/volatility linspaces for the fragility surface heatmap. All matrix computations in the 7×7 adversarial grid use NumPy for performance.",
                link: "https://numpy.org",
                color: "#c0c1ff",
                tag: "COMPUTE",
              },
            ].map((lib, i) => (
              <div key={i} className="bg-[#161519] border border-[#2e2c33] rounded-xl p-5 hover:border-opacity-60 transition-all space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ color: lib.color, backgroundColor: `${lib.color}12`, border: `1px solid ${lib.color}20` }}>
                        {lib.tag}
                      </span>
                    </div>
                    <h3 className="font-bold text-[#e5e1e4]">{lib.name}</h3>
                    <p className="text-[10px] font-mono mt-0.5" style={{ color: lib.color }}>{lib.role}</p>
                  </div>
                </div>
                <p className="text-xs text-[#908fa0] leading-relaxed">{lib.desc}</p>
                <a href={lib.link} target="_blank" rel="noopener noreferrer"
                  className="text-[10px] font-mono text-[#464554] hover:text-[#908fa0] transition-colors">
                  {lib.link.replace("https://", "")} ↗
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section id="cta" className="py-28 px-6 border-t border-[#2e2c33] bg-[#0b0b0d]">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#1a1820] border border-[#c0c1ff]/20 text-[#c0c1ff] text-xs font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            Ready in 30 seconds
          </div>

          <h2 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight">
            Find Your Model's<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
              Breaking Point Today
            </span>
          </h2>

          <p className="text-[#908fa0] text-lg max-w-xl mx-auto leading-relaxed">
            Paste your Python pricing model. Get back a Fragility Index, breaking market parameters, Greek drifts, and an SR 11-7 compliance report — all in one click.
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

          {/* Quick links bar */}
          <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 pt-4 text-xs font-mono text-[#908fa0]">
            {[
              { href: "/editor", label: "Model Sandbox" },
              { href: "/dashboard", label: "Model Registry" },
              { href: "/validations", label: "Fragility Reports" },
              { href: "/market", label: "Market Monitor" },
            ].map(l => (
              <Link key={l.href} href={l.href} className="hover:text-[#c0c1ff] transition-colors">
                {l.label} →
              </Link>
            ))}
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
            <span className="text-xs text-[#464554] font-mono ml-2">Adversarial Model Risk Validation Platform</span>
          </div>
          <div className="flex items-center gap-6 text-xs font-mono text-[#464554]">
            <span>QuantLib 1.43</span>
            <span>·</span>
            <span>SR 11-7 Compliant</span>
            <span>·</span>
            <span>Python 3.12</span>
            <span>·</span>
            <span>FastAPI</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
