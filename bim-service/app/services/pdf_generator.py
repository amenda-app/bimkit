"""PDF report generation for BIM data using ReportLab."""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from app.models import Room, Area, Material, Project, QuantityItem


# DCAB brand colors
DCAB_NAVY = colors.HexColor("#1B3A5C")
DCAB_BLUE = colors.HexColor("#2E6DA4")
DCAB_ACCENT = colors.HexColor("#D4A843")
DCAB_LIGHT = colors.HexColor("#E8EDF2")
HEADER_BG = DCAB_NAVY
HEADER_FG = colors.white


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "DCTitle", parent=styles["Title"],
        textColor=DCAB_NAVY, fontSize=16, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "DCSubtitle", parent=styles["Normal"],
        textColor=DCAB_BLUE, fontSize=10, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "DCCell", parent=styles["Normal"], fontSize=7, leading=9,
    ))
    return styles


def _table_style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, DCAB_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])


def _build_pdf(title: str, subtitle: str, elements_fn) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=15 * mm,
    )
    styles = _get_styles()
    story = [
        Paragraph(title, styles["DCTitle"]),
        Paragraph(subtitle, styles["DCSubtitle"]),
        Paragraph(f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]
    story.extend(elements_fn(styles))
    doc.build(story)
    buf.seek(0)
    return buf


def generate_pdf_raumbuch(project: Project, rooms: list[Room]) -> io.BytesIO:
    def elements(styles):
        headers = ["Nr.", "Raumname", "Geschoss", "Fläche m²", "Höhe m", "Nutzung", "Boden", "Wand", "Decke"]
        data = [headers]
        for r in sorted(rooms, key=lambda x: (x.floor, x.number)):
            data.append([
                r.number, r.name, r.floor, f"{r.area:.1f}", f"{r.height:.1f}",
                r.usage_type, r.finish_floor, r.finish_wall, r.finish_ceiling,
            ])
        # Sum row
        total = sum(r.area for r in rooms)
        data.append(["", "GESAMT", "", f"{total:.1f}", "", "", "", "", ""])

        col_widths = [30, 80, 35, 35, 30, 35, 55, 55, 55]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = _table_style()
        # Bold last row
        style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        style.add("BACKGROUND", (0, -1), (-1, -1), DCAB_LIGHT)
        table.setStyle(style)
        return [table]

    return _build_pdf(
        f"Raumbuch - {project.name}",
        project.address,
        elements,
    )


def generate_pdf_flaechen(project: Project, areas: list[Area]) -> io.BytesIO:
    def elements(styles):
        headers = ["Bezeichnung", "Kategorie", "Geschoss", "Fläche m²", "Räume"]
        data = [headers]
        for a in sorted(areas, key=lambda x: (x.category, x.floor)):
            data.append([a.name, a.category, a.floor, f"{a.area:.1f}", str(len(a.rooms))])

        total = sum(a.area for a in areas)
        data.append(["NRF Gesamt", "", "", f"{total:.1f}", ""])

        col_widths = [120, 50, 50, 50, 40]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = _table_style()
        style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        style.add("BACKGROUND", (0, -1), (-1, -1), DCAB_LIGHT)
        table.setStyle(style)
        return [table]

    return _build_pdf(
        f"Flächenübersicht DIN 277 - {project.name}",
        project.address,
        elements,
    )


def generate_pdf_materialien(project: Project, materials: list[Material]) -> io.BytesIO:
    def elements(styles):
        headers = ["Material", "Kategorie", "Menge", "Einheit", "Hersteller", "Produkt"]
        data = [headers]
        for m in sorted(materials, key=lambda x: (x.category, x.name)):
            data.append([m.name, m.category, f"{m.quantity:.1f}", m.unit, m.manufacturer, m.product])

        col_widths = [80, 45, 40, 30, 70, 70]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(_table_style())
        return [table]

    return _build_pdf(
        f"Materialliste - {project.name}",
        project.address,
        elements,
    )


def generate_pdf_mengen(project: Project, quantities: list[QuantityItem]) -> io.BytesIO:
    def elements(styles):
        headers = ["Pos.", "Gewerk", "Kategorie", "Beschreibung", "Menge", "Einheit", "EP EUR", "GP EUR"]
        data = [headers]
        sorted_items = sorted(quantities, key=lambda q: (q.trade, q.category))
        for i, item in enumerate(sorted_items, 1):
            desc = f"{item.element_type} {item.description}".strip()
            data.append([
                str(i), item.trade, item.category, desc,
                f"{item.quantity:.1f}", item.unit,
                f"{item.unit_price:,.2f}", f"{item.total_price:,.2f}",
            ])

        total = sum(q.total_price for q in quantities)
        data.append(["", "", "", "GESAMTSUMME", "", "", "", f"{total:,.2f}"])

        col_widths = [25, 50, 45, 90, 35, 30, 40, 50]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = _table_style()
        style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        style.add("BACKGROUND", (0, -1), (-1, -1), DCAB_LIGHT)
        style.add("ALIGN", (-2, 1), (-1, -1), "RIGHT")
        table.setStyle(style)
        return [table]

    return _build_pdf(
        f"Mengenermittlung - {project.name}",
        project.address,
        elements,
    )
