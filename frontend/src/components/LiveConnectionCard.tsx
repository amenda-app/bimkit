"use client";

import { useState, useRef, useCallback } from "react";
import { Wifi, WifiOff, Plus, Upload, Loader2, CheckCircle2, XCircle } from "lucide-react";
import type { Project, HealthResponse } from "@/lib/types";
import { uploadIFC } from "@/lib/api";

interface LiveConnectionCardProps {
  health: HealthResponse | null;
  projects: Project[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onProjectAdded: (project: Project) => void;
}

const SOURCE_BADGES: Record<string, { label: string; className: string }> = {
  ifc: { label: "IFC", className: "bg-blue-100 text-blue-700" },
  archicad: { label: "AC", className: "bg-green-100 text-green-700" },
};

export function LiveConnectionCard({
  health,
  projects,
  selectedId,
  onSelect,
  onProjectAdded,
}: LiveConnectionCardProps) {
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isLive = health?.mode === "live";
  const selectedProject = projects.find((p) => p.id === selectedId);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".ifc")) {
      setUploadResult({ success: false, message: "Nur .ifc Dateien werden akzeptiert" });
      return;
    }
    setUploading(true);
    setUploadResult(null);
    try {
      const data = await uploadIFC(file);
      setUploadResult({ success: true, message: data.message });
      onProjectAdded(data.project);
      setTimeout(() => {
        setShowUpload(false);
        setUploadResult(null);
      }, 2000);
    } catch (e) {
      setUploadResult({
        success: false,
        message: e instanceof Error ? e.message : "Upload fehlgeschlagen",
      });
    } finally {
      setUploading(false);
    }
  }, [onProjectAdded]);

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      e.target.value = "";
    },
    [handleFile],
  );

  return (
    <div className={`bg-white rounded-lg shadow p-5 border-l-4 ${isLive ? "border-l-emerald-500" : "border-l-dcab-accent"}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Status */}
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-2 h-2 rounded-full ${isLive ? "bg-emerald-500 animate-pulse" : "bg-gray-400"}`} />
            <span className="text-xs font-semibold text-dcab-gray uppercase tracking-wide">
              {isLive ? "Live" : "Offline"}
            </span>
          </div>

          {/* Project dropdown */}
          <div className="flex items-center gap-2">
            <select
              value={selectedId || ""}
              onChange={(e) => onSelect(e.target.value)}
              className="text-sm font-bold text-dcab-navy bg-transparent border border-gray-200 rounded px-2 py-1 pr-6 max-w-[200px] truncate focus:outline-none focus:border-dcab-blue"
            >
              {projects.length === 0 && (
                <option value="">Kein Projekt</option>
              )}
              {projects.map((p) => {
                const badge = SOURCE_BADGES[p.source];
                return (
                  <option key={p.id} value={p.id}>
                    {badge ? `[${badge.label}] ` : ""}{p.name}
                  </option>
                );
              })}
            </select>
            <button
              onClick={() => setShowUpload(!showUpload)}
              className="p-1 rounded hover:bg-gray-100 transition-colors"
              title="IFC-Datei importieren"
            >
              <Plus className="w-4 h-4 text-dcab-gray" />
            </button>
          </div>

          {/* Subtitle */}
          <p className="text-xs text-dcab-gray mt-1">
            {selectedProject
              ? `${selectedProject.total_area.toLocaleString("de-DE", { maximumFractionDigits: 0 })} m² · ${selectedProject.floors} Geschosse`
              : `${projects.length} Projekt${projects.length !== 1 ? "e" : ""}`}
          </p>
        </div>

        {isLive ? (
          <Wifi className="w-5 h-5 mt-0.5 text-emerald-500" />
        ) : (
          <WifiOff className="w-5 h-5 mt-0.5 text-dcab-accent" />
        )}
      </div>

      {/* IFC Upload popover */}
      {showUpload && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <input
            ref={inputRef}
            type="file"
            accept=".ifc"
            onChange={onFileChange}
            className="hidden"
          />
          {uploading ? (
            <div className="flex items-center gap-2 text-sm text-dcab-gray">
              <Loader2 className="w-4 h-4 animate-spin" />
              Wird verarbeitet...
            </div>
          ) : (
            <button
              onClick={() => inputRef.current?.click()}
              className="flex items-center gap-2 text-sm text-dcab-blue hover:text-dcab-navy transition-colors"
            >
              <Upload className="w-4 h-4" />
              IFC-Datei importieren
            </button>
          )}
          {uploadResult && (
            <div className={`mt-2 flex items-center gap-1.5 text-xs ${uploadResult.success ? "text-green-600" : "text-red-500"}`}>
              {uploadResult.success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              {uploadResult.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
