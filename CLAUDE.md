# DCAB BIM Report Studio

## Projektstruktur
- **Monorepo** mit pnpm Workspaces
- `frontend/` - Next.js 14 (App Router, Tailwind, shadcn/ui)
- `backend/` - Express + TypeScript API Server
- `bim-service/` - Python FastAPI (ArchiCAD-Anbindung, Report-Generierung)

## Konventionen
- TypeScript strict mode im Frontend und Backend
- Python: Type Hints, Pydantic Models
- API-Kommunikation: Frontend → Backend (Port 4000) → BIM Service (Port 8000)
- Sprache: Code und Kommentare auf Englisch, UI-Texte auf Deutsch

## Ports
- Frontend: 3000
- Backend: 4000
- BIM Service: 8000

## Wichtige Befehle
- `pnpm dev` - Alle Services starten (Frontend + Backend)
- `cd bim-service && uvicorn app.main:app --reload --port 8000` - BIM Service starten
- `docker compose up --build` - Alles via Docker starten
