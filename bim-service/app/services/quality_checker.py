"""Quality checks for BIM model data."""
from __future__ import annotations

from datetime import datetime, timezone

from app.models import (
    Room, QualityIssue, QualityReport,
    BimElement, BoundingBox3D, Collision, StoryInfo, ZoneBoundary,
)

# Expected element types in a complete model
EXPECTED_TYPES = {"Wall", "Slab", "Door", "Window", "Column", "Roof"}

# Volume threshold (m³) above which an element is flagged
MAX_PLAUSIBLE_VOLUME = 50_000.0


def run_quality_checks(
    project_id: str,
    rooms: list[Room],
    *,
    elements: list[BimElement] | None = None,
    collisions: list[Collision] | None = None,
    bounding_boxes: list[BoundingBox3D] | None = None,
    stories: list[StoryInfo] | None = None,
    zone_boundaries: list[ZoneBoundary] | None = None,
) -> QualityReport:
    """Run quality checks on rooms and model elements, return a scored report."""
    issues: list[QualityIssue] = []

    # --- Room checks (existing) ---
    issues.extend(_check_rooms(rooms))

    # --- Enhanced model checks ---
    if elements is not None:
        issues.extend(_check_classifications(elements))
        issues.extend(_check_completeness(elements))
        issues.extend(_check_layers(elements))

    if collisions is not None:
        issues.extend(_check_collisions(collisions))

    if bounding_boxes is not None:
        issues.extend(_check_bounding_boxes(bounding_boxes, elements))

    if stories is not None and elements is not None:
        issues.extend(_check_stories(elements, stories))

    if zone_boundaries is not None:
        issues.extend(_check_zone_boundaries(zone_boundaries))

    # Score calculation
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    infos = sum(1 for i in issues if i.severity == "info")
    score = max(0, 100 - errors * 10 - warnings * 3 - infos * 1)

    # Issues by category
    cat_counts: dict[str, int] = {}
    for issue in issues:
        cat = issue.check_category or "other"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    checked = len(rooms) + (len(elements) if elements else 0)

    return QualityReport(
        score=score,
        issues_by_severity={"error": errors, "warning": warnings, "info": infos},
        issues=issues,
        issues_by_category=cat_counts,
        checked_elements=checked,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# --- Room checks ---

def _check_rooms(rooms: list[Room]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    seen_numbers: dict[str, str] = {}

    for room in rooms:
        if not room.name or room.name.strip() == "":
            issues.append(QualityIssue(
                severity="error",
                category="Vollständigkeit",
                element_id=room.id,
                element_name=room.number,
                message=f"Raum {room.number} hat keinen Namen",
                check_category="room",
            ))

        if not room.usage_type or room.usage_type.strip() == "":
            issues.append(QualityIssue(
                severity="error",
                category="Vollständigkeit",
                element_id=room.id,
                element_name=room.name or room.number,
                message=f"Raum {room.number} hat keine Nutzungsart",
                check_category="room",
            ))

        if room.area <= 0:
            issues.append(QualityIssue(
                severity="error",
                category="Geometrie",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat Fläche 0 m²",
                check_category="room",
            ))

        if room.height <= 0 and "terrasse" not in room.name.lower():
            issues.append(QualityIssue(
                severity="warning",
                category="Geometrie",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat Höhe 0 m",
                check_category="room",
            ))

        if room.number in seen_numbers:
            issues.append(QualityIssue(
                severity="warning",
                category="Konsistenz",
                element_id=room.id,
                element_name=room.name,
                message=f"Raumnummer {room.number} ist doppelt vergeben",
                check_category="room",
            ))
        seen_numbers[room.number] = room.id

        if 0 < room.area < 2.0:
            issues.append(QualityIssue(
                severity="info",
                category="Plausibilität",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat ungewöhnlich kleine Fläche ({room.area} m²)",
                check_category="room",
            ))
        if room.area > 500:
            issues.append(QualityIssue(
                severity="info",
                category="Plausibilität",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat ungewöhnlich große Fläche ({room.area} m²)",
                check_category="room",
            ))

        if room.height > 8.0:
            issues.append(QualityIssue(
                severity="info",
                category="Plausibilität",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat ungewöhnliche Höhe ({room.height} m)",
                check_category="room",
            ))

    return issues


# --- Classification checks ---

def _check_classifications(elements: list[BimElement]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for elem in elements:
        if not elem.classification:
            issues.append(QualityIssue(
                severity="error",
                category="Klassifizierung",
                element_id=elem.id,
                element_name=f"{elem.element_type} ({elem.id[:12]})",
                message=f"{elem.element_type}-Element hat keine IFC-Klassifizierung",
                check_category="completeness",
            ))
    return issues


# --- Completeness checks ---

def _check_completeness(elements: list[BimElement]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    present_types = {e.element_type for e in elements}
    missing = EXPECTED_TYPES - present_types
    for t in sorted(missing):
        issues.append(QualityIssue(
            severity="warning",
            category="Vollständigkeit",
            element_id="model",
            element_name="Gesamtmodell",
            message=f"Elementtyp '{t}' fehlt im Modell",
            check_category="completeness",
        ))
    return issues


# --- Layer checks ---

def _check_layers(elements: list[BimElement]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for elem in elements:
        if not elem.layer:
            issues.append(QualityIssue(
                severity="info",
                category="Eigenschaften",
                element_id=elem.id,
                element_name=f"{elem.element_type} ({elem.id[:12]})",
                message=f"{elem.element_type}-Element hat keine Layer-Zuordnung",
                check_category="property",
            ))
    return issues


# --- Collision checks ---

def _check_collisions(collisions: list[Collision]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for c in collisions:
        issues.append(QualityIssue(
            severity="error",
            category="Kollision",
            element_id=c.element1_id,
            element_name=f"{c.element1_type} / {c.element2_type}",
            message=f"Kollision zwischen {c.element1_type} ({c.element1_id[:12]}) und {c.element2_type} ({c.element2_id[:12]})",
            check_category="clash",
        ))
    return issues


# --- Bounding box checks ---

def _check_bounding_boxes(
    boxes: list[BoundingBox3D],
    elements: list[BimElement] | None,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    elem_map: dict[str, BimElement] = {}
    if elements:
        elem_map = {e.id: e for e in elements}

    for bb in boxes:
        dx = bb.x_max - bb.x_min
        dy = bb.y_max - bb.y_min
        dz = bb.z_max - bb.z_min
        volume = dx * dy * dz
        elem = elem_map.get(bb.element_id)
        name = f"{elem.element_type} ({bb.element_id[:12]})" if elem else bb.element_id[:12]

        if volume == 0.0:
            issues.append(QualityIssue(
                severity="error",
                category="Geometrie",
                element_id=bb.element_id,
                element_name=name,
                message=f"Element hat Volumen 0 (Bounding Box kollabiert)",
                check_category="geometry",
            ))
        elif volume > MAX_PLAUSIBLE_VOLUME:
            issues.append(QualityIssue(
                severity="info",
                category="Geometrie",
                element_id=bb.element_id,
                element_name=name,
                message=f"Element hat unplausibel großes Volumen ({volume:,.0f} m³)",
                check_category="geometry",
            ))
    return issues


# --- Story checks ---

def _check_stories(
    elements: list[BimElement],
    stories: list[StoryInfo],
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    known_stories = {s.name for s in stories}

    for elem in elements:
        if elem.story and elem.story not in known_stories:
            issues.append(QualityIssue(
                severity="warning",
                category="Geschoss",
                element_id=elem.id,
                element_name=f"{elem.element_type} ({elem.id[:12]})",
                message=f"Element ist Geschoss '{elem.story}' zugeordnet, das nicht definiert ist",
                check_category="story",
            ))
    return issues


# --- Zone boundary checks ---

def _check_zone_boundaries(boundaries: list[ZoneBoundary]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for zb in boundaries:
        if zb.boundary_count == 0:
            issues.append(QualityIssue(
                severity="error",
                category="Zonengrenzen",
                element_id=zb.zone_id,
                element_name=zb.zone_name,
                message=f"Zone '{zb.zone_name}' hat keine Begrenzungen (0 Boundaries)",
                check_category="zone",
            ))
        elif zb.boundary_count < 3:
            issues.append(QualityIssue(
                severity="warning",
                category="Zonengrenzen",
                element_id=zb.zone_id,
                element_name=zb.zone_name,
                message=f"Zone '{zb.zone_name}' hat nur {zb.boundary_count} Begrenzungen (min. 3 erwartet)",
                check_category="zone",
            ))
    return issues
