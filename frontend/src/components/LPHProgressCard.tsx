"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, ChevronDown, ChevronUp, ListChecks, AlertTriangle } from "lucide-react";

interface LPHPhase {
  lph: number;
  label: string;
  overall_progress: number;
  room_properties_progress: number;
  element_types_progress: number;
  element_properties_progress: number;
  room_properties_detail: Record<string, number>;
  element_types_detail: Record<string, boolean>;
  missing_room_properties: string[];
  missing_element_types: string[];
  missing_element_properties: string[];
}

export interface LPHProgressData {
  current_phase: string;
  phases: LPHPhase[];
  next_steps: string[];
}

interface LPHProgressCardProps {
  data: LPHProgressData;
}

function progressColor(pct: number): string {
  if (pct >= 90) return "bg-emerald-500";
  if (pct >= 60) return "bg-amber-400";
  return "bg-red-500";
}

function progressTextColor(pct: number): string {
  if (pct >= 90) return "text-emerald-600";
  if (pct >= 60) return "text-amber-600";
  return "text-red-600";
}

function SubProgressBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-dcab-gray w-40 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${progressColor(value)} transition-all`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`text-xs font-mono w-10 text-right ${progressTextColor(value)}`}>
        {value.toFixed(0)}%
      </span>
    </div>
  );
}

function PhaseDetail({ phase }: { phase: LPHPhase }) {
  const roomPropEntries = Object.entries(phase.room_properties_detail);
  const elementTypeEntries = Object.entries(phase.element_types_detail);

  return (
    <div className="mt-3 space-y-4 pl-2 border-l-2 border-gray-200 ml-2">
      {/* Sub-progress bars */}
      <div className="space-y-2">
        <SubProgressBar label="Raumeigenschaften" value={phase.room_properties_progress} />
        <SubProgressBar label="Elementtypen" value={phase.element_types_progress} />
        <SubProgressBar label="Elementeigenschaften" value={phase.element_properties_progress} />
      </div>

      {/* Room properties detail */}
      {roomPropEntries.length > 0 && (
        <div>
          <p className="text-xs font-medium text-dcab-navy mb-1.5">Raumeigenschaften (Befüllungsgrad)</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {roomPropEntries.map(([field, pct]) => (
              <div key={field} className="flex items-center gap-1.5 text-xs">
                <div className={`w-2 h-2 rounded-full ${progressColor(pct)}`} />
                <span className="text-dcab-gray truncate">{field}</span>
                <span className={`font-mono ml-auto ${progressTextColor(pct)}`}>{pct.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Element types detail */}
      {elementTypeEntries.length > 0 && (
        <div>
          <p className="text-xs font-medium text-dcab-navy mb-1.5">Elementtypen</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {elementTypeEntries.map(([name, present]) => (
              <div key={name} className="flex items-center gap-1.5 text-xs">
                {present ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
                )}
                <span className="text-dcab-gray truncate">{name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing items */}
      {(phase.missing_room_properties.length > 0 ||
        phase.missing_element_types.length > 0 ||
        phase.missing_element_properties.length > 0) && (
        <div className="bg-red-50 rounded p-2.5">
          <p className="text-xs font-medium text-red-700 mb-1.5 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            Fehlende Elemente
          </p>
          {phase.missing_room_properties.length > 0 && (
            <div className="mb-1">
              <span className="text-xs text-red-600 font-medium">Raumeigenschaften: </span>
              <span className="text-xs text-red-600">{phase.missing_room_properties.join(", ")}</span>
            </div>
          )}
          {phase.missing_element_types.length > 0 && (
            <div className="mb-1">
              <span className="text-xs text-red-600 font-medium">Elementtypen: </span>
              <span className="text-xs text-red-600">{phase.missing_element_types.join(", ")}</span>
            </div>
          )}
          {phase.missing_element_properties.length > 0 && (
            <div>
              <span className="text-xs text-red-600 font-medium">Elementeigenschaften: </span>
              <span className="text-xs text-red-600">{phase.missing_element_properties.join(", ")}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function LPHProgressCard({ data }: LPHProgressCardProps) {
  const [expandedLPH, setExpandedLPH] = useState<number | null>(null);

  const toggleExpand = (lph: number) => {
    setExpandedLPH(expandedLPH === lph ? null : lph);
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-dcab-navy">LPH-Fortschritt</h3>
        <span className="text-xs text-dcab-gray px-2 py-0.5 rounded-full bg-dcab-light">
          Aktuelle Phase: {data.current_phase}
        </span>
      </div>

      <div className="p-4 space-y-3">
        {data.phases.map((phase) => {
          const isExpanded = expandedLPH === phase.lph;
          const pct = phase.overall_progress;

          return (
            <div key={phase.lph} className="border border-gray-100 rounded-lg p-3">
              {/* Phase header with progress bar */}
              <button
                onClick={() => toggleExpand(phase.lph)}
                className="w-full flex items-center gap-3 text-left"
              >
                <div className="shrink-0">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${progressColor(pct)}`}
                  >
                    {phase.lph}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-dcab-navy truncate">
                      LPH {phase.lph} – {phase.label}
                    </span>
                    <span className={`text-sm font-bold ml-2 ${progressTextColor(pct)}`}>
                      {pct.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full ${progressColor(pct)} transition-all`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                </div>
                <div className="shrink-0 ml-1">
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-dcab-gray" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-dcab-gray" />
                  )}
                </div>
              </button>

              {/* Expanded detail */}
              {isExpanded && <PhaseDetail phase={phase} />}
            </div>
          );
        })}
      </div>

      {/* Next steps */}
      {data.next_steps.length > 0 && (
        <div className="p-4 border-t border-gray-100 bg-dcab-light/30">
          <div className="flex items-center gap-1.5 mb-2">
            <ListChecks className="w-4 h-4 text-dcab-navy" />
            <h4 className="text-xs font-semibold text-dcab-navy">Nächste Schritte</h4>
          </div>
          <ul className="space-y-1">
            {data.next_steps.map((step, i) => (
              <li key={i} className="text-xs text-dcab-gray flex items-start gap-1.5">
                <span className="text-dcab-blue mt-0.5 shrink-0">•</span>
                {step}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
