"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { uploadIFC } from "@/lib/api";
import type { Project } from "@/lib/types";

interface IFCUploadProps {
  onProjectAdded: (project: Project) => void;
}

export function IFCUpload({ onProjectAdded }: IFCUploadProps) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".ifc")) {
      setResult({ success: false, message: "Nur .ifc Dateien werden akzeptiert" });
      return;
    }

    setUploading(true);
    setResult(null);

    try {
      const data = await uploadIFC(file);
      setResult({ success: true, message: data.message });
      onProjectAdded(data.project);
    } catch (e) {
      setResult({
        success: false,
        message: e instanceof Error ? e.message : "Upload fehlgeschlagen",
      });
    } finally {
      setUploading(false);
    }
  }, [onProjectAdded]);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      // Reset input so the same file can be re-uploaded
      e.target.value = "";
    },
    [handleFile],
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`relative rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
        dragging
          ? "border-dcab-blue bg-dcab-light"
          : "border-gray-300 bg-white hover:border-dcab-blue/40"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".ifc"
        onChange={onFileChange}
        className="hidden"
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="w-8 h-8 text-dcab-blue animate-spin" />
          <p className="text-sm text-dcab-gray">IFC-Datei wird verarbeitet...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2">
          <Upload className="w-8 h-8 text-dcab-gray" />
          <p className="text-sm text-dcab-navy font-medium">
            IFC-Datei hierher ziehen
          </p>
          <p className="text-xs text-dcab-gray">oder</p>
          <button
            onClick={() => inputRef.current?.click()}
            className="px-4 py-1.5 bg-dcab-blue text-white text-sm rounded-lg hover:bg-dcab-navy transition-colors"
          >
            Datei auswählen
          </button>
        </div>
      )}

      {result && (
        <div
          className={`mt-3 flex items-center justify-center gap-2 text-sm ${
            result.success ? "text-green-600" : "text-red-500"
          }`}
        >
          {result.success ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <XCircle className="w-4 h-4" />
          )}
          {result.message}
        </div>
      )}
    </div>
  );
}
