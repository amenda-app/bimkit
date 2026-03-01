"""ArchiCAD API client with mock fallback."""

import httpx

from app.models import Project, Room, Area, Material
from app import mock_data


class ArchiCADClient:
    """Client for the ArchiCAD JSON API (port 19723)."""

    def __init__(self, host: str = "localhost", port: int = 19723):
        self.base_url = f"http://{host}:{port}"
        self._connected = False

    async def connect(self) -> bool:
        """Test connection to ArchiCAD."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.base_url)
                self._connected = resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            self._connected = False
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get_projects(self) -> list[Project]:
        # TODO: Implement real ArchiCAD API call
        raise NotImplementedError("Real ArchiCAD integration not yet available")

    async def get_rooms(self, project_id: str) -> list[Room]:
        raise NotImplementedError("Real ArchiCAD integration not yet available")

    async def get_areas(self, project_id: str) -> list[Area]:
        raise NotImplementedError("Real ArchiCAD integration not yet available")

    async def get_materials(self, project_id: str) -> list[Material]:
        raise NotImplementedError("Real ArchiCAD integration not yet available")


class MockArchiCADClient:
    """Mock client returning realistic test data."""

    def __init__(self):
        self._connected = True

    async def connect(self) -> bool:
        self._connected = True
        return True

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get_projects(self) -> list[Project]:
        return mock_data.get_projects()

    async def get_rooms(self, project_id: str) -> list[Room]:
        return mock_data.get_rooms(project_id)

    async def get_areas(self, project_id: str) -> list[Area]:
        return mock_data.get_areas(project_id)

    async def get_materials(self, project_id: str) -> list[Material]:
        return mock_data.get_materials(project_id)


async def create_client(host: str = "localhost", port: int = 19723) -> ArchiCADClient | MockArchiCADClient:
    """Create an ArchiCAD client, falling back to mock if connection fails."""
    client = ArchiCADClient(host, port)
    connected = await client.connect()
    if connected:
        return client
    return MockArchiCADClient()
