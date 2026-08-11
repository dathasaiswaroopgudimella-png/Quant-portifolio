"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { fetchApi, ValidationRunData } from "@/lib/api";
import { Activity, ShieldAlert, CheckCircle2, AlertTriangle, ArrowUpRight, Cpu, Search, FileText } from "lucide-react";

export default function ValidationsListPage() {
  const [validations, setValidations] = useState<ValidationRunData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadValidations();
  }, []);

  async function loadValidations() {
    setIsLoading(true);
    try {
      const data = await fetchApi<ValidationRunData[]>("/validations");
      setValidations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  const filteredRuns = validations.filter(
    (v) =>
      v.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (v.classification && v.classification.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-[#0e0e10] text-[#e5e1e4] p-6 font-sans pb-16">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#2e2c33] pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#e5e1e4] flex items-center gap-2">
              <Activity className="w-6 h-6 text-[#c0c1ff]" />
              Adversarial Validation Runs & Fragility Reports
            </h1>
            <p className="text-xs text-[#908fa0] font-mono">
              QuantLib 1.43 Ground Truth Baseline &bull; SciPy Non-Convex Differential Evolution &bull; Hexagonal Radar Audits
            </p>
          </div>

          <Link
            href="/editor"
            className="px-5 py-2.5 rounded-xl text-xs font-bold font-mono bg-[#c0c1ff] text-[#1000a9] hover:bg-[#8083ff] transition-all shadow"
          >
            + Run New Adversarial Search
          </Link>
        </div>

        {/* Summary Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
          <div className="bg-[#161519] border border-[#2e2c33] p-4 rounded-xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Total Validation Runs</span>
            <div className="text-2xl font-bold text-[#e5e1e4]">{validations.length}</div>
            <span className="text-[10px] text-[#4edea3]">QuantLib Benchmarked</span>
          </div>

          <div className="bg-[#161519] border border-[#2e2c33] p-4 rounded-xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Robust Tier (&le;15 Score)</span>
            <div className="text-2xl font-bold text-[#4edea3]">
              {validations.filter((v) => v.classification === "ROBUST").length}
            </div>
            <span className="text-[10px] text-[#908fa0]">Passes Boundary Safety</span>
          </div>

          <div className="bg-[#161519] border border-[#2e2c33] p-4 rounded-xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Fragile Tier (&gt;40 Score)</span>
            <div className="text-2xl font-bold text-[#ffb95f]">
              {validations.filter((v) => v.classification === "MODERATE" || v.classification === "FRAGILE").length}
            </div>
            <span className="text-[10px] text-[#ffb95f]">Requires Vol Skew Bounds</span>
          </div>

          <div className="bg-[#161519] border border-[#2e2c33] p-4 rounded-xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Critical Tier (&gt;70 Score)</span>
            <div className="text-2xl font-bold text-[#ff7878]">
              {validations.filter((v) => v.classification === "CRITICAL").length}
            </div>
            <span className="text-[10px] text-[#ff7878]">Action Required</span>
          </div>
        </div>

        {/* Validation Runs Inventory Table */}
        <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#2e2c33] pb-4">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#908fa0]">
              Adversarial Validation Logs & Hexagonal Reports
            </h2>
            <div className="relative">
              <Search className="w-4 h-4 text-[#908fa0] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search run ID or classification..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-[#0e0e10] border border-[#2e2c33] pl-9 pr-4 py-1.5 rounded-lg text-xs text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] w-64 font-mono"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="py-16 text-center text-xs font-mono text-[#908fa0]">
              Loading quantitative validation runs...
            </div>
          ) : filteredRuns.length === 0 ? (
            <div className="py-16 text-center space-y-3 font-mono text-xs">
              <Cpu className="w-8 h-8 text-[#908fa0] mx-auto opacity-60" />
              <p className="text-[#908fa0]">No validation runs found. Open the Model Sandbox to launch your first test.</p>
              <Link
                href="/editor"
                className="inline-flex items-center gap-1.5 text-[#c0c1ff] hover:underline font-bold"
              >
                Launch Sandbox Editor →
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0e0e10] border-b border-[#2e2c33] text-[#908fa0] uppercase">
                  <tr>
                    <th className="py-3 px-4">Run ID</th>
                    <th className="py-3 px-4">Fragility Index</th>
                    <th className="py-3 px-4">Conceptual Soundness</th>
                    <th className="py-3 px-4">Max Divergence</th>
                    <th className="py-3 px-4">Execution Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2e2c33]">
                  {filteredRuns.map((v) => (
                    <tr key={v.id} className="hover:bg-[#1f1e24] transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#c0c1ff]">{v.id.substring(0, 8)}...</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[11px] font-bold ${
                            v.classification === "ROBUST"
                              ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
                              : v.classification === "MODERATE"
                              ? "bg-[#ffb95f]/10 text-[#ffb95f] border border-[#ffb95f]/30"
                              : "bg-[#ff7878]/10 text-[#ff7878] border border-[#ff7878]/30"
                          }`}
                        >
                          {v.fragility_score}/100 ({v.classification})
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-[#e5e1e4]">
                        {v.hexagonal_scores?.conceptual_soundness ?? 85}%
                      </td>
                      <td className="py-3.5 px-4 text-[#ffb95f] font-bold">
                        ${v.max_pricing_error?.toFixed(4) || "0.0000"}
                      </td>
                      <td className="py-3.5 px-4 text-[#908fa0]">
                        {new Date(v.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/validations/${v.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#c0c1ff]/10 text-[#c0c1ff] border border-[#c0c1ff]/30 hover:bg-[#c0c1ff] hover:text-[#1000a9] font-bold transition-all"
                        >
                          <FileText className="w-3.5 h-3.5" />
                          View Full Report
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
