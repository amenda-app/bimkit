from __future__ import annotations

from pydantic import BaseModel


class Room(BaseModel):
    id: str
    number: str
    name: str
    floor: str
    area: float  # m²
    height: float  # m
    volume: float  # m³
    usage_type: str  # DIN 277 Nutzungsart
    finish_floor: str
    finish_wall: str
    finish_ceiling: str


class Area(BaseModel):
    id: str
    name: str
    category: str  # NUF, TF, VF (DIN 277)
    floor: str
    area: float  # m²
    rooms: list[str]  # Room IDs


class Material(BaseModel):
    id: str
    name: str
    category: str  # Wand, Boden, Decke, Fenster, Tür
    quantity: float
    unit: str  # m², m³, Stk
    manufacturer: str
    product: str


class Project(BaseModel):
    id: str
    name: str
    address: str
    building_type: str
    total_area: float  # BGF in m²
    floors: int
    status: str
    source: str = "mock"  # "mock" | "ifc" | "archicad"


# --- V2 Models ---

class QuantityItem(BaseModel):
    trade: str  # Gewerk
    category: str  # Boden, Wand, Decke, etc.
    element_type: str
    description: str
    quantity: float
    unit: str
    unit_price: float  # EUR
    total_price: float  # EUR


class Snapshot(BaseModel):
    id: str
    project_id: str
    timestamp: str  # ISO 8601
    label: str
    room_count: int
    material_count: int
    total_area: float


class ChangeEntry(BaseModel):
    type: str  # added, removed, changed
    entity_type: str  # room, material
    entity_id: str
    field: str
    old_value: str | None = None
    new_value: str | None = None


class QualityIssue(BaseModel):
    severity: str  # error, warning, info
    category: str
    element_id: str
    element_name: str
    message: str


class QualityReport(BaseModel):
    score: int  # 0-100
    issues_by_severity: dict[str, int]
    issues: list[QualityIssue]


class CostGroup(BaseModel):
    kg_number: str  # e.g. "300", "330"
    name: str
    level: int  # 1 = KG 300, 2 = KG 330
    subtotal: float
    items: list[QuantityItem] = []


class CostEstimate(BaseModel):
    total_cost: float
    cost_per_sqm: float
    cost_groups: list[CostGroup]


# Request/Response Models

class ProjectRequest(BaseModel):
    project_id: str


class ConnectRequest(BaseModel):
    host: str = "localhost"
    port: int = 19723


class ConnectResponse(BaseModel):
    connected: bool
    mode: str  # "live" or "mock"
    message: str


class ExcelRequest(BaseModel):
    project_id: str
    report_type: str  # "raumbuch", "flaechen", "materialien", "mengen"


class ExcelResponse(BaseModel):
    filename: str
    message: str


class PdfRequest(BaseModel):
    project_id: str
    report_type: str  # "raumbuch", "flaechen", "materialien", "mengen"


class SnapshotRequest(BaseModel):
    project_id: str
    label: str


class CompareRequest(BaseModel):
    project_id: str
    snapshot_a: str
    snapshot_b: str


# --- Monitoring Models ---

class SnapshotTrendPoint(BaseModel):
    timestamp: str
    label: str
    room_count: int
    material_count: int
    total_area: float


class MonitoringAlert(BaseModel):
    severity: str  # "info" | "warning" | "critical"
    message: str
    timestamp: str
    snapshot_id: str
    details: dict[str, str]


class SchedulerStatus(BaseModel):
    active: bool
    interval_minutes: int
    last_run: str | None
    next_run: str | None
    snapshot_count: int


class SchedulerConfig(BaseModel):
    interval_minutes: int = 60
    enabled: bool = True
