"""AI-powered project report generation using LLM providers (OpenRouter / Ollama)."""

import json
import logging
import os
import re

from openai import AsyncOpenAI

from app.models import (
    Area, CostEstimate, ChangeEntry, Material, Project, QualityReport, Room, Snapshot,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Du bist ein erfahrener BIM-Manager und erstellst einen strukturierten \
Projektbericht auf Deutsch. Verwende die bereitgestellten Projektdaten \
und interpretiere sie fachlich korrekt. Beziehe dich auf DIN 277 \
(Flächenberechnung) und DIN 276 (Kostengruppen) wo relevant.

Schreibe sachlich und präzise. Nenne konkrete Zahlen aus den Daten. \
Hebe kritische Probleme hervor und gib priorisierte Handlungsempfehlungen.

Der Bericht muss exakt folgende 7 Abschnitte enthalten:

1. PROJEKTÜBERSICHT
2. RAUMSTRUKTUR & FLÄCHENBILANZ
3. MATERIALIEN & BAUKONSTRUKTION
4. KOSTENPROGNOSE
5. MODELLQUALITÄT
6. PHASEN-COMPLIANCE
7. HANDLUNGSEMPFEHLUNGEN

Beginne mit einer Kopfzeile im Format:
PROJEKTBERICHT — {Projektname}
Stand: {Datum} | {Phase}

Verwende Markdown-Formatierung. Jeder Abschnitt beginnt mit ## {Nummer}. {Titel}.
"""

REPORT_SECTIONS = [
    "PROJEKTÜBERSICHT",
    "RAUMSTRUKTUR & FLÄCHENBILANZ",
    "MATERIALIEN & BAUKONSTRUKTION",
    "KOSTENPROGNOSE",
    "MODELLQUALITÄT",
    "PHASEN-COMPLIANCE",
    "HANDLUNGSEMPFEHLUNGEN",
]

# Provider configuration
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openrouter")  # "openrouter" or "ollama"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")


def _get_client() -> tuple[AsyncOpenAI, str]:
    """Return (client, model) for the configured AI provider."""
    if AI_PROVIDER == "ollama":
        client = AsyncOpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",  # Ollama doesn't need a real key
        )
        return client, OLLAMA_MODEL

    # Default: OpenRouter
    if not OPENROUTER_API_KEY:
        raise EnvironmentError(
            "OPENROUTER_API_KEY ist nicht gesetzt. "
            "Bitte die Umgebungsvariable setzen oder AI_PROVIDER=ollama verwenden."
        )
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    return client, OPENROUTER_MODEL


def _summarize_rooms(rooms: list[Room]) -> str:
    if not rooms:
        return "Keine Raumdaten vorhanden."
    floors = {}
    for r in rooms:
        floors.setdefault(r.floor, []).append(r)
    lines = [f"Anzahl Räume: {len(rooms)}"]
    total_area = sum(r.area for r in rooms)
    lines.append(f"Gesamtfläche: {total_area:.1f} m²")
    for floor, floor_rooms in sorted(floors.items()):
        fa = sum(r.area for r in floor_rooms)
        lines.append(f"  {floor}: {len(floor_rooms)} Räume, {fa:.1f} m²")
    smallest = min(rooms, key=lambda r: r.area)
    largest = max(rooms, key=lambda r: r.area)
    lines.append(f"Kleinster Raum: {smallest.name} ({smallest.area:.1f} m²)")
    lines.append(f"Größter Raum: {largest.name} ({largest.area:.1f} m²)")
    missing_finish = [r for r in rooms if not r.finish_floor or r.finish_floor == "—"]
    if missing_finish:
        lines.append(f"Räume ohne Bodenbelag: {len(missing_finish)}")
    return "\n".join(lines)


def _summarize_areas(areas: list[Area]) -> str:
    if not areas:
        return "Keine DIN 277 Flächendaten vorhanden."
    by_cat: dict[str, float] = {}
    for a in areas:
        by_cat[a.category] = by_cat.get(a.category, 0) + a.area
    lines = ["DIN 277 Flächenbilanz:"]
    for cat in ("NUF", "TF", "VF"):
        val = by_cat.get(cat, 0)
        lines.append(f"  {cat}: {val:.1f} m²")
    total = sum(by_cat.values())
    lines.append(f"  Gesamt NGF: {total:.1f} m²")
    return "\n".join(lines)


def _summarize_materials(materials: list[Material]) -> str:
    if not materials:
        return "Keine Materialdaten vorhanden."
    by_cat: dict[str, list[Material]] = {}
    for m in materials:
        by_cat.setdefault(m.category, []).append(m)
    lines = [f"Anzahl Materialien: {len(materials)}"]
    for cat, mats in sorted(by_cat.items()):
        lines.append(f"  {cat}: {len(mats)} Materialien")
    missing_mfr = [m for m in materials if not m.manufacturer or m.manufacturer == "—"]
    if missing_mfr:
        lines.append(f"Materialien ohne Herstellerangabe: {len(missing_mfr)}")
    return "\n".join(lines)


def _summarize_quality(report: QualityReport) -> str:
    lines = [
        f"Qualitätsscore: {report.score}/100",
        f"Geprüfte Elemente: {report.checked_elements}",
    ]
    for sev in ("error", "warning", "info"):
        count = report.issues_by_severity.get(sev, 0)
        if count:
            lines.append(f"  {sev}: {count}")
    top_issues = report.issues[:10]
    if top_issues:
        lines.append("Top-Probleme:")
        for issue in top_issues:
            lines.append(f"  [{issue.severity}] {issue.message}")
    if report.phase_compliance:
        pc = report.phase_compliance
        lines.append(f"\nPhasen-Compliance: {pc.lph_label}")
        lines.append(f"  Erfüllungsgrad: {pc.compliance_score}%")
        lines.append(f"  Konform: {'Ja' if pc.compliant else 'Nein'}")
        lines.append(f"  Verstöße: {len(pc.violations)}")
        by_rule = pc.violations_by_rule
        if by_rule:
            lines.append("  Verstöße nach Regel:")
            for rule, cnt in sorted(by_rule.items(), key=lambda x: -x[1]):
                lines.append(f"    {rule}: {cnt}")
    return "\n".join(lines)


def _summarize_cost(estimate: CostEstimate) -> str:
    lines = [
        f"Gesamtkosten: {estimate.total_cost:,.2f} EUR",
        f"Kosten pro m²: {estimate.cost_per_sqm:,.2f} EUR/m²",
        "Kostengruppen (DIN 276):",
    ]
    for cg in estimate.cost_groups:
        prefix = "  " if cg.level == 1 else "    "
        lines.append(f"{prefix}KG {cg.kg_number} {cg.name}: {cg.subtotal:,.2f} EUR")
    return "\n".join(lines)


def _summarize_snapshots(
    snapshots: list[Snapshot] | None,
    changes: list[ChangeEntry] | None,
) -> str:
    if not snapshots:
        return "Keine Snapshots vorhanden."
    lines = [f"Anzahl Snapshots: {len(snapshots)}"]
    latest = snapshots[-1]
    lines.append(f"Letzter Snapshot: {latest.label} ({latest.timestamp})")
    if changes:
        added = sum(1 for c in changes if c.type == "added")
        removed = sum(1 for c in changes if c.type == "removed")
        changed = sum(1 for c in changes if c.type == "changed")
        lines.append(f"Änderungen seit letztem Snapshot: {added} hinzugefügt, {removed} entfernt, {changed} geändert")
    return "\n".join(lines)


def _build_user_prompt(
    project: Project,
    rooms: list[Room],
    areas: list[Area],
    materials: list[Material],
    quality_report: QualityReport,
    cost_estimate: CostEstimate,
    snapshots: list[Snapshot] | None = None,
    changes: list[ChangeEntry] | None = None,
) -> str:
    sections = [
        f"# Projektdaten: {project.name}",
        f"Adresse: {project.address}",
        f"Gebäudetyp: {project.building_type}",
        f"BGF: {project.total_area} m²",
        f"Geschosse: {project.floors}",
        f"Status: {project.status}",
        "",
        "## Räume",
        _summarize_rooms(rooms),
        "",
        "## Flächen (DIN 277)",
        _summarize_areas(areas),
        "",
        "## Materialien",
        _summarize_materials(materials),
        "",
        "## Kostenprognose (DIN 276)",
        _summarize_cost(cost_estimate),
        "",
        "## Modellqualität",
        _summarize_quality(quality_report),
        "",
        "## Snapshot-Verlauf",
        _summarize_snapshots(snapshots, changes),
    ]
    return "\n".join(sections)


async def generate_project_report(
    project: Project,
    rooms: list[Room],
    areas: list[Area],
    materials: list[Material],
    quality_report: QualityReport,
    cost_estimate: CostEstimate,
    snapshots: list[Snapshot] | None = None,
    changes: list[ChangeEntry] | None = None,
    model_override: str | None = None,
) -> tuple[str, str]:
    """Generate a narrative project report using an LLM.

    Returns (report_markdown, model_used).
    """
    client, default_model = _get_client()
    model = model_override or default_model

    user_prompt = _build_user_prompt(
        project, rooms, areas, materials, quality_report, cost_estimate,
        snapshots, changes,
    )

    logger.info("Generating AI report for project %s using %s (%s)", project.id, AI_PROVIDER, model)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    report = response.choices[0].message.content or ""
    return report, model


def extract_sections(report_markdown: str) -> list[str]:
    """Extract section titles from the generated report."""
    return re.findall(r"^##\s+\d+\.\s+(.+)$", report_markdown, re.MULTILINE)
