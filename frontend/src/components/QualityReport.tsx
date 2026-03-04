"use client";

import type { QualityReportData } from "@/lib/types";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";

interface QualityReportProps {
  report: QualityReportData;
}

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 80 ? "#22c55e" : score >= 50 ? "#eab308" : "#ef4444";
  const angle = (score / 100) * 180;
  const rad = (angle * Math.PI) / 180;
  const x = 50 + 40 * Math.cos(Math.PI - rad);
  const y = 50 - 40 * Math.sin(Math.PI - rad);
  const largeArc = angle > 180 ? 1 : 0;

  return (
    <svg viewBox="0 0 100 60" className="w-40 mx-auto">
      {/* Background arc */}
      <path
        d="M 10 50 A 40 40 0 0 1 90 50"
        fill="none" stroke="#e5e7eb" strokeWidth="8" strokeLinecap="round"
      />
      {/* Score arc */}
      {score > 0 && (
        <path
          d={`M 10 50 A 40 40 0 ${largeArc} 1 ${x} ${y}`}
          fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
        />
      )}
      <text x="50" y="48" textAnchor="middle" className="text-2xl font-bold" fill={color} fontSize="18">
        {score}
      </text>
      <text x="50" y="58" textAnchor="middle" fill="#6b7280" fontSize="6">
        von 100
      </text>
    </svg>
  );
}

const SEVERITY_CONFIG = {
  error: { icon: AlertCircle, color: "text-red-600", bg: "bg-red-50", label: "Fehler" },
  warning: { icon: AlertTriangle, color: "text-yellow-600", bg: "bg-yellow-50", label: "Warnungen" },
  info: { icon: Info, color: "text-blue-500", bg: "bg-blue-50", label: "Hinweise" },
};

export function QualityReport({ report }: QualityReportProps) {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-dcab-navy">Qualitätsprüfung</h3>
      </div>

      <div className="p-4">
        <ScoreGauge score={report.score} />

        {/* Severity summary */}
        <div className="flex justify-center gap-4 mt-4 mb-4">
          {(["error", "warning", "info"] as const).map((sev) => {
            const cfg = SEVERITY_CONFIG[sev];
            const count = report.issues_by_severity[sev] || 0;
            return (
              <div key={sev} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${cfg.bg}`}>
                <cfg.icon className={`w-3.5 h-3.5 ${cfg.color}`} />
                <span className={`text-xs font-medium ${cfg.color}`}>{count} {cfg.label}</span>
              </div>
            );
          })}
        </div>

        {/* Issues list */}
        {report.issues.length > 0 && (
          <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
            {report.issues.map((issue, i) => {
              const cfg = SEVERITY_CONFIG[issue.severity];
              return (
                <div key={i} className={`flex items-start gap-2 p-2 rounded text-xs ${cfg.bg}`}>
                  <cfg.icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${cfg.color}`} />
                  <div>
                    <span className="font-medium text-dcab-navy">{issue.element_name}</span>
                    <span className="text-dcab-gray ml-1">– {issue.message}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {report.issues.length === 0 && (
          <p className="text-center text-sm text-green-600 mt-4">Keine Probleme gefunden!</p>
        )}
      </div>
    </div>
  );
}
