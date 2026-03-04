"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus, GitCompare, Loader2, Trash2, Play, Pause, Clock,
  AlertTriangle, AlertCircle, Info, TrendingUp,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { Snapshot, ChangeEntry, SnapshotTrendPoint, MonitoringAlert, SchedulerStatus } from "@/lib/types";
import {
  createSnapshot, compareSnapshots, deleteSnapshot,
  getMonitoringStatus, configureMonitoring, getTrends, getAlerts,
} from "@/lib/api";

interface MonitoringDashboardProps {
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

const SEVERITY_ICONS = {
  info: Info,
  warning: AlertTriangle,
  critical: AlertCircle,
};

const SEVERITY_COLORS = {
  info: "bg-blue-50 border-blue-200 text-blue-800",
  warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
  critical: "bg-red-50 border-red-200 text-red-800",
};

function formatDate(ts: string) {
  const d = new Date(ts);
  return d.toLocaleDateString("de-DE", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function formatShortDate(ts: string) {
  const d = new Date(ts);
  return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
}

export function MonitoringDashboard({ projectId, snapshots, onSnapshotsChange }: MonitoringDashboardProps) {
  const [label, setLabel] = useState("");
  const [loading, setLoading] = useState(false);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [trends, setTrends] = useState<SnapshotTrendPoint[]>([]);
  const [alertList, setAlertList] = useState<MonitoringAlert[]>([]);
  const [interval, setInterval] = useState(60);

  // Comparison state
  const [snapA, setSnapA] = useState("");
  const [snapB, setSnapB] = useState("");
  const [changes, setChanges] = useState<ChangeEntry[] | null>(null);
  const [summary, setSummary] = useState<Record<string, number> | null>(null);

  const loadMonitoringData = useCallback(async () => {
    try {
      const [status, trendData, alertData] = await Promise.all([
        getMonitoringStatus(),
        getTrends(projectId),
        getAlerts(projectId),
      ]);
      setSchedulerStatus(status);
      setTrends(trendData);
      setAlertList(alertData);
      setInterval(status.interval_minutes);
    } catch {
      // Monitoring endpoints may not be available yet
    }
  }, [projectId]);

  useEffect(() => {
    loadMonitoringData();
  }, [loadMonitoringData]);

  const handleCreate = async () => {
    if (!label.trim()) return;
    setLoading(true);
    try {
      const snap = await createSnapshot(projectId, label.trim());
      onSnapshotsChange([...snapshots, snap]);
      setLabel("");
      await loadMonitoringData();
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (snapshotId: string) => {
    try {
      await deleteSnapshot(projectId, snapshotId);
      onSnapshotsChange(snapshots.filter((s) => s.id !== snapshotId));
      await loadMonitoringData();
    } catch {
      // ignore
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

  const handleToggleScheduler = async () => {
    if (!schedulerStatus) return;
    const newStatus = await configureMonitoring({
      interval_minutes: interval,
      enabled: !schedulerStatus.active,
    });
    setSchedulerStatus(newStatus);
  };

  const handleUpdateInterval = async () => {
    if (!schedulerStatus) return;
    const newStatus = await configureMonitoring({
      interval_minutes: interval,
      enabled: schedulerStatus.active,
    });
    setSchedulerStatus(newStatus);
  };

  return (
    <div className="space-y-6">
      {/* Scheduler Control Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-dcab-navy" />
            <h3 className="text-sm font-semibold text-dcab-navy">Auto-Snapshots</h3>
            {schedulerStatus && (
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                schedulerStatus.active
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-600"
              }`}>
                {schedulerStatus.active ? "Aktiv" : "Inaktiv"}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-dcab-gray">Intervall (Min):</label>
            <input
              type="number"
              min={1}
              max={1440}
              value={interval}
              onChange={(e) => setInterval(Number(e.target.value))}
              className="w-16 text-xs border border-gray-200 rounded px-2 py-1 text-center"
            />
            <button
              onClick={handleUpdateInterval}
              className="text-xs px-2 py-1 border border-gray-200 rounded hover:bg-gray-50"
            >
              Setzen
            </button>
            <button
              onClick={handleToggleScheduler}
              className={`flex items-center gap-1 text-xs px-3 py-1 rounded text-white transition-colors ${
                schedulerStatus?.active
                  ? "bg-red-500 hover:bg-red-600"
                  : "bg-emerald-500 hover:bg-emerald-600"
              }`}
            >
              {schedulerStatus?.active ? (
                <><Pause className="w-3 h-3" /> Stop</>
              ) : (
                <><Play className="w-3 h-3" /> Start</>
              )}
            </button>
          </div>
        </div>
        {schedulerStatus && (schedulerStatus.last_run || schedulerStatus.next_run) && (
          <div className="mt-2 flex gap-4 text-xs text-dcab-gray">
            {schedulerStatus.last_run && (
              <span>Letzter Lauf: {formatDate(schedulerStatus.last_run)}</span>
            )}
            {schedulerStatus.next_run && schedulerStatus.active && (
              <span>Nächster Lauf: {formatDate(schedulerStatus.next_run)}</span>
            )}
            <span>{schedulerStatus.snapshot_count} Snapshots gesamt</span>
          </div>
        )}
      </div>

      {/* Alerts */}
      {alertList.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-dcab-navy flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Änderungshinweise
          </h3>
          {alertList.map((alert, i) => {
            const Icon = SEVERITY_ICONS[alert.severity as keyof typeof SEVERITY_ICONS] || Info;
            const colorClass = SEVERITY_COLORS[alert.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.info;
            return (
              <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${colorClass}`}>
                <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{alert.message}</p>
                  <p className="text-xs opacity-75 mt-0.5">{formatDate(alert.timestamp)}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Trend Charts */}
      {trends.length >= 2 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-dcab-navy mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Entwicklung
          </h3>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends.map((t) => ({
                ...t,
                date: formatShortDate(t.timestamp),
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ fontSize: 12 }}
                  formatter={(value, name) => {
                    const labels: Record<string, string> = {
                      room_count: "Räume",
                      material_count: "Materialien",
                      total_area: "Fläche (m²)",
                    };
                    return [value, labels[String(name)] || String(name)];
                  }}
                />
                <Legend
                  formatter={(value: string) => {
                    const labels: Record<string, string> = {
                      room_count: "Räume",
                      material_count: "Materialien",
                      total_area: "Fläche (m²)",
                    };
                    return labels[value] || value;
                  }}
                />
                <Line yAxisId="left" type="monotone" dataKey="room_count" stroke="#1e3a5f" strokeWidth={2} dot={{ r: 3 }} />
                <Line yAxisId="left" type="monotone" dataKey="material_count" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
                <Line yAxisId="right" type="monotone" dataKey="total_area" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Create Snapshot + Timeline */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-dcab-navy">Snapshot-Verlauf</h3>
        </div>

        {/* Create snapshot */}
        <div className="p-4 border-b border-gray-100 flex gap-2">
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Snapshot-Bezeichnung..."
            className="flex-1 text-sm border border-gray-200 rounded px-3 py-1.5 focus:outline-none focus:border-dcab-blue"
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
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

        {/* Snapshot timeline */}
        {snapshots.length > 0 && (
          <div className="p-4">
            <p className="text-xs text-dcab-gray mb-3">{snapshots.length} Snapshot(s)</p>
            <div className="space-y-1">
              {[...snapshots].reverse().map((s) => (
                <div key={s.id} className="flex items-center justify-between p-2.5 bg-gray-50 rounded group">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-dcab-blue shrink-0" />
                    <div>
                      <span className="text-sm font-medium text-dcab-navy">{s.label}</span>
                      <div className="flex gap-3 text-xs text-dcab-gray mt-0.5">
                        <span>{formatDate(s.timestamp)}</span>
                        <span>{s.room_count} Räume</span>
                        <span>{s.total_area.toFixed(0)} m²</span>
                        <span>{s.material_count} Mat.</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(s.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-red-400 hover:text-red-600 transition-all"
                    title="Snapshot löschen"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {snapshots.length === 0 && (
          <div className="p-4 text-center text-xs text-dcab-gray">
            Noch keine Snapshots vorhanden. Erstellen Sie den ersten Snapshot oben.
          </div>
        )}
      </div>

      {/* Snapshot Comparison */}
      {snapshots.length >= 2 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-dcab-navy">Snapshot-Vergleich</h3>
          </div>

          <div className="p-4 flex gap-2 items-end flex-wrap">
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

          {/* Diff results */}
          {changes && summary && (
            <div className="p-4 border-t border-gray-100">
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
        </div>
      )}
    </div>
  );
}
