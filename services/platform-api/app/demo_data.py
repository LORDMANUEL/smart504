"""Deterministic SmartDiag504 demo catalog used by the staging experience.

The records are intentionally explicit so the public portal, warehouse demo and
Excel fixture all present the same compatibility and pricing information.
"""

DEMO_VEHICLES = [
    {
        "id": "escape-2020",
        "make": "Ford",
        "model": "Escape",
        "year": 2020,
        "engine": "2.0 EcoBoost",
    },
    {"id": "f150-2020", "make": "Ford", "model": "F-150", "year": 2020, "engine": "3.5 EcoBoost"},
    {"id": "civic-2008", "make": "Honda", "model": "Civic", "year": 2008, "engine": "1.8 i-VTEC"},
]

# Broad internal fitment catalog. These entries do not claim exact part-number
# compatibility: every generated placeholder remains inactive and requires VIN
# validation before it can be priced, stocked or published.
VEHICLE_CATALOG = [
    *DEMO_VEHICLES,
    {
        "id": "explorer-2020",
        "make": "Ford",
        "model": "Explorer",
        "year": 2020,
        "engine": "2.3 EcoBoost",
    },
    {
        "id": "ranger-2021",
        "make": "Ford",
        "model": "Ranger",
        "year": 2021,
        "engine": "2.3 EcoBoost",
    },
    {"id": "focus-2016", "make": "Ford", "model": "Focus", "year": 2016, "engine": "2.0"},
    {"id": "crv-2018", "make": "Honda", "model": "CR-V", "year": 2018, "engine": "1.5 Turbo"},
    {"id": "accord-2017", "make": "Honda", "model": "Accord", "year": 2017, "engine": "2.4"},
    {"id": "hrv-2020", "make": "Honda", "model": "HR-V", "year": 2020, "engine": "1.8"},
    {"id": "corolla-2018", "make": "Toyota", "model": "Corolla", "year": 2018, "engine": "1.8"},
    {"id": "rav4-2020", "make": "Toyota", "model": "RAV4", "year": 2020, "engine": "2.5"},
    {"id": "hilux-2021", "make": "Toyota", "model": "Hilux", "year": 2021, "engine": "2.8 Diesel"},
    {
        "id": "prado-2019",
        "make": "Toyota",
        "model": "Land Cruiser Prado",
        "year": 2019,
        "engine": "2.8 Diesel",
    },
    {"id": "sentra-2019", "make": "Nissan", "model": "Sentra", "year": 2019, "engine": "1.8"},
    {"id": "xtrail-2020", "make": "Nissan", "model": "X-Trail", "year": 2020, "engine": "2.5"},
    {
        "id": "frontier-2021",
        "make": "Nissan",
        "model": "Frontier",
        "year": 2021,
        "engine": "2.5 Diesel",
    },
    {"id": "tucson-2020", "make": "Hyundai", "model": "Tucson", "year": 2020, "engine": "2.0"},
    {"id": "elantra-2019", "make": "Hyundai", "model": "Elantra", "year": 2019, "engine": "2.0"},
    {"id": "accent-2018", "make": "Hyundai", "model": "Accent", "year": 2018, "engine": "1.6"},
    {"id": "sportage-2020", "make": "Kia", "model": "Sportage", "year": 2020, "engine": "2.0"},
    {"id": "rio-2019", "make": "Kia", "model": "Rio", "year": 2019, "engine": "1.6"},
    {"id": "sorento-2018", "make": "Kia", "model": "Sorento", "year": 2018, "engine": "2.4"},
    {"id": "bt50-2020", "make": "Mazda", "model": "BT-50", "year": 2020, "engine": "3.2 Diesel"},
    {"id": "cx5-2019", "make": "Mazda", "model": "CX-5", "year": 2019, "engine": "2.5"},
    {"id": "mazda3-2018", "make": "Mazda", "model": "Mazda3", "year": 2018, "engine": "2.0"},
    {"id": "dmax-2021", "make": "Isuzu", "model": "D-Max", "year": 2021, "engine": "3.0 Diesel"},
    {
        "id": "l200-2020",
        "make": "Mitsubishi",
        "model": "L200",
        "year": 2020,
        "engine": "2.4 Diesel",
    },
    {
        "id": "montero-2018",
        "make": "Mitsubishi",
        "model": "Montero Sport",
        "year": 2018,
        "engine": "2.4 Diesel",
    },
    {
        "id": "silverado-2020",
        "make": "Chevrolet",
        "model": "Silverado 1500",
        "year": 2020,
        "engine": "5.3",
    },
    {
        "id": "tracker-2021",
        "make": "Chevrolet",
        "model": "Tracker",
        "year": 2021,
        "engine": "1.2 Turbo",
    },
    {
        "id": "colorado-2019",
        "make": "Chevrolet",
        "model": "Colorado",
        "year": 2019,
        "engine": "2.8 Diesel",
    },
    {
        "id": "grand-cherokee-2018",
        "make": "Jeep",
        "model": "Grand Cherokee",
        "year": 2018,
        "engine": "3.6",
    },
    {
        "id": "wrangler-2020",
        "make": "Jeep",
        "model": "Wrangler",
        "year": 2020,
        "engine": "2.0 Turbo",
    },
    {
        "id": "amarok-2020",
        "make": "Volkswagen",
        "model": "Amarok",
        "year": 2020,
        "engine": "2.0 TDI",
    },
    {"id": "jetta-2019", "make": "Volkswagen", "model": "Jetta", "year": 2019, "engine": "1.4 TSI"},
    {"id": "bmw-x3-2018", "make": "BMW", "model": "X3", "year": 2018, "engine": "2.0 Turbo"},
    {
        "id": "mercedes-glc-2019",
        "make": "Mercedes-Benz",
        "model": "GLC",
        "year": 2019,
        "engine": "2.0 Turbo",
    },
]

_PLACEHOLDER_TYPES = [
    ("OIL", "Filtro de aceite por validar"),
    ("AIR", "Filtro de aire por validar"),
    ("BRK", "Pastillas de freno delanteras por validar"),
]
PRELOADED_PARTS = [
    {
        "code": f"CAT-{vehicle['id'].upper()}-{suffix}",
        "description": description,
        "vehicle_id": vehicle["id"],
        "location": "SIN-ASIGNAR",
        "stock": 0,
        "cost": 0,
        "price": 0,
        "requires_vin_validation": True,
    }
    for vehicle in VEHICLE_CATALOG
    for suffix, description in _PLACEHOLDER_TYPES
]

DEMO_LABOR = [
    {
        "code": "MO-DIAG-001",
        "description": "Diagnóstico electrónico completo",
        "hours": 1.5,
        "cost": 650,
        "price": 1200,
    },
    {
        "code": "MO-ACEITE-001",
        "description": "Cambio de aceite y filtro",
        "hours": 0.7,
        "cost": 280,
        "price": 650,
    },
    {
        "code": "MO-FRENOS-001",
        "description": "Servicio de frenos delanteros",
        "hours": 2.0,
        "cost": 900,
        "price": 1850,
    },
    {
        "code": "MO-SUSP-001",
        "description": "Inspección y ajuste de suspensión",
        "hours": 1.2,
        "cost": 520,
        "price": 1100,
    },
    {
        "code": "MO-AC-001",
        "description": "Diagnóstico de aire acondicionado",
        "hours": 1.0,
        "cost": 450,
        "price": 950,
    },
]

# Three parts per vehicle. Cost remains internal; public clients only receive the sale price.
DEMO_PARTS = [
    {
        "code": "ESC-FIL-2020",
        "description": "Filtro de aceite Motorcraft FL-910S",
        "vehicle_id": "escape-2020",
        "location": "A-01-02",
        "stock": 8,
        "cost": 165,
        "price": 285,
    },
    {
        "code": "ESC-AIR-2020",
        "description": "Filtro de aire Motorcraft FA-1912",
        "vehicle_id": "escape-2020",
        "location": "A-01-04",
        "stock": 5,
        "cost": 260,
        "price": 420,
    },
    {
        "code": "ESC-BRK-2020",
        "description": "Pastillas de freno delanteras",
        "vehicle_id": "escape-2020",
        "location": "B-03-01",
        "stock": 4,
        "cost": 720,
        "price": 1250,
    },
    {
        "code": "F150-FIL-2020",
        "description": "Filtro de aceite Motorcraft FL-500S",
        "vehicle_id": "f150-2020",
        "location": "A-01-03",
        "stock": 10,
        "cost": 190,
        "price": 320,
    },
    {
        "code": "F150-AIR-2020",
        "description": "Filtro de aire Motorcraft FA-1883",
        "vehicle_id": "f150-2020",
        "location": "A-02-01",
        "stock": 3,
        "cost": 340,
        "price": 560,
    },
    {
        "code": "F150-BRK-2020",
        "description": "Juego de pastillas delanteras F-150",
        "vehicle_id": "f150-2020",
        "location": "B-03-04",
        "stock": 2,
        "cost": 980,
        "price": 1680,
    },
    {
        "code": "CIV-FIL-2008",
        "description": "Filtro de aceite Honda 15400-PLM-A02",
        "vehicle_id": "civic-2008",
        "location": "A-01-01",
        "stock": 12,
        "cost": 150,
        "price": 270,
    },
    {
        "code": "CIV-AIR-2008",
        "description": "Filtro de aire Honda Civic 1.8",
        "vehicle_id": "civic-2008",
        "location": "A-02-03",
        "stock": 7,
        "cost": 230,
        "price": 390,
    },
    {
        "code": "CIV-SPK-2008",
        "description": "Juego de bujías iridium Civic",
        "vehicle_id": "civic-2008",
        "location": "C-01-02",
        "stock": 6,
        "cost": 760,
        "price": 1320,
    },
]
