# BIM Service

FastAPI service for BIM data extraction from ArchiCAD and report generation.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health` - Health check
- `POST /bim/connect` - Test ArchiCAD connection
- `GET /bim/projects` - List projects
- `POST /bim/extract/rooms` - Extract room data
- `POST /bim/extract/areas` - Extract area data (DIN 277)
- `POST /bim/extract/materials` - Extract material data
- `POST /bim/generate/excel` - Generate Excel report
- `POST /bim/generate/pdf` - Generate PDF report (not yet implemented)

## Mock Mode

When ArchiCAD is not available, the service automatically uses mock data with 3 sample projects.
