"use client";

import type { Project } from "@/lib/types";
import { Building2 } from "lucide-react";

interface ProjectSelectorProps {
  projects: Project[];
  selected: string | null;
  onSelect: (id: string) => void;
}

const SOURCE_BADGES: Record<string, { label: string; className: string }> = {
  mock: { label: "Demo", className: "bg-gray-100 text-gray-600" },
  ifc: { label: "IFC", className: "bg-blue-100 text-blue-700" },
  archicad: { label: "ArchiCAD", className: "bg-green-100 text-green-700" },
};

export function ProjectSelector({ projects, selected, onSelect }: ProjectSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {projects.map((p) => {
        const badge = SOURCE_BADGES[p.source] ?? SOURCE_BADGES.mock;
        return (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className={`text-left rounded-lg border-2 p-4 transition-all ${
              selected === p.id
                ? "border-dcab-blue bg-dcab-light shadow-md"
                : "border-gray-200 bg-white hover:border-dcab-blue/40 hover:shadow"
            }`}
          >
            <div className="flex items-center gap-3">
              <Building2 className={`w-5 h-5 ${selected === p.id ? "text-dcab-blue" : "text-dcab-gray"}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-dcab-navy truncate">{p.name}</p>
                  <span className={`inline-block text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${badge.className}`}>
                    {badge.label}
                  </span>
                </div>
                <p className="text-xs text-dcab-gray">{p.building_type}</p>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-4 text-xs text-dcab-gray">
              <span>{p.total_area.toLocaleString("de-DE")} m² BGF</span>
              <span>{p.floors} Geschosse</span>
            </div>
            <div className="mt-1">
              <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-dcab-light text-dcab-navy font-medium">
                {p.status}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
