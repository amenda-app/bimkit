"use client";

import { useState } from "react";
import { FileSpreadsheet, FileText, Download, Loader2 } from "lucide-react";
import { downloadExcel, downloadPdf } from "@/lib/api";

interface ReportDownloadProps {
  projectId: string;
  projectName: string;
}

const REPORT_TYPES = [
  { id: "raumbuch", label: "Raumbuch", description: "Detaillierte Raumliste mit Ausstattung" },
  { id: "flaechen", label: "Flächenübersicht", description: "DIN 277 Flächenberechnung" },
  { id: "materialien", label: "Materialliste", description: "Alle Materialien mit Mengen" },
  { id: "mengen", label: "Mengenermittlung", description: "Mengen und Kosten nach Gewerk" },
];

export function ReportDownload({ projectId, projectName }: ReportDownloadProps) {
  const [loading, setLoading] = useState<string | null>(null);

  const handleDownload = async (reportType: string, format: "excel" | "pdf") => {
    const key = `${format}-${reportType}`;
    setLoading(key);
    try {
      if (format === "excel") {
        await downloadExcel(projectId, reportType);
      } else {
        await downloadPdf(projectId, reportType);
      }
    } catch {
      alert("Download fehlgeschlagen");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-5">
      <h3 className="text-sm font-semibold text-dcab-navy mb-4">Reports herunterladen</h3>
      <p className="text-xs text-dcab-gray mb-3">Projekt: {projectName}</p>
      <div className="space-y-2">
        {REPORT_TYPES.map((rt) => (
          <div
            key={rt.id}
            className="flex items-center gap-3 p-3 rounded-lg border border-gray-200"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-dcab-navy">{rt.label}</p>
              <p className="text-xs text-dcab-gray">{rt.description}</p>
            </div>
            <button
              onClick={() => handleDownload(rt.id, "excel")}
              disabled={loading !== null}
              className="flex items-center gap-1 px-2 py-1 text-xs rounded border border-gray-200 hover:border-emerald-400 hover:bg-emerald-50 transition-all disabled:opacity-50"
              title="Excel herunterladen"
            >
              {loading === `excel-${rt.id}` ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
              )}
              <span>.xlsx</span>
            </button>
            <button
              onClick={() => handleDownload(rt.id, "pdf")}
              disabled={loading !== null}
              className="flex items-center gap-1 px-2 py-1 text-xs rounded border border-gray-200 hover:border-red-400 hover:bg-red-50 transition-all disabled:opacity-50"
              title="PDF herunterladen"
            >
              {loading === `pdf-${rt.id}` ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <FileText className="w-3.5 h-3.5 text-red-500" />
              )}
              <span>.pdf</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
