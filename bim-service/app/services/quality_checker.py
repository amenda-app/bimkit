"""Quality checks for BIM model data."""
from __future__ import annotations

from app.models import Room, QualityIssue, QualityReport


def run_quality_checks(project_id: str, rooms: list[Room]) -> QualityReport:
    """Run quality checks on rooms and return a scored report."""
    issues: list[QualityIssue] = []

    seen_numbers: dict[str, str] = {}

    for room in rooms:
        # Missing name
        if not room.name or room.name.strip() == "":
            issues.append(QualityIssue(
                severity="error",
                category="Vollständigkeit",
                element_id=room.id,
                element_name=room.number,
                message=f"Raum {room.number} hat keinen Namen",
            ))

        # Missing usage_type
        if not room.usage_type or room.usage_type.strip() == "":
            issues.append(QualityIssue(
                severity="error",
                category="Vollständigkeit",
                element_id=room.id,
                element_name=room.name or room.number,
                message=f"Raum {room.number} hat keine Nutzungsart",
            ))

        # Area = 0
        if room.area <= 0:
            issues.append(QualityIssue(
                severity="error",
                category="Geometrie",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat Fläche 0 m²",
            ))

        # Height = 0 (except outdoor areas)
        if room.height <= 0 and "terrasse" not in room.name.lower():
            issues.append(QualityIssue(
                severity="warning",
                category="Geometrie",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat Höhe 0 m",
            ))

        # Duplicate room numbers
        if room.number in seen_numbers:
            issues.append(QualityIssue(
                severity="warning",
                category="Konsistenz",
                element_id=room.id,
                element_name=room.name,
                message=f"Raumnummer {room.number} ist doppelt vergeben",
            ))
        seen_numbers[room.number] = room.id

        # Unusual area (very small or very large)
        if 0 < room.area < 2.0:
            issues.append(QualityIssue(
                severity="info",
                category="Plausibilität",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat ungewöhnlich kleine Fläche ({room.area} m²)",
            ))
        if room.area > 500:
            issues.append(QualityIssue(
                severity="info",
                category="Plausibilität",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat ungewöhnlich große Fläche ({room.area} m²)",
            ))

        # Height plausibility
        if room.height > 8.0:
            issues.append(QualityIssue(
                severity="info",
                category="Plausibilität",
                element_id=room.id,
                element_name=room.name,
                message=f"Raum {room.number} hat ungewöhnliche Höhe ({room.height} m)",
            ))

    # Score calculation
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    infos = sum(1 for i in issues if i.severity == "info")
    score = max(0, 100 - errors * 10 - warnings * 3 - infos * 1)

    return QualityReport(
        score=score,
        issues_by_severity={"error": errors, "warning": warnings, "info": infos},
        issues=issues,
    )
