"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { QuantityItem } from "@/lib/types";

interface QuantityTableProps {
  quantities: QuantityItem[];
  totalCost: number;
}

type SortKey = "trade" | "category" | "element_type" | "quantity" | "total_price";

const EUR = (v: number) => v.toLocaleString("de-DE", { style: "currency", currency: "EUR" });

export function QuantityTable({ quantities, totalCost }: QuantityTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("trade");
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  };

  const sorted = [...quantities].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    const cmp = typeof av === "number" ? av - (bv as number) : String(av).localeCompare(String(bv));
    return sortAsc ? cmp : -cmp;
  });

  // Group by trade for subtotals
  const trades = Array.from(new Set(quantities.map((q) => q.trade))).sort();
  const tradeSubtotals = Object.fromEntries(
    trades.map((t) => [t, quantities.filter((q) => q.trade === t).reduce((s, q) => s + q.total_price, 0)])
  );

  const SortIcon = sortAsc ? ChevronUp : ChevronDown;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-dcab-navy">
          Mengenermittlung ({quantities.length} Positionen)
        </h3>
        <span className="text-sm font-semibold text-dcab-navy">{EUR(totalCost)}</span>
      </div>

      {/* Trade subtotals */}
      <div className="px-4 py-2 bg-dcab-light/50 flex flex-wrap gap-3">
        {trades.map((t) => (
          <span key={t} className="text-xs text-dcab-navy">
            <span className="font-medium">{t}:</span> {EUR(tradeSubtotals[t])}
          </span>
        ))}
      </div>

      <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-dcab-navy text-white sticky top-0">
            <tr>
              {([
                ["trade", "Gewerk"],
                ["category", "Kategorie"],
                ["element_type", "Beschreibung"],
                ["quantity", "Menge"],
                ["total_price", "GP (EUR)"],
              ] as [SortKey, string][]).map(([key, label]) => (
                <th
                  key={key}
                  onClick={() => handleSort(key)}
                  className="px-3 py-2.5 text-left cursor-pointer hover:bg-dcab-dark transition-colors select-none"
                >
                  <div className="flex items-center gap-1">
                    {label}
                    {sortKey === key && <SortIcon className="w-3 h-3" />}
                  </div>
                </th>
              ))}
              <th className="px-3 py-2.5 text-left">Einheit</th>
              <th className="px-3 py-2.5 text-right">EP (EUR)</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((item, i) => (
              <tr key={`${item.trade}-${item.element_type}-${i}`} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2">
                  <span className="inline-block text-xs px-1.5 py-0.5 rounded bg-dcab-light text-dcab-navy">
                    {item.trade}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs">{item.category}</td>
                <td className="px-3 py-2 text-xs">{item.element_type}</td>
                <td className="px-3 py-2 text-right font-mono text-xs">{item.quantity.toFixed(1)}</td>
                <td className="px-3 py-2 text-right font-mono text-xs font-medium">{EUR(item.total_price)}</td>
                <td className="px-3 py-2 text-xs text-dcab-gray">{item.unit}</td>
                <td className="px-3 py-2 text-right font-mono text-xs text-dcab-gray">{EUR(item.unit_price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
