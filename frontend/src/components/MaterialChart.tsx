"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import type { Material } from "@/lib/types";

interface MaterialChartProps {
  materials: Material[];
}

const COLORS = ["#1B3A5C", "#2E6DA4", "#D4A843", "#6B7B8D", "#0F2235", "#4A90C4", "#E8B960"];

export function MaterialDistributionChart({ materials }: MaterialChartProps) {
  // Group by category, sum quantities (only m² for comparability)
  const catMap = new Map<string, number>();
  for (const m of materials) {
    if (m.unit !== "m²") continue;
    catMap.set(m.category, (catMap.get(m.category) || 0) + m.quantity);
  }

  const data = Array.from(catMap.entries())
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="bg-white rounded-lg shadow p-5">
      <h3 className="text-sm font-semibold text-dcab-navy mb-4">Materialverteilung (m²)</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={95}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `${Number(value).toLocaleString("de-DE")} m²`} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
