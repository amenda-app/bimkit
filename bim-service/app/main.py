"""BIM Report Studio - FastAPI Service."""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.models import (
    ConnectRequest, ConnectResponse, ExcelRequest, ExcelResponse,
    ProjectRequest,
)
from app.services.archicad import create_client, MockArchiCADClient
from app.services.report_generator import (
    generate_raumbuch, generate_flaechen, generate_materialien,
)
from app import mock_data

app = FastAPI(
    title="DCAB BIM Report Studio",
    version="0.1.0",
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
_client = MockArchiCADClient()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "bim-service", "mode": "mock" if isinstance(_client, MockArchiCADClient) else "live"}


@app.post("/bim/connect", response_model=ConnectResponse)
async def connect(req: ConnectRequest):
    global _client
    _client = await create_client(req.host, req.port)
    is_mock = isinstance(_client, MockArchiCADClient)
    return ConnectResponse(
        connected=True,
        mode="mock" if is_mock else "live",
        message="Verbunden mit Mock-Daten (ArchiCAD nicht erreichbar)" if is_mock
        else "Verbunden mit ArchiCAD",
    )


@app.get("/bim/projects")
async def list_projects():
    projects = await _client.get_projects()
    return {"projects": [p.model_dump() for p in projects]}


@app.post("/bim/extract/rooms")
async def extract_rooms(req: ProjectRequest):
    project = mock_data.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    rooms = await _client.get_rooms(req.project_id)
    return {
        "project": project.model_dump(),
        "rooms": [r.model_dump() for r in rooms],
        "count": len(rooms),
    }


@app.post("/bim/extract/areas")
async def extract_areas(req: ProjectRequest):
    project = mock_data.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    areas = await _client.get_areas(req.project_id)
    return {
        "project": project.model_dump(),
        "areas": [a.model_dump() for a in areas],
        "count": len(areas),
    }


@app.post("/bim/extract/materials")
async def extract_materials(req: ProjectRequest):
    project = mock_data.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")
    materials = await _client.get_materials(req.project_id)
    return {
        "project": project.model_dump(),
        "materials": [m.model_dump() for m in materials],
        "count": len(materials),
    }


@app.post("/bim/generate/excel")
async def generate_excel(req: ExcelRequest):
    project = mock_data.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Projekt '{req.project_id}' nicht gefunden")

    generators = {
        "raumbuch": lambda: generate_raumbuch(project, mock_data.get_rooms(req.project_id)),
        "flaechen": lambda: generate_flaechen(project, mock_data.get_areas(req.project_id)),
        "materialien": lambda: generate_materialien(project, mock_data.get_materials(req.project_id)),
    }

    gen = generators.get(req.report_type)
    if gen is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannter Report-Typ '{req.report_type}'. Erlaubt: raumbuch, flaechen, materialien",
        )

    output = gen()
    filename = f"{req.report_type}_{req.project_id}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/bim/generate/pdf")
async def generate_pdf(req: ExcelRequest):
    # PDF generation will be implemented later
    raise HTTPException(status_code=501, detail="PDF-Generierung noch nicht implementiert")
