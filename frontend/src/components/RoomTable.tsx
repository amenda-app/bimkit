"use client";

import { useState, useMemo } from "react";
import type { Room } from "@/lib/types";
import { ChevronDown, ChevronUp, Search } from "lucide-react";

interface RoomTableProps {
  rooms: Room[];
}

type SortKey = "number" | "name" | "floor" | "area" | "usage_type";

export function RoomTable({ rooms }: RoomTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("number");
  const [sortAsc, setSortAsc] = useState(true);
  const [floorFilter, setFloorFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const floors = ["all", ...Array.from(new Set(rooms.map((r) => r.floor))).sort()];

  const filtered = useMemo(() => {
    let result = floorFilter === "all" ? rooms : rooms.filter((r) => r.floor === floorFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.number.toLowerCase().includes(q) ||
          r.usage_type.toLowerCase().includes(q)
      );
    }
    return result;
  }, [rooms, floorFilter, search]);

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    const cmp = typeof av === "number" ? av - (bv as number) : String(av).localeCompare(String(bv));
    return sortAsc ? cmp : -cmp;
  });

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  };

  const SortIcon = sortAsc ? ChevronUp : ChevronDown;

  const totalArea = filtered.reduce((sum, r) => sum + r.area, 0);

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between gap-3 flex-wrap">
        <h3 className="text-sm font-semibold text-dcab-navy">
          Raumliste ({filtered.length} Räume, {totalArea.toLocaleString("de-DE", { maximumFractionDigits: 1 })} m²)
        </h3>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-dcab-gray" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Suchen..."
              className="text-sm border border-gray-200 rounded pl-7 pr-2 py-1 w-40 focus:outline-none focus:border-dcab-blue"
            />
          </div>
          <select
            value={floorFilter}
            onChange={(e) => setFloorFilter(e.target.value)}
            className="text-sm border border-gray-200 rounded px-2 py-1 text-dcab-navy"
          >
            {floors.map((f) => (
              <option key={f} value={f}>{f === "all" ? "Alle Geschosse" : f}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-dcab-navy text-white sticky top-0">
            <tr>
              {([
                ["number", "Nr."],
                ["name", "Raumname"],
                ["floor", "Geschoss"],
                ["area", "Fläche (m²)"],
                ["usage_type", "Nutzungsart"],
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
              <th className="px-3 py-2.5 text-left">Boden</th>
              <th className="px-3 py-2.5 text-left">Wand</th>
              <th className="px-3 py-2.5 text-left">Decke</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((room, i) => (
              <tr key={room.id} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-mono text-xs">{room.number}</td>
                <td className="px-3 py-2">{room.name}</td>
                <td className="px-3 py-2">{room.floor}</td>
                <td className="px-3 py-2 text-right font-mono">{room.area.toFixed(1)}</td>
                <td className="px-3 py-2">
                  <span className="inline-block text-xs px-1.5 py-0.5 rounded bg-dcab-light text-dcab-navy">
                    {room.usage_type}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs text-dcab-gray">{room.finish_floor}</td>
                <td className="px-3 py-2 text-xs text-dcab-gray">{room.finish_wall}</td>
                <td className="px-3 py-2 text-xs text-dcab-gray">{room.finish_ceiling}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
