"use client";

import { useState } from "react";
import { Plus, GitCompare, Loader2 } from "lucide-react";
import type { Snapshot, ChangeEntry } from "@/lib/types";
import { createSnapshot, compareSnapshots } from "@/lib/api";

interface ChangeLogProps {
  projectId: string;
  snapshots: Snapshot[];
  onSnapshotsChange: (snapshots: Snapshot[]) => void;
}

const TYPE_COLORS = {
  added: "bg-green-100 text-green-800",
  removed: "bg-red-100 text-red-800",
  changed: "bg-yellow-100 text-yellow-800",
};

const TYPE_LABELS = {
  added: "Hinzugefügt",
  removed: "Entfernt",
  changed: "Geändert",
};

export function ChangeLog({ projectId, snapshots, onSnapshotsChange }: ChangeLogProps) {
  const [snapA, setSnapA] = useState<string>("");
  const [snapB, setSnapB] = useState<string>("");
  const [changes, setChanges] = useState<ChangeEntry[] | null>(null);
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [label, setLabel] = useState("");

  const handleCreate = async () => {
    if (!label.trim()) return;
    setLoading(true);
    try {
      const snap = await createSnapshot(projectId, label.trim());
      onSnapshotsChange([...snapshots, snap]);
      setLabel("");
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!snapA || !snapB || snapA === snapB) return;
    setLoading(true);
    try {
      const result = await compareSnapshots(projectId, snapA, snapB);
      setChanges(result.changes);
      setSummary(result.summary);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-dcab-navy">Änderungsverfolgung</h3>
      </div>

      {/* Create snapshot */}
      <div className="p-4 border-b border-gray-100 flex gap-2">
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Snapshot-Bezeichnung..."
          className="flex-1 text-sm border border-gray-200 rounded px-3 py-1.5 focus:outline-none focus:border-dcab-blue"
        />
        <button
          onClick={handleCreate}
          disabled={loading || !label.trim()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-dcab-blue text-white text-sm rounded hover:bg-dcab-navy transition-colors disabled:opacity-50"
        >
          <Plus className="w-3.5 h-3.5" />
          Snapshot
        </button>
      </div>

      {/* Compare selectors */}
      {snapshots.length >= 2 && (
        <div className="p-4 border-b border-gray-100 flex gap-2 items-end flex-wrap">
          <div className="flex-1 min-w-[140px]">
            <label className="text-xs text-dcab-gray block mb-1">Snapshot A (alt)</label>
            <select
              value={snapA}
              onChange={(e) => setSnapA(e.target.value)}
              className="w-full text-sm border border-gray-200 rounded px-2 py-1.5"
            >
              <option value="">Auswählen...</option>
              {snapshots.map((s) => (
                <option key={s.id} value={s.id}>{s.label} ({formatDate(s.timestamp)})</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[140px]">
            <label className="text-xs text-dcab-gray block mb-1">Snapshot B (neu)</label>
            <select
              value={snapB}
              onChange={(e) => setSnapB(e.target.value)}
              className="w-full text-sm border border-gray-200 rounded px-2 py-1.5"
            >
              <option value="">Auswählen...</option>
              {snapshots.map((s) => (
                <option key={s.id} value={s.id}>{s.label} ({formatDate(s.timestamp)})</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleCompare}
            disabled={loading || !snapA || !snapB || snapA === snapB}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-dcab-navy text-white text-sm rounded hover:bg-dcab-dark transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
            Vergleichen
          </button>
        </div>
      )}

      {/* Snapshot list */}
      {snapshots.length > 0 && !changes && (
        <div className="p-4">
          <p className="text-xs text-dcab-gray mb-2">{snapshots.length} Snapshot(s)</p>
          <div className="space-y-1.5">
            {snapshots.map((s) => (
              <div key={s.id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs">
                <span className="font-medium text-dcab-navy">{s.label}</span>
                <span className="text-dcab-gray">{formatDate(s.timestamp)} – {s.room_count} Räume, {s.total_area.toFixed(0)} m²</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Diff results */}
      {changes && summary && (
        <div className="p-4">
          <div className="flex gap-3 mb-3">
            {(["added", "removed", "changed"] as const).map((t) => (
              <span key={t} className={`text-xs px-2 py-1 rounded-full font-medium ${TYPE_COLORS[t]}`}>
                {summary[t] || 0} {TYPE_LABELS[t]}
              </span>
            ))}
          </div>
          {changes.length === 0 ? (
            <p className="text-sm text-dcab-gray text-center py-4">Keine Änderungen gefunden.</p>
          ) : (
            <div className="max-h-[300px] overflow-y-auto space-y-1">
              {changes.map((c, i) => (
                <div key={i} className={`flex items-start gap-2 p-2 rounded text-xs ${TYPE_COLORS[c.type]}`}>
                  <span className="font-medium shrink-0">{c.entity_type === "room" ? "Raum" : "Material"}</span>
                  <span className="flex-1">
                    {c.type === "added" && `${c.new_value} hinzugefügt`}
                    {c.type === "removed" && `${c.old_value} entfernt`}
                    {c.type === "changed" && (
                      <>{c.entity_id}: <span className="font-medium">{c.field}</span> {c.old_value} → {c.new_value}</>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {snapshots.length < 2 && !changes && (
        <div className="p-4 text-center text-xs text-dcab-gray">
          Erstellen Sie mindestens 2 Snapshots, um Änderungen zu vergleichen.
        </div>
      )}
    </div>
  );
}
