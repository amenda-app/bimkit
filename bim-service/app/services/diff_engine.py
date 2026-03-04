"""Diff engine for comparing BIM snapshots."""
from __future__ import annotations

from datetime import datetime

from app.models import Snapshot, ChangeEntry, MonitoringAlert
from app.services.project_store import store
from app.services.snapshot_store import snapshot_store


def create_snapshot(project_id: str, label: str) -> Snapshot:
    """Create a snapshot of the current project state from the project store."""
    rooms = store.get_rooms(project_id)
    materials = store.get_materials(project_id)

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

    snapshot_store.save(
        snap,
        rooms=[r.model_dump() for r in rooms],
        materials=[m.model_dump() for m in materials],
    )

    return snap


def get_snapshots(project_id: str) -> list[Snapshot]:
    """List all snapshots for a project."""
    return snapshot_store.list(project_id)


def delete_snapshot(project_id: str, snapshot_id: str) -> bool:
    """Delete a snapshot."""
    return snapshot_store.delete(project_id, snapshot_id)


def compute_diff(snapshot_a_id: str, snapshot_b_id: str, project_id: str = "") -> list[ChangeEntry]:
    """Compare two snapshots and return list of changes."""
    # Try to find the project_id from the snapshot ID if not provided
    if not project_id:
        # snapshot IDs are formatted as snap-{project_id}-{timestamp}
        parts = snapshot_a_id.split("-")
        if len(parts) >= 3:
            project_id = "-".join(parts[1:-1])

    data_a = snapshot_store.load(project_id, snapshot_a_id)
    data_b = snapshot_store.load(project_id, snapshot_b_id)

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


def detect_alerts(project_id: str) -> list[MonitoringAlert]:
    """Detect significant changes between the two most recent snapshots."""
    snapshots = snapshot_store.list(project_id)
    if len(snapshots) < 2:
        return []

    prev = snapshots[-2]
    curr = snapshots[-1]

    alerts: list[MonitoringAlert] = []

    # Room count change
    room_diff = curr.room_count - prev.room_count
    if abs(room_diff) >= 5:
        severity = "critical" if abs(room_diff) >= 20 else "warning"
        direction = "hinzugefügt" if room_diff > 0 else "entfernt"
        alerts.append(MonitoringAlert(
            severity=severity,
            message=f"{abs(room_diff)} Räume {direction} seit letztem Snapshot",
            timestamp=curr.timestamp,
            snapshot_id=curr.id,
            details={"previous": str(prev.room_count), "current": str(curr.room_count)},
        ))
    elif room_diff != 0:
        direction = "hinzugefügt" if room_diff > 0 else "entfernt"
        alerts.append(MonitoringAlert(
            severity="info",
            message=f"{abs(room_diff)} Raum/Räume {direction}",
            timestamp=curr.timestamp,
            snapshot_id=curr.id,
            details={"previous": str(prev.room_count), "current": str(curr.room_count)},
        ))

    # Area change
    area_diff = curr.total_area - prev.total_area
    area_pct = abs(area_diff / prev.total_area * 100) if prev.total_area > 0 else 0
    if area_pct >= 5:
        severity = "critical" if area_pct >= 15 else "warning"
        direction = "gestiegen" if area_diff > 0 else "gesunken"
        alerts.append(MonitoringAlert(
            severity=severity,
            message=f"Gesamtfläche um {area_pct:.1f}% {direction} ({area_diff:+.1f} m²)",
            timestamp=curr.timestamp,
            snapshot_id=curr.id,
            details={"previous": f"{prev.total_area:.1f}", "current": f"{curr.total_area:.1f}"},
        ))

    # Material count change
    mat_diff = curr.material_count - prev.material_count
    if abs(mat_diff) >= 5:
        severity = "warning"
        direction = "hinzugefügt" if mat_diff > 0 else "entfernt"
        alerts.append(MonitoringAlert(
            severity=severity,
            message=f"{abs(mat_diff)} Materialien {direction}",
            timestamp=curr.timestamp,
            snapshot_id=curr.id,
            details={"previous": str(prev.material_count), "current": str(curr.material_count)},
        ))

    return alerts
