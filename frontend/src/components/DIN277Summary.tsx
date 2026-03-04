"use client";

import type { Area, Room } from "@/lib/types";

interface DIN277SummaryProps {
  areas: Area[];
  rooms: Room[];
  totalArea: number; // BGF from project
}

export function DIN277Summary({ areas, rooms, totalArea }: DIN277SummaryProps) {
  const nuf = areas.filter((a) => a.category.startsWith("NUF")).reduce((s, a) => s + a.area, 0);
  const tf = areas.filter((a) => a.category === "TF").reduce((s, a) => s + a.area, 0);
  const vf = areas.filter((a) => a.category === "VF").reduce((s, a) => s + a.area, 0);
  const nrf = nuf + tf + vf;

  const pct = (val: number, ref: number) => ref > 0 ? `${((val / ref) * 100).toFixed(1)}%` : "–";
  const fmt = (v: number) => v.toLocaleString("de-DE", { maximumFractionDigits: 0 });

  const cards = [
    { label: "BGF", sublabel: "Brutto-Grundfläche", value: totalArea, ref: totalArea, color: "border-dcab-navy" },
    { label: "NRF", sublabel: "Netto-Raumfläche", value: nrf, ref: totalArea, color: "border-dcab-blue" },
    { label: "NUF", sublabel: "Nutzungsfläche", value: nuf, ref: nrf, color: "border-emerald-500" },
    { label: "TF", sublabel: "Techn. Funktionsfl.", value: tf, ref: nrf, color: "border-amber-500" },
    { label: "VF", sublabel: "Verkehrsfläche", value: vf, ref: nrf, color: "border-purple-500" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.label} className={`bg-white rounded-lg shadow p-3 border-l-4 ${c.color}`}>
          <p className="text-xs text-dcab-gray">{c.sublabel}</p>
          <p className="text-lg font-bold text-dcab-navy">{fmt(c.value)} m²</p>
          <p className="text-xs text-dcab-gray">{pct(c.value, c.ref)} {c.label === "BGF" ? "" : c.label === "NRF" ? "der BGF" : "der NRF"}</p>
        </div>
      ))}
    </div>
  );
}
