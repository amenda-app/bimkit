"""Auto-snapshot scheduler that periodically captures BIM state."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from app.models import SchedulerStatus
from app.services.diff_engine import create_snapshot
from app.services.snapshot_store import snapshot_store

logger = logging.getLogger(__name__)


class SnapshotScheduler:
    """Background scheduler that creates snapshots at configurable intervals."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._interval_minutes: int = 60
        self._active: bool = False
        self._last_run: datetime | None = None
        self._project_id: str = "archicad-live"
        self._refresh_callback = None  # async callable to refresh ArchiCAD data

    def set_refresh_callback(self, callback) -> None:
        """Set the async callback used to refresh data from ArchiCAD before snapshotting."""
        self._refresh_callback = callback

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    async def _run(self) -> None:
        """Main scheduler loop."""
        while self._active:
            try:
                await asyncio.sleep(self._interval_minutes * 60)
                if not self._active:
                    break

                # Refresh data from ArchiCAD before taking snapshot
                if self._refresh_callback:
                    try:
                        await self._refresh_callback()
                    except Exception as e:
                        logger.warning("Failed to refresh ArchiCAD data: %s", e)

                label = f"Auto-Snapshot {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                create_snapshot(self._project_id, label)
                self._last_run = datetime.now()
                logger.info("Auto-snapshot created: %s", label)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler error: %s", e)

    def start(self, interval_minutes: int = 60) -> None:
        """Start the scheduler. If already running, restarts with new interval."""
        self.stop()
        self._interval_minutes = interval_minutes
        self._active = True
        self._task = asyncio.ensure_future(self._run())
        logger.info("Snapshot scheduler started (interval: %d min)", interval_minutes)

    def stop(self) -> None:
        """Stop the scheduler."""
        self._active = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
        logger.info("Snapshot scheduler stopped")

    def get_status(self) -> SchedulerStatus:
        """Return the current scheduler status."""
        next_run = None
        if self._active and self._last_run:
            next_dt = self._last_run + timedelta(minutes=self._interval_minutes)
            next_run = next_dt.isoformat()
        elif self._active:
            # First run hasn't happened yet — next run is interval from now
            next_dt = datetime.now() + timedelta(minutes=self._interval_minutes)
            next_run = next_dt.isoformat()

        return SchedulerStatus(
            active=self._active,
            interval_minutes=self._interval_minutes,
            last_run=self._last_run.isoformat() if self._last_run else None,
            next_run=next_run,
            snapshot_count=snapshot_store.count(),
        )


# Singleton instance
scheduler = SnapshotScheduler()
