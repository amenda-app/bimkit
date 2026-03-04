export interface Project {
  id: string;
  name: string;
  address: string;
  building_type: string;
  total_area: number;
  floors: number;
  status: string;
  source: "mock" | "ifc" | "archicad";
}

export interface Room {
  id: string;
  number: string;
  name: string;
  floor: string;
  area: number;
  height: number;
  volume: number;
  usage_type: string;
  finish_floor: string;
  finish_wall: string;
  finish_ceiling: string;
}

export interface Area {
  id: string;
  name: string;
  category: string;
  floor: string;
  area: number;
  rooms: string[];
}

export interface Material {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  manufacturer: string;
  product: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  mode: string;
}

// V2 Types

export interface QuantityItem {
  trade: string;
  category: string;
  element_type: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
}

export interface Snapshot {
  id: string;
  project_id: string;
  timestamp: string;
  label: string;
  room_count: number;
  material_count: number;
  total_area: number;
}

export interface ChangeEntry {
  type: "added" | "removed" | "changed";
  entity_type: "room" | "material";
  entity_id: string;
  field: string;
  old_value: string | null;
  new_value: string | null;
}

export interface QualityIssue {
  severity: "error" | "warning" | "info";
  category: string;
  element_id: string;
  element_name: string;
  message: string;
}

export interface QualityReportData {
  score: number;
  issues_by_severity: Record<string, number>;
  issues: QualityIssue[];
}

export interface CostGroup {
  kg_number: string;
  name: string;
  level: number;
  subtotal: number;
  items: QuantityItem[];
}

export interface CostEstimate {
  total_cost: number;
  cost_per_sqm: number;
  cost_groups: CostGroup[];
}

// Monitoring types

export interface SnapshotTrendPoint {
  timestamp: string;
  label: string;
  room_count: number;
  material_count: number;
  total_area: number;
}

export interface MonitoringAlert {
  severity: "info" | "warning" | "critical";
  message: string;
  timestamp: string;
  snapshot_id: string;
  details: Record<string, string>;
}

export interface SchedulerStatus {
  active: boolean;
  interval_minutes: number;
  last_run: string | null;
  next_run: string | null;
  snapshot_count: number;
}

export interface SchedulerConfig {
  interval_minutes: number;
  enabled: boolean;
}
