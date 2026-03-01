"""Realistic mock data for BIM Report Studio - 3 projects with DIN 277 conformant data."""

from app.models import Project, Room, Area, Material


# --- Projects ---

PROJECTS: dict[str, Project] = {
    "museum": Project(
        id="museum",
        name="Stadtmuseum Neustadt",
        address="Kulturplatz 1, 70173 Stuttgart",
        building_type="Museum / Ausstellungsgebäude",
        total_area=4850.0,
        floors=3,
        status="Entwurfsplanung",
    ),
    "wohnhaus": Project(
        id="wohnhaus",
        name="Wohnanlage Am Parkring",
        address="Parkring 12-18, 80339 München",
        building_type="Mehrfamilienhaus",
        total_area=8920.0,
        floors=6,
        status="Ausführungsplanung",
    ),
    "schule": Project(
        id="schule",
        name="Grundschule Sonnenberg",
        address="Schulstraße 5, 10115 Berlin",
        building_type="Schulgebäude",
        total_area=3200.0,
        floors=2,
        status="Genehmigungsplanung",
    ),
}


def _museum_rooms() -> list[Room]:
    rooms: list[Room] = []

    # EG - Erdgeschoss
    eg_rooms = [
        ("M-E01", "Foyer / Empfang", "EG", 185.0, 5.5, "NUF 1", "Naturstein poliert", "Sichtbeton", "Akustikdecke"),
        ("M-E02", "Kasse / Information", "EG", 28.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("M-E03", "Garderobe", "EG", 42.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("M-E04", "Museumsshop", "EG", 65.0, 3.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Akustikdecke"),
        ("M-E05", "Ausstellungshalle 1", "EG", 320.0, 6.0, "NUF 1", "Estrich geschliffen", "Sichtbeton", "Sichtbeton"),
        ("M-E06", "Ausstellungshalle 2", "EG", 280.0, 6.0, "NUF 1", "Estrich geschliffen", "Sichtbeton", "Sichtbeton"),
        ("M-E07", "Wechselausstellung", "EG", 195.0, 5.0, "NUF 1", "Estrich geschliffen", "Sichtbeton", "Akustikdecke"),
        ("M-E08", "Museumscafé", "EG", 120.0, 3.5, "NUF 1", "Fliesen", "Gipskarton gestr.", "Akustikdecke"),
        ("M-E09", "Café-Küche", "EG", 35.0, 3.2, "NUF 1", "Fliesen", "Fliesen", "Akustikdecke"),
        ("M-E10", "WC Damen", "EG", 24.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-E11", "WC Herren", "EG", 22.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-E12", "WC Barrierefrei", "EG", 8.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-E13", "Technikraum 1", "EG", 45.0, 3.0, "TF", "Estrich", "Putz gestr.", "Putz"),
        ("M-E14", "Treppenhaus 1", "EG", 18.0, 6.0, "VF", "Naturstein", "Sichtbeton", "Sichtbeton"),
        ("M-E15", "Aufzug", "EG", 6.0, 3.0, "VF", "Edelstahl", "Edelstahl", "Edelstahl"),
    ]

    # OG1
    og1_rooms = [
        ("M-101", "Ausstellungsraum Antike", "OG1", 210.0, 4.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Akustikdecke"),
        ("M-102", "Ausstellungsraum Mittelalter", "OG1", 185.0, 4.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Akustikdecke"),
        ("M-103", "Ausstellungsraum Neuzeit", "OG1", 195.0, 4.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Akustikdecke"),
        ("M-104", "Kabinett 1", "OG1", 45.0, 3.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Akustikdecke"),
        ("M-105", "Kabinett 2", "OG1", 45.0, 3.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Akustikdecke"),
        ("M-106", "Medienraum", "OG1", 55.0, 3.5, "NUF 1", "Teppich", "Akustikpaneel", "Akustikdecke"),
        ("M-107", "Galerie / Luftraum", "OG1", 120.0, 4.5, "NUF 1", "Parkett Eiche", "Gipskarton gestr.", "Sichtbeton"),
        ("M-108", "Büro Kurator", "OG1", 22.0, 3.2, "NUF 2", "Teppich", "Gipskarton gestr.", "Akustikdecke"),
        ("M-109", "Büro Verwaltung", "OG1", 35.0, 3.2, "NUF 2", "Teppich", "Gipskarton gestr.", "Akustikdecke"),
        ("M-110", "Besprechungsraum", "OG1", 28.0, 3.2, "NUF 2", "Teppich", "Gipskarton gestr.", "Akustikdecke"),
        ("M-111", "Teeküche", "OG1", 12.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-112", "WC OG1", "OG1", 18.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-113", "Treppenhaus 1", "OG1", 18.0, 4.5, "VF", "Naturstein", "Sichtbeton", "Sichtbeton"),
        ("M-114", "Aufzug", "OG1", 6.0, 3.0, "VF", "Edelstahl", "Edelstahl", "Edelstahl"),
        ("M-115", "Flur OG1", "OG1", 65.0, 3.2, "VF", "Naturstein", "Gipskarton gestr.", "Akustikdecke"),
    ]

    # OG2 / DG
    og2_rooms = [
        ("M-201", "Werkstatt Restaurierung", "OG2", 85.0, 3.5, "NUF 1", "Estrich", "Putz gestr.", "Putz"),
        ("M-202", "Depot 1", "OG2", 120.0, 3.5, "NUF 5", "Estrich", "Putz gestr.", "Putz"),
        ("M-203", "Depot 2", "OG2", 95.0, 3.5, "NUF 5", "Estrich", "Putz gestr.", "Putz"),
        ("M-204", "Fotostudio", "OG2", 55.0, 3.5, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("M-205", "Registratur / Archiv", "OG2", 40.0, 3.2, "NUF 5", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("M-206", "Serverraum", "OG2", 18.0, 3.0, "TF", "Doppelboden", "Putz gestr.", "Kühldecke"),
        ("M-207", "Technikraum 2", "OG2", 55.0, 3.0, "TF", "Estrich", "Putz gestr.", "Putz"),
        ("M-208", "Lüftungszentrale", "OG2", 65.0, 3.0, "TF", "Estrich", "Putz gestr.", "Putz"),
        ("M-209", "Personalraum", "OG2", 25.0, 3.0, "NUF 7", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("M-210", "Umkleide / Dusche", "OG2", 15.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-211", "WC OG2", "OG2", 12.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("M-212", "Treppenhaus 1", "OG2", 18.0, 4.0, "VF", "Naturstein", "Sichtbeton", "Sichtbeton"),
        ("M-213", "Aufzug", "OG2", 6.0, 3.0, "VF", "Edelstahl", "Edelstahl", "Edelstahl"),
        ("M-214", "Flur OG2", "OG2", 45.0, 3.0, "VF", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("M-215", "Dachterrasse", "OG2", 80.0, 0.0, "NUF 1", "WPC Dielen", "—", "—"),
    ]

    for data in eg_rooms + og1_rooms + og2_rooms:
        number, name, floor, area, height, usage, f_floor, f_wall, f_ceil = data
        rooms.append(Room(
            id=f"room-{number.lower()}",
            number=number,
            name=name,
            floor=floor,
            area=area,
            height=height,
            volume=round(area * height, 1),
            usage_type=usage,
            finish_floor=f_floor,
            finish_wall=f_wall,
            finish_ceiling=f_ceil,
        ))
    return rooms


def _wohnhaus_rooms() -> list[Room]:
    rooms: list[Room] = []
    floor_labels = ["UG", "EG", "OG1", "OG2", "OG3", "DG"]

    # Common apartment room templates
    apt_types = {
        "2Z": [
            ("Wohnen/Essen/Kochen", 28.5, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Schlafen", 14.2, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Bad", 6.8, 2.5, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
            ("Flur", 5.5, 2.5, "VF", "Fliesen", "Raufaser gestr.", "Gipskarton gestr."),
            ("Abstellraum", 2.8, 2.5, "NUF 5", "Linoleum", "Putz gestr.", "Putz gestr."),
        ],
        "3Z": [
            ("Wohnen/Essen", 32.0, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Kochen", 10.5, 2.6, "NUF 1", "Fliesen", "Fliesen h=1.5m, Raufaser", "Gipskarton gestr."),
            ("Schlafen", 16.0, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Kind", 12.5, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Bad", 8.2, 2.5, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
            ("Gäste-WC", 3.2, 2.5, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
            ("Flur", 8.0, 2.5, "VF", "Fliesen", "Raufaser gestr.", "Gipskarton gestr."),
            ("Abstellraum", 3.5, 2.5, "NUF 5", "Linoleum", "Putz gestr.", "Putz gestr."),
        ],
        "4Z": [
            ("Wohnen/Essen", 38.0, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Kochen", 12.0, 2.6, "NUF 1", "Fliesen", "Fliesen h=1.5m, Raufaser", "Gipskarton gestr."),
            ("Schlafen", 18.5, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Kind 1", 13.0, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Kind 2", 11.5, 2.6, "NUF 1", "Parkett Eiche", "Raufaser gestr.", "Gipskarton gestr."),
            ("Bad", 9.5, 2.5, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
            ("Gäste-WC", 3.5, 2.5, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
            ("Flur", 10.0, 2.5, "VF", "Fliesen", "Raufaser gestr.", "Gipskarton gestr."),
            ("Abstellraum", 4.0, 2.5, "NUF 5", "Linoleum", "Putz gestr.", "Putz gestr."),
        ],
    }

    # Floor layout: 2 apartments per floor (mix of types)
    floor_apts = {
        "UG": [],  # No apartments in UG
        "EG": [("A", "3Z"), ("B", "2Z")],
        "OG1": [("A", "4Z"), ("B", "3Z")],
        "OG2": [("A", "3Z"), ("B", "3Z")],
        "OG3": [("A", "4Z"), ("B", "2Z")],
        "DG": [("A", "4Z")],  # Penthouse only
    }

    room_counter = 0

    # UG rooms (shared)
    ug_shared = [
        ("Tiefgarage", 420.0, 2.8, "TF", "Beschichtung", "Beton", "Beton"),
        ("Fahrradkeller", 35.0, 2.5, "NUF 5", "Beschichtung", "Putz gestr.", "Putz"),
        ("Technikraum Heizung", 28.0, 2.5, "TF", "Estrich", "Putz gestr.", "Putz"),
        ("Technikraum Elektro", 15.0, 2.5, "TF", "Estrich", "Putz gestr.", "Putz"),
        ("Waschküche", 22.0, 2.5, "NUF 7", "Fliesen", "Fliesen h=1.5m, Putz", "Putz"),
        ("Trockenraum", 18.0, 2.5, "NUF 7", "Fliesen", "Putz gestr.", "Putz"),
        ("Kellerabteil 1", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 2", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 3", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 4", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 5", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 6", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 7", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerabteil 8", 8.0, 2.3, "NUF 5", "Estrich", "Putz", "Putz"),
        ("Kellerflur", 32.0, 2.3, "VF", "Beschichtung", "Putz gestr.", "Putz"),
        ("Treppenhaus UG", 12.0, 2.8, "VF", "Fliesen", "Putz gestr.", "Putz"),
        ("Aufzug UG", 4.5, 2.5, "VF", "Edelstahl", "Edelstahl", "Edelstahl"),
        ("Müllraum", 12.0, 2.5, "TF", "Beschichtung", "Putz gestr.", "Putz"),
    ]

    for name, area, height, usage, f_floor, f_wall, f_ceil in ug_shared:
        room_counter += 1
        rooms.append(Room(
            id=f"room-w-{room_counter:03d}",
            number=f"W-U{room_counter:02d}",
            name=name,
            floor="UG",
            area=area,
            height=height,
            volume=round(area * height, 1),
            usage_type=usage,
            finish_floor=f_floor,
            finish_wall=f_wall,
            finish_ceiling=f_ceil,
        ))

    # Shared per-floor rooms
    for floor in floor_labels[1:]:  # EG to DG
        floor_num = floor_labels.index(floor)

        # Treppenhaus
        room_counter += 1
        rooms.append(Room(
            id=f"room-w-{room_counter:03d}",
            number=f"W-{floor_num}{room_counter % 100:02d}",
            name=f"Treppenhaus {floor}",
            floor=floor,
            area=12.0,
            height=2.8,
            volume=33.6,
            usage_type="VF",
            finish_floor="Fliesen",
            finish_wall="Putz gestr.",
            finish_ceiling="Putz",
        ))

        # Aufzug
        room_counter += 1
        rooms.append(Room(
            id=f"room-w-{room_counter:03d}",
            number=f"W-{floor_num}{room_counter % 100:02d}",
            name=f"Aufzug {floor}",
            floor=floor,
            area=4.5,
            height=2.5,
            volume=11.3,
            usage_type="VF",
            finish_floor="Edelstahl",
            finish_wall="Edelstahl",
            finish_ceiling="Edelstahl",
        ))

        # Hausflur
        room_counter += 1
        rooms.append(Room(
            id=f"room-w-{room_counter:03d}",
            number=f"W-{floor_num}{room_counter % 100:02d}",
            name=f"Hausflur {floor}",
            floor=floor,
            area=15.0,
            height=2.5,
            volume=37.5,
            usage_type="VF",
            finish_floor="Fliesen",
            finish_wall="Putz gestr.",
            finish_ceiling="Gipskarton gestr.",
        ))

        # Apartments
        for apt_letter, apt_type in floor_apts.get(floor, []):
            apt_name = f"Whg. {floor}-{apt_letter}"
            for r_name, r_area, r_height, r_usage, f_floor, f_wall, f_ceil in apt_types[apt_type]:
                room_counter += 1
                rooms.append(Room(
                    id=f"room-w-{room_counter:03d}",
                    number=f"W-{floor_num}{room_counter % 100:02d}",
                    name=f"{r_name} ({apt_name})",
                    floor=floor,
                    area=r_area,
                    height=r_height,
                    volume=round(r_area * r_height, 1),
                    usage_type=r_usage,
                    finish_floor=f_floor,
                    finish_wall=f_wall,
                    finish_ceiling=f_ceil,
                ))

    return rooms


def _schule_rooms() -> list[Room]:
    rooms: list[Room] = []

    eg_rooms = [
        ("S-E01", "Eingangsbereich / Aula", "EG", 180.0, 4.0, "NUF 1", "Linoleum", "Akustikpaneel", "Akustikdecke"),
        ("S-E02", "Sekretariat", "EG", 25.0, 3.2, "NUF 2", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-E03", "Rektorat", "EG", 22.0, 3.2, "NUF 2", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-E04", "Lehrerzimmer", "EG", 55.0, 3.2, "NUF 2", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-E05", "Klassenzimmer 1a", "EG", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-E06", "Klassenzimmer 1b", "EG", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-E07", "Betreuung / Hort", "EG", 85.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-E08", "Mensa", "EG", 110.0, 3.5, "NUF 1", "Linoleum", "Akustikpaneel", "Akustikdecke"),
        ("S-E09", "Küche", "EG", 45.0, 3.2, "NUF 1", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-E10", "WC Mädchen", "EG", 18.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-E11", "WC Jungen", "EG", 18.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-E12", "WC Barrierefrei", "EG", 6.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-E13", "WC Lehrer", "EG", 8.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-E14", "Hausmeister", "EG", 15.0, 3.0, "NUF 2", "Linoleum", "Putz gestr.", "Putz"),
        ("S-E15", "Putzmittelraum", "EG", 8.0, 3.0, "NUF 5", "Fliesen", "Fliesen", "Putz"),
        ("S-E16", "Technikraum", "EG", 25.0, 3.0, "TF", "Estrich", "Putz gestr.", "Putz"),
        ("S-E17", "Treppenhaus", "EG", 15.0, 4.0, "VF", "Linoleum", "Putz gestr.", "Putz"),
        ("S-E18", "Flur EG", "EG", 85.0, 3.2, "VF", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
    ]

    og_rooms = [
        ("S-101", "Klassenzimmer 2a", "OG1", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-102", "Klassenzimmer 2b", "OG1", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-103", "Klassenzimmer 3a", "OG1", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-104", "Klassenzimmer 3b", "OG1", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-105", "Klassenzimmer 4a", "OG1", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-106", "Klassenzimmer 4b", "OG1", 65.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-107", "Werkraum", "OG1", 75.0, 3.2, "NUF 1", "Linoleum", "Putz gestr.", "Akustikdecke"),
        ("S-108", "Musikraum", "OG1", 70.0, 3.2, "NUF 1", "Linoleum", "Akustikpaneel", "Akustikdecke"),
        ("S-109", "Computerraum", "OG1", 55.0, 3.2, "NUF 1", "Doppelboden", "Gipskarton gestr.", "Akustikdecke"),
        ("S-110", "Bibliothek", "OG1", 50.0, 3.2, "NUF 1", "Teppich", "Gipskarton gestr.", "Akustikdecke"),
        ("S-111", "Gruppenraum 1", "OG1", 25.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-112", "Gruppenraum 2", "OG1", 25.0, 3.2, "NUF 1", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-113", "Lehrmittel", "OG1", 20.0, 3.0, "NUF 5", "Linoleum", "Putz gestr.", "Putz"),
        ("S-114", "WC Mädchen OG", "OG1", 18.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-115", "WC Jungen OG", "OG1", 18.0, 3.0, "NUF 7", "Fliesen", "Fliesen", "Feuchtraumdecke"),
        ("S-116", "Treppenhaus", "OG1", 15.0, 3.5, "VF", "Linoleum", "Putz gestr.", "Putz"),
        ("S-117", "Flur OG", "OG1", 95.0, 3.2, "VF", "Linoleum", "Gipskarton gestr.", "Akustikdecke"),
        ("S-118", "Serverraum", "OG1", 10.0, 3.0, "TF", "Doppelboden", "Putz gestr.", "Kühldecke"),
    ]

    for data in eg_rooms + og_rooms:
        number, name, floor, area, height, usage, f_floor, f_wall, f_ceil = data
        rooms.append(Room(
            id=f"room-{number.lower()}",
            number=number,
            name=name,
            floor=floor,
            area=area,
            height=height,
            volume=round(area * height, 1),
            usage_type=usage,
            finish_floor=f_floor,
            finish_wall=f_wall,
            finish_ceiling=f_ceil,
        ))
    return rooms


def _areas_for_project(project_id: str, rooms: list[Room]) -> list[Area]:
    """Generate DIN 277 area summary from rooms."""
    categories: dict[str, list[Room]] = {}
    for room in rooms:
        cat = room.usage_type.split(" ")[0]  # NUF, TF, VF
        categories.setdefault(cat, []).append(room)

    areas: list[Area] = []
    for cat_key, cat_rooms in sorted(categories.items()):
        by_floor: dict[str, list[Room]] = {}
        for r in cat_rooms:
            by_floor.setdefault(r.floor, []).append(r)

        for floor, floor_rooms in sorted(by_floor.items()):
            cat_labels = {
                "NUF": "Nutzungsfläche",
                "TF": "Technische Funktionsfläche",
                "VF": "Verkehrsfläche",
            }
            areas.append(Area(
                id=f"area-{project_id}-{cat_key.lower()}-{floor.lower()}",
                name=f"{cat_labels.get(cat_key, cat_key)} {floor}",
                category=cat_key,
                floor=floor,
                area=round(sum(r.area for r in floor_rooms), 1),
                rooms=[r.id for r in floor_rooms],
            ))
    return areas


def _museum_materials() -> list[Material]:
    return [
        Material(id="mat-m-001", name="Sichtbeton C30/37", category="Wand", quantity=1850.0, unit="m²", manufacturer="—", product="Ortbeton"),
        Material(id="mat-m-002", name="Gipskartonplatte 12.5mm", category="Wand", quantity=2200.0, unit="m²", manufacturer="Knauf", product="Diamant"),
        Material(id="mat-m-003", name="Akustikdecke", category="Decke", quantity=1650.0, unit="m²", manufacturer="Armstrong", product="Perla OP"),
        Material(id="mat-m-004", name="Naturstein Jura Kalkstein", category="Boden", quantity=420.0, unit="m²", manufacturer="Jura Marmor", product="Jura Gelb"),
        Material(id="mat-m-005", name="Parkett Eiche geölt", category="Boden", quantity=960.0, unit="m²", manufacturer="Haro", product="Eiche Puro"),
        Material(id="mat-m-006", name="Estrich geschliffen", category="Boden", quantity=795.0, unit="m²", manufacturer="—", product="CT-C30-F5"),
        Material(id="mat-m-007", name="Fliesen 30x60", category="Boden", quantity=280.0, unit="m²", manufacturer="Villeroy & Boch", product="Architectura"),
        Material(id="mat-m-008", name="Linoleum", category="Boden", quantity=185.0, unit="m²", manufacturer="Forbo", product="Marmoleum Real"),
        Material(id="mat-m-009", name="Feuchtraumdecke", category="Decke", quantity=120.0, unit="m²", manufacturer="Armstrong", product="Bioguard"),
        Material(id="mat-m-010", name="Brandschutztür T30", category="Tür", quantity=12.0, unit="Stk", manufacturer="Hörmann", product="H3D"),
        Material(id="mat-m-011", name="Innentür Holz", category="Tür", quantity=35.0, unit="Stk", manufacturer="Schörghuber", product="T30-1"),
        Material(id="mat-m-012", name="Festverglasung", category="Fenster", quantity=380.0, unit="m²", manufacturer="Schüco", product="FWS 50+"),
        Material(id="mat-m-013", name="Sonnenschutzglas", category="Fenster", quantity=220.0, unit="m²", manufacturer="Guardian", product="SunGuard"),
        Material(id="mat-m-014", name="Teppichboden", category="Boden", quantity=120.0, unit="m²", manufacturer="Interface", product="Urban Retreat"),
        Material(id="mat-m-015", name="WPC Terrassendielen", category="Boden", quantity=80.0, unit="m²", manufacturer="Megawood", product="Classic"),
    ]


def _wohnhaus_materials() -> list[Material]:
    return [
        Material(id="mat-w-001", name="Kalksandstein 17.5cm", category="Wand", quantity=3200.0, unit="m²", manufacturer="KS-Original", product="KS-Quadro"),
        Material(id="mat-w-002", name="Porenbeton 24cm", category="Wand", quantity=1800.0, unit="m²", manufacturer="Ytong", product="PP2-0.45"),
        Material(id="mat-w-003", name="Parkett Eiche", category="Boden", quantity=2400.0, unit="m²", manufacturer="Haro", product="Eiche Puro"),
        Material(id="mat-w-004", name="Fliesen 60x60", category="Boden", quantity=850.0, unit="m²", manufacturer="Villeroy & Boch", product="Century Unlimited"),
        Material(id="mat-w-005", name="Linoleum", category="Boden", quantity=180.0, unit="m²", manufacturer="Forbo", product="Marmoleum"),
        Material(id="mat-w-006", name="Gipskartondecke", category="Decke", quantity=4200.0, unit="m²", manufacturer="Knauf", product="Cleaneo Akustik"),
        Material(id="mat-w-007", name="Feuchtraumdecke", category="Decke", quantity=380.0, unit="m²", manufacturer="Armstrong", product="Bioguard"),
        Material(id="mat-w-008", name="Kunststofffenster 3-fach", category="Fenster", quantity=340.0, unit="m²", manufacturer="Schüco", product="LivIng 82"),
        Material(id="mat-w-009", name="Wohnungseingangstür T30", category="Tür", quantity=9.0, unit="Stk", manufacturer="Hörmann", product="WAT"),
        Material(id="mat-w-010", name="Innentür CPL", category="Tür", quantity=85.0, unit="Stk", manufacturer="Hörmann", product="BaseLine"),
        Material(id="mat-w-011", name="Beschichtung Tiefgarage", category="Boden", quantity=420.0, unit="m²", manufacturer="StoCretec", product="StoPox"),
        Material(id="mat-w-012", name="WDVS EPS 160mm", category="Wand", quantity=2800.0, unit="m²", manufacturer="Sto", product="StoTherm Classic"),
    ]


def _schule_materials() -> list[Material]:
    return [
        Material(id="mat-s-001", name="Linoleum", category="Boden", quantity=1850.0, unit="m²", manufacturer="Forbo", product="Marmoleum Real"),
        Material(id="mat-s-002", name="Fliesen 30x30", category="Boden", quantity=320.0, unit="m²", manufacturer="Agrob Buchtal", product="Plural"),
        Material(id="mat-s-003", name="Akustikdecke", category="Decke", quantity=1400.0, unit="m²", manufacturer="Armstrong", product="Perla OP"),
        Material(id="mat-s-004", name="Gipskartonwand", category="Wand", quantity=2600.0, unit="m²", manufacturer="Knauf", product="Diamant"),
        Material(id="mat-s-005", name="Akustikpaneel Wand", category="Wand", quantity=450.0, unit="m²", manufacturer="Ecophon", product="Akusto Wall"),
        Material(id="mat-s-006", name="Feuchtraumdecke", category="Decke", quantity=180.0, unit="m²", manufacturer="Armstrong", product="Bioguard"),
        Material(id="mat-s-007", name="Holz-Alu-Fenster", category="Fenster", quantity=480.0, unit="m²", manufacturer="Internorm", product="HF 410"),
        Material(id="mat-s-008", name="Brandschutztür T30", category="Tür", quantity=8.0, unit="Stk", manufacturer="Hörmann", product="H3D"),
        Material(id="mat-s-009", name="Innentür HPL", category="Tür", quantity=42.0, unit="Stk", manufacturer="Schörghuber", product="T30"),
        Material(id="mat-s-010", name="Teppichboden", category="Boden", quantity=50.0, unit="m²", manufacturer="Interface", product="Urban Retreat"),
        Material(id="mat-s-011", name="Doppelboden", category="Boden", quantity=65.0, unit="m²", manufacturer="Lindner", product="Floor and more"),
        Material(id="mat-s-012", name="Sonnenschutz Raffstore", category="Fenster", quantity=380.0, unit="m²", manufacturer="Warema", product="E80"),
    ]


# --- Public API ---

_ROOMS_CACHE: dict[str, list[Room]] = {}
_MATERIALS_CACHE: dict[str, list[Material]] = {}


def get_rooms(project_id: str) -> list[Room]:
    if project_id not in _ROOMS_CACHE:
        generators = {
            "museum": _museum_rooms,
            "wohnhaus": _wohnhaus_rooms,
            "schule": _schule_rooms,
        }
        gen = generators.get(project_id)
        if gen is None:
            return []
        _ROOMS_CACHE[project_id] = gen()
    return _ROOMS_CACHE[project_id]


def get_areas(project_id: str) -> list[Area]:
    rooms = get_rooms(project_id)
    return _areas_for_project(project_id, rooms)


def get_materials(project_id: str) -> list[Material]:
    if project_id not in _MATERIALS_CACHE:
        generators = {
            "museum": _museum_materials,
            "wohnhaus": _wohnhaus_materials,
            "schule": _schule_materials,
        }
        gen = generators.get(project_id)
        if gen is None:
            return []
        _MATERIALS_CACHE[project_id] = gen()
    return _MATERIALS_CACHE[project_id]


def get_projects() -> list[Project]:
    return list(PROJECTS.values())


def get_project(project_id: str) -> Project | None:
    return PROJECTS.get(project_id)
