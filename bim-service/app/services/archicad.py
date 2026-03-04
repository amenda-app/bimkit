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

    async def _post(self, command: str, parameters: dict | None = None, timeout: float = 10.0) -> dict:
        """Send a JSON command to ArchiCAD."""
        payload: dict = {"command": command}
        if parameters:
            payload["parameters"] = parameters

        async with httpx.AsyncClient(timeout=timeout) as client:
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

    async def get_all_elements(self) -> list[dict]:
        """Get all element IDs and types in the model."""
        result = await self._post("API.GetAllElements")
        return result.get("elements", [])

    async def get_element_details(self, element_ids: list[dict]) -> list[dict]:
        """Get element details (layer, story) for given element IDs."""
        result = await self._post(
            "API.GetDetailsOfElements",
            {"elements": element_ids},
        )
        return result.get("detailsOfElements", [])

    async def get_classifications(self, element_ids: list[dict]) -> list[dict]:
        """Get IFC classification per element."""
        result = await self._post(
            "API.GetClassificationsOfElements",
            {"elements": element_ids},
        )
        return result.get("elementClassifications", [])

    async def get_collisions(self, group1: list[dict], group2: list[dict]) -> list[dict]:
        """Run clash detection between two element groups."""
        result = await self._post(
            "API.GetCollisions",
            {"elements1": group1, "elements2": group2},
            timeout=60.0,
        )
        return result.get("collisions", [])

    async def get_3d_bounding_boxes(self, element_ids: list[dict]) -> list[dict]:
        """Get 3D bounding boxes for elements."""
        result = await self._post(
            "API.Get3DBoundingBoxes",
            {"elements": element_ids},
            timeout=30.0,
        )
        return result.get("boundingBoxes3D", [])

    async def get_stories(self) -> list[dict]:
        """Get story/level definitions."""
        result = await self._post("API.GetStories")
        return result.get("stories", [])

    async def get_zone_boundaries(self, zone_ids: list[dict]) -> list[dict]:
        """Get zone boundary integrity data."""
        result = await self._post(
            "API.GetZoneBoundaries",
            {"zones": zone_ids},
        )
        return result.get("zoneBoundaries", [])

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

    async def get_all_elements(self) -> list[dict]:
        """Return ~50 mock elements across multiple types."""
        elements = []
        types_and_counts = [
            ("Wall", 15), ("Slab", 8), ("Door", 6), ("Window", 6),
            ("Column", 5), ("Zone", 5), ("Beam", 3), ("Roof", 2),
        ]
        idx = 0
        for elem_type, count in types_and_counts:
            for i in range(count):
                idx += 1
                elements.append({
                    "elementId": {"guid": f"mock-{elem_type.lower()}-{i+1:03d}"},
                    "type": elem_type,
                })
        return elements

    async def get_element_details(self, element_ids: list[dict]) -> list[dict]:
        stories = ["EG", "OG1", "OG2"]
        details = []
        for i, elem in enumerate(element_ids):
            details.append({
                "elementId": elem.get("elementId", elem),
                "story": stories[i % len(stories)],
                "layer": f"A-{elem.get('type', 'General')}" if i % 8 != 0 else "",
            })
        return details

    async def get_classifications(self, element_ids: list[dict]) -> list[dict]:
        classifications = []
        for i, elem in enumerate(element_ids):
            # 3 elements without classification
            if i in (5, 18, 35):
                classifications.append({
                    "elementId": elem.get("elementId", elem),
                    "classificationId": None,
                    "classificationName": "",
                })
            else:
                elem_type = elem.get("type", "BuildingElement")
                classifications.append({
                    "elementId": elem.get("elementId", elem),
                    "classificationId": {"guid": f"ifc-{elem_type.lower()}"},
                    "classificationName": f"IfcBuildingElement/{elem_type}",
                })
        return classifications

    async def get_collisions(self, group1: list[dict], group2: list[dict]) -> list[dict]:
        """Return 2 collision pairs."""
        collisions = []
        if len(group1) >= 2 and len(group2) >= 2:
            collisions.append({
                "element1": group1[0].get("elementId", group1[0]),
                "element2": group2[1].get("elementId", group2[1]),
            })
            collisions.append({
                "element1": group1[1].get("elementId", group1[1]),
                "element2": group2[0].get("elementId", group2[0]),
            })
        return collisions

    async def get_3d_bounding_boxes(self, element_ids: list[dict]) -> list[dict]:
        boxes = []
        for i, elem in enumerate(element_ids):
            if i == 7:
                # Zero-volume bounding box
                boxes.append({
                    "elementId": elem.get("elementId", elem),
                    "boundingBox3D": {
                        "xMin": 5.0, "yMin": 3.0, "zMin": 0.0,
                        "xMax": 5.0, "yMax": 3.0, "zMax": 0.0,
                    },
                })
            elif i == 3:
                # Unreasonably large volume
                boxes.append({
                    "elementId": elem.get("elementId", elem),
                    "boundingBox3D": {
                        "xMin": 0.0, "yMin": 0.0, "zMin": 0.0,
                        "xMax": 500.0, "yMax": 500.0, "zMax": 50.0,
                    },
                })
            else:
                boxes.append({
                    "elementId": elem.get("elementId", elem),
                    "boundingBox3D": {
                        "xMin": float(i), "yMin": 0.0, "zMin": 0.0,
                        "xMax": float(i) + 4.0, "yMax": 3.0, "zMax": 3.0,
                    },
                })
        return boxes

    async def get_stories(self) -> list[dict]:
        return [
            {"name": "EG", "index": 0, "elevation": 0.0},
            {"name": "OG1", "index": 1, "elevation": 3.2},
            {"name": "OG2", "index": 2, "elevation": 6.4},
        ]

    async def get_zone_boundaries(self, zone_ids: list[dict]) -> list[dict]:
        boundaries = []
        for i, zone in enumerate(zone_ids):
            if i == 0:
                # Zone with 0 boundaries
                boundaries.append({
                    "zoneId": zone.get("elementId", zone),
                    "zoneName": "Lager (fehlend)",
                    "boundaryCount": 0,
                })
            elif i == 1:
                # Zone with only 2 boundaries
                boundaries.append({
                    "zoneId": zone.get("elementId", zone),
                    "zoneName": "Flur (unvollständig)",
                    "boundaryCount": 2,
                })
            else:
                boundaries.append({
                    "zoneId": zone.get("elementId", zone),
                    "zoneName": f"Zone {i+1}",
                    "boundaryCount": 4,
                })
        return boundaries


async def create_client(host: str = "localhost", port: int = 19723) -> ArchiCADClient | MockArchiCADClient:
    """Create an ArchiCAD client, falling back to mock if connection fails."""
    client = ArchiCADClient(host, port)
    connected = await client.connect()
    if connected:
        return client
    return MockArchiCADClient()
