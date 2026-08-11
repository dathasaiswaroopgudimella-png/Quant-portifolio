"use client";

import { useState, useMemo } from "react";

interface MarketChartProps {
  ticker: string;
  spotPrice: number;
  volatility: number;
  riskFreeRate: number;
}

export default function MarketChart({ ticker, spotPrice, volatility, riskFreeRate }: MarketChartProps) {
  const [activeTab, setActiveTab] = useState<"trend" | "smile">("trend");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Generate 30-day realistic price & volatility trajectory based on live spot & volatility
  const priceHistory = useMemo(() => {
    const data = [];
    let S = spotPrice * 0.94;
    const vol = volatility;
    const dt = 1 / 252;
    const now = new Date();

    for (let i = 30; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);
      
      // Deterministic smooth curve with pseudo-stochastic noise
      const pseudoNoise = Math.sin(i * 0.7) * 0.015 + Math.cos(i * 1.3) * 0.01;
      const drift = (riskFreeRate - 0.5 * vol * vol) * dt + vol * Math.sqrt(dt) * pseudoNoise;
      S = S * Math.exp(drift);

      const dayVol = Math.max(0.05, vol + Math.sin(i * 0.5) * 0.03);

      data.push({
        date: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        price: i === 0 ? spotPrice : parseFloat(S.toFixed(2)),
        volatility: parseFloat((dayVol * 100).toFixed(2)),
      });
    }
    return data;
  }, [ticker, spotPrice, volatility, riskFreeRate]);

  // Generate Volatility Smile (Strike vs Implied Volatility)
  const volSmile = useMemo(() => {
    const strikes = [];
    const baseVol = volatility * 100;
    const S = spotPrice;

    for (let kRel = 0.70; kRel <= 1.30; kRel += 0.05) {
      const strike = parseFloat((S * kRel).toFixed(2));
      // Volatility skew / smile formula: quadratic U-shape for OTM puts and deep OTM calls
      const moneyness = Math.log(strike / S);
      const skewVol = baseVol + 12.5 * (moneyness * moneyness) - 4.2 * moneyness;
      strikes.push({
        strike,
        impliedVol: parseFloat(Math.max(5.0, skewVol).toFixed(2)),
        delta: parseFloat((0.50 - moneyness * 0.65).toFixed(2)),
      });
    }
    return strikes;
  }, [ticker, spotPrice, volatility]);

  // SVG Chart Dimensions
  const W = 720;
  const H = 220;
  const pad = 35;

  // Trend Chart Math
  const minP = Math.min(...priceHistory.map((d) => d.price)) * 0.98;
  const maxP = Math.max(...priceHistory.map((d) => d.price)) * 1.02;

  const points = priceHistory
    .map((d, i) => {
      const x = pad + (i / (priceHistory.length - 1)) * (W - 2 * pad);
      const y = H - pad - ((d.price - minP) / (maxP - minP || 1)) * (H - 2 * pad);
      return `${x},${y}`;
    })
    .join(" ");

  const areaPoints = `${pad},${H - pad} ${points} ${W - pad},${H - pad}`;

  // Smile Chart Math
  const minVol = Math.min(...volSmile.map((s) => s.impliedVol)) * 0.90;
  const maxVol = Math.max(...volSmile.map((s) => s.impliedVol)) * 1.10;

  const smilePoints = volSmile
    .map((s, i) => {
      const x = pad + (i / (volSmile.length - 1)) * (W - 2 * pad);
      const y = H - pad - ((s.impliedVol - minVol) / (maxVol - minVol || 1)) * (H - 2 * pad);
      return `${x},${y}`;
    })
    .join(" ");

  const hoveredData = hoverIndex !== null ? priceHistory[hoverIndex] : priceHistory[priceHistory.length - 1];

  return (
    <div className="bg-[#161519] border border-[#2e2c33] rounded-xl p-6 font-sans space-y-4">
      {/* Header controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#2e2c33] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-[#e5e1e4]">{ticker} Volatility & Price Analytics</h2>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#c0c1ff]/10 text-[#c0c1ff] border border-[#c0c1ff]/20">
              LIVE SIMULATION
            </span>
          </div>
          <p className="text-xs text-[#908fa0] mt-0.5">
            30-Day Historical Trend · Implied Volatility Smile Skew Matrix
          </p>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center gap-1.5 bg-[#0e0e10] p-1 rounded-lg border border-[#2e2c33]">
          <button
            onClick={() => setActiveTab("trend")}
            className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
              activeTab === "trend"
                ? "bg-[#c0c1ff] text-[#1000a9]"
                : "text-[#908fa0] hover:text-[#e5e1e4]"
            }`}
          >
            30D Price Trend
          </button>
          <button
            onClick={() => setActiveTab("smile")}
            className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
              activeTab === "smile"
                ? "bg-[#4edea3] text-[#003822]"
                : "text-[#908fa0] hover:text-[#e5e1e4]"
            }`}
          >
            Vol Smile Skew
          </button>
        </div>
      </div>

      {/* SVG Interactive Canvas */}
      <div className="relative w-full overflow-hidden bg-[#0e0e10] border border-[#2e2c33] rounded-lg p-3">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#c0c1ff" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#c0c1ff" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="smileGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4edea3" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#4edea3" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((r) => {
            const y = pad + r * (H - 2 * pad);
            return (
              <line
                key={r}
                x1={pad}
                y1={y}
                x2={W - pad}
                y2={y}
                stroke="#1e1d21"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
            );
          })}

          {activeTab === "trend" ? (
            <>
              {/* Fill Area */}
              <polygon points={areaPoints} fill="url(#trendGrad)" />
              {/* Curve Line */}
              <polyline
                points={points}
                fill="none"
                stroke="#c0c1ff"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Interactive Dots */}
              {priceHistory.map((d, i) => {
                const x = pad + (i / (priceHistory.length - 1)) * (W - 2 * pad);
                const y = H - pad - ((d.price - minP) / (maxP - minP || 1)) * (H - 2 * pad);
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r={hoverIndex === i ? "5" : "2.5"}
                    fill={hoverIndex === i ? "#4edea3" : "#c0c1ff"}
                    className="cursor-pointer transition-all"
                    onMouseEnter={() => setHoverIndex(i)}
                  />
                );
              })}
            </>
          ) : (
            <>
              {/* Smile Curve Line */}
              <polyline
                points={smilePoints}
                fill="none"
                stroke="#4edea3"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Smile Dots */}
              {volSmile.map((s, i) => {
                const x = pad + (i / (volSmile.length - 1)) * (W - 2 * pad);
                const y = H - pad - ((s.impliedVol - minVol) / (maxVol - minVol || 1)) * (H - 2 * pad);
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r="4"
                    fill="#4edea3"
                    stroke="#0e0e10"
                    strokeWidth="1.5"
                  />
                );
              })}
            </>
          )}
        </svg>

        {/* Live Metrics Bar below chart */}
        <div className="flex flex-wrap items-center justify-between gap-4 mt-3 pt-3 border-t border-[#1e1d21] text-xs font-mono">
          <div className="flex items-center gap-4">
            <span className="text-[#908fa0]">Date: <strong className="text-[#e5e1e4]">{hoveredData.date}</strong></span>
            <span className="text-[#908fa0]">Spot Price: <strong className="text-[#c0c1ff]">${hoveredData.price.toFixed(2)}</strong></span>
            <span className="text-[#908fa0]">21D Vol: <strong className="text-[#4edea3]">{hoveredData.volatility}%</strong></span>
          </div>
          <span className="text-[11px] text-[#606070]">Hover nodes to inspect historical data points</span>
        </div>
      </div>
    </div>
  );
}
