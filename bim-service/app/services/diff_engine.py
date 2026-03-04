"""Diff engine for comparing BIM snapshots."""

from datetime import datetime, timedelta
import copy
import random

from app.models import Room, Material, Snapshot, ChangeEntry


# In-memory snapshot storage
_snapshots: dict[str, list[Snapshot]] = {}
_snapshot_data: dict[str, dict] = {}  # snapshot_id -> {rooms: [...], materials: [...]}


def _seed_demo_snapshots() -> None:
    """Pre-seed one demo snapshot per project with slight variations."""
    if _snapshots:
        return  # Already seeded

    for project_id in ("museum", "wohnhaus", "schule"):
        from app import mock_data

        rooms = mock_data.get_rooms(project_id)
        materials = mock_data.get_materials(project_id)

        # Create a "previous" snapshot with small variations
        old_rooms = []
        for r in rooms:
            rd = r.model_dump()
            # Slight area variation on some rooms
            if random.Random(hash(r.id)).random() < 0.15:
                rd["area"] = round(rd["area"] * 0.95, 1)
                rd["volume"] = round(rd["area"] * rd["height"], 1)
            old_rooms.append(rd)

        # Remove last 2 rooms (simulating "added" rooms in current)
        if len(old_rooms) > 2:
            old_rooms = old_rooms[:-2]

        old_materials = [m.model_dump() for m in materials]
        # Slightly different quantities on some materials
        for md in old_materials:
            if random.Random(hash(md["id"])).random() < 0.2:
                md["quantity"] = round(md["quantity"] * 0.9, 1)

        snap_id = f"snap-{project_id}-initial"
        ts = (datetime.now() - timedelta(days=14)).isoformat()

        snap = Snapshot(
            id=snap_id,
            project_id=project_id,
            timestamp=ts,
            label="Ersterfassung",
            room_count=len(old_rooms),
            material_count=len(old_materials),
            total_area=round(sum(r["area"] for r in old_rooms), 1),
        )

        _snapshots.setdefault(project_id, []).append(snap)
        _snapshot_data[snap_id] = {"rooms": old_rooms, "materials": old_materials}


def create_snapshot(project_id: str, label: str) -> Snapshot:
    """Create a snapshot of the current project state."""
    _seed_demo_snapshots()

    from app import mock_data

    rooms = mock_data.get_rooms(project_id)
    materials = mock_data.get_materials(project_id)

    snap_id = f"snap-{project_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    snap = Snapshot(
        id=snap_id,
        project_id=project_id,
        timestamp=datetime.now().isoformat(),
        label=label,
        room_count=len(rooms),
        material_count=len(materials),
        total_area=round(sum(r.area for r in rooms), 1),
    )

    _snapshots.setdefault(project_id, []).append(snap)
    _snapshot_data[snap_id] = {
        "rooms": [r.model_dump() for r in rooms],
        "materials": [m.model_dump() for m in materials],
    }

    return snap


def get_snapshots(project_id: str) -> list[Snapshot]:
    """List all snapshots for a project."""
    _seed_demo_snapshots()
    return _snapshots.get(project_id, [])


def compute_diff(snapshot_a_id: str, snapshot_b_id: str) -> list[ChangeEntry]:
    """Compare two snapshots and return list of changes."""
    _seed_demo_snapshots()

    data_a = _snapshot_data.get(snapshot_a_id)
    data_b = _snapshot_data.get(snapshot_b_id)

    if not data_a or not data_b:
        return []

    changes: list[ChangeEntry] = []

    # Compare rooms
    rooms_a = {r["id"]: r for r in data_a["rooms"]}
    rooms_b = {r["id"]: r for r in data_b["rooms"]}

    for rid in set(rooms_a.keys()) | set(rooms_b.keys()):
        if rid not in rooms_a:
            rb = rooms_b[rid]
            changes.append(ChangeEntry(
                type="added", entity_type="room", entity_id=rid,
                field="", old_value=None, new_value=rb.get("name", rid),
            ))
        elif rid not in rooms_b:
            ra = rooms_a[rid]
            changes.append(ChangeEntry(
                type="removed", entity_type="room", entity_id=rid,
                field="", old_value=ra.get("name", rid), new_value=None,
            ))
        else:
            ra, rb = rooms_a[rid], rooms_b[rid]
            for field in ("name", "area", "height", "usage_type", "finish_floor", "finish_wall", "finish_ceiling"):
                if ra.get(field) != rb.get(field):
                    changes.append(ChangeEntry(
                        type="changed", entity_type="room", entity_id=rid,
                        field=field,
                        old_value=str(ra.get(field)),
                        new_value=str(rb.get(field)),
                    ))

    # Compare materials
    mats_a = {m["id"]: m for m in data_a["materials"]}
    mats_b = {m["id"]: m for m in data_b["materials"]}

    for mid in set(mats_a.keys()) | set(mats_b.keys()):
        if mid not in mats_a:
            mb = mats_b[mid]
            changes.append(ChangeEntry(
                type="added", entity_type="material", entity_id=mid,
                field="", old_value=None, new_value=mb.get("name", mid),
            ))
        elif mid not in mats_b:
            ma = mats_a[mid]
            changes.append(ChangeEntry(
                type="removed", entity_type="material", entity_id=mid,
                field="", old_value=ma.get("name", mid), new_value=None,
            ))
        else:
            ma, mb = mats_a[mid], mats_b[mid]
            for field in ("quantity", "manufacturer", "product"):
                if ma.get(field) != mb.get(field):
                    changes.append(ChangeEntry(
                        type="changed", entity_type="material", entity_id=mid,
                        field=field,
                        old_value=str(ma.get(field)),
                        new_value=str(mb.get(field)),
                    ))

    return changes
