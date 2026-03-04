import type {
  Project, Room, Area, Material, HealthResponse,
  QuantityItem, QualityReportData, CostEstimate, Snapshot, ChangeEntry,
  SnapshotTrendPoint, MonitoringAlert, SchedulerStatus, SchedulerConfig,
} from "./types";

const BIM_URL = process.env.NEXT_PUBLIC_BIM_SERVICE_URL || "http://localhost:8000";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchJSON(`${BIM_URL}/health`);
}

export async function getProjects(): Promise<Project[]> {
  const data = await fetchJSON<{ projects: Project[] }>(`${BIM_URL}/bim/projects`);
  return data.projects;
}

export async function getRooms(projectId: string): Promise<{ rooms: Room[]; count: number }> {
  return fetchJSON(`${BIM_URL}/bim/extract/rooms`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export async function getAreas(projectId: string): Promise<{ areas: Area[]; count: number }> {
  return fetchJSON(`${BIM_URL}/bim/extract/areas`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export async function getMaterials(projectId: string): Promise<{ materials: Material[]; count: number }> {
  return fetchJSON(`${BIM_URL}/bim/extract/materials`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export function getExcelDownloadUrl(projectId: string, reportType: string): string {
  return `${BIM_URL}/bim/generate/excel`;
}

export async function downloadExcel(projectId: string, reportType: string): Promise<void> {
  const res = await fetch(`${BIM_URL}/bim/generate/excel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, report_type: reportType }),
  });
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${reportType}_${projectId}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
}

// V2 API functions

export async function getQuantities(projectId: string): Promise<{ quantities: QuantityItem[]; total_cost: number }> {
  return fetchJSON(`${BIM_URL}/bim/extract/quantities`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export async function getQualityReport(projectId: string): Promise<QualityReportData> {
  return fetchJSON(`${BIM_URL}/bim/quality/${projectId}`, { method: "POST" });
}

export async function getCostEstimate(projectId: string): Promise<CostEstimate> {
  return fetchJSON(`${BIM_URL}/bim/cost-estimate/${projectId}`, { method: "POST" });
}

export async function createSnapshot(projectId: string, label: string): Promise<Snapshot> {
  return fetchJSON(`${BIM_URL}/bim/snapshots/create`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, label }),
  });
}

export async function getSnapshots(projectId: string): Promise<Snapshot[]> {
  const data = await fetchJSON<{ snapshots: Snapshot[] }>(`${BIM_URL}/bim/snapshots/${projectId}`);
  return data.snapshots;
}

export async function compareSnapshots(
  projectId: string, snapshotA: string, snapshotB: string
): Promise<{ changes: ChangeEntry[]; count: number; summary: Record<string, number> }> {
  return fetchJSON(`${BIM_URL}/bim/compare`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, snapshot_a: snapshotA, snapshot_b: snapshotB }),
  });
}

export async function uploadIFC(file: File): Promise<{ project: Project; rooms_count: number; materials_count: number; message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BIM_URL}/bim/upload/ifc`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload fehlgeschlagen");
  }
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${BIM_URL}/bim/projects/${projectId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Projekt konnte nicht gelöscht werden");
}

export async function deleteSnapshot(projectId: string, snapshotId: string): Promise<void> {
  const res = await fetch(`${BIM_URL}/bim/snapshots/${projectId}/${snapshotId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Snapshot konnte nicht gelöscht werden");
}

export async function getMonitoringStatus(): Promise<SchedulerStatus> {
  return fetchJSON(`${BIM_URL}/bim/monitoring/status`);
}

export async function configureMonitoring(config: SchedulerConfig): Promise<SchedulerStatus> {
  return fetchJSON(`${BIM_URL}/bim/monitoring/configure`, {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function getTrends(projectId: string): Promise<SnapshotTrendPoint[]> {
  const data = await fetchJSON<{ trends: SnapshotTrendPoint[] }>(`${BIM_URL}/bim/trends/${projectId}`);
  return data.trends;
}

export async function getAlerts(projectId: string): Promise<MonitoringAlert[]> {
  const data = await fetchJSON<{ alerts: MonitoringAlert[] }>(`${BIM_URL}/bim/alerts/${projectId}`);
  return data.alerts;
}

export async function downloadPdf(projectId: string, reportType: string): Promise<void> {
  const res = await fetch(`${BIM_URL}/bim/generate/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, report_type: reportType }),
  });
  if (!res.ok) throw new Error("PDF download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${reportType}_${projectId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
