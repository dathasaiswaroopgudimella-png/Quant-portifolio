"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { fetchApi, ModelData, ValidationRunData } from "@/lib/api";

const FragilitySurface3D = dynamic(() => import("@/components/FragilitySurface3D"), { ssr: false, loading: () => null });

/* ── Mini SparkLine ────────────────────────────────────────────────── */
function SparkLine({ values, color }: { values: number[]; color: string }) {
  const max = Math.max(...values, 1);
  const W = 80, H = 28;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * W},${H - (v / max) * H}`).join(" ");
  return (
    <svg width={W} height={H} className="opacity-70">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points={`0,${H} ${pts} ${W},${H}`} fill={color} fillOpacity="0.1" stroke="none" />
    </svg>
  );
}

/* ── Hex Radar (compact) ───────────────────────────────────────────── */
function MiniRadar({ scores, size = 80 }: { scores: number[]; size?: number }) {
  const N = 6, cx = size / 2, cy = size / 2, R = size * 0.38;
  const angle = (i: number) => (Math.PI / 2) + (2 * Math.PI * i) / N;
  const pt = (i: number, r: number): [number, number] => [cx + r * Math.cos(angle(i)), cy - r * Math.sin(angle(i))];
  const rings = [0.33, 0.66, 1.0];
  const dataPoints = scores.map((s, i) => pt(i, (s / 100) * R));
  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
      {rings.map(r => (
        <polygon key={r}
          points={Array.from({ length: N }, (_, i) => pt(i, r * R).join(",")).join(" ")}
          fill="none" stroke="#2e2c33" strokeWidth="0.8" />
      ))}
      <polygon
        points={dataPoints.map(p => p.join(",")).join(" ")}
        fill="#c0c1ff" fillOpacity="0.2" stroke="#c0c1ff" strokeWidth="1" />
      {dataPoints.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="2" fill="#c0c1ff" />
      ))}
    </svg>
  );
}

/* ── Stat Card with 3D tilt ────────────────────────────────────────── */
function StatCard({ label, value, sub, color, spark }: {
  label: string; value: string | number; sub: string; color: string; spark?: number[];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const onMM = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    ref.current.style.transform = `perspective(600px) rotateY(${x * 12}deg) rotateX(${-y * 8}deg)`;
  };
  const onML = () => { if (ref.current) ref.current.style.transform = "perspective(600px) rotateY(0) rotateX(0)"; };

  return (
    <div ref={ref} onMouseMove={onMM} onMouseLeave={onML}
      className="relative bg-[#111116] border border-[#2e2c33] rounded-2xl p-5 overflow-hidden group cursor-default transition-transform duration-150"
      style={{ transformStyle: "preserve-3d", willChange: "transform" }}>
      {/* top gradient line */}
      <div className="absolute top-0 left-0 right-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${color}60, transparent)` }} />
      {/* glow bg */}
      <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full opacity-0 group-hover:opacity-100 transition-opacity blur-2xl"
        style={{ background: color }} />

      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-mono text-[#606070] uppercase tracking-widest mb-1">{label}</p>
          <p className="text-3xl font-black" style={{ color }}>{value}</p>
          <p className="text-[10px] text-[#606070] mt-1">{sub}</p>
        </div>
        {spark && <SparkLine values={spark} color={color} />}
      </div>
    </div>
  );
}

/* ── Classification Badge ──────────────────────────────────────────── */
function Badge({ cls }: { cls: string }) {
  const cfg: Record<string, { bg: string; text: string; border: string }> = {
    ROBUST:   { bg: "#4edea3/10", text: "#4edea3", border: "#4edea3/30" },
    MODERATE: { bg: "#ffb95f/10", text: "#ffb95f", border: "#ffb95f/30" },
    FRAGILE:  { bg: "#ff7878/10", text: "#ff7878", border: "#ff7878/30" },
    CRITICAL: { bg: "#ff4040/10", text: "#ff4040", border: "#ff4040/40" },
  };
  const c = cfg[cls] ?? cfg["MODERATE"];
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border`}
      style={{ background: `rgba(${c.text === "#4edea3" ? "78,222,163" : c.text === "#ffb95f" ? "255,185,95" : c.text === "#ff4040" ? "255,64,64" : "255,120,120"},0.1)`, color: c.text, borderColor: c.text + "50" }}>
      {cls}
    </span>
  );
}

/* ── Score Bar ─────────────────────────────────────────────────────── */
function ScoreBar({ score }: { score: number }) {
  const color = score < 30 ? "#4edea3" : score < 65 ? "#ffb95f" : "#ff7878";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[#2e2c33] rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono w-7 text-right" style={{ color }}>{score}</span>
    </div>
  );
}

/* ── Main Dashboard ────────────────────────────────────────────────── */
export default function DashboardPage() {
  const [models, setModels] = useState<ModelData[]>([]);
  const [validations, setValidations] = useState<ValidationRunData[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [assetFilter, setAssetFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [view, setView] = useState<"grid" | "table">("grid");
  const [showSurface, setShowSurface] = useState(false);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setIsLoading(true);
    try {
      const [mList, vList] = await Promise.all([
        fetchApi<ModelData[]>("/models"),
        fetchApi<ValidationRunData[]>("/validations"),
      ]);
      setModels(mList);
      setValidations(vList);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }

  const assetClasses = Array.from(new Set(["ALL", ...models.map(m => m.asset_class)]));
  const filteredModels = models.filter(m => {
    const s = searchQuery.toLowerCase();
    return (m.name.toLowerCase().includes(s) || m.asset_class.toLowerCase().includes(s))
      && (assetFilter === "ALL" || m.asset_class === assetFilter);
  });

  const robust = validations.filter(v => v.classification === "ROBUST").length;
  const fragile = validations.filter(v => ["FRAGILE", "CRITICAL"].includes(v.classification ?? "")).length;
  const avgScore = validations.length
    ? Math.round(validations.reduce((a, v) => a + (v.fragility_score || 0), 0) / validations.length)
    : 0;

  const sparkData = [12, 18, 14, 22, 19, 30, 26, 35, 28, 40];

  return (
    <div className="min-h-screen bg-[#08080d] text-[#e5e1e4] font-sans overflow-x-hidden" style={{ fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>

      {/* ── Ambient 3D Background ─────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-[#c0c1ff]/[0.03] blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[#4edea3]/[0.03] blur-[100px]" />
        <div className="absolute top-[40%] left-[30%] w-[400px] h-[400px] rounded-full bg-[#ffb95f]/[0.02] blur-[100px]" />
        {/* Grid lines */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.025]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#c0c1ff" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="relative" style={{ zIndex: 1 }}>

        {/* ── Nav ──────────────────────────────────────────────────── */}
        <nav className="sticky top-0 z-50 border-b border-[#2e2c33]/60 bg-[#08080d]/80 backdrop-blur-xl px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[#c0c1ff] to-[#4edea3] flex items-center justify-center text-[#08080d] font-black text-[10px]">F</div>
                <span className="font-bold text-xs tracking-widest text-[#e5e1e4]">FRAGMENT</span>
              </Link>
              <div className="hidden md:flex items-center gap-1 text-xs font-sans font-medium">
                {[["Dashboard", "/dashboard", "#c0c1ff"], ["Editor", "/editor", "#4edea3"], ["Market", "/market", "#ffb95f"], ["Validations", "/validations", "#908fa0"]].map(([label, href, color]) => (
                  <Link key={href} href={href}
                    className="px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors"
                    style={{ color: href === "/dashboard" ? color : "#908fa0" }}>
                    {label}
                  </Link>
                ))}
              </div>
            </div>
            <Link href="/editor"
              className="px-4 py-2 bg-gradient-to-r from-[#c0c1ff] to-[#8889ff] text-[#08080d] font-bold text-xs rounded-lg hover:shadow-[0_0_20px_rgba(192,193,255,0.3)] transition-all hover:scale-105 font-sans">
              + New Validation
            </Link>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-6 py-8 space-y-8 font-sans">

          {/* ── Page Header ──────────────────────────────────────────── */}
          <div className="flex flex-wrap items-start justify-between gap-6 font-sans">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
                <span className="text-[11px] font-sans font-semibold text-[#4edea3] tracking-widest uppercase">Live · SR 11-7 Aligned</span>
              </div>
              <h1 className="text-3xl font-black text-[#e5e1e4] leading-tight font-sans">
                Model Risk{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#c0c1ff] to-[#4edea3]">
                  Governance
                </span>
              </h1>
              <p className="text-xs text-[#908fa0] font-sans font-medium mt-1">
                QuantLib 1.43 · SciPy Differential Evolution · AST Inspection · Three.js WebGL
              </p>
            </div>

            <div className="flex items-center gap-3 font-sans">
              <button onClick={() => setShowSurface(!showSurface)}
                className={`px-4 py-2 text-xs font-sans font-medium rounded-lg border transition-all ${showSurface ? "bg-[#c0c1ff]/10 border-[#c0c1ff]/30 text-[#c0c1ff]" : "bg-white/5 border-white/10 text-[#908fa0] hover:text-[#e5e1e4]"}`}>
                {showSurface ? "▼ Hide 3D Surface" : "▲ Show 3D Surface"}
              </button>
              <button onClick={() => setView(view === "grid" ? "table" : "grid")}
                className="px-4 py-2 text-xs font-sans font-medium bg-white/5 border border-white/10 text-[#908fa0] hover:text-[#e5e1e4] rounded-lg transition-all">
                {view === "grid" ? "⊞ Table View" : "⊟ Grid View"}
              </button>
            </div>
          </div>

          {/* ── Stats Row ─────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 font-sans">
            <StatCard label="Registered Models" value={models.length} sub="In governance inventory" color="#c0c1ff" spark={sparkData} />
            <StatCard label="Validation Runs" value={validations.length} sub="Adversarial searches run" color="#4edea3" spark={[...sparkData].reverse()} />
            <StatCard label="Robust Tier" value={robust} sub="Pass Fed boundaries" color="#4edea3" />
            <StatCard label="Avg Fragility Score" value={`${avgScore}/100`} sub={fragile > 0 ? `${fragile} flagged for review` : "All within bounds"} color={avgScore > 60 ? "#ff7878" : "#ffb95f"} />
          </div>

          {/* ── 3D Surface (collapsible) ───────────────────────────────── */}
          {showSurface && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#c0c1ff]/5 via-[#4edea3]/5 to-[#ffb95f]/5 rounded-3xl blur-3xl" />
              <div className="relative backdrop-blur bg-white/[0.02] border border-white/[0.06] rounded-2xl p-1 shadow-[0_0_60px_rgba(192,193,255,0.06)]">
                <FragilitySurface3D title="Portfolio Aggregate Fragility Surface — Drag to Rotate" />
              </div>
            </div>
          )}

          {/* ── Filter Row ────────────────────────────────────────────── */}
          <div className="flex flex-wrap items-center gap-3 font-sans">
            <div className="relative flex-1 min-w-[200px] max-w-xs">
              <svg className="w-3.5 h-3.5 text-[#606070] absolute left-3 top-1/2 -translate-y-1/2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-[#111116] border border-[#2e2c33] pl-9 pr-4 py-2 rounded-xl text-xs text-[#e5e1e4] placeholder-[#606070] focus:outline-none focus:border-[#c0c1ff]/50 font-sans transition-colors"
              />
            </div>

            <div className="flex items-center gap-1.5 flex-wrap font-sans">
              {assetClasses.map(ac => (
                <button key={ac} onClick={() => setAssetFilter(ac)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-sans font-medium transition-all ${assetFilter === ac ? "bg-[#c0c1ff] text-[#08080d] font-bold" : "bg-[#111116] border border-[#2e2c33] text-[#908fa0] hover:text-[#e5e1e4]"}`}>
                  {ac}
                </button>
              ))}
            </div>
          </div>

          {/* ── Model Grid / Table ────────────────────────────────────── */}
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-32 gap-4 font-sans">
              <div className="w-10 h-10 border-2 border-[#c0c1ff]/20 border-t-[#c0c1ff] rounded-full animate-spin" />
              <p className="text-xs font-sans text-[#908fa0] font-medium">Loading model inventory…</p>
            </div>
          ) : filteredModels.length === 0 ? (
            <div className="py-32 text-center font-sans">
              <div className="text-4xl mb-4">🔭</div>
              <p className="text-sm text-[#908fa0] font-sans font-medium mb-6">No models match your filter.</p>
              <Link href="/editor" className="px-6 py-2.5 bg-gradient-to-r from-[#c0c1ff] to-[#8889ff] text-[#08080d] font-bold text-xs rounded-xl hover:scale-105 transition-all font-sans">
                Register First Model →
              </Link>
            </div>
          ) : view === "grid" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 font-sans">
              {filteredModels.map(m => {
                const latestVal = validations.find(v => v.model_id === m.id);
                const demoScores = [88, 91, 76, 94, 83, 89];
                return (
                  <div key={m.id}
                    className="relative bg-[#111116] border border-[#2e2c33] rounded-2xl p-5 hover:border-[#c0c1ff]/25 transition-all duration-300 group overflow-hidden font-sans"
                    style={{ transformStyle: "preserve-3d" }}
                    onMouseMove={e => {
                      const el = e.currentTarget;
                      const r = el.getBoundingClientRect();
                      const x = (e.clientX - r.left) / r.width - 0.5;
                      const y = (e.clientY - r.top) / r.height - 0.5;
                      el.style.transform = `perspective(700px) rotateY(${x * 8}deg) rotateX(${-y * 6}deg)`;
                    }}
                    onMouseLeave={e => { e.currentTarget.style.transform = "perspective(700px) rotateY(0) rotateX(0)"; }}>
                    {/* top shimmer */}
                    <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#c0c1ff]/15 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                    <div className="flex items-start justify-between gap-3 mb-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 font-sans">
                          <div className="w-2 h-2 rounded-full" style={{ background: latestVal?.classification === "ROBUST" ? "#4edea3" : latestVal ? "#ff7878" : "#606070" }} />
                          <span className="text-[11px] font-sans font-medium text-[#908fa0]">{m.asset_class}</span>
                        </div>
                        <h3 className="font-bold text-sm text-[#e5e1e4] truncate font-sans">{m.name}</h3>
                        <p className="text-[11px] text-[#908fa0] font-sans mt-0.5">
                          Registered {new Date(m.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <MiniRadar scores={latestVal ? demoScores : [50, 50, 50, 50, 50, 50]} />
                    </div>

                    {latestVal ? (
                      <div className="space-y-2 mb-4 font-sans">
                        <div className="flex items-center justify-between text-xs font-sans font-medium">
                          <span className="text-[#908fa0]">Robustness Score: {(100 - (latestVal.fragility_score || 0)).toFixed(0)}/100</span>
                          <Badge cls={latestVal.classification ?? "MODERATE"} />
                        </div>
                        <ScoreBar score={latestVal.fragility_score || 0} />
                      </div>
                    ) : (
                      <div className="py-3 mb-4 border border-dashed border-[#2e2c33] rounded-xl text-center text-xs font-sans text-[#908fa0]">
                        No validation run yet
                      </div>
                    )}

                    <div className="flex gap-2 font-sans">
                      <Link href={`/editor?modelId=${m.id}`}
                        className="flex-1 py-2 text-center text-xs font-bold font-sans bg-[#c0c1ff]/10 border border-[#c0c1ff]/20 text-[#c0c1ff] rounded-lg hover:bg-[#c0c1ff] hover:text-[#08080d] transition-all">
                        Validate →
                      </Link>
                      {latestVal && (
                        <Link href={`/validations/${latestVal.id}`}
                          className="flex-1 py-2 text-center text-xs font-bold font-sans bg-white/5 border border-white/10 text-[#908fa0] rounded-lg hover:text-[#e5e1e4] transition-all">
                          Report
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Table View */
            <div className="bg-[#111116] border border-[#2e2c33] rounded-2xl overflow-hidden font-sans">
              <div className="border-b border-[#2e2c33] px-6 py-4 flex items-center justify-between">
                <h2 className="text-xs font-sans font-bold text-[#908fa0] uppercase tracking-widest">
                  Financial Model Inventory · {filteredModels.length} Models
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-sans">
                  <thead>
                    <tr className="bg-[#0d0d12] border-b border-[#2e2c33] text-[#908fa0] uppercase text-[11px] font-sans font-semibold">
                      <th className="py-3 px-5 text-left font-semibold">Model</th>
                      <th className="py-3 px-5 text-left font-semibold">Asset Class</th>
                      <th className="py-3 px-5 text-left font-semibold">Fragility</th>
                      <th className="py-3 px-5 text-left font-semibold">Classification</th>
                      <th className="py-3 px-5 text-left font-semibold">Registered</th>
                      <th className="py-3 px-5 text-right font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#2e2c33]/60 font-sans">
                    {filteredModels.map(m => {
                      const v = validations.find(v => v.model_id === m.id);
                      return (
                        <tr key={m.id} className="hover:bg-white/[0.02] transition-colors font-sans">
                          <td className="py-3.5 px-5 font-bold text-[#e5e1e4] font-sans">
                            <div className="flex items-center gap-2">
                              <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: v?.classification === "ROBUST" ? "#4edea3" : v ? "#ff7878" : "#606070" }} />
                              {m.name}
                            </div>
                          </td>
                          <td className="py-3.5 px-5 text-[#908fa0] font-medium">{m.asset_class}</td>
                          <td className="py-3.5 px-5 w-36">
                            {v ? <ScoreBar score={v.fragility_score || 0} /> : <span className="text-[#606070] italic text-xs font-sans">Unvalidated</span>}
                          </td>
                          <td className="py-3.5 px-5">
                            {v ? <Badge cls={v.classification ?? "MODERATE"} /> : "—"}
                          </td>
                          <td className="py-3.5 px-5 text-[#908fa0] font-medium">{new Date(m.created_at).toLocaleDateString()}</td>
                          <td className="py-3.5 px-5 text-right">
                            <div className="flex items-center justify-end gap-2 font-sans font-medium">
                              {v && (
                                <Link href={`/validations/${v.id}`} className="text-[#4edea3] hover:underline">Report</Link>
                              )}
                              <Link href={`/editor?modelId=${m.id}`}
                                className="px-3 py-1 bg-[#c0c1ff]/10 border border-[#c0c1ff]/20 text-[#c0c1ff] rounded-lg hover:bg-[#c0c1ff] hover:text-[#08080d] font-bold transition-all">
                                Validate →
                              </Link>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── Recent Validations ───────────────────────────────────── */}
          {validations.length > 0 && (
            <div className="bg-[#111116] border border-[#2e2c33] rounded-2xl overflow-hidden font-sans">
              <div className="border-b border-[#2e2c33] px-6 py-4 flex items-center justify-between">
                <h2 className="text-xs font-sans font-bold text-[#908fa0] uppercase tracking-widest">Recent Validation Runs</h2>
                <Link href="/validations" className="text-xs font-sans font-semibold text-[#c0c1ff] hover:underline">View All →</Link>
              </div>
              <div className="divide-y divide-[#2e2c33]/40 font-sans">
                {validations.slice(0, 5).map(v => {
                  const model = models.find(m => m.id === v.model_id);
                  return (
                    <div key={v.id} className="px-6 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors group font-sans">
                      <div className="flex items-center gap-4 font-sans">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm"
                          style={{ background: v.classification === "ROBUST" ? "#4edea3/10" : "#ff7878/10" }}>
                          {v.classification === "ROBUST" ? "✓" : "⚠"}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-[#e5e1e4] font-sans">{model?.name ?? "Unknown Model"}</p>
                          <p className="text-[11px] text-[#908fa0] font-sans font-medium">
                            {new Date(v.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 font-sans">
                        <div className="hidden sm:block w-32">
                          <ScoreBar score={v.fragility_score || 0} />
                        </div>
                        <Badge cls={v.classification ?? "MODERATE"} />
                        <Link href={`/validations/${v.id}`}
                          className="text-xs font-sans font-semibold text-[#c0c1ff] opacity-0 group-hover:opacity-100 transition-opacity hover:underline">
                          View →
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Footer ─────────────────────────────────────────────── */}
          <div className="border-t border-[#2e2c33]/40 pt-6 flex flex-wrap items-center justify-between gap-3 text-xs font-sans text-[#908fa0]">
            <span className="font-medium">FRAGMENT · Adversarial Model Risk Validation Platform</span>
            <div className="flex items-center gap-4 text-[11px] font-sans">
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

        </div>
      </div>
    </div>
  );
}
