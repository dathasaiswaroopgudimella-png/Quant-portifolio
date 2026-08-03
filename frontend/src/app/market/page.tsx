"use client";

import { useState, useEffect } from "react";
import { fetchApi, MarketQuoteData } from "@/lib/api";

const TICKERS = ["AAPL", "SPY", "NVDA", "TSLA", "MSFT", "AMZN", "META"];

// Inline SVG icons
const RefreshIcon = ({ spin }: { spin?: boolean }) => (
  <svg className={`w-4 h-4 ${spin ? "animate-spin" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </svg>
);
const TrendingUpIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" />
  </svg>
);
const ActivityIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);
const AlertIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

function VolatilityBar({ value }: { value: number }) {
  const pct = Math.min(value * 100, 100);
  const color = pct < 20 ? "#4edea3" : pct < 40 ? "#ffb95f" : "#ff7878";
  return (
    <div className="mt-2">
      <div className="h-1.5 rounded-full bg-[#1e1d21] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-[#908fa0] mt-1 font-mono">
        <span>0%</span><span>50%+</span>
      </div>
    </div>
  );
}

function StatCard({
  label, value, sub, accent, extra
}: {
  label: string; value: string; sub: string; accent: string; extra?: React.ReactNode;
}) {
  return (
    <div className="bg-[#161519] border border-[#2e2c33] rounded-xl p-5 space-y-1 hover:border-[#464554] transition-colors">
      <p className="text-[10px] font-mono uppercase tracking-widest text-[#908fa0]">{label}</p>
      <p className="text-3xl font-bold font-mono" style={{ color: accent }}>{value}</p>
      <p className="text-xs text-[#908fa0]">{sub}</p>
      {extra}
    </div>
  );
}

export default function MarketMonitorPage() {
  const [selectedTicker, setSelectedTicker] = useState("AAPL");
  const [quote, setQuote] = useState<MarketQuoteData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    loadQuote(selectedTicker);
  }, [selectedTicker]);

  async function loadQuote(symbol: string) {
    setIsLoading(true);
    setError(null);
    setQuote(null);
    try {
      const data = await fetchApi<MarketQuoteData>(`/market-data/${symbol}`);
      setQuote(data);
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err?.message || `Failed to fetch data for ${symbol}. Ensure backend is running at 127.0.0.1:8000.`);
    } finally {
      setIsLoading(false);
    }
  }

  const volPct = quote ? (quote.historical_volatility_21d * 100) : 0;
  const volLabel = volPct < 20 ? "LOW" : volPct < 35 ? "MODERATE" : volPct < 55 ? "HIGH" : "EXTREME";
  const volColor = volPct < 20 ? "#4edea3" : volPct < 35 ? "#ffb95f" : "#ff7878";

  return (
    <div className="min-h-screen bg-[#0e0e10] text-[#e5e1e4] font-sans">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">

        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <ActivityIcon />
              <h1 className="text-2xl font-bold tracking-tight">Live Market Monitor</h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/20 ml-1">
                Yahoo Finance
              </span>
            </div>
            <p className="text-sm text-[#908fa0] font-mono">
              21-Day Rolling Historical Volatility · US 10Y Risk-Free Rate · Real-Time Spot Pricing
            </p>
          </div>

          <button
            onClick={() => loadQuote(selectedTicker)}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#1e1d21] border border-[#2e2c33] text-sm font-mono text-[#c7c4d7] hover:bg-[#2a2831] hover:border-[#c0c1ff]/40 transition-all disabled:opacity-50"
          >
            <RefreshIcon spin={isLoading} />
            {isLoading ? "Fetching..." : "Refresh Data"}
          </button>
        </div>

        {/* Ticker Tabs */}
        <div className="flex flex-wrap gap-2">
          {TICKERS.map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedTicker(sym)}
              className={`px-5 py-2 rounded-lg font-mono text-sm font-semibold transition-all ${
                selectedTicker === sym
                  ? "bg-[#c0c1ff] text-[#1000a9] shadow-lg shadow-[#c0c1ff]/20"
                  : "bg-[#161519] text-[#c7c4d7] border border-[#2e2c33] hover:border-[#c0c1ff]/40 hover:text-[#e5e1e4]"
              }`}
            >
              {sym}
            </button>
          ))}
        </div>

        {/* Error State */}
        {error && (
          <div className="flex items-start gap-3 p-5 rounded-xl bg-[#ff7878]/8 border border-[#ff7878]/25 text-[#ff7878]">
            <AlertIcon />
            <div>
              <p className="font-semibold text-sm">Failed to load market data</p>
              <p className="text-xs mt-1 text-[#ff7878]/80">{error}</p>
              <p className="text-xs mt-2 font-mono text-[#908fa0]">
                Make sure the backend server is running: <code className="text-[#c0c1ff]">cd backend && uvicorn app.main:app --reload</code>
              </p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && !error && (
          <div className="grid md:grid-cols-3 gap-5">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-[#161519] border border-[#2e2c33] rounded-xl p-5 h-32 animate-pulse">
                <div className="h-2 bg-[#2e2c33] rounded mb-3 w-24" />
                <div className="h-8 bg-[#2e2c33] rounded mb-2 w-32" />
                <div className="h-2 bg-[#2e2c33] rounded w-20" />
              </div>
            ))}
          </div>
        )}

        {/* Quote Data */}
        {quote && !isLoading && (
          <>
            {/* Hero Row */}
            <div className="grid md:grid-cols-3 gap-5">
              <StatCard
                label={`${quote.ticker} Live Spot Price`}
                value={`$${quote.spot_price.toFixed(2)}`}
                sub="Real-time via Yahoo Finance"
                accent="#e5e1e4"
                extra={
                  <div className="flex items-center gap-1 text-xs text-[#4edea3] mt-1">
                    <TrendingUpIcon />
                    <span>Live Quote · {lastUpdated?.toLocaleTimeString()}</span>
                  </div>
                }
              />
              <StatCard
                label="21-Day Historical Volatility (σ)"
                value={`${volPct.toFixed(2)}%`}
                sub={`Annualized std deviation of log returns`}
                accent={volColor}
                extra={
                  <div>
                    <VolatilityBar value={quote.historical_volatility_21d} />
                    <span className="text-[10px] font-mono mt-1 inline-block" style={{ color: volColor }}>
                      {volLabel} VOLATILITY REGIME
                    </span>
                  </div>
                }
              />
              <StatCard
                label="Risk-Free Rate (r)"
                value={`${(quote.risk_free_rate * 100).toFixed(2)}%`}
                sub="US 10-Year Treasury Yield"
                accent="#c0c1ff"
                extra={
                  <p className="text-[10px] font-mono text-[#908fa0] mt-1">
                    Used as r in BSM: e<sup>-rT</sup> discounting
                  </p>
                }
              />
            </div>

            {/* Option Pricing Inputs Preview */}
            <div className="bg-[#161519] border border-[#2e2c33] rounded-xl p-6">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-base font-bold text-[#e5e1e4]">Live BSM Pricing Inputs — {quote.ticker}</h2>
                  <p className="text-xs text-[#908fa0] mt-0.5 font-mono">
                    These parameters auto-populate the Model Sandbox Editor for adversarial validation
                  </p>
                </div>
                <a
                  href="/editor"
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#c0c1ff] text-[#1000a9] font-bold text-sm hover:bg-[#8083ff] transition-colors shadow-lg shadow-[#c0c1ff]/20"
                >
                  Validate in Editor →
                </a>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-sm">
                {[
                  { label: "Spot (S)", value: `$${quote.spot_price.toFixed(2)}`, desc: "Current market price" },
                  { label: "Volatility (σ)", value: `${(quote.historical_volatility_21d * 100).toFixed(2)}%`, desc: "21D rolling HV" },
                  { label: "Risk-Free (r)", value: `${(quote.risk_free_rate * 100).toFixed(2)}%`, desc: "US 10Y Treasury" },
                  { label: "Strike (K)", value: `$${(quote.spot_price).toFixed(2)}`, desc: "ATM suggestion" },
                ].map(item => (
                  <div key={item.label} className="bg-[#0e0e10] border border-[#2e2c33] rounded-lg p-3 space-y-1">
                    <p className="text-[10px] uppercase tracking-wider text-[#908fa0]">{item.label}</p>
                    <p className="text-lg font-bold text-[#c0c1ff]">{item.value}</p>
                    <p className="text-[10px] text-[#908fa0]">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Volatility Regime Explanation */}
            <div className="bg-[#161519] border border-[#2e2c33] rounded-xl p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#908fa0] mb-4 font-mono">
                Why Volatility Matters for Adversarial Testing
              </h2>
              <div className="grid md:grid-cols-3 gap-4 text-sm">
                {[
                  {
                    title: "Low Vol (&lt;20%)",
                    desc: "Black-Scholes performs well. Model fragility is lower. Standard assumptions hold.",
                    color: "#4edea3"
                  },
                  {
                    title: "High Vol (&gt;40%)",
                    desc: "BSM log-normality breaks down. Fat tails appear. This is where model errors explode.",
                    color: "#ffb95f"
                  },
                  {
                    title: "FRAGMENT's Role",
                    desc: "We find the exact vol perturbation that maximizes your model's error using SciPy adversarial search.",
                    color: "#c0c1ff"
                  }
                ].map(item => (
                  <div key={item.title} className="space-y-1">
                    <p className="font-semibold" style={{ color: item.color }} dangerouslySetInnerHTML={{ __html: item.title }} />
                    <p className="text-[#908fa0] text-xs leading-relaxed">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
