"use client";

import type { CostEstimate } from "@/lib/types";

interface CostBreakdownProps {
  estimate: CostEstimate;
}

const EUR = (v: number) => v.toLocaleString("de-DE", { style: "currency", currency: "EUR" });

const BAR_COLORS = [
  "bg-dcab-navy", "bg-dcab-blue", "bg-emerald-500", "bg-amber-500",
  "bg-purple-500", "bg-rose-500", "bg-teal-500", "bg-orange-500", "bg-indigo-500",
];

export function CostBreakdown({ estimate }: CostBreakdownProps) {
  const maxSubtotal = Math.max(...estimate.cost_groups.map((cg) => cg.subtotal), 1);

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-dcab-navy">Kostenschätzung DIN 276</h3>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 p-4 bg-dcab-light/50">
        <div>
          <p className="text-xs text-dcab-gray">Gesamtkosten</p>
          <p className="text-lg font-bold text-dcab-navy">{EUR(estimate.total_cost)}</p>
        </div>
        <div>
          <p className="text-xs text-dcab-gray">Kosten pro m²</p>
          <p className="text-lg font-bold text-dcab-navy">{EUR(estimate.cost_per_sqm)}</p>
        </div>
      </div>

      {/* Horizontal bar chart */}
      <div className="p-4 space-y-3">
        {estimate.cost_groups.map((cg, i) => {
          const pct = (cg.subtotal / maxSubtotal) * 100;
          return (
            <div key={cg.kg_number}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-dcab-navy font-medium">
                  KG {cg.kg_number} – {cg.name}
                </span>
                <span className="text-dcab-gray font-mono">{EUR(cg.subtotal)}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-4">
                <div
                  className={`h-4 rounded-full ${BAR_COLORS[i % BAR_COLORS.length]} transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
