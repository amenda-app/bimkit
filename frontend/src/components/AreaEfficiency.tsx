"use client";

import { useMemo } from "react";
import type { Area } from "@/lib/types";

interface AreaEfficiencyProps {
  areas: Area[];
  totalArea: number; // BGF
  buildingType: string; // e.g. "Bürogebäude"
}

interface Benchmark {
  label: string;
  min: number;
  max: number;
}

// Benchmarks by building type and ratio
const BENCHMARKS: Record<string, { nuf: Benchmark; tf: Benchmark; vf: Benchmark }> = {
  Bürogebäude: {
    nuf: { label: "Büro", min: 0.55, max: 0.65 },
    tf: { label: "Büro", min: 0.05, max: 0.10 },
    vf: { label: "Büro", min: 0.15, max: 0.25 },
  },
  Wohngebäude: {
    nuf: { label: "Wohnen", min: 0.75, max: 0.80 },
    tf: { label: "Wohnen", min: 0.03, max: 0.06 },
    vf: { label: "Wohnen", min: 0.10, max: 0.15 },
  },
  Schulgebäude: {
    nuf: { label: "Schule", min: 0.55, max: 0.65 },
    tf: { label: "Schule", min: 0.05, max: 0.10 },
    vf: { label: "Schule", min: 0.20, max: 0.30 },
  },
};

const DEFAULT_BENCHMARK = {
  nuf: { label: "Standard", min: 0.55, max: 0.70 },
  tf: { label: "Standard", min: 0.05, max: 0.10 },
  vf: { label: "Standard", min: 0.15, max: 0.25 },
};

function getVerdict(value: number, bench: Benchmark): { text: string; color: string } {
  if (value >= bench.min && value <= bench.max) return { text: "Gut", color: "emerald" };
  if (value >= bench.min * 0.85) return { text: "Akzeptabel", color: "amber" };
  if (value > bench.max * 1.1) return { text: "Hoch", color: "amber" };
  return { text: "Niedrig", color: "red" };
}

function gaugeColor(verdict: string): string {
  if (verdict === "Gut") return "#22c55e";
  if (verdict === "Akzeptabel" || verdict === "Hoch") return "#eab308";
  return "#ef4444";
}

interface GaugeProps {
  title: string;
  value: number;
  benchmark: Benchmark;
  unit?: string;
}

function EfficiencyGauge({ title, value, benchmark }: GaugeProps) {
  const verdict = getVerdict(value, benchmark);
  const color = gaugeColor(verdict.text);

  // Map value to 0-180 degrees. Scale: 0.0 maps to 0, 1.0 maps to 180.
  const clampedValue = Math.max(0, Math.min(value, 1));
  const angle = clampedValue * 180;
  const rad = (angle * Math.PI) / 180;
  const x = 50 + 40 * Math.cos(Math.PI - rad);
  const y = 50 - 40 * Math.sin(Math.PI - rad);
  const largeArc = angle > 180 ? 1 : 0;

  // Benchmark range markers
  const benchMinAngle = benchmark.min * 180;
  const benchMaxAngle = benchmark.max * 180;
  const benchMinRad = (benchMinAngle * Math.PI) / 180;
  const benchMaxRad = (benchMaxAngle * Math.PI) / 180;
  const bMinX = 50 + 40 * Math.cos(Math.PI - benchMinRad);
  const bMinY = 50 - 40 * Math.sin(Math.PI - benchMinRad);
  const bMaxX = 50 + 40 * Math.cos(Math.PI - benchMaxRad);
  const bMaxY = 50 - 40 * Math.sin(Math.PI - benchMaxRad);
  const benchLargeArc = (benchMaxAngle - benchMinAngle) > 180 ? 1 : 0;

  const pctDisplay = (value * 100).toFixed(1);

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs font-medium text-dcab-navy mb-1">{title}</p>
      <svg viewBox="0 0 100 60" className="w-36">
        {/* Background arc */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none" stroke="#e5e7eb" strokeWidth="8" strokeLinecap="round"
        />
        {/* Benchmark range arc (green zone) */}
        <path
          d={`M ${bMinX} ${bMinY} A 40 40 0 ${benchLargeArc} 1 ${bMaxX} ${bMaxY}`}
          fill="none" stroke="#bbf7d0" strokeWidth="8" strokeLinecap="round"
        />
        {/* Value arc */}
        {clampedValue > 0 && (
          <path
            d={`M 10 50 A 40 40 0 ${largeArc} 1 ${x} ${y}`}
            fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          />
        )}
        <text x="50" y="44" textAnchor="middle" fill={color} fontSize="14" fontWeight="bold">
          {pctDisplay}%
        </text>
        <text x="50" y="55" textAnchor="middle" fill="#6b7280" fontSize="5.5">
          {title}
        </text>
      </svg>
      <div className="text-center mt-1 space-y-0.5">
        <span
          className={`inline-block text-xs font-bold px-2 py-0.5 rounded-full ${
            verdict.color === "emerald"
              ? "bg-emerald-100 text-emerald-700"
              : verdict.color === "amber"
                ? "bg-amber-100 text-amber-700"
                : "bg-red-100 text-red-700"
          }`}
        >
          {verdict.text}
        </span>
        <p className="text-[10px] text-dcab-gray">
          Richtwert: {(benchmark.min * 100).toFixed(0)}–{(benchmark.max * 100).toFixed(0)}%
        </p>
      </div>
    </div>
  );
}

export function AreaEfficiency({ areas, totalArea, buildingType }: AreaEfficiencyProps) {
  const benchmarks = BENCHMARKS[buildingType] || DEFAULT_BENCHMARK;

  const { nufRatio, tfRatio, vfRatio, nufArea, tfArea, vfArea } = useMemo(() => {
    const nuf = areas
      .filter((a) => a.category.startsWith("NUF"))
      .reduce((s, a) => s + a.area, 0);
    const tf = areas
      .filter((a) => a.category === "TF")
      .reduce((s, a) => s + a.area, 0);
    const vf = areas
      .filter((a) => a.category === "VF")
      .reduce((s, a) => s + a.area, 0);

    return {
      nufArea: nuf,
      tfArea: tf,
      vfArea: vf,
      nufRatio: totalArea > 0 ? nuf / totalArea : 0,
      tfRatio: totalArea > 0 ? tf / totalArea : 0,
      vfRatio: totalArea > 0 ? vf / totalArea : 0,
    };
  }, [areas, totalArea]);

  const fmt = (v: number) => v.toLocaleString("de-DE", { maximumFractionDigits: 0 });

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-dcab-navy">Flächeneffizienz (DIN 277)</h3>
        <span className="text-xs text-dcab-gray px-2 py-0.5 rounded-full bg-dcab-light">
          {buildingType} · BGF: {fmt(totalArea)} m²
        </span>
      </div>

      <div className="p-4">
        {/* Gauges */}
        <div className="grid grid-cols-3 gap-4">
          <EfficiencyGauge
            title="NUF / BGF"
            value={nufRatio}
            benchmark={benchmarks.nuf}
          />
          <EfficiencyGauge
            title="TF / BGF"
            value={tfRatio}
            benchmark={benchmarks.tf}
          />
          <EfficiencyGauge
            title="VF / BGF"
            value={vfRatio}
            benchmark={benchmarks.vf}
          />
        </div>

        {/* Summary table */}
        <div className="mt-4 grid grid-cols-3 gap-3">
          {[
            { label: "Nutzfläche (NUF)", area: nufArea, ratio: nufRatio },
            { label: "Technikfläche (TF)", area: tfArea, ratio: tfRatio },
            { label: "Verkehrsfläche (VF)", area: vfArea, ratio: vfRatio },
          ].map((item) => (
            <div key={item.label} className="text-center bg-dcab-light/40 rounded p-2">
              <p className="text-[10px] text-dcab-gray">{item.label}</p>
              <p className="text-sm font-bold text-dcab-navy">{fmt(item.area)} m²</p>
              <p className="text-[10px] text-dcab-gray">
                {(item.ratio * 100).toFixed(1)}% der BGF
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
