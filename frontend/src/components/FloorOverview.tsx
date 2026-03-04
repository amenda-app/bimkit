"use client";

import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Layers, DoorOpen } from "lucide-react";
import type { Room, Area } from "@/lib/types";

interface FloorOverviewProps {
  rooms: Room[];
  areas: Area[];
}

interface FloorData {
  floor: string;
  roomCount: number;
  totalArea: number;
  usageDistribution: Record<string, number>;
  sortOrder: number;
}

// Assign a sort order to floor names for logical ordering
function floorSortOrder(floor: string): number {
  const normalized = floor.trim().toUpperCase();

  // Underground levels: 2. UG < 1. UG < UG
  if (normalized.includes("UG")) {
    const match = normalized.match(/(\d+)/);
    const level = match ? parseInt(match[1]) : 1;
    return -level;
  }

  // Ground floor
  if (normalized === "EG" || normalized.includes("ERDGESCHOSS")) return 0;

  // Upper floors
  if (normalized.includes("OG")) {
    const match = normalized.match(/(\d+)/);
    const level = match ? parseInt(match[1]) : 1;
    return level;
  }

  // Dachgeschoss
  if (normalized === "DG" || normalized.includes("DACH")) return 100;

  // Staffelgeschoss
  if (normalized === "SG" || normalized.includes("STAFFEL")) return 101;

  // Fallback: try to extract a number
  const numMatch = normalized.match(/(\d+)/);
  if (numMatch) return parseInt(numMatch[1]);

  return 50; // Unknown floors in the middle
}

const USAGE_COLORS = [
  "bg-dcab-navy", "bg-dcab-blue", "bg-dcab-accent", "bg-emerald-500",
  "bg-purple-500", "bg-rose-500", "bg-teal-500", "bg-orange-500",
  "bg-indigo-500", "bg-cyan-500",
];

export function FloorOverview({ rooms, areas }: FloorOverviewProps) {
  const floorData = useMemo(() => {
    const floorMap = new Map<string, FloorData>();

    for (const room of rooms) {
      const floorKey = room.floor || "Unbekannt";
      if (!floorMap.has(floorKey)) {
        floorMap.set(floorKey, {
          floor: floorKey,
          roomCount: 0,
          totalArea: 0,
          usageDistribution: {},
          sortOrder: floorSortOrder(floorKey),
        });
      }
      const entry = floorMap.get(floorKey)!;
      entry.roomCount++;
      entry.totalArea += room.area || 0;

      const usage = room.usage_type || "Sonstige";
      entry.usageDistribution[usage] = (entry.usageDistribution[usage] || 0) + 1;
    }

    // Also include area data from the areas prop
    for (const area of areas) {
      const floorKey = area.floor || "Unbekannt";
      if (!floorMap.has(floorKey)) {
        floorMap.set(floorKey, {
          floor: floorKey,
          roomCount: 0,
          totalArea: 0,
          usageDistribution: {},
          sortOrder: floorSortOrder(floorKey),
        });
      }
    }

    return Array.from(floorMap.values()).sort((a, b) => a.sortOrder - b.sortOrder);
  }, [rooms, areas]);

  // Chart data
  const chartData = floorData.map((fd) => ({
    floor: fd.floor,
    Fläche: Math.round(fd.totalArea),
  }));

  // Collect all unique usage types for consistent color assignment
  const allUsageTypes = useMemo(() => {
    const types = new Set<string>();
    for (const fd of floorData) {
      for (const usage of Object.keys(fd.usageDistribution)) {
        types.add(usage);
      }
    }
    return Array.from(types).sort();
  }, [floorData]);

  const usageColorMap = useMemo(() => {
    const map = new Map<string, string>();
    allUsageTypes.forEach((type, i) => {
      map.set(type, USAGE_COLORS[i % USAGE_COLORS.length]);
    });
    return map;
  }, [allUsageTypes]);

  const totalRooms = rooms.length;
  const totalArea = floorData.reduce((s, fd) => s + fd.totalArea, 0);
  const fmt = (v: number) => v.toLocaleString("de-DE", { maximumFractionDigits: 1 });

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-dcab-navy flex items-center gap-1.5">
          <Layers className="w-4 h-4" />
          Geschossübersicht
        </h3>
        <span className="text-xs text-dcab-gray">
          {floorData.length} Geschosse · {totalRooms} Räume · {fmt(totalArea)} m²
        </span>
      </div>

      <div className="p-4">
        {/* Bar chart comparing floors */}
        <div className="mb-5">
          <p className="text-xs text-dcab-gray mb-2">Fläche je Geschoss (m²)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8EDF2" />
              <XAxis dataKey="floor" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value) => `${Number(value).toLocaleString("de-DE")} m²`}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="Fläche" name="Fläche (m²)" fill="#1B3A5C" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Floor cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {floorData.map((fd) => {
            const usageEntries = Object.entries(fd.usageDistribution).sort((a, b) => b[1] - a[1]);

            return (
              <div
                key={fd.floor}
                className="border border-gray-100 rounded-lg p-3 hover:border-dcab-blue/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-dcab-navy">{fd.floor}</h4>
                  <span className="text-xs text-dcab-gray font-mono">{fmt(fd.totalArea)} m²</span>
                </div>

                <div className="flex items-center gap-3 mb-2.5 text-xs text-dcab-gray">
                  <span className="flex items-center gap-1">
                    <DoorOpen className="w-3.5 h-3.5" />
                    {fd.roomCount} Räume
                  </span>
                </div>

                {/* Usage type badges */}
                {usageEntries.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {usageEntries.map(([usage, count]) => (
                      <span
                        key={usage}
                        className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-dcab-light text-dcab-navy"
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${usageColorMap.get(usage) || "bg-gray-400"}`} />
                        {usage}: {count}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
