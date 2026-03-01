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
    report_type: str  # "raumbuch", "flaechen", "materialien"


class ExcelResponse(BaseModel):
    filename: str
    message: str
