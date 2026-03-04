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


class BimElement(BaseModel):
    id: str
    element_type: str  # Wall, Slab, Column, etc.
    story: str
    layer: str
    classification: str  # IFC classification, empty if missing


class BoundingBox3D(BaseModel):
    element_id: str
    x_min: float
    y_min: float
    z_min: float
    x_max: float
    y_max: float
    z_max: float


class Collision(BaseModel):
    element1_id: str
    element1_type: str
    element2_id: str
    element2_type: str


class StoryInfo(BaseModel):
    name: str
    index: int
    elevation: float


class ZoneBoundary(BaseModel):
    zone_id: str
    zone_name: str
    boundary_count: int


class QualityIssue(BaseModel):
    severity: str  # error, warning, info
    category: str
    element_id: str
    element_name: str
    message: str
    check_category: str = ""  # machine key for filtering


class PhaseRequirement(BaseModel):
    lph: int
    label: str
    room_properties_required: list[str]
    room_properties_optional: list[str]
    element_types_required: list[str]
    element_properties_required: list[str]


class StandardsViolation(BaseModel):
    severity: str          # "error" | "warning"
    rule_id: str           # e.g. "room.missing_finish_floor"
    element_id: str
    element_name: str
    message: str           # German, human-readable


class PhaseComplianceReport(BaseModel):
    project_phase: str     # e.g. "Ausführungsplanung"
    lph: int
    lph_label: str         # e.g. "LPH 5 – Ausführungsplanung"
    compliant: bool
    compliance_score: int  # 0-100
    violations: list[StandardsViolation]
    violations_by_rule: dict[str, int]
    checked_rooms: int
    checked_elements: int


class QualityReport(BaseModel):
    score: int  # 0-100
    issues_by_severity: dict[str, int]
    issues: list[QualityIssue]
    issues_by_category: dict[str, int] = {}
    checked_elements: int = 0
    timestamp: str = ""
    phase_compliance: PhaseComplianceReport | None = None


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


# --- LPH Progress Models ---

class LPHPhaseProgress(BaseModel):
    lph: int
    label: str
    overall_progress: float  # 0-100
    room_properties_progress: float  # 0-100
    element_types_progress: float  # 0-100
    element_properties_progress: float  # 0-100
    room_properties_detail: dict[str, float]  # field -> % filled
    element_types_detail: dict[str, bool]  # type -> present
    missing_room_properties: list[str]  # fields with <100% fill
    missing_element_types: list[str]  # types not present
    missing_element_properties: list[str]  # props not filled


class LPHProgressResponse(BaseModel):
    current_phase: str  # project status
    phases: list[LPHPhaseProgress]
    next_steps: list[str]  # German-language "next steps" to improve


# --- AI Report Models ---

class ProjectReportRequest(BaseModel):
    model: str | None = None  # override default model


class ProjectReportResponse(BaseModel):
    project_id: str
    report: str  # markdown
    model_used: str
    sections: list[str]
