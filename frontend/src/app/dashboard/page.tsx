"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { fetchApi, ModelData, ValidationRunData } from "@/lib/api";
import {
  LayoutDashboard,
  ShieldAlert,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
  Search,
  Code2,
  Activity,
  Layers,
  FileText,
} from "lucide-react";

export default function DashboardPage() {
  const [models, setModels] = useState<ModelData[]>([]);
  const [validations, setValidations] = useState<ValidationRunData[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [assetClassFilter, setAssetClassFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setIsLoading(true);
    try {
      const [mList, vList] = await Promise.all([
        fetchApi<ModelData[]>("/models"),
        fetchApi<ValidationRunData[]>("/validations"),
      ]);
      setModels(mList);
      setValidations(vList);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  const assetClasses = Array.from(new Set(["ALL", ...models.map((m) => m.asset_class)]));

  const filteredModels = models.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.asset_class.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAsset = assetClassFilter === "ALL" || m.asset_class === assetClassFilter;
    return matchesSearch && matchesAsset;
  });

  return (
    <div className="min-h-screen bg-[#0e0e10] text-[#e5e1e4] p-6 font-sans pb-16">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#2e2c33] pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#e5e1e4] flex items-center gap-2">
              <LayoutDashboard className="w-6 h-6 text-[#c0c1ff]" />
              Quantitative Model Governance Dashboard
            </h1>
            <p className="text-xs text-[#908fa0] font-mono">
              Federal Reserve SR 11-7 Enterprise Governance &bull; QuantLib 1.43 Ground Truth Engine &bull; Hexagonal Audits
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/editor"
              className="px-5 py-2.5 rounded-xl text-xs font-bold font-mono bg-[#c0c1ff] text-[#1000a9] hover:bg-[#8083ff] transition-all shadow"
            >
              + Register / Synthesize Option Model
            </Link>
          </div>
        </div>

        {/* Top Stat Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
          <div className="bg-[#161519] border border-[#2e2c33] p-5 rounded-2xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Registered Models</span>
            <div className="text-3xl font-bold text-[#e5e1e4]">{models.length}</div>
            <span className="text-[10px] text-[#4edea3]">Active in Inventory</span>
          </div>

          <div className="bg-[#161519] border border-[#2e2c33] p-5 rounded-2xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Validation Runs</span>
            <div className="text-3xl font-bold text-[#c0c1ff]">{validations.length}</div>
            <span className="text-[10px] text-[#908fa0]">SciPy Adversarial Searches</span>
          </div>

          <div className="bg-[#161519] border border-[#2e2c33] p-5 rounded-2xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Robust Tier</span>
            <div className="text-3xl font-bold text-[#4edea3]">
              {validations.filter((v) => v.classification === "ROBUST").length}
            </div>
            <span className="text-[10px] text-[#4edea3]">Passes Fed Boundaries</span>
          </div>

          <div className="bg-[#161519] border border-[#2e2c33] p-5 rounded-2xl space-y-1">
            <span className="text-[#908fa0] uppercase tracking-wider text-[10px]">Fragile Tier</span>
            <div className="text-3xl font-bold text-[#ff7878]">
              {validations.filter((v) => v.classification === "FRAGILE" || v.classification === "CRITICAL").length}
            </div>
            <span className="text-[10px] text-[#ff7878]">Requires Governance Review</span>
          </div>
        </div>

        {/* Asset Class Filter Tabs */}
        <div className="flex items-center gap-2 font-mono text-xs border-b border-[#2e2c33] pb-3 overflow-x-auto">
          <span className="text-[#908fa0] mr-2">Asset Class:</span>
          {assetClasses.map((ac) => (
            <button
              key={ac}
              onClick={() => setAssetClassFilter(ac)}
              className={`px-3.5 py-1.5 rounded-lg transition-all ${
                assetClassFilter === ac
                  ? "bg-[#c0c1ff] text-[#1000a9] font-bold shadow"
                  : "bg-[#161519] text-[#908fa0] hover:text-[#e5e1e4]"
              }`}
            >
              {ac}
            </button>
          ))}
        </div>

        {/* Model Inventory Table */}
        <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#2e2c33] pb-4">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#908fa0]">
              Financial Model Inventory & Robustness Matrix
            </h2>
            <div className="relative">
              <Search className="w-4 h-4 text-[#908fa0] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-[#0e0e10] border border-[#2e2c33] pl-9 pr-4 py-1.5 rounded-lg text-xs text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] w-64 font-mono"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="py-16 text-center text-xs font-mono text-[#908fa0]">
              Loading financial model inventory...
            </div>
          ) : filteredModels.length === 0 ? (
            <div className="py-16 text-center text-xs font-mono text-[#908fa0]">
              No financial models match your criteria.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0e0e10] border-b border-[#2e2c33] text-[#908fa0] uppercase">
                  <tr>
                    <th className="py-3 px-4">Model Name</th>
                    <th className="py-3 px-4">Asset Class</th>
                    <th className="py-3 px-4">Latest Fragility Score</th>
                    <th className="py-3 px-4">Registered Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2e2c33]">
                  {filteredModels.map((m) => {
                    const latestVal = validations.find((v) => v.model_id === m.id);

                    return (
                      <tr key={m.id} className="hover:bg-[#1f1e24] transition-colors">
                        <td className="py-3.5 px-4 font-bold text-[#e5e1e4] flex items-center gap-2">
                          <Code2 className="w-4 h-4 text-[#c0c1ff]" />
                          {m.name}
                        </td>
                        <td className="py-3.5 px-4 text-[#908fa0]">{m.asset_class}</td>
                        <td className="py-3.5 px-4">
                          {latestVal ? (
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                                latestVal.classification === "ROBUST"
                                  ? "bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30"
                                  : "bg-[#ff7878]/10 text-[#ff7878] border border-[#ff7878]/30"
                              }`}
                            >
                              {latestVal.fragility_score}/100 ({latestVal.classification})
                            </span>
                          ) : (
                            <span className="text-[#908fa0] italic">Unvalidated</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-[#908fa0]">
                          {new Date(m.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3.5 px-4 text-right space-x-2">
                          {latestVal && (
                            <Link
                              href={`/validations/${latestVal.id}`}
                              className="inline-flex items-center gap-1 text-xs text-[#4edea3] hover:underline font-semibold mr-3"
                            >
                              <FileText className="w-3.5 h-3.5" /> Report
                            </Link>
                          )}
                          <Link
                            href={`/editor?modelId=${m.id}`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#c0c1ff]/10 text-[#c0c1ff] border border-[#c0c1ff]/30 hover:bg-[#c0c1ff] hover:text-[#1000a9] font-bold transition-all"
                          >
                            Validate in Sandbox
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
