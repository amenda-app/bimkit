"""BIM Report Studio - FastAPI Service."""

import os
import uuid
import tempfile
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.models import (
    ConnectRequest, ConnectResponse, ExcelRequest, PdfRequest,
    ProjectRequest, SnapshotRequest, CompareRequest,
    ProjectReportRequest, ProjectReportResponse,
)
from app.services.archicad import create_client, ArchiCADClient, MockArchiCADClient
from app.services.project_store import store
from app.services.report_generator import (
    generate_raumbuch, generate_flaechen, generate_materialien, generate_mengen,
)
from app.services.pdf_generator import (
    generate_pdf_raumbuch, generate_pdf_flaechen, generate_pdf_materialien, generate_pdf_mengen,
)
from app.services.quality_checker import run_quality_checks
from app.services.quality_data_collector import collect_quality_data
from app.services.standards_loader import resolve_lph_for_status, get_requirement
from app.services.standards_checker import check_standards_compliance
from app.services.diff_engine import create_snapshot, get_snapshots, compute_diff
from app.services.ai_assistant import generate_project_report, extract_sections

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DCAB BIM Report Studio",
    version="0.3.0",
    description="BIM data extraction and report generation service",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client - starts as mock
_client: ArchiCADClient | MockArchiCADClient = MockArchiCADClient()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "bim-service", "mode": "mock" if isinstance(_client, MockArchiCADClient) else "live"}


@app.post("/bim/connect", response_model=ConnectResponse)
async def connect(req: ConnectRequest):
    global _client
    _client = await create_client(req.host, req.port)
    is_mock = isinstance(_client, MockArchiCADClient)

    # If real ArchiCAD connected, pull data into store
    if not is_mock and isinstance(_client, ArchiCADClient):
        try:
            projects = await _client.get_projects()
            for project in projects:
                rooms = await _client.get_rooms(project.id)
                materials = await _client.get_materials(project.id)
                # Update total_area from actual rooms
                project.total_area = round(sum(r.area for r in rooms), 2)
                project.floors = len(set(r.floor for r in rooms))
                store.add_project(project, rooms, materials, "archicad")
        except Exception as e:
            logger.warning("Failed to pull ArchiCAD data into store: %s", e)

    return ConnectResponse(
        connected=True,
        mode="mock" if is_mock else "live",
        message="Verbunden mit Mock-Daten (ArchiCAD nicht erreichbar)" if is_mock
        else "Verbunden mit ArchiCAD — Projektdaten importiert",
    )


@app.get("/bim/projects")
async def list_projects():
    projects = store.get_projects()
    return {"projects": [p.model_dump() for p in projects]}


@app.post("/bim/upload/ifc")
async def upload_ifc(file: UploadFile = File(...)):
    """Upload an IFC file and parse it into the project store."""
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Nur .ifc Dateien werden akzeptiert")

    # Save to temp file for ifcopenshell
    try:
        from app.services.ifc_parser import parse_ifc
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="ifcopenshell ist nicht installiert. Bitte 'pip install ifcopenshell' ausführen.",
        )

    suffix = ".ifc"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        project_id = f"ifc-{uuid.uuid4().hex[:8]}"
        project, rooms, materials = parse_ifc(tmp_path, project_id)
        store.add_project(project, rooms, materials, "ifc")

        return {
            "project": project.model_dump(),
            "rooms_count": len(rooms),
            "materials_count": len(materials),
            "message": f"IFC-Datei '{file.filename}' erfolgreich importiert",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Parsen der IFC-Datei: {e}")
    finally:
        os.unlink(tmp_path)


@app.delete("/bim/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete an uploaded or ArchiCAD project (not mock)."""
    removed = store.remove_project(project_id)
    if not removed:
        raise HTTPException(
            status_code=400,
            detail="Projekt nicht gefunden oder ist ein Demo-Projekt (kann nicht gelöscht werden)",
        )
    return {"message": f"Projekt '{project_id}' gelöscht", "deleted": True}


@app.post("/bim/extract/rooms")
async def extract_rooms(req: ProjectRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    rooms = store.get_rooms(req.project_id)
    return {
        "project": project.model_dump(),
        "rooms": [r.model_dump() for r in rooms],
        "count": len(rooms),
    }


@app.post("/bim/extract/areas")
async def extract_areas(req: ProjectRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    areas = store.get_areas(req.project_id)
    return {
        "project": project.model_dump(),
        "areas": [a.model_dump() for a in areas],
        "count": len(areas),
    }


@app.post("/bim/extract/materials")
async def extract_materials(req: ProjectRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    materials = store.get_materials(req.project_id)
    return {
        "project": project.model_dump(),
        "materials": [m.model_dump() for m in materials],
        "count": len(materials),
    }


# --- V2 Endpoints ---

@app.post("/bim/extract/quantities")
async def extract_quantities(req: ProjectRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    quantities = store.get_quantities(req.project_id)
    total_cost = sum(q.total_price for q in quantities)
    return {
        "project": project.model_dump(),
        "quantities": [q.model_dump() for q in quantities],
        "count": len(quantities),
        "total_cost": round(total_cost, 2),
    }


@app.post("/bim/quality/{project_id}")
async def quality_report(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")
    rooms = store.get_rooms(project_id)

    extra_data: dict = {}
    if isinstance(_client, (ArchiCADClient, MockArchiCADClient)):
        try:
            extra_data = await collect_quality_data(_client)
        except Exception as e:
            logger.warning("Failed to collect enhanced quality data: %s", e)

    report = run_quality_checks(project_id, rooms, **extra_data)

    lph = resolve_lph_for_status(project.status)
    if lph is not None:
        requirement = get_requirement(lph)
        if requirement is not None:
            compliance = check_standards_compliance(
                project.status, requirement, rooms, extra_data.get("elements", []))
            report.phase_compliance = compliance

    return report.model_dump()


@app.post("/bim/cost-estimate/{project_id}")
async def cost_estimate(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")
    estimate = store.get_cost_estimate(project_id)
    return estimate.model_dump()


@app.post("/bim/snapshots/create")
async def snapshot_create(req: SnapshotRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    snap = create_snapshot(req.project_id, req.label)
    return snap.model_dump()


@app.get("/bim/snapshots/{project_id}")
async def snapshot_list(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")
    snaps = get_snapshots(project_id)
    return {"snapshots": [s.model_dump() for s in snaps]}


@app.post("/bim/compare")
async def compare_snapshots(req: CompareRequest):
    changes = compute_diff(req.snapshot_a, req.snapshot_b)
    return {
        "changes": [c.model_dump() for c in changes],
        "count": len(changes),
        "summary": {
            "added": sum(1 for c in changes if c.type == "added"),
            "removed": sum(1 for c in changes if c.type == "removed"),
            "changed": sum(1 for c in changes if c.type == "changed"),
        },
    }


# --- AI Report ---

@app.post("/bim/ai/project-report/{project_id}", response_model=ProjectReportResponse)
async def ai_project_report(project_id: str, req: ProjectReportRequest | None = None):
    """Generate an AI-powered narrative project report."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")

    # Collect all project data
    rooms = store.get_rooms(project_id)
    areas = store.get_areas(project_id)
    materials = store.get_materials(project_id)
    cost = store.get_cost_estimate(project_id)

    # Run quality checks (reuse existing logic)
    extra_data: dict = {}
    if isinstance(_client, (ArchiCADClient, MockArchiCADClient)):
        try:
            extra_data = await collect_quality_data(_client)
        except Exception as e:
            logger.warning("Failed to collect quality data for AI report: %s", e)

    quality = run_quality_checks(project_id, rooms, **extra_data)
    lph = resolve_lph_for_status(project.status)
    if lph is not None:
        requirement = get_requirement(lph)
        if requirement is not None:
            compliance = check_standards_compliance(
                project.status, requirement, rooms, extra_data.get("elements", []))
            quality.phase_compliance = compliance

    # Snapshots (optional)
    snapshots = get_snapshots(project_id)
    changes = None
    if len(snapshots) >= 2:
        changes = compute_diff(snapshots[-2].id, snapshots[-1].id)

    model_override = req.model if req else None

    try:
        report_md, model_used = await generate_project_report(
            project, rooms, areas, materials, quality, cost,
            snapshots or None, changes, model_override,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))

    sections = extract_sections(report_md)

    return ProjectReportResponse(
        project_id=project_id,
        report=report_md,
        model_used=model_used,
        sections=sections,
    )


# --- Report Generation ---

@app.post("/bim/generate/excel")
async def generate_excel(req: ExcelRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")

    generators = {
        "raumbuch": lambda: generate_raumbuch(project, store.get_rooms(req.project_id)),
        "flaechen": lambda: generate_flaechen(project, store.get_areas(req.project_id)),
        "materialien": lambda: generate_materialien(project, store.get_materials(req.project_id)),
        "mengen": lambda: generate_mengen(project, store.get_quantities(req.project_id)),
    }

    gen = generators.get(req.report_type)
    if gen is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannter Report-Typ '{req.report_type}'. Erlaubt: raumbuch, flaechen, materialien, mengen",
        )

    output = gen()
    filename = f"{req.report_type}_{req.project_id}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/bim/generate/pdf")
async def generate_pdf(req: PdfRequest):
    project = store.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")

    generators = {
        "raumbuch": lambda: generate_pdf_raumbuch(project, store.get_rooms(req.project_id)),
        "flaechen": lambda: generate_pdf_flaechen(project, store.get_areas(req.project_id)),
        "materialien": lambda: generate_pdf_materialien(project, store.get_materials(req.project_id)),
        "mengen": lambda: generate_pdf_mengen(project, store.get_quantities(req.project_id)),
    }

    gen = generators.get(req.report_type)
    if gen is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannter Report-Typ '{req.report_type}'. Erlaubt: raumbuch, flaechen, materialien, mengen",
        )

    output = gen()
    filename = f"{req.report_type}_{req.project_id}.pdf"

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
