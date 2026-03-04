"""Load modeling standards from YAML config."""

from functools import lru_cache
from pathlib import Path

import yaml

from app.models import PhaseRequirement

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "modeling_standards.yaml"


@lru_cache(maxsize=1)
def _load_raw() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_phase_mapping() -> dict[str, int]:
    return _load_raw()["phase_mapping"]


def resolve_lph_for_status(status: str) -> int | None:
    return get_phase_mapping().get(status)


def get_requirement(lph: int) -> PhaseRequirement | None:
    phases = _load_raw().get("phases", {})
    phase = phases.get(lph)
    if phase is None:
        return None
    return PhaseRequirement(
        lph=lph,
        label=phase["label"],
        room_properties_required=phase.get("room_properties", {}).get("required", []),
        room_properties_optional=phase.get("room_properties", {}).get("optional", []),
        element_types_required=phase.get("element_types_required", []),
        element_properties_required=phase.get("element_properties", {}).get("required", []),
    )
