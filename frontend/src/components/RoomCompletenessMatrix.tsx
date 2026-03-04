"use client";

import { useMemo, useState } from "react";
import type { Room } from "@/lib/types";
import { ChevronDown, ChevronUp } from "lucide-react";

interface RoomCompletenessMatrixProps {
  rooms: Room[];
}

const PLACEHOLDER_VALUES = new Set(["", "—", "k. A", "k.A.", "-", "n/a", "N/A"]);
const INITIAL_DISPLAY = 50;

interface ColumnDef {
  key: keyof Room;
  label: string;
  type: "text" | "number";
}

const COLUMNS: ColumnDef[] = [
  { key: "number", label: "Nr.", type: "text" },
  { key: "name", label: "Name", type: "text" },
  { key: "floor", label: "Geschoss", type: "text" },
  { key: "area", label: "Fläche", type: "number" },
  { key: "height", label: "Höhe", type: "number" },
  { key: "usage_type", label: "Nutzung", type: "text" },
  { key: "finish_floor", label: "Boden", type: "text" },
  { key: "finish_wall", label: "Wand", type: "text" },
  { key: "finish_ceiling", label: "Decke", type: "text" },
];

// Fields to check for completeness (excluding id)
const CHECKED_FIELDS: ColumnDef[] = COLUMNS;

function isMissing(value: unknown, type: "text" | "number"): boolean {
  if (value === null || value === undefined) return true;
  if (type === "number") return value === 0 || value === "";
  return PLACEHOLDER_VALUES.has(String(value).trim()) || String(value).trim() === "";
}

function cellBg(value: unknown, type: "text" | "number"): string {
  return isMissing(value, type) ? "bg-red-100" : "bg-emerald-50";
}

function formatValue(value: unknown, type: "text" | "number"): string {
  if (isMissing(value, type)) return "—";
  if (type === "number") return Number(value).toLocaleString("de-DE", { maximumFractionDigits: 1 });
  return String(value);
}

export function RoomCompletenessMatrix({ rooms }: RoomCompletenessMatrixProps) {
  const [showAll, setShowAll] = useState(false);

  const displayedRooms = showAll ? rooms : rooms.slice(0, INITIAL_DISPLAY);

  // Calculate per-field completeness
  const fieldCompleteness = useMemo(() => {
    const result: Record<string, number> = {};
    for (const col of CHECKED_FIELDS) {
      const filled = rooms.filter((r) => !isMissing(r[col.key], col.type)).length;
      result[col.key] = rooms.length > 0 ? Math.round((filled / rooms.length) * 100) : 0;
    }
    return result;
  }, [rooms]);

  // Calculate overall completeness
  const overallCompleteness = useMemo(() => {
    const totalCells = rooms.length * CHECKED_FIELDS.length;
    if (totalCells === 0) return 0;
    let filled = 0;
    for (const room of rooms) {
      for (const col of CHECKED_FIELDS) {
        if (!isMissing(room[col.key], col.type)) filled++;
      }
    }
    return Math.round((filled / totalCells) * 100);
  }, [rooms]);

  function completionBadgeColor(pct: number): string {
    if (pct >= 90) return "bg-emerald-100 text-emerald-700";
    if (pct >= 60) return "bg-amber-100 text-amber-700";
    return "bg-red-100 text-red-700";
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-dcab-navy">Raum-Vollständigkeit</h3>
        <div className={`text-xs font-bold px-2.5 py-1 rounded-full ${completionBadgeColor(overallCompleteness)}`}>
          Gesamt: {overallCompleteness}% vollständig
        </div>
      </div>

      {/* Per-field completeness badges */}
      <div className="p-3 border-b border-gray-50 flex flex-wrap gap-1.5">
        {CHECKED_FIELDS.map((col) => {
          const pct = fieldCompleteness[col.key];
          return (
            <span
              key={col.key}
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${completionBadgeColor(pct)}`}
            >
              {col.label}: {pct}%
            </span>
          );
        })}
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-dcab-navy text-white sticky top-0">
            <tr>
              {COLUMNS.map((col) => (
                <th key={col.key} className="px-3 py-2.5 text-left text-xs font-medium">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedRooms.map((room, rowIdx) => (
              <tr key={room.id} className={rowIdx % 2 === 0 ? "" : "bg-gray-50/50"}>
                {COLUMNS.map((col) => {
                  const val = room[col.key];
                  const missing = isMissing(val, col.type);
                  return (
                    <td
                      key={col.key}
                      className={`px-3 py-1.5 text-xs ${cellBg(val, col.type)} border-b border-white/60 ${
                        col.type === "number" ? "text-right font-mono" : ""
                      } ${missing ? "text-red-400" : "text-dcab-navy"}`}
                    >
                      {formatValue(val, col.type)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show more / less */}
      {rooms.length > INITIAL_DISPLAY && (
        <div className="p-3 border-t border-gray-100 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-xs text-dcab-blue hover:text-dcab-navy font-medium inline-flex items-center gap-1 transition-colors"
          >
            {showAll ? (
              <>
                Weniger anzeigen <ChevronUp className="w-3.5 h-3.5" />
              </>
            ) : (
              <>
                Alle {rooms.length} Räume anzeigen <ChevronDown className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
