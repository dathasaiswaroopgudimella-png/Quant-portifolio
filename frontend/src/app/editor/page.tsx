"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { fetchApi, ModelData, ValidationRunData, AssumptionData } from "@/lib/api";
import {
  Code2,
  Play,
  ShieldCheck,
  AlertTriangle,
  Cpu,
  Layers,
  RefreshCw,
  Sparkles,
  Upload,
  BookOpen,
  ArrowRight,
  FileCode,
  CheckCircle2,
} from "lucide-react";

const PRESET_MODELS = [
  {
    name: "Standard Black-Scholes Call",
    asset_class: "Equity Options",
    desc: "Baseline analytical European call option pricing function with constant volatility",
    code: `def black_scholes_call(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
`,
  },
  {
    name: "Black-Scholes European Put",
    asset_class: "Equity Options",
    desc: "Analytical European put option using put-call parity formulation",
    code: `def black_scholes_put(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(0.0, K - S)
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return K * math.exp(-r*T) * N(-d2) - S * N(-d1)
`,
  },
  {
    name: "Garman-Kohlhagen Foreign Exchange (FX) Model",
    asset_class: "FX Options",
    desc: "Currency option model with domestic rate r=4% and foreign rate rf=2%",
    code: `def garman_kohlhagen_fx(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    rf = 0.02
    d1 = (math.log(S/K) + (r - rf + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * math.exp(-rf*T) * N(d1) - K * math.exp(-r*T) * N(d2)
`,
  },
  {
    name: "Merton (1976) Jump-Diffusion Pricing Engine",
    asset_class: "Equity Options",
    desc: "Poisson jump-diffusion model for heavy-tailed, discontinuous market shocks",
    code: `def merton_jump_diffusion(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    lam = 0.75
    gamma_j = -0.05
    delta_j = 0.15
    k = math.exp(gamma_j + 0.5 * delta_j**2) - 1.0
    lam_prime = lam * (1.0 + k)
    total_price = 0.0
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    for n in range(25):
        p_n = (math.exp(-lam_prime * T) * (lam_prime * T)**n) / math.factorial(n)
        sigma_n = math.sqrt(sigma**2 + n * (delta_j**2) / T)
        r_n = r - lam * k + n * math.log(1.0 + k) / T
        d1 = (math.log(S/K) + (r_n + 0.5 * sigma_n**2) * T) / (sigma_n * math.sqrt(T))
        d2 = d1 - sigma_n * math.sqrt(T)
        bs_n = S * N(d1) - K * math.exp(-r_n * T) * N(d2)
        total_price += p_n * max(0.0, bs_n)
    return total_price
`,
  },
  {
    name: "Bjerksund-Stensland (2002) American Option Model",
    asset_class: "American Options",
    desc: "High-precision closed-form approximation for early-exercise American options",
    code: `def bjerksund_stensland_american(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(0.0, S - K)
    q = 0.01
    b = r - q
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    d1 = (math.log(S/K) + (b + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    bs_call = S * math.exp(-q*T) * N(d1) - K * math.exp(-r*T) * N(d2)
    beta = (0.5 - b / sigma**2) + math.sqrt((b / sigma**2 - 0.5)**2 + 2 * r / sigma**2)
    B_inf = (beta / (beta - 1.0)) * K
    B_0 = max(K, (r / (r - b)) * K) if r != b else K
    h_t = -(b * T + 2 * sigma * math.sqrt(T)) * (B_0 / (B_inf - B_0))
    I = B_0 + (B_inf - B_0) * (1.0 - math.exp(h_t))
    if S >= I:
        return S - K
    return max(bs_call, bs_call + (I - K) * ((S / I) ** beta) * (1.0 - math.exp(-r*T)))
`,
  },
  {
    name: "Corrado-Su Gram-Charlier Skewness & Kurtosis Model",
    asset_class: "Index Options",
    desc: "Adjusts Black-Scholes for observed non-Gaussian skewness and kurtosis",
    code: `def corrado_su_skew_kurtosis(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    skewness = -0.65
    kurtosis = 3.90
    sqrt_T = math.sqrt(T)
    d = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*sqrt_T)
    d2 = d - sigma*sqrt_T
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    n_d = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d**2)
    c_bs = S * N(d) - K * math.exp(-r*T) * N(d2)
    mu3 = skewness
    mu4 = kurtosis - 3.0
    Q3 = (1.0 / 6.0) * S * sqrt_T * (2 * sigma * sqrt_T - d) * n_d
    Q4 = (1.0 / 24.0) * S * sqrt_T * (d**2 - 1.0 - 3*d*sigma*sqrt_T + 3*(sigma*sqrt_T)**2) * n_d
    return max(0.0, c_bs + mu3 * Q3 + mu4 * Q4)
`,
  },
  {
    name: "Bachelier (1900) Normal Spread & Negative Rate Model",
    asset_class: "Commodity / Spread",
    desc: "Bachelier arithmetic Brownian motion supporting negative rates & spread valuation",
    code: `def bachelier_normal_pricer(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K)
    sigma_normal = sigma * S
    sqrt_T = math.sqrt(T)
    d = (S - K) / (sigma_normal * sqrt_T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    n_d = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d**2)
    disc = math.exp(-r * T)
    return max(0.0, disc * ((S - K) * N(d) + sigma_normal * sqrt_T * n_d))
`,
  },
  {
    name: "High-Volatility Skew Vulnerable Option",
    asset_class: "Commodity Options",
    desc: "Pricing model susceptible to extreme volatility skew breakdown",
    code: `def skew_vulnerable_option(S, K, T, r, sigma):
    import math
    adj_sigma = sigma * (1.0 + 0.15 * (S - K) / K)
    adj_sigma = max(0.01, adj_sigma)
    d1 = (math.log(S/K) + (r + 0.5*adj_sigma**2)*T) / (adj_sigma*math.sqrt(T))
    d2 = d1 - adj_sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
`,
  },
  {
    name: "Short Maturity Zero-Yield Edge Model",
    asset_class: "Index Options",
    desc: "Edge-case pricing function evaluated near zero rate & short tenor limits",
    code: `def short_tenor_option(S, K, T, r, sigma):
    import math
    T_safe = max(T, 1e-5)
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T_safe) / (sigma*math.sqrt(T_safe))
    d2 = d1 - sigma*math.sqrt(T_safe)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T_safe) * N(d2)
`,
  },
];

function ModelEditorInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const modelIdParam = searchParams?.get("modelId");

  const [activeTab, setActiveTab] = useState<"code" | "prompt" | "upload" | "preset">("code");
  const [code, setCode] = useState(PRESET_MODELS[0].code);
  const [modelName, setModelName] = useState("Custom Black-Scholes Call");
  const [assetClass, setAssetClass] = useState("Equity Options");
  const [promptText, setPromptText] = useState("European call option using Black-Scholes formula with continuous dividend yield q");

  const [models, setModels] = useState<ModelData[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [assumptions, setAssumptions] = useState<AssumptionData[]>([]);

  // Valuation Parameters
  const [spot, setSpot] = useState(100.0);
  const [strike, setStrike] = useState(100.0);
  const [maturity, setMaturity] = useState(1.0);
  const [rate, setRate] = useState(0.05);
  const [volatility, setVolatility] = useState(0.20);

  // Execution States
  const [isLoading, setIsLoading] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationRunData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  async function loadModels() {
    try {
      const data = await fetchApi<ModelData[]>("/models");
      const modelList = Array.isArray(data) ? data : [];
      setModels(modelList);
      if (modelIdParam) {
        const target = modelList.find((m) => m.id === modelIdParam);
        if (target) {
          setSelectedModelId(target.id);
          setCode(target.code);
          setModelName(target.name);
          setAssetClass(target.asset_class);
          loadAssumptions(target.id);
          return;
        }
      }
      if (modelList.length > 0) {
        setSelectedModelId(modelList[0].id);
        setCode(modelList[0].code);
        setModelName(modelList[0].name);
        setAssetClass(modelList[0].asset_class);
        loadAssumptions(modelList[0].id);
      }
    } catch (err: any) {
      console.error(err);
    }
  }

  async function loadAssumptions(modelId: string) {
    try {
      const data = await fetchApi<AssumptionData[]>(`/models/${modelId}/assumptions`);
      setAssumptions(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error(err);
    }
  }

  async function handleSynthesizeFromPrompt() {
    if (!promptText.trim()) return;
    setIsSynthesizing(true);
    setErrorMsg(null);
    setStatusMsg("Synthesizing Python model via OpenRouter AI...");
    try {
      const synthesized = await fetchApi<ModelData>("/models/synthesize", {
        method: "POST",
        body: JSON.stringify({
          prompt: promptText,
          asset_class: assetClass,
        }),
      });

      if (synthesized && synthesized.code) {
        setSelectedModelId(synthesized.id);
        setCode(synthesized.code);
        setModelName(synthesized.name || "AI Synthesized Option Model");
        setAssetClass(synthesized.asset_class);
        await loadAssumptions(synthesized.id);

        setActiveTab("code");
        setStatusMsg("Model synthesized successfully from prompt!");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to synthesize model from prompt.");
    } finally {
      setIsSynthesizing(false);
    }
  }

  function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setCode(content);
        setModelName(file.name.replace(/\.[^/.]+$/, ""));
        setActiveTab("code");
        setStatusMsg(`Uploaded code from file: ${file.name}`);
      }
    };
    reader.readAsText(file);
  }

  function handleSelectPreset(preset: typeof PRESET_MODELS[0]) {
    setCode(preset.code);
    setModelName(preset.name);
    setAssetClass(preset.asset_class);
    setActiveTab("code");
    setStatusMsg(`Loaded preset model: '${preset.name}'`);
  }

  async function handleRunValidation() {
    setIsLoading(true);
    setErrorMsg(null);
    setStatusMsg(null);
    try {
      // Step 1: Upload or update current code
      const uploadedModel = await fetchApi<ModelData>("/models/upload", {
        method: "POST",
        body: JSON.stringify({
          name: modelName,
          description: "User submitted option model for validation",
          asset_class: assetClass,
          code: code,
        }),
      });

      const validModelId = uploadedModel?.id || "m-seed-01";
      setSelectedModelId(validModelId);
      await loadAssumptions(validModelId);

      // Step 2: Trigger SciPy Adversarial Validation Search
      const result = await fetchApi<ValidationRunData>("/validations", {
        method: "POST",
        body: JSON.stringify({
          model_id: validModelId,
          spot_price: spot,
          strike_price: strike,
          time_to_maturity: maturity,
          risk_free_rate: rate,
          volatility: volatility,
          option_type: "call",
        }),
      });

      if (result) {
        setValidationResult(result);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute adversarial validation search.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0e0e10] text-[#e5e1e4] p-6 pt-20 font-sans pb-16">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-[#161519] p-5 rounded-2xl border border-[#2e2c33] font-sans">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#c0c1ff]/10 border border-[#c0c1ff]/30 flex items-center justify-center text-[#c0c1ff]">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-[#e5e1e4] flex items-center gap-2 font-sans">
                Multi-Format Model Sandbox & AST Inspector
              </h1>
              <p className="text-xs text-[#908fa0] font-sans font-medium">
                Code Sandbox &bull; Natural Language Synthesis &bull; File Upload &bull; Quant Presets
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 font-sans">
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="bg-[#0e0e10] border border-[#2e2c33] px-3.5 py-2 rounded-lg text-xs text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] font-sans w-48"
              placeholder="Model Name"
            />
            <button
              onClick={handleRunValidation}
              disabled={isLoading || isSynthesizing}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-[#c0c1ff] text-[#1000a9] font-bold text-xs hover:bg-[#8083ff] transition-all disabled:opacity-50 shadow-lg shadow-[#c0c1ff]/20 font-sans"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>SciPy Searching...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Adversarial Validation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Status Alerts */}
        {statusMsg && (
          <div className="p-3.5 rounded-xl bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/30 flex items-center gap-2 text-xs font-sans font-medium">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{statusMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 rounded-xl bg-[#ff7878]/10 text-[#ff7878] border border-[#ff7878]/30 flex items-center gap-3 text-xs font-sans font-medium">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* 4 Ingestion Mode Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-[#2e2c33] pb-3 font-sans">
          {[
            { id: "code", label: "Direct Python Code Sandbox", icon: Code2 },
            { id: "prompt", label: "Natural Language / Formula Prompt (OpenRouter)", icon: Sparkles },
            { id: "upload", label: "File Upload (.py, .txt, .json)", icon: Upload },
            { id: "preset", label: "Quant Model Presets", icon: BookOpen },
          ].map((tab) => {
            const IconComp = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-sans font-semibold transition-all ${
                  isActive
                    ? "bg-[#c0c1ff] text-[#1000a9] shadow-md"
                    : "bg-[#161519] text-[#908fa0] border border-[#2e2c33] hover:text-[#e5e1e4] hover:border-[#464554]"
                }`}
              >
                <IconComp className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Main Ingestion Workspaces */}
        <div className="grid lg:grid-cols-12 gap-6 font-sans">
          
          {/* Left Main Pane (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            
            {/* Tab 1: Code Sandbox */}
            {activeTab === "code" && (
              <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-5 space-y-3 font-sans">
                <div className="flex items-center justify-between text-xs font-sans text-[#908fa0] border-b border-[#2e2c33] pb-2 font-medium">
                  <span className="flex items-center gap-2 text-[#4edea3]">
                    <ShieldCheck className="w-4 h-4" /> PYTHON AST SECURITY INSPECTOR ACTIVE
                  </span>
                  <span>Allowed: math, scipy.stats, numpy</span>
                </div>

                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full h-[400px] bg-[#0e0e10] text-[#e5e1e4] font-mono text-xs p-4 rounded-xl border border-[#2e2c33] focus:outline-none focus:border-[#c0c1ff] resize-none leading-relaxed"
                  spellCheck={false}
                />

                <div className="flex items-center justify-between text-[11px] font-sans text-[#908fa0] font-medium">
                  <span>Signature requirement: (S, K, T, r, sigma)</span>
                  <span>Execution limit: 5.0s hard timeout</span>
                </div>
              </div>
            )}

            {/* Tab 2: Prompt / Formula Synthesis */}
            {activeTab === "prompt" && (
              <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-6 space-y-4 font-sans">
                <div className="space-y-1">
                  <h3 className="font-bold text-sm text-[#e5e1e4] flex items-center gap-2 font-sans">
                    <Sparkles className="w-4 h-4 text-[#c0c1ff]" />
                    OpenRouter Natural Language & Formula Model Synthesizer
                  </h3>
                  <p className="text-xs text-[#908fa0] font-sans">
                    Describe your financial model in plain text, LaTeX formula, or trading specifications. OpenRouter AI will synthesize a complete, sandboxed Python function.
                  </p>
                </div>

                <textarea
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  className="w-full h-[180px] bg-[#0e0e10] text-[#e5e1e4] font-sans text-xs p-4 rounded-xl border border-[#2e2c33] focus:outline-none focus:border-[#c0c1ff] resize-none leading-relaxed"
                  placeholder="e.g. European call option using Black-Scholes formula with continuous dividend yield q"
                />

                <div className="flex items-center justify-between font-sans">
                  <select
                    value={assetClass}
                    onChange={(e) => setAssetClass(e.target.value)}
                    className="bg-[#0e0e10] border border-[#2e2c33] px-3 py-2 rounded-lg text-xs font-sans text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff]"
                  >
                    <option value="Equity Options">Equity Options</option>
                    <option value="FX Options">FX Options</option>
                    <option value="Commodity Options">Commodity Options</option>
                    <option value="Index Options">Index Options</option>
                  </select>

                  <button
                    onClick={handleSynthesizeFromPrompt}
                    disabled={isSynthesizing}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-[#c0c1ff] text-[#1000a9] font-bold text-xs hover:bg-[#8083ff] transition-all disabled:opacity-50 shadow font-sans"
                  >
                    {isSynthesizing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Synthesizing Code...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Synthesize Python Model with OpenRouter</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Tab 3: File Upload */}
            {activeTab === "upload" && (
              <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-8 text-center space-y-4 font-sans">
                <Upload className="w-12 h-12 text-[#c0c1ff] mx-auto opacity-80" />
                <div>
                  <h3 className="font-bold text-base text-[#e5e1e4] font-sans">Upload Quant Pricing Code</h3>
                  <p className="text-xs text-[#908fa0] max-w-sm mx-auto mt-1 font-sans">
                    Select a Python (.py), JSON (.json), or script file containing your option valuation code.
                  </p>
                </div>

                <input
                  type="file"
                  accept=".py,.txt,.json"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload-input"
                />
                <label
                  htmlFor="file-upload-input"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#c0c1ff] text-[#1000a9] font-bold text-xs cursor-pointer hover:bg-[#8083ff] transition-colors shadow font-sans"
                >
                  <Upload className="w-4 h-4" /> Select File from Device
                </label>
              </div>
            )}

            {/* Tab 4: Presets */}
            {activeTab === "preset" && (
              <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-5 space-y-3 font-sans">
                <h3 className="font-bold text-xs uppercase font-sans tracking-wider text-[#908fa0]">
                  Pre-Built Quantitative Models Library
                </h3>

                <div className="space-y-2.5 font-sans">
                  {PRESET_MODELS.map((preset, i) => (
                    <div
                      key={i}
                      onClick={() => handleSelectPreset(preset)}
                      className="p-4 rounded-xl bg-[#0e0e10] border border-[#2e2c33] hover:border-[#c0c1ff]/50 cursor-pointer transition-all flex items-center justify-between group font-sans"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-[#e5e1e4] group-hover:text-[#c0c1ff] font-sans">
                            {preset.name}
                          </span>
                          <span className="text-[10px] font-sans font-medium px-2 py-0.5 rounded bg-[#161519] text-[#908fa0]">
                            {preset.asset_class}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#908fa0] font-sans">{preset.desc}</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-[#908fa0] group-hover:text-[#c0c1ff] group-hover:translate-x-1 transition-all" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Parameter Adjustment Panel */}
            <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-5 space-y-3 font-sans text-xs">
              <h3 className="font-bold uppercase tracking-wider text-[#908fa0] text-[11px] font-sans">
                Valuation Parameters & Baseline Conditions
              </h3>

              <div className="grid grid-cols-5 gap-3 font-sans">
                <div>
                  <label className="text-[#908fa0] block text-[10px] mb-1 font-sans font-medium">Spot (S)</label>
                  <input
                    type="number"
                    value={spot}
                    onChange={(e) => setSpot(parseFloat(e.target.value))}
                    className="w-full bg-[#0e0e10] border border-[#2e2c33] p-2 rounded-lg text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-[#908fa0] block text-[10px] mb-1 font-sans font-medium">Strike (K)</label>
                  <input
                    type="number"
                    value={strike}
                    onChange={(e) => setStrike(parseFloat(e.target.value))}
                    className="w-full bg-[#0e0e10] border border-[#2e2c33] p-2 rounded-lg text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-[#908fa0] block text-[10px] mb-1 font-sans font-medium">Tenor (T y)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={maturity}
                    onChange={(e) => setMaturity(parseFloat(e.target.value))}
                    className="w-full bg-[#0e0e10] border border-[#2e2c33] p-2 rounded-lg text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-[#908fa0] block text-[10px] mb-1 font-sans font-medium">Rate (r)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={rate}
                    onChange={(e) => setRate(parseFloat(e.target.value))}
                    className="w-full bg-[#0e0e10] border border-[#2e2c33] p-2 rounded-lg text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-[#908fa0] block text-[10px] mb-1 font-sans font-medium">Vol (&sigma;)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={volatility}
                    onChange={(e) => setVolatility(parseFloat(e.target.value))}
                    className="w-full bg-[#0e0e10] border border-[#2e2c33] p-2 rounded-lg text-[#e5e1e4] focus:outline-none focus:border-[#c0c1ff] font-mono text-xs"
                  />
                </div>
              </div>
            </div>

          </div>

          {/* Right Main Pane: Live Results & Assumptions (5 cols) */}
          <div className="lg:col-span-5 space-y-4 font-sans">
            
            {/* Validation Outcome Card */}
            {validationResult ? (
              <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-5 space-y-4 font-sans">
                <div className="flex items-center justify-between border-b border-[#2e2c33] pb-3 font-sans">
                  <div>
                    <h3 className="font-bold text-sm text-[#e5e1e4] flex items-center gap-2 font-sans">
                      Fragility Index:
                      <span className={`font-sans font-bold px-2.5 py-0.5 rounded text-xs ${
                        validationResult.classification === "ROBUST"
                          ? "bg-[#4edea3]/10 text-[#4edea3]"
                          : "bg-[#ff7878]/10 text-[#ff7878]"
                      }`}>
                        {validationResult.fragility_score}/100 ({validationResult.classification})
                      </span>
                    </h3>
                  </div>

                  <Link
                    href={`/validations/${validationResult.id}`}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#c0c1ff] text-[#1000a9] font-bold text-xs hover:bg-[#8083ff] transition-all font-sans"
                  >
                    View Deep Report →
                  </Link>
                </div>

                {validationResult.breaking_parameters && (
                  <div className="space-y-2 text-xs font-sans bg-[#0e0e10] p-4 rounded-xl border border-[#2e2c33]">
                    <p className="text-[#ffb95f] font-bold uppercase tracking-wider text-[11px] font-sans">
                      SciPy Worst-Case Market Regime
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-[#908fa0] font-sans">
                      <div>Perturbed Spot: <span className="text-[#e5e1e4] font-mono">${validationResult.breaking_parameters.spot}</span></div>
                      <div>Perturbed Vol: <span className="text-[#e5e1e4] font-mono">{(validationResult.breaking_parameters.volatility * 100).toFixed(1)}%</span></div>
                      <div>User Model Price: <span className="text-[#e5e1e4] font-mono">${validationResult.breaking_parameters.user_price}</span></div>
                      <div>QuantLib Truth: <span className="text-[#e5e1e4] font-mono">${validationResult.breaking_parameters.quantlib_price}</span></div>
                      <div className="col-span-2 text-[#ff7878] font-bold pt-1.5 border-t border-[#2e2c33] font-sans">
                        Max Divergence: <span className="font-mono">${validationResult.breaking_parameters.absolute_error} ({validationResult.breaking_parameters.percentage_error}%)</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-6 text-center space-y-3 font-sans">
                <Cpu className="w-10 h-10 text-[#c0c1ff] mx-auto opacity-80" />
                <h3 className="font-bold text-sm text-[#e5e1e4] font-sans">No Validation Run Executed Yet</h3>
                <p className="text-xs text-[#908fa0] max-w-xs mx-auto font-sans">
                  Click 'Run Adversarial Validation' above to execute SciPy parameter search against QuantLib 1.43 ground truth.
                </p>
              </div>
            )}

            {/* Extracted SymPy Assumptions */}
            <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-5 space-y-3 font-sans">
              <div className="flex items-center justify-between border-b border-[#2e2c33] pb-2 font-sans">
                <h3 className="font-bold text-xs uppercase tracking-wider font-sans text-[#e5e1e4] flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[#ffb95f]" />
                  Extracted Mathematical Assumptions ({assumptions.length})
                </h3>
              </div>

              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1 font-sans">
                {assumptions.map((a) => (
                  <div key={a.id} className="p-3.5 rounded-xl bg-[#0e0e10] border border-[#2e2c33] text-xs space-y-1 font-sans">
                    <div className="flex items-center justify-between font-semibold font-sans">
                      <span className="text-[#c0c1ff]">{a.name}</span>
                      <span className="font-sans font-medium text-[10px] px-2 py-0.5 rounded bg-[#161519] text-[#908fa0]">
                        {a.category}
                      </span>
                    </div>
                    <p className="font-mono text-[11px] text-[#4edea3]">{a.mathematical_form}</p>
                    <p className="text-[#908fa0] text-[11px] leading-snug font-sans">{a.description}</p>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

export default function ModelEditorPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center text-[#c0c1ff] font-sans text-xs">Loading editor…</div>}>
      <ModelEditorInner />
    </Suspense>
  );
}
