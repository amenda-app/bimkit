"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { Area } from "@/lib/types";

interface AreaChartProps {
  areas: Area[];
}

export function AreaByFloorChart({ areas }: AreaChartProps) {
  // Group by floor, split by category
  const floorMap = new Map<string, { floor: string; NUF: number; TF: number; VF: number }>();

  for (const a of areas) {
    const cat = a.category as "NUF" | "TF" | "VF";
    if (!floorMap.has(a.floor)) {
      floorMap.set(a.floor, { floor: a.floor, NUF: 0, TF: 0, VF: 0 });
    }
    const entry = floorMap.get(a.floor)!;
    if (cat in entry) entry[cat] += a.area;
  }

  const data = Array.from(floorMap.values()).sort((a, b) => {
    const order = ["UG", "EG", "OG1", "OG2", "OG3", "OG4", "DG"];
    return order.indexOf(a.floor) - order.indexOf(b.floor);
  });

  return (
    <div className="bg-white rounded-lg shadow p-5">
      <h3 className="text-sm font-semibold text-dcab-navy mb-4">Flächen nach Geschoss (m²)</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF2" />
          <XAxis dataKey="floor" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value) => `${Number(value).toFixed(1)} m²`}
            contentStyle={{ fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="NUF" name="Nutzfläche" fill="#1B3A5C" radius={[2, 2, 0, 0]} />
          <Bar dataKey="TF" name="Technikfläche" fill="#2E6DA4" radius={[2, 2, 0, 0]} />
          <Bar dataKey="VF" name="Verkehrsfläche" fill="#D4A843" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
