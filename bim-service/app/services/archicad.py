"""ArchiCAD JSON API client with mock fallback."""
from __future__ import annotations

import logging

import httpx

from app.models import Project, Room, Area, Material
from app import mock_data

logger = logging.getLogger(__name__)

# Zone properties we need (nonLocalizedName -> our key)
_ZONE_PROPERTY_NAMES: list[tuple[str, str]] = [
    ("Zone_ZoneName", "name"),
    ("Zone_ZoneNumber", "number"),
    ("Zone_NetArea", "area"),
    ("General_Height", "height"),
    ("General_NetVolume", "volume"),
    ("Zone_ZoneCategoryCode", "category"),
    ("General_ElevationToStory", "story_name"),
]

# DCA custom properties for room finishes
_DCA_FINISH_PROPERTIES: list[tuple[list[str], str]] = [
    (["DCA 1758", "Oberfläche_Boden"], "finish_floor"),
    (["DCA 1758", "Oberflächenbeschichtung_Wand"], "finish_wall"),
    (["DCA 1758", "Oberfläche_Decke"], "finish_ceiling"),
]

# DCA room properties
_DCA_ROOM_PROPERTIES: list[tuple[list[str], str]] = [
    (["DCA Berechnung Räume", "Raumname"], "dca_name"),
    (["DCA Berechnung Räume", "DCA Raumnummer"], "dca_number"),
    (["DCA Berechnung Räume", "NUF Bezeichnung nach DIN 277"], "dca_nuf"),
    (["DCA Berechnung Räume", "Lage Raum"], "dca_floor"),
]


class ArchiCADClient:
    """Client for the ArchiCAD JSON API (port 19723)."""

    def __init__(self, host: str = "localhost", port: int = 19723):
        self.base_url = f"http://{host}:{port}"
        self._connected = False
        self._project_id = "archicad-live"
        self._property_ids: dict[str, dict] = {}  # our key -> {"propertyId": {"guid": ...}}
        self._product_info: dict = {}

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
            # Cache product info
            try:
                self._product_info = await self._post("API.GetProductInfo")
            except Exception:
                self._product_info = {}
            # Resolve property IDs upfront
            await self._resolve_property_ids()
        except (httpx.ConnectError, httpx.TimeoutException, Exception):
            self._connected = False
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def _resolve_property_ids(self) -> None:
        """Resolve property names to GUIDs using API.GetPropertyIds."""
        # Resolve built-in properties
        builtin_request = [
            {"type": "BuiltIn", "nonLocalizedName": name}
            for name, _ in _ZONE_PROPERTY_NAMES
        ]
        try:
            result = await self._post("API.GetPropertyIds", {"properties": builtin_request})
            prop_ids = result.get("properties", [])
            for i, (_, key) in enumerate(_ZONE_PROPERTY_NAMES):
                if i < len(prop_ids):
                    self._property_ids[key] = prop_ids[i]
        except Exception as e:
            logger.warning("Failed to resolve built-in property IDs: %s", e)

        # Resolve DCA custom properties
        dca_request = [
            {"type": "UserDefined", "localizedName": names}
            for names, _ in _DCA_FINISH_PROPERTIES + _DCA_ROOM_PROPERTIES
        ]
        try:
            result = await self._post("API.GetPropertyIds", {"properties": dca_request})
            prop_ids = result.get("properties", [])
            all_dca = _DCA_FINISH_PROPERTIES + _DCA_ROOM_PROPERTIES
            for i, (_, key) in enumerate(all_dca):
                if i < len(prop_ids):
                    self._property_ids[key] = prop_ids[i]
        except Exception as e:
            logger.warning("Failed to resolve DCA property IDs: %s", e)

    async def get_projects(self) -> list[Project]:
        """Get project info from the currently open ArchiCAD file."""
        try:
            version = self._product_info.get("version", "?")
            lang = self._product_info.get("languageCode", "")

            # Get zone count to estimate total area later
            name = f"ArchiCAD {version} Projekt"
            if lang:
                name += f" ({lang})"

            return [Project(
                id=self._project_id,
                name=name,
                address="Live-Verbindung",
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

            # Build property request from resolved IDs
            prop_request = []
            prop_keys = []
            for key, pid in self._property_ids.items():
                prop_request.append(pid)
                prop_keys.append(key)

            if not prop_request:
                logger.warning("No property IDs resolved, cannot extract zone data")
                return []

            # Get property values for all zone elements
            props_result = await self._post(
                "API.GetPropertyValuesOfElements",
                {
                    "elements": element_ids,
                    "properties": prop_request,
                },
            )

            rooms: list[Room] = []
            for i, elem_data in enumerate(props_result.get("propertyValuesForElements", [])):
                elem_id = element_ids[i].get("elementId", {}).get("guid", f"zone-{i}")
                values = self._extract_property_values(elem_data, prop_keys)

                name = values.get("dca_name") or values.get("name", "Unbenannt")
                number = values.get("dca_number") or values.get("number", f"Z-{i+1:03d}")
                area = values.get("area", 0.0)
                height = values.get("height", 0.0)
                volume = values.get("volume", area * height if area and height else 0.0)
                category = values.get("dca_nuf") or values.get("category", "NUF 1")
                floor = values.get("dca_floor") or values.get("story_name", "Unbekannt")

                # Convert story elevation to floor name if it's a number
                if isinstance(floor, (int, float)):
                    floor = f"Ebene {floor}"

                rooms.append(Room(
                    id=f"room-ac-{elem_id}",
                    number=str(number),
                    name=str(name),
                    floor=str(floor),
                    area=round(float(area), 2) if isinstance(area, (int, float)) else 0.0,
                    height=round(float(height), 2) if isinstance(height, (int, float)) else 0.0,
                    volume=round(float(volume), 2) if isinstance(volume, (int, float)) else 0.0,
                    usage_type=str(category),
                    finish_floor=str(values.get("finish_floor", "—")),
                    finish_wall=str(values.get("finish_wall", "—")),
                    finish_ceiling=str(values.get("finish_ceiling", "—")),
                ))

            return rooms
        except Exception as e:
            logger.warning("Failed to get rooms from ArchiCAD: %s", e)
            return []

    def _extract_property_values(self, elem_data: dict, prop_keys: list[str]) -> dict[str, str | float]:
        """Extract property values into a flat dict keyed by our property keys."""
        values: dict[str, str | float] = {}
        prop_values = elem_data.get("propertyValues", [])

        for i, pv in enumerate(prop_values):
            if i >= len(prop_keys):
                break
            key = prop_keys[i]
            pval = pv.get("propertyValue", {})
            status = pval.get("status", "")
            if status == "notAvailable" or status == "notEvaluated":
                continue
            val = pval.get("value", "")
            val = self._unwrap_value(val)
            if val is not None and val != "":
                values[key] = val

        return values

    @staticmethod
    def _unwrap_value(val) -> str | float | None:
        """Unwrap ArchiCAD property value from nested dict/list structures."""
        if val is None:
            return None
        # {"type": "displayValue", "displayValue": "Natursteinbelag"}
        if isinstance(val, dict):
            if "displayValue" in val:
                return val["displayValue"]
            if "value" in val:
                return val["value"]
            return str(val)
        # [{"enumValueId": {"type": "displayValue", "displayValue": "k. A"}}]
        if isinstance(val, list):
            parts = []
            for item in val:
                if isinstance(item, dict):
                    evid = item.get("enumValueId", item)
                    if isinstance(evid, dict) and "displayValue" in evid:
                        parts.append(evid["displayValue"])
                    elif isinstance(evid, dict) and "nonLocalizedValue" in evid:
                        parts.append(evid["nonLocalizedValue"])
                    else:
                        parts.append(str(evid))
                else:
                    parts.append(str(item))
            return ", ".join(parts) if parts else None
        return val

    async def get_areas(self, project_id: str) -> list[Area]:
        """Derive areas from rooms."""
        rooms = await self.get_rooms(project_id)
        return mock_data._areas_for_project(project_id, rooms)

    async def get_all_elements(self) -> list[dict]:
        """Get all element IDs and types in the model."""
        element_types = ["Wall", "Slab", "Door", "Window", "Column", "Roof", "Beam", "Zone"]
        all_elements: list[dict] = []
        for elem_type in element_types:
            try:
                result = await self._post(
                    "API.GetElementsByType",
                    {"elementType": elem_type},
                )
                for elem in result.get("elements", []):
                    elem["type"] = elem_type
                    all_elements.append(elem)
            except Exception as e:
                logger.warning("Failed to get elements of type %s: %s", elem_type, e)
        return all_elements

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
            attr_ids = result.get("attributeIds", result.get("attributes", []))
            if not attr_ids:
                return []

            # Fetch actual material names via GetBuildingMaterialAttributes
            # Process in batches of 50 to avoid timeouts
            materials: list[Material] = []
            batch_size = 50
            for batch_start in range(0, len(attr_ids), batch_size):
                batch = attr_ids[batch_start:batch_start + batch_size]
                try:
                    detail_result = await self._post(
                        "API.GetBuildingMaterialAttributes",
                        {"attributeIds": batch},
                    )
                    attrs = detail_result.get("attributes", [])
                    for j, attr_data in enumerate(attrs):
                        bm = attr_data.get("buildingMaterialAttribute", {})
                        name = bm.get("name", f"Baustoff {batch_start + j + 1}")
                        mat_id = bm.get("id", "")
                        guid = bm.get("attributeId", {}).get("guid", "")

                        # Classify category based on material ID prefix
                        category = self._classify_material(name, mat_id)

                        materials.append(Material(
                            id=f"mat-ac-{batch_start + j + 1:03d}",
                            name=name,
                            category=category,
                            quantity=0.0,
                            unit="m²",
                            manufacturer="—",
                            product=mat_id or "—",
                        ))
                except Exception as e:
                    logger.warning("Failed to get material details for batch %d: %s", batch_start, e)

            return materials
        except Exception as e:
            logger.warning("Failed to get materials from ArchiCAD: %s", e)
            return []

    @staticmethod
    def _classify_material(name: str, mat_id: str) -> str:
        """Classify a building material into a category based on name/id."""
        lower = name.lower()
        if any(k in lower for k in ("beton", "stb", "stahlbeton")):
            return "Wand"
        if any(k in lower for k in ("mauerwerk", "ziegel", "kalksand", "porenbeton", "hlz")):
            return "Wand"
        if any(k in lower for k in ("gips", "trockenbau", "gk")):
            return "Wand"
        if any(k in lower for k in ("dämm", "isolier", "mineral", "eps", "xps", "wdvs")):
            return "Wand"
        if any(k in lower for k in ("estrich", "boden", "parkett", "fliese", "linoleum", "teppich")):
            return "Boden"
        if any(k in lower for k in ("decke", "akustik")):
            return "Decke"
        if any(k in lower for k in ("fenster", "glas", "verglasung")):
            return "Fenster"
        if any(k in lower for k in ("tür", "tor")):
            return "Tür"
        if any(k in lower for k in ("holz", "bsh", "fsh", "kvh")):
            return "Wand"
        if any(k in lower for k in ("stahl", "metall", "alu")):
            return "Wand"
        if any(k in lower for k in ("putz", "farbe", "beschicht", "anstrich")):
            return "Wand"
        return "Sonstiges"


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
