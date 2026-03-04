"""BIM Report Studio - FastAPI Service."""
from __future__ import annotations

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
    SchedulerConfig,
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
from app.services.diff_engine import create_snapshot, get_snapshots, compute_diff, delete_snapshot, detect_alerts
from app.services.snapshot_store import snapshot_store
from app.services.snapshot_scheduler import scheduler
from app.services.lph_progress import compute_lph_progress

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DCAB BIM Report Studio",
    version="0.4.0",
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


@app.on_event("startup")
async def _auto_connect() -> None:
    """Try to connect to ArchiCAD automatically on startup."""
    global _client
    _client = await create_client("localhost", 19723)
    if isinstance(_client, ArchiCADClient):
        logger.info("Auto-connected to ArchiCAD on startup")
        await _refresh_archicad_data()
        scheduler.set_refresh_callback(_refresh_archicad_data)
        scheduler.set_project_id("archicad-live")
        scheduler.start(interval_minutes=60)
    else:
        logger.info("ArchiCAD not available on startup, running without projects")


async def _refresh_archicad_data() -> None:
    """Refresh project data from ArchiCAD into the store."""
    if not isinstance(_client, ArchiCADClient):
        return
    try:
        projects = await _client.get_projects()
        for project in projects:
            rooms = await _client.get_rooms(project.id)
            materials = await _client.get_materials(project.id)
            project.total_area = round(sum(r.area for r in rooms), 2)
            project.floors = len(set(r.floor for r in rooms))
            store.add_project(project, rooms, materials, "archicad")
    except Exception as e:
        logger.warning("Failed to refresh ArchiCAD data: %s", e)


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
        await _refresh_archicad_data()

        # Start auto-snapshot scheduler
        scheduler.set_refresh_callback(_refresh_archicad_data)
        scheduler.set_project_id("archicad-live")
        scheduler.start(interval_minutes=60)

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
    """Delete a project."""
    removed = store.remove_project(project_id)
    if not removed:
        raise HTTPException(
            status_code=400,
            detail="Projekt nicht gefunden",
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


@app.get("/bim/lph-progress/{project_id}")
async def lph_progress(project_id: str):
    """Get LPH progress for all phases (2-5)."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")
    rooms = store.get_rooms(project_id)

    # Collect element data for element type/property checks
    elements: list = []
    if isinstance(_client, (ArchiCADClient, MockArchiCADClient)):
        try:
            extra_data = await collect_quality_data(_client)
            elements = extra_data.get("elements", [])
        except Exception as e:
            logger.warning("Failed to collect elements for LPH progress: %s", e)

    result = compute_lph_progress(project_id, rooms, elements, current_phase=project.status)
    return result.model_dump()


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


@app.delete("/bim/snapshots/{project_id}/{snapshot_id}")
async def snapshot_delete(project_id: str, snapshot_id: str):
    """Delete a specific snapshot."""
    deleted = delete_snapshot(project_id, snapshot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    return {"message": "Snapshot gelöscht", "deleted": True}


@app.post("/bim/compare")
async def compare_snapshots(req: CompareRequest):
    changes = compute_diff(req.snapshot_a, req.snapshot_b, req.project_id)
    return {
        "changes": [c.model_dump() for c in changes],
        "count": len(changes),
        "summary": {
            "added": sum(1 for c in changes if c.type == "added"),
            "removed": sum(1 for c in changes if c.type == "removed"),
            "changed": sum(1 for c in changes if c.type == "changed"),
        },
    }


@app.post("/bim/refresh")
async def refresh():
    """Re-read project data from ArchiCAD."""
    if not isinstance(_client, ArchiCADClient):
        raise HTTPException(status_code=400, detail="Keine Live-Verbindung zu ArchiCAD")
    await _refresh_archicad_data()
    projects = store.get_projects()
    return {"message": "Daten aktualisiert", "projects": [p.model_dump() for p in projects]}


# --- Monitoring Endpoints ---

@app.get("/bim/monitoring/status")
async def monitoring_status():
    """Get auto-snapshot scheduler status."""
    return scheduler.get_status().model_dump()


@app.post("/bim/monitoring/configure")
async def monitoring_configure(config: SchedulerConfig):
    """Configure the auto-snapshot scheduler."""
    if config.enabled:
        scheduler.start(interval_minutes=config.interval_minutes)
    else:
        scheduler.stop()
    return scheduler.get_status().model_dump()


@app.get("/bim/trends/{project_id}")
async def trends(project_id: str):
    """Get snapshot trend data for a project."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")
    trend_data = snapshot_store.get_trends(project_id)
    return {"trends": [t.model_dump() for t in trend_data]}


@app.get("/bim/alerts/{project_id}")
async def alerts(project_id: str):
    """Detect significant changes between latest snapshots."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{project_id}' nicht gefunden")
    alert_list = detect_alerts(project_id)
    return {"alerts": [a.model_dump() for a in alert_list]}


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
