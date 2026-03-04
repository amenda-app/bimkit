"""Unified in-memory project store for all data sources (mock, IFC, ArchiCAD)."""

from app.models import (
    Project, Room, Area, Material, QuantityItem, CostGroup, CostEstimate,
)
from app import mock_data


class ProjectStore:
    """Central store that holds projects from any source."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._rooms: dict[str, list[Room]] = {}
        self._materials: dict[str, list[Material]] = {}
        self._sources: dict[str, str] = {}
        self._load_mock_data()

    def _load_mock_data(self) -> None:
        for project in mock_data.get_projects():
            pid = project.id
            project.source = "mock"
            self._projects[pid] = project
            self._rooms[pid] = mock_data.get_rooms(pid)
            self._materials[pid] = mock_data.get_materials(pid)
            self._sources[pid] = "mock"

    def add_project(
        self,
        project: Project,
        rooms: list[Room],
        materials: list[Material],
        source: str,
    ) -> None:
        pid = project.id
        project.source = source
        self._projects[pid] = project
        self._rooms[pid] = rooms
        self._materials[pid] = materials
        self._sources[pid] = source

    def remove_project(self, project_id: str) -> bool:
        if project_id not in self._projects:
            return False
        if self._sources.get(project_id) == "mock":
            return False  # don't allow deleting mock projects
        del self._projects[project_id]
        self._rooms.pop(project_id, None)
        self._materials.pop(project_id, None)
        self._sources.pop(project_id, None)
        return True

    def get_projects(self) -> list[Project]:
        return list(self._projects.values())

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def get_rooms(self, project_id: str) -> list[Room]:
        return self._rooms.get(project_id, [])

    def get_materials(self, project_id: str) -> list[Material]:
        return self._materials.get(project_id, [])

    def get_areas(self, project_id: str) -> list[Area]:
        rooms = self.get_rooms(project_id)
        return mock_data._areas_for_project(project_id, rooms)

    def get_source(self, project_id: str) -> str:
        return self._sources.get(project_id, "unknown")

    def get_quantities(self, project_id: str) -> list[QuantityItem]:
        """Generate quantity items from materials + structural extras."""
        materials = self.get_materials(project_id)
        items: list[QuantityItem] = []

        for mat in materials:
            trade, price = mock_data.UNIT_PRICES.get(mat.name, ("Sonstiges", 50.0))
            items.append(QuantityItem(
                trade=trade,
                category=mat.category,
                element_type=mat.name,
                description=f"{mat.manufacturer} {mat.product}".strip("— "),
                quantity=mat.quantity,
                unit=mat.unit,
                unit_price=price,
                total_price=round(mat.quantity * price, 2),
            ))

        for desc, cat, qty, unit, price in mock_data.ROHBAU_EXTRAS.get(project_id, []):
            items.append(QuantityItem(
                trade="Rohbau",
                category=cat,
                element_type=desc,
                description="",
                quantity=qty,
                unit=unit,
                unit_price=price,
                total_price=round(qty * price, 2),
            ))

        return items

    def get_cost_estimate(self, project_id: str) -> CostEstimate:
        """Generate DIN 276 cost estimate from quantities."""
        project = self.get_project(project_id)
        if not project:
            return CostEstimate(total_cost=0, cost_per_sqm=0, cost_groups=[])

        quantities = self.get_quantities(project_id)

        kg_data: dict[str, list[QuantityItem]] = {}
        for item in quantities:
            kg_num, _ = mock_data.DIN_276_MAPPING.get(item.trade, ("390", "Sonstige Maßnahmen"))
            kg_data.setdefault(kg_num, []).append(item)

        kg_names = {
            "300": "Bauwerk - Baukonstruktionen",
            "330": "Außenwände",
            "334": "Außentüren und -fenster",
            "336": "Außenwandbekleidung außen",
            "338": "Sonnenschutz",
            "340": "Innenwände",
            "344": "Innentüren und -fenster",
            "352": "Deckenbeläge",
            "390": "Sonstige Maßnahmen",
        }

        cost_groups: list[CostGroup] = []
        for kg_num in sorted(kg_data.keys()):
            items = kg_data[kg_num]
            subtotal = sum(i.total_price for i in items)
            level = 1 if kg_num == "300" else 2
            cost_groups.append(CostGroup(
                kg_number=kg_num,
                name=kg_names.get(kg_num, f"KG {kg_num}"),
                level=level,
                subtotal=round(subtotal, 2),
                items=items,
            ))

        total = sum(cg.subtotal for cg in cost_groups)
        return CostEstimate(
            total_cost=round(total, 2),
            cost_per_sqm=round(total / project.total_area, 2) if project.total_area > 0 else 0,
            cost_groups=cost_groups,
        )


# Singleton instance
store = ProjectStore()
