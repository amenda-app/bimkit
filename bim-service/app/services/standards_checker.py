"""Phase-based modeling standards compliance checker."""

from collections import Counter

from app.models import (
    BimElement,
    PhaseComplianceReport,
    PhaseRequirement,
    Room,
    StandardsViolation,
)


def check_standards_compliance(
    project_phase: str,
    requirement: PhaseRequirement,
    rooms: list[Room],
    elements: list[BimElement],
) -> PhaseComplianceReport:
    """Check BIM model compliance against phase-specific modeling standards."""
    violations: list[StandardsViolation] = []

    violations.extend(_check_room_properties(rooms, requirement))
    violations.extend(_check_element_types(elements, requirement))
    violations.extend(_check_element_properties(elements, requirement))

    errors = sum(1 for v in violations if v.severity == "error")
    warnings = sum(1 for v in violations if v.severity == "warning")
    score = max(0, 100 - errors * 10 - warnings * 3)

    violations_by_rule = dict(Counter(v.rule_id for v in violations))

    return PhaseComplianceReport(
        project_phase=project_phase,
        lph=requirement.lph,
        lph_label=requirement.label,
        compliant=len(violations) == 0,
        compliance_score=score,
        violations=violations,
        violations_by_rule=violations_by_rule,
        checked_rooms=len(rooms),
        checked_elements=len(elements),
    )


# Field name → German display name for messages
_ROOM_FIELD_LABELS: dict[str, str] = {
    "name": "name",
    "number": "number",
    "area": "area",
    "height": "height",
    "usage_type": "usage_type",
    "finish_floor": "finish_floor",
    "finish_wall": "finish_wall",
    "finish_ceiling": "finish_ceiling",
}


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    return False


def _check_room_properties(
    rooms: list[Room],
    requirement: PhaseRequirement,
) -> list[StandardsViolation]:
    violations: list[StandardsViolation] = []
    for room in rooms:
        for field in requirement.room_properties_required:
            value = getattr(room, field, None)
            if _is_empty(value):
                violations.append(StandardsViolation(
                    severity="error",
                    rule_id=f"room.missing_{field}",
                    element_id=room.id,
                    element_name=f"{room.name} ({room.number})",
                    message=(
                        f"Raum {room.number} ({room.name}): "
                        f"Feld '{field}' ist leer oder fehlt "
                        f"(erforderlich ab {requirement.label})"
                    ),
                ))
    return violations


def _check_element_types(
    elements: list[BimElement],
    requirement: PhaseRequirement,
) -> list[StandardsViolation]:
    violations: list[StandardsViolation] = []
    present_types = {e.element_type for e in elements}
    for required_type in requirement.element_types_required:
        if required_type not in present_types:
            violations.append(StandardsViolation(
                severity="error",
                rule_id=f"element_type.missing_{required_type.lower()}",
                element_id="model",
                element_name="Gesamtmodell",
                message=(
                    f"Elementtyp '{required_type}' fehlt im Modell "
                    f"(erforderlich ab {requirement.label})"
                ),
            ))
    return violations


def _check_element_properties(
    elements: list[BimElement],
    requirement: PhaseRequirement,
) -> list[StandardsViolation]:
    violations: list[StandardsViolation] = []
    for elem in elements:
        for field in requirement.element_properties_required:
            value = getattr(elem, field, None)
            if _is_empty(value):
                violations.append(StandardsViolation(
                    severity="warning",
                    rule_id=f"element.missing_{field}",
                    element_id=elem.id,
                    element_name=f"{elem.element_type} ({elem.id[:12]})",
                    message=(
                        f"{elem.element_type}-Element ({elem.id[:12]}): "
                        f"Feld '{field}' ist leer oder fehlt "
                        f"(erforderlich ab {requirement.label})"
                    ),
                ))
    return violations
