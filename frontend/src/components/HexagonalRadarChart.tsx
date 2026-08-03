"use client";

import React from "react";
import { HexagonalScoresData } from "@/lib/api";

interface Props {
  scores?: HexagonalScoresData;
  size?: number;
}

const DEFAULT_SCORES: HexagonalScoresData = {
  conceptual_soundness: 85,
  numerical_stability: 92,
  parameter_robustness: 70,
  boundary_condition_safety: 88,
  greek_fidelity: 90,
  benchmark_alignment: 95,
};

const AXES = [
  { key: "conceptual_soundness", label: "Conceptual Soundness", color: "#c0c1ff" },
  { key: "numerical_stability", label: "Numerical Stability", color: "#4edea3" },
  { key: "parameter_robustness", label: "Parameter Robustness", color: "#ffb95f" },
  { key: "boundary_condition_safety", label: "Boundary Safety", color: "#ff7878" },
  { key: "greek_fidelity", label: "Greek Fidelity", color: "#8083ff" },
  { key: "benchmark_alignment", label: "Benchmark Alignment", color: "#38bdf8" },
];

export function HexagonalRadarChart({ scores = DEFAULT_SCORES, size = 380 }: Props) {
  const center = size / 2;
  const radius = size * 0.35;
  const numAxes = AXES.length;
  const angleStep = (2 * Math.PI) / numAxes;

  // Grid levels (20%, 40%, 60%, 80%, 100%)
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];

  const getCoordinates = (valueNormalized: number, index: number) => {
    const angle = index * angleStep - Math.PI / 2; // Start from top
    const r = radius * valueNormalized;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y };
  };

  // Build points for current score polygon
  const scorePoints = AXES.map((axis, i) => {
    const rawVal = (scores as any)[axis.key] ?? 75;
    const normVal = Math.max(0.05, Math.min(1.0, rawVal / 100));
    return getCoordinates(normVal, i);
  });

  const polygonPathString = scorePoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

  return (
    <div className="relative flex flex-col items-center justify-center p-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
        <defs>
          {/* Glowing gradient for radar fill */}
          <radialGradient id="hexRadarGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#8083ff" stopOpacity="0.45" />
            <stop offset="70%" stopColor="#c0c1ff" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#4edea3" stopOpacity="0.05" />
          </radialGradient>

          {/* Stroke gradient */}
          <linearGradient id="hexStrokeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#c0c1ff" />
            <stop offset="50%" stopColor="#4edea3" />
            <stop offset="100%" stopColor="#8083ff" />
          </linearGradient>

          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Concentric Hexagonal Grids */}
        {gridLevels.map((lvl) => {
          const gridPts = AXES.map((_, i) => getCoordinates(lvl, i));
          const gridPathStr = gridPts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
          return (
            <path
              key={lvl}
              d={gridPathStr}
              fill="none"
              stroke="#2e2c33"
              strokeWidth={lvl === 1.0 ? "1.5" : "1"}
              strokeDasharray={lvl === 1.0 ? undefined : "3 3"}
              className="opacity-60"
            />
          );
        })}

        {/* Axis Lines from center */}
        {AXES.map((axis, i) => {
          const outer = getCoordinates(1.0, i);
          return (
            <line
              key={axis.key}
              x1={center}
              y1={center}
              x2={outer.x}
              y2={outer.y}
              stroke="#2e2c33"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
          );
        })}

        {/* Filled Data Polygon */}
        <path
          d={polygonPathString}
          fill="url(#hexRadarGlow)"
          stroke="url(#hexStrokeGrad)"
          strokeWidth="2.5"
          filter="url(#glow)"
          className="transition-all duration-700 ease-out"
        />

        {/* Vertex Points & Labels */}
        {scorePoints.map((pt, i) => {
          const axis = AXES[i];
          const rawVal = (scores as any)[axis.key] ?? 75;
          const outerPos = getCoordinates(1.18, i);

          return (
            <g key={axis.key} className="group cursor-pointer">
              {/* Pulsing Vertex Circle */}
              <circle
                cx={pt.x}
                cy={pt.y}
                r="5"
                fill={axis.color}
                stroke="#0e0e10"
                strokeWidth="2"
                className="transition-transform duration-300 group-hover:scale-150"
              />
              <circle
                cx={pt.x}
                cy={pt.y}
                r="9"
                fill="none"
                stroke={axis.color}
                strokeWidth="1"
                className="animate-ping opacity-40"
              />

              {/* Axis Label */}
              <text
                x={outerPos.x}
                y={outerPos.y}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#c7c4d7"
                fontSize="11"
                fontWeight="600"
                fontFamily="sans-serif"
                className="transition-colors group-hover:fill-[#e5e1e4]"
              >
                {axis.label}
              </text>

              {/* Score Value Tag */}
              <text
                x={outerPos.x}
                y={outerPos.y + 14}
                textAnchor="middle"
                dominantBaseline="central"
                fill={axis.color}
                fontSize="11"
                fontWeight="700"
                fontFamily="monospace"
              >
                {rawVal.toFixed(0)}/100
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
