"""Parse IFC files into Room, Material, and Project models using ifcopenshell."""
from __future__ import annotations

import uuid
from collections import defaultdict

import ifcopenshell
import ifcopenshell.util.element

from app.models import Project, Room, Material


# Map common ObjectType / OccupancyType values to DIN 277 categories
_USAGE_TYPE_MAP: dict[str, str] = {
    "office": "NUF 2",
    "büro": "NUF 2",
    "meeting": "NUF 2",
    "besprechung": "NUF 2",
    "residential": "NUF 1",
    "wohnen": "NUF 1",
    "living": "NUF 1",
    "bedroom": "NUF 1",
    "schlafen": "NUF 1",
    "kitchen": "NUF 1",
    "küche": "NUF 1",
    "bathroom": "NUF 7",
    "bad": "NUF 7",
    "wc": "NUF 7",
    "toilet": "NUF 7",
    "storage": "NUF 5",
    "lager": "NUF 5",
    "abstellraum": "NUF 5",
    "corridor": "VF",
    "flur": "VF",
    "hallway": "VF",
    "stairway": "VF",
    "treppenhaus": "VF",
    "elevator": "VF",
    "aufzug": "VF",
    "technical": "TF",
    "technik": "TF",
    "mechanical": "TF",
    "electrical": "TF",
    "server": "TF",
    "parking": "TF",
    "garage": "TF",
    "classroom": "NUF 1",
    "exhibition": "NUF 1",
    "shop": "NUF 1",
    "retail": "NUF 1",
}

# Map IFC element types to material categories
_ELEMENT_CATEGORY_MAP: dict[str, str] = {
    "IfcWall": "Wand",
    "IfcWallStandardCase": "Wand",
    "IfcSlab": "Boden",
    "IfcRoof": "Decke",
    "IfcCovering": "Boden",
    "IfcDoor": "Tür",
    "IfcWindow": "Fenster",
    "IfcColumn": "Wand",
    "IfcBeam": "Decke",
    "IfcStair": "Boden",
    "IfcRailing": "Wand",
    "IfcCurtainWall": "Fenster",
    "IfcPlate": "Wand",
    "IfcMember": "Wand",
}


def _classify_usage(raw: str | None) -> str:
    """Map a raw usage/type string to a DIN 277 category."""
    if not raw:
        return "NUF 1"
    lower = raw.lower().strip()
    for key, value in _USAGE_TYPE_MAP.items():
        if key in lower:
            return value
    return "NUF 1"


def _get_space_quantities(space: ifcopenshell.entity_instance) -> tuple[float, float, float]:
    """Extract area, height, volume from IfcSpace quantity sets."""
    area = 0.0
    height = 0.0
    volume = 0.0

    for rel in getattr(space, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        prop_def = rel.RelatingPropertyDefinition
        if not prop_def.is_a("IfcElementQuantity"):
            continue
        for qty in prop_def.Quantities:
            name = qty.Name if hasattr(qty, "Name") else ""
            if qty.is_a("IfcQuantityArea"):
                if "net" in name.lower() and "floor" in name.lower():
                    area = qty.AreaValue
                elif area == 0.0 and "area" in name.lower():
                    area = qty.AreaValue
            elif qty.is_a("IfcQuantityLength"):
                if "height" in name.lower():
                    height = qty.LengthValue
            elif qty.is_a("IfcQuantityVolume"):
                if "net" in name.lower() or volume == 0.0:
                    volume = qty.VolumeValue

    return area, height, volume


def _get_pset_value(element: ifcopenshell.entity_instance, pset_name: str, prop_name: str) -> str | None:
    """Get a property value from a property set."""
    for rel in getattr(element, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        prop_def = rel.RelatingPropertyDefinition
        if not prop_def.is_a("IfcPropertySet"):
            continue
        if prop_def.Name != pset_name:
            continue
        for prop in prop_def.HasProperties:
            if prop.Name == prop_name and hasattr(prop, "NominalValue") and prop.NominalValue:
                return str(prop.NominalValue.wrappedValue)
    return None


def _get_storey_name(space: ifcopenshell.entity_instance) -> str:
    """Get the parent storey name for a space."""
    for rel in getattr(space, "Decomposes", []):
        if rel.is_a("IfcRelAggregates"):
            parent = rel.RelatingObject
            if parent.is_a("IfcBuildingStorey"):
                return parent.Name or "Unbekannt"
    return "Unbekannt"


def _get_element_materials(
    ifc_file: ifcopenshell.file,
) -> dict[str, tuple[float, str]]:
    """Collect materials from building elements, aggregating quantities by material name.

    Returns dict of material_name -> (total_quantity, unit).
    """
    materials: dict[str, tuple[float, str, str]] = {}  # name -> (qty, unit, category)

    element_types = [
        "IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcDoor",
        "IfcWindow", "IfcColumn", "IfcBeam", "IfcRoof",
        "IfcCovering", "IfcCurtainWall", "IfcStair",
    ]

    for element_type in element_types:
        category = _ELEMENT_CATEGORY_MAP.get(element_type, "Sonstiges")
        for element in ifc_file.by_type(element_type):
            mat_names = _extract_material_names(element)
            if not mat_names:
                continue

            # Try to get element quantity (area or volume)
            qty, unit = _get_element_quantity(element)

            for mat_name in mat_names:
                if mat_name in materials:
                    existing_qty, existing_unit, existing_cat = materials[mat_name]
                    materials[mat_name] = (existing_qty + qty, existing_unit, existing_cat)
                else:
                    materials[mat_name] = (qty, unit, category)

    return materials


def _extract_material_names(element: ifcopenshell.entity_instance) -> list[str]:
    """Extract material names from an element's material associations."""
    names: list[str] = []
    for rel in getattr(element, "HasAssociations", []):
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        mat_select = rel.RelatingMaterial
        if mat_select.is_a("IfcMaterial"):
            names.append(mat_select.Name or "Unbekannt")
        elif mat_select.is_a("IfcMaterialLayerSetUsage"):
            layer_set = mat_select.ForLayerSet
            for layer in layer_set.MaterialLayers:
                if layer.Material:
                    names.append(layer.Material.Name or "Unbekannt")
        elif mat_select.is_a("IfcMaterialLayerSet"):
            for layer in mat_select.MaterialLayers:
                if layer.Material:
                    names.append(layer.Material.Name or "Unbekannt")
        elif mat_select.is_a("IfcMaterialList"):
            for mat in mat_select.Materials:
                names.append(mat.Name or "Unbekannt")
    return names


def _get_element_quantity(element: ifcopenshell.entity_instance) -> tuple[float, str]:
    """Get the primary quantity (area or count) of an element."""
    for rel in getattr(element, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        prop_def = rel.RelatingPropertyDefinition
        if not prop_def.is_a("IfcElementQuantity"):
            continue
        for qty in prop_def.Quantities:
            if qty.is_a("IfcQuantityArea"):
                return qty.AreaValue, "m²"
            elif qty.is_a("IfcQuantityVolume"):
                return qty.VolumeValue, "m³"
    # Fallback: count as 1 piece
    return 1.0, "Stk"


def parse_ifc(file_path: str, project_id: str) -> tuple[Project, list[Room], list[Material]]:
    """Parse an IFC file and return Project, Rooms, and Materials.

    Args:
        file_path: Path to the .ifc file
        project_id: ID to assign to the project

    Returns:
        Tuple of (Project, list[Room], list[Material])
    """
    ifc_file = ifcopenshell.open(file_path)

    # --- Project ---
    ifc_projects = ifc_file.by_type("IfcProject")
    project_name = "IFC Projekt"
    if ifc_projects:
        project_name = ifc_projects[0].Name or project_name

    address = ""
    building_type = "Gebäude"
    buildings = ifc_file.by_type("IfcBuilding")
    if buildings:
        bldg = buildings[0]
        building_type = bldg.ObjectType or bldg.Name or building_type
        if hasattr(bldg, "BuildingAddress") and bldg.BuildingAddress:
            addr = bldg.BuildingAddress
            parts = []
            if hasattr(addr, "AddressLines") and addr.AddressLines:
                parts.extend(addr.AddressLines)
            if hasattr(addr, "Town") and addr.Town:
                parts.append(addr.Town)
            address = ", ".join(parts)

    storeys = ifc_file.by_type("IfcBuildingStorey")

    # --- Rooms (IfcSpace) ---
    rooms: list[Room] = []
    spaces = ifc_file.by_type("IfcSpace")

    for i, space in enumerate(spaces):
        space_id = space.GlobalId or f"space-{i}"
        name = space.LongName or space.Name or "Unbenannt"
        number = space.Name or f"R-{i+1:03d}"
        floor = _get_storey_name(space)

        area, height, volume = _get_space_quantities(space)

        # If volume is 0 but we have area and height, calculate it
        if volume == 0.0 and area > 0 and height > 0:
            volume = round(area * height, 1)

        # Usage type from ObjectType or Pset_SpaceCommon.OccupancyType
        usage_raw = space.ObjectType
        if not usage_raw:
            usage_raw = _get_pset_value(space, "Pset_SpaceCommon", "OccupancyType")
        usage_type = _classify_usage(usage_raw)

        # Finishes from property sets
        finish_floor = _get_pset_value(space, "Pset_SpaceCommon", "FinishFloor") or "—"
        finish_wall = _get_pset_value(space, "Pset_SpaceCommon", "FinishWall") or "—"
        finish_ceiling = _get_pset_value(space, "Pset_SpaceCommon", "FinishCeiling") or "—"

        rooms.append(Room(
            id=f"room-ifc-{space_id}",
            number=number,
            name=name,
            floor=floor,
            area=round(area, 2),
            height=round(height, 2),
            volume=round(volume, 2),
            usage_type=usage_type,
            finish_floor=finish_floor,
            finish_wall=finish_wall,
            finish_ceiling=finish_ceiling,
        ))

    # --- Materials ---
    raw_materials = _get_element_materials(ifc_file)
    material_list: list[Material] = []

    for i, (mat_name, (qty, unit, category)) in enumerate(sorted(raw_materials.items())):
        material_list.append(Material(
            id=f"mat-ifc-{i+1:03d}",
            name=mat_name,
            category=category,
            quantity=round(qty, 2),
            unit=unit,
            manufacturer="—",
            product="—",
        ))

    # --- Build project ---
    total_area = sum(r.area for r in rooms)
    project = Project(
        id=project_id,
        name=project_name,
        address=address or "—",
        building_type=building_type,
        total_area=round(total_area, 2),
        floors=len(storeys) if storeys else 1,
        status="IFC Import",
        source="ifc",
    )

    return project, rooms, material_list
