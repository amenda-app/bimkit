"""Compute LPH progress across all HOAI phases (2-5)."""
from __future__ import annotations

from app.models import (
    BimElement,
    LPHPhaseProgress,
    LPHProgressResponse,
    PhaseRequirement,
    Room,
)
from app.services.standards_loader import get_requirement


# LPH phases to evaluate
_LPH_RANGE = range(2, 6)

# German labels for "next steps" generation
_FIELD_LABELS: dict[str, str] = {
    "name": "Raumname",
    "number": "Raumnummer",
    "area": "Raumfläche",
    "height": "Raumhöhe",
    "usage_type": "Nutzungsart",
    "finish_floor": "Bodenbelag",
    "finish_wall": "Wandbelag",
    "finish_ceiling": "Deckenbelag",
    "story": "Geschoss",
    "layer": "Layer/Ebene",
    "classification": "Klassifizierung",
}


def _is_empty(value: object) -> bool:
    """Return True if a value should be considered unfilled / missing."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in ("", "—", "k. A", "k.A."):
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    return False


def _room_properties_progress(
    rooms: list[Room],
    required_fields: list[str],
) -> tuple[float, dict[str, float], list[str]]:
    """Calculate room-property fill rates.

    Returns (overall_pct, field_detail, missing_fields).
    """
    if not required_fields:
        return 100.0, {}, []

    if not rooms:
        detail = {f: 0.0 for f in required_fields}
        return 0.0, detail, list(required_fields)

    total_cells = len(rooms) * len(required_fields)
    filled_cells = 0
    field_filled: dict[str, int] = {f: 0 for f in required_fields}

    for room in rooms:
        for field in required_fields:
            value = getattr(room, field, None)
            if not _is_empty(value):
                filled_cells += 1
                field_filled[field] += 1

    detail = {
        field: round(field_filled[field] / len(rooms) * 100, 1)
        for field in required_fields
    }
    missing = [f for f in required_fields if detail[f] < 100.0]
    overall = round(filled_cells / total_cells * 100, 1)

    return overall, detail, missing


def _element_types_progress(
    elements: list[BimElement],
    required_types: list[str],
) -> tuple[float, dict[str, bool], list[str]]:
    """Calculate element-type presence.

    Returns (overall_pct, type_detail, missing_types).
    """
    if not required_types:
        return 100.0, {}, []

    present_types = {e.element_type for e in elements}
    detail = {t: (t in present_types) for t in required_types}
    missing = [t for t, present in detail.items() if not present]
    found = sum(1 for p in detail.values() if p)
    overall = round(found / len(required_types) * 100, 1)

    return overall, detail, missing


def _element_properties_progress(
    elements: list[BimElement],
    required_props: list[str],
) -> tuple[float, list[str]]:
    """Calculate element-property fill rates.

    Returns (overall_pct, missing_props).
    """
    if not required_props:
        return 100.0, []

    if not elements:
        return 0.0, list(required_props)

    total_cells = len(elements) * len(required_props)
    filled_cells = 0
    prop_filled: dict[str, int] = {p: 0 for p in required_props}

    for elem in elements:
        for prop in required_props:
            value = getattr(elem, prop, None)
            if not _is_empty(value):
                filled_cells += 1
                prop_filled[prop] += 1

    missing = [
        p for p in required_props
        if prop_filled[p] < len(elements)
    ]
    overall = round(filled_cells / total_cells * 100, 1)

    return overall, missing


def _compute_phase_progress(
    requirement: PhaseRequirement,
    rooms: list[Room],
    elements: list[BimElement],
) -> LPHPhaseProgress:
    """Compute progress metrics for a single LPH phase."""
    room_pct, room_detail, room_missing = _room_properties_progress(
        rooms, requirement.room_properties_required,
    )
    type_pct, type_detail, type_missing = _element_types_progress(
        elements, requirement.element_types_required,
    )
    prop_pct, prop_missing = _element_properties_progress(
        elements, requirement.element_properties_required,
    )

    # Weighted overall: room properties 40%, element types 30%, element properties 30%
    overall = round(room_pct * 0.4 + type_pct * 0.3 + prop_pct * 0.3, 1)

    return LPHPhaseProgress(
        lph=requirement.lph,
        label=requirement.label,
        overall_progress=overall,
        room_properties_progress=room_pct,
        element_types_progress=type_pct,
        element_properties_progress=prop_pct,
        room_properties_detail=room_detail,
        element_types_detail=type_detail,
        missing_room_properties=room_missing,
        missing_element_types=type_missing,
        missing_element_properties=prop_missing,
    )


def _generate_next_steps(phases: list[LPHPhaseProgress]) -> list[str]:
    """Generate German-language next-step suggestions.

    Finds the first phase that is not yet at 100 % and produces
    actionable hints for reaching full compliance.
    """
    steps: list[str] = []

    for phase in phases:
        if phase.overall_progress >= 100.0:
            continue

        label = phase.label

        # Room property hints
        for field in phase.missing_room_properties:
            nice = _FIELD_LABELS.get(field, field)
            pct = phase.room_properties_detail.get(field, 0.0)
            steps.append(
                f"{label}: '{nice}' bei allen Raeumen ausfuellen "
                f"(aktuell {pct:.0f} % ausgefuellt)"
            )

        # Missing element types
        for etype in phase.missing_element_types:
            steps.append(
                f"{label}: Elementtyp '{etype}' im Modell ergaenzen"
            )

        # Missing element properties
        for prop in phase.missing_element_properties:
            nice = _FIELD_LABELS.get(prop, prop)
            steps.append(
                f"{label}: '{nice}' fuer alle Elemente ausfuellen"
            )

        # Only show next steps for the first incomplete phase
        break

    if not steps:
        steps.append("Alle Leistungsphasen vollstaendig erfuellt!")

    return steps


def compute_lph_progress(
    project_id: str,
    rooms: list[Room],
    elements: list[BimElement],
    current_phase: str = "",
) -> LPHProgressResponse:
    """Compute LPH progress for phases 2-5.

    Parameters
    ----------
    project_id:
        Project identifier (used for context, not for data lookup).
    rooms:
        List of rooms from the project store.
    elements:
        List of BIM elements from the project store.
    current_phase:
        Human-readable project status (e.g. "Entwurfsplanung").

    Returns
    -------
    LPHProgressResponse with per-phase metrics and next steps.
    """
    phase_results: list[LPHPhaseProgress] = []

    for lph in _LPH_RANGE:
        requirement = get_requirement(lph)
        if requirement is None:
            continue
        progress = _compute_phase_progress(requirement, rooms, elements)
        phase_results.append(progress)

    next_steps = _generate_next_steps(phase_results)

    return LPHProgressResponse(
        current_phase=current_phase,
        phases=phase_results,
        next_steps=next_steps,
    )
