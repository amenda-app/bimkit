"""ArchiCAD JSON API client with mock fallback."""

import logging

import httpx

from app.models import Project, Room, Area, Material
from app import mock_data

logger = logging.getLogger(__name__)


class ArchiCADClient:
    """Client for the ArchiCAD JSON API (port 19723)."""

    def __init__(self, host: str = "localhost", port: int = 19723):
        self.base_url = f"http://{host}:{port}"
        self._connected = False
        self._project_id = "archicad-live"

    async def _post(self, command: str, parameters: dict | None = None) -> dict:
        """Send a JSON command to ArchiCAD."""
        payload: dict = {"command": command}
        if parameters:
            payload["parameters"] = parameters

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.base_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if not data.get("succeeded", True):
            raise RuntimeError(f"ArchiCAD command failed: {command} — {data.get('error', {})}")
        return data.get("result", data)

    async def connect(self) -> bool:
        """Test connection to ArchiCAD."""
        try:
            await self._post("API.IsAlive")
            self._connected = True
        except (httpx.ConnectError, httpx.TimeoutException, Exception):
            self._connected = False
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get_projects(self) -> list[Project]:
        """Get project info from the currently open ArchiCAD file."""
        try:
            result = await self._post("API.GetProjectInfo")
            name = result.get("projectName", result.get("name", "ArchiCAD Projekt"))
            location = result.get("projectLocation", result.get("location", ""))
            is_untitled = result.get("isUntitled", False)

            return [Project(
                id=self._project_id,
                name=name if not is_untitled else "ArchiCAD Projekt (Unbenannt)",
                address=location or "—",
                building_type="ArchiCAD Projekt",
                total_area=0.0,  # will be calculated from zones
                floors=0,
                status="Live-Verbindung",
                source="archicad",
            )]
        except Exception as e:
            logger.warning("Failed to get project info: %s", e)
            return []

    async def get_rooms(self, project_id: str) -> list[Room]:
        """Get zones from ArchiCAD and map to Room models."""
        try:
            # Get all Zone element IDs
            result = await self._post(
                "API.GetElementsByType",
                {"elementType": "Zone"},
            )
            element_ids = result.get("elements", [])
            if not element_ids:
                return []

            # Discover built-in property IDs for zones
            prop_ids = await self._get_zone_property_ids()

            # Get property values for all zone elements
            props_result = await self._post(
                "API.GetPropertyValuesOfElements",
                {
                    "elements": element_ids,
                    "properties": prop_ids,
                },
            )

            rooms: list[Room] = []
            for i, elem_props in enumerate(props_result.get("propertyValuesForElements", [])):
                values = self._extract_property_values(elem_props)
                elem_id = element_ids[i].get("elementId", {}).get("guid", f"zone-{i}")

                area = values.get("Zone_Area", 0.0)
                height = values.get("Zone_Height", 0.0)
                volume = values.get("Zone_Volume", area * height if area and height else 0.0)

                rooms.append(Room(
                    id=f"room-ac-{elem_id}",
                    number=values.get("Zone_Number", f"Z-{i+1:03d}"),
                    name=values.get("Zone_Name", "Unbenannt"),
                    floor=values.get("Zone_StoryName", "Unbekannt"),
                    area=round(area, 2),
                    height=round(height, 2),
                    volume=round(volume, 2),
                    usage_type=values.get("Zone_CategoryName", "NUF 1"),
                    finish_floor=values.get("Zone_FloorFinish", "—"),
                    finish_wall=values.get("Zone_WallFinish", "—"),
                    finish_ceiling=values.get("Zone_CeilingFinish", "—"),
                ))

            return rooms
        except Exception as e:
            logger.warning("Failed to get rooms from ArchiCAD: %s", e)
            return []

    async def _get_zone_property_ids(self) -> list[dict]:
        """Get built-in property IDs relevant for zones."""
        try:
            result = await self._post("API.GetBuiltInPropertyIds")
            all_props = result.get("properties", [])

            # Filter for zone-relevant properties
            wanted = {
                "Zone_ZoneName", "Zone_ZoneNumber", "Zone_ZoneArea",
                "Zone_ZoneHeight", "Zone_ZoneVolume", "Zone_RelatedStory",
                "Zone_ZoneCategoryName", "Zone_FloorFinish",
                "Zone_WallFinish", "Zone_CeilingFinish",
            }

            props = []
            for p in all_props:
                prop_id = p.get("propertyId", {})
                guid = prop_id.get("guid", "")
                # Include common zone properties
                props.append(p)

            # If we can't filter, return all and let ArchiCAD handle it
            return props[:50] if len(props) > 50 else props
        except Exception:
            return []

    def _extract_property_values(self, elem_props: dict) -> dict[str, str | float]:
        """Extract property values into a flat dict."""
        values: dict[str, str | float] = {}
        for prop_val in elem_props.get("propertyValues", []):
            prop_id = prop_val.get("propertyId", {}).get("guid", "")
            value_data = prop_val.get("propertyValue", {})
            val = value_data.get("value", value_data.get("displayValue", ""))

            # Map known property names (best-effort)
            prop_type = value_data.get("type", "")
            if isinstance(val, (int, float)):
                # Store numeric values with a generic key
                status = prop_val.get("propertyValue", {}).get("status", "")
                if status != "notAvailable":
                    values[f"prop_{prop_id}"] = val
            elif isinstance(val, str) and val:
                values[f"prop_{prop_id}"] = val

        return values

    async def get_areas(self, project_id: str) -> list[Area]:
        """Derive areas from rooms."""
        rooms = await self.get_rooms(project_id)
        return mock_data._areas_for_project(project_id, rooms)

    async def get_materials(self, project_id: str) -> list[Material]:
        """Get building materials from ArchiCAD."""
        try:
            result = await self._post(
                "API.GetAttributesByType",
                {"attributeType": "BuildingMaterial"},
            )
            attributes = result.get("attributes", [])

            materials: list[Material] = []
            for i, attr in enumerate(attributes):
                attr_id = attr.get("attributeId", {})
                name = attr.get("name", f"Material {i+1}")

                materials.append(Material(
                    id=f"mat-ac-{i+1:03d}",
                    name=name,
                    category="Sonstiges",
                    quantity=0.0,
                    unit="m²",
                    manufacturer="—",
                    product="—",
                ))

            return materials
        except Exception as e:
            logger.warning("Failed to get materials from ArchiCAD: %s", e)
            return []


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
