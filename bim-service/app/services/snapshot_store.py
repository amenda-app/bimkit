"""Persistent JSON file storage for BIM snapshots."""
from __future__ import annotations

import json
import os
from pathlib import Path

from app.models import Snapshot, SnapshotTrendPoint


# Storage root — relative to bim-service/ directory
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "snapshots"


class SnapshotStore:
    """Persists snapshots as JSON files under data/snapshots/{project_id}/."""

    def __init__(self, data_dir: Path = _DATA_DIR) -> None:
        self._dir = data_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        d = self._dir / project_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(
        self,
        snapshot: Snapshot,
        rooms: list[dict],
        materials: list[dict],
    ) -> None:
        """Save a snapshot with its data to a JSON file."""
        payload = {
            "snapshot": snapshot.model_dump(),
            "rooms": rooms,
            "materials": materials,
        }
        path = self._project_dir(snapshot.project_id) / f"{snapshot.id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    def load(self, project_id: str, snapshot_id: str) -> dict | None:
        """Load a snapshot file. Returns {snapshot, rooms, materials} or None."""
        path = self._project_dir(project_id) / f"{snapshot_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def list(self, project_id: str) -> list[Snapshot]:
        """List all snapshots for a project, sorted by timestamp."""
        d = self._dir / project_id
        if not d.exists():
            return []

        snapshots: list[Snapshot] = []
        for f in d.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                snapshots.append(Snapshot(**data["snapshot"]))
            except (json.JSONDecodeError, KeyError):
                continue

        snapshots.sort(key=lambda s: s.timestamp)
        return snapshots

    def delete(self, project_id: str, snapshot_id: str) -> bool:
        """Delete a snapshot file. Returns True if deleted."""
        path = self._project_dir(project_id) / f"{snapshot_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def get_trends(self, project_id: str) -> list[SnapshotTrendPoint]:
        """Return trend data points from all snapshots for a project."""
        snapshots = self.list(project_id)
        return [
            SnapshotTrendPoint(
                timestamp=s.timestamp,
                label=s.label,
                room_count=s.room_count,
                material_count=s.material_count,
                total_area=s.total_area,
            )
            for s in snapshots
        ]

    def count(self, project_id: str | None = None) -> int:
        """Count snapshots, optionally filtered by project."""
        if project_id:
            d = self._dir / project_id
            if not d.exists():
                return 0
            return len(list(d.glob("*.json")))
        total = 0
        if self._dir.exists():
            for d in self._dir.iterdir():
                if d.is_dir():
                    total += len(list(d.glob("*.json")))
        return total


# Singleton instance
snapshot_store = SnapshotStore()
