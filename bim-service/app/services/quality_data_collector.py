"""Orchestrates Tapir API calls and converts raw JSON to typed models."""

import logging

from app.models import BimElement, BoundingBox3D, Collision, StoryInfo, ZoneBoundary

logger = logging.getLogger(__name__)


async def collect_quality_data(client) -> dict:
    """Collect quality-relevant data from the ArchiCAD/Mock client.

    Returns a dict with keys: elements, collisions, bounding_boxes, stories, zone_boundaries.
    Each step is wrapped in try/except for graceful degradation.
    """
    result: dict = {}

    # 1. Get all elements
    all_elements_raw: list[dict] = []
    try:
        all_elements_raw = await client.get_all_elements()
        elements = _parse_elements(all_elements_raw)
        result["elements"] = elements
    except Exception as e:
        logger.warning("Failed to collect elements: %s", e)
        result["elements"] = []

    if not all_elements_raw:
        return {
            "elements": [], "collisions": [], "bounding_boxes": [],
            "stories": [], "zone_boundaries": [],
        }

    # 2. Enrich elements with details and classifications
    try:
        details = await client.get_element_details(all_elements_raw)
        classifications = await client.get_classifications(all_elements_raw)
        _enrich_elements(result["elements"], details, classifications)
    except Exception as e:
        logger.warning("Failed to enrich element details: %s", e)

    # 3. Collisions — walls vs. slabs as a representative check
    try:
        walls = [e for e in all_elements_raw if e.get("type") == "Wall"]
        slabs = [e for e in all_elements_raw if e.get("type") == "Slab"]
        if walls and slabs:
            collisions_raw = await client.get_collisions(walls, slabs)
            result["collisions"] = _parse_collisions(collisions_raw, all_elements_raw)
        else:
            result["collisions"] = []
    except Exception as e:
        logger.warning("Failed to collect collisions: %s", e)
        result["collisions"] = []

    # 4. Bounding boxes
    try:
        boxes_raw = await client.get_3d_bounding_boxes(all_elements_raw)
        result["bounding_boxes"] = _parse_bounding_boxes(boxes_raw, all_elements_raw)
    except Exception as e:
        logger.warning("Failed to collect bounding boxes: %s", e)
        result["bounding_boxes"] = []

    # 5. Stories
    try:
        stories_raw = await client.get_stories()
        result["stories"] = [
            StoryInfo(
                name=s.get("name", ""),
                index=s.get("index", 0),
                elevation=s.get("elevation", 0.0),
            )
            for s in stories_raw
        ]
    except Exception as e:
        logger.warning("Failed to collect stories: %s", e)
        result["stories"] = []

    # 6. Zone boundaries
    try:
        zones = [e for e in all_elements_raw if e.get("type") == "Zone"]
        if zones:
            zb_raw = await client.get_zone_boundaries(zones)
            result["zone_boundaries"] = _parse_zone_boundaries(zb_raw)
        else:
            result["zone_boundaries"] = []
    except Exception as e:
        logger.warning("Failed to collect zone boundaries: %s", e)
        result["zone_boundaries"] = []

    return result


def _parse_elements(raw: list[dict]) -> list[BimElement]:
    elements = []
    for e in raw:
        guid = e.get("elementId", {}).get("guid", "")
        elements.append(BimElement(
            id=guid,
            element_type=e.get("type", "Unknown"),
            story="",
            layer="",
            classification="",
        ))
    return elements


def _enrich_elements(
    elements: list[BimElement],
    details: list[dict],
    classifications: list[dict],
) -> None:
    for i, elem in enumerate(elements):
        if i < len(details):
            elem.story = details[i].get("story", "")
            elem.layer = details[i].get("layer", "")
        if i < len(classifications):
            elem.classification = classifications[i].get("classificationName", "")


def _parse_collisions(raw: list[dict], all_elements: list[dict]) -> list[Collision]:
    type_map: dict[str, str] = {}
    for e in all_elements:
        guid = e.get("elementId", {}).get("guid", "")
        type_map[guid] = e.get("type", "Unknown")

    collisions = []
    for c in raw:
        e1 = c.get("element1", {})
        e2 = c.get("element2", {})
        e1_id = e1.get("guid", "") if isinstance(e1, dict) else str(e1)
        e2_id = e2.get("guid", "") if isinstance(e2, dict) else str(e2)
        collisions.append(Collision(
            element1_id=e1_id,
            element1_type=type_map.get(e1_id, "Unknown"),
            element2_id=e2_id,
            element2_type=type_map.get(e2_id, "Unknown"),
        ))
    return collisions


def _parse_bounding_boxes(raw: list[dict], all_elements: list[dict]) -> list[BoundingBox3D]:
    boxes = []
    for i, b in enumerate(raw):
        elem_id_data = b.get("elementId", {})
        elem_id = elem_id_data.get("guid", "") if isinstance(elem_id_data, dict) else str(elem_id_data)
        if not elem_id and i < len(all_elements):
            elem_id = all_elements[i].get("elementId", {}).get("guid", "")

        bb = b.get("boundingBox3D", {})
        boxes.append(BoundingBox3D(
            element_id=elem_id,
            x_min=bb.get("xMin", 0.0),
            y_min=bb.get("yMin", 0.0),
            z_min=bb.get("zMin", 0.0),
            x_max=bb.get("xMax", 0.0),
            y_max=bb.get("yMax", 0.0),
            z_max=bb.get("zMax", 0.0),
        ))
    return boxes


def _parse_zone_boundaries(raw: list[dict]) -> list[ZoneBoundary]:
    boundaries = []
    for zb in raw:
        zone_id_data = zb.get("zoneId", {})
        zone_id = zone_id_data.get("guid", "") if isinstance(zone_id_data, dict) else str(zone_id_data)
        boundaries.append(ZoneBoundary(
            zone_id=zone_id,
            zone_name=zb.get("zoneName", ""),
            boundary_count=zb.get("boundaryCount", 0),
        ))
    return boundaries
