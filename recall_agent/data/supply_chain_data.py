"""
Supply Chain Mock Data — realistic manufacturing scenario for Product Recall Agent.
Scenario: Automotive brake pad manufacturer discovers a defective batch of raw
friction compound from Supplier SUP-003, potentially affecting 4 production batches,
3 warehouses, 12 distributors and ~2,400 end customers.
"""

from datetime import datetime, timedelta
import random

BASE_DATE = datetime(2026, 8, 1)


def d(offset_days: int) -> str:
    return (BASE_DATE + timedelta(days=offset_days)).strftime("%Y-%m-%d")


# ── Suppliers ────────────────────────────────────────────────────────────────
SUPPLIERS = {
    "SUP-001": {"name": "AlloyCo Raw Materials", "country": "USA", "category": "Metal Alloys", "risk_level": "low"},
    "SUP-002": {"name": "ChemBase Inc.", "country": "Germany", "category": "Chemical Binders", "risk_level": "medium"},
    "SUP-003": {"name": "FrictionTech Ltd.", "country": "China", "category": "Friction Compounds", "risk_level": "high", "flagged": True},
    "SUP-004": {"name": "SteelForm Co.", "country": "USA", "category": "Steel Backing Plates", "risk_level": "low"},
    "SUP-005": {"name": "PackagePro", "country": "Mexico", "category": "Packaging Materials", "risk_level": "low"},
}

# ── Raw Material Lots ─────────────────────────────────────────────────────────
RAW_MATERIAL_LOTS = {
    "RML-1001": {"supplier": "SUP-001", "material": "Iron Alloy Powder", "qty_kg": 5000, "received": d(-60), "status": "consumed", "lot_quality": "pass"},
    "RML-1002": {"supplier": "SUP-002", "material": "Phenolic Resin Binder", "qty_kg": 2000, "received": d(-55), "status": "consumed", "lot_quality": "pass"},
    "RML-1003": {"supplier": "SUP-003", "material": "Friction Compound FC-99", "qty_kg": 3000, "received": d(-50), "status": "consumed", "lot_quality": "FAIL", "defect": "Excessive silica content (18% vs 9% spec)", "cert_number": "FT-2026-0812"},
    "RML-1004": {"supplier": "SUP-003", "material": "Friction Compound FC-99", "qty_kg": 1500, "received": d(-45), "status": "in_stock", "lot_quality": "FAIL", "defect": "Excessive silica content", "cert_number": "FT-2026-0819"},
    "RML-1005": {"supplier": "SUP-004", "material": "Steel Backing Plate SP-7", "qty_kg": 8000, "received": d(-52), "status": "consumed", "lot_quality": "pass"},
    "RML-1006": {"supplier": "SUP-001", "material": "Iron Alloy Powder", "qty_kg": 4000, "received": d(-30), "status": "in_stock", "lot_quality": "pass"},
    "RML-1007": {"supplier": "SUP-002", "material": "Phenolic Resin Binder", "qty_kg": 1000, "received": d(-28), "status": "in_stock", "lot_quality": "pass"},
}

# ── Production Batches ────────────────────────────────────────────────────────
PRODUCTION_BATCHES = {
    "BATCH-4401": {
        "product_code": "BP-2200-F",
        "product_name": "Heavy Duty Brake Pad (Front)",
        "produced": d(-45),
        "machine": "PRESS-07",
        "operator": "EMP-1142",
        "qty_units": 6000,
        "raw_materials": ["RML-1001", "RML-1002", "RML-1003", "RML-1005"],
        "status": "distributed",
        "quality_check": "passed_initially",
        "affected": True,
    },
    "BATCH-4402": {
        "product_code": "BP-2200-R",
        "product_name": "Heavy Duty Brake Pad (Rear)",
        "produced": d(-42),
        "machine": "PRESS-08",
        "operator": "EMP-1155",
        "qty_units": 4800,
        "raw_materials": ["RML-1001", "RML-1002", "RML-1003", "RML-1005"],
        "status": "distributed",
        "quality_check": "passed_initially",
        "affected": True,
    },
    "BATCH-4403": {
        "product_code": "BP-2200-F",
        "product_name": "Heavy Duty Brake Pad (Front)",
        "produced": d(-38),
        "machine": "PRESS-07",
        "operator": "EMP-1142",
        "qty_units": 5500,
        "raw_materials": ["RML-1001", "RML-1002", "RML-1003", "RML-1004", "RML-1005"],
        "status": "partially_distributed",
        "quality_check": "passed_initially",
        "affected": True,
    },
    "BATCH-4404": {
        "product_code": "BP-2200-HV",
        "product_name": "Heavy Duty Brake Pad (Heavy Vehicle)",
        "produced": d(-33),
        "machine": "PRESS-09",
        "operator": "EMP-1161",
        "qty_units": 2400,
        "raw_materials": ["RML-1001", "RML-1002", "RML-1004", "RML-1005"],
        "status": "in_warehouse",
        "quality_check": "passed_initially",
        "affected": True,
    },
    "BATCH-4405": {
        "product_code": "BP-2200-F",
        "product_name": "Heavy Duty Brake Pad (Front)",
        "produced": d(-20),
        "machine": "PRESS-07",
        "operator": "EMP-1142",
        "qty_units": 7000,
        "raw_materials": ["RML-1006", "RML-1007", "RML-1005"],
        "status": "in_warehouse",
        "quality_check": "pass",
        "affected": False,
    },
}

# ── Warehouses ────────────────────────────────────────────────────────────────
WAREHOUSES = {
    "WH-EAST": {"name": "East Region DC", "location": "Newark, NJ", "manager": "Sarah Chen", "phone": "+1-973-555-0101"},
    "WH-WEST": {"name": "West Region DC", "location": "Los Angeles, CA", "manager": "James Torres", "phone": "+1-310-555-0202"},
    "WH-CENT": {"name": "Central DC", "location": "Chicago, IL", "manager": "Maria Gonzalez", "phone": "+1-312-555-0303"},
}

# ── Warehouse Inventory ───────────────────────────────────────────────────────
WAREHOUSE_INVENTORY = {
    "INV-E-4401": {"warehouse": "WH-EAST", "batch": "BATCH-4401", "qty_received": 2000, "qty_current": 120, "status": "active", "hold": False},
    "INV-E-4402": {"warehouse": "WH-EAST", "batch": "BATCH-4402", "qty_received": 1600, "qty_current": 85, "status": "active", "hold": False},
    "INV-W-4401": {"warehouse": "WH-WEST", "batch": "BATCH-4401", "qty_received": 2200, "qty_current": 95, "status": "active", "hold": False},
    "INV-W-4402": {"warehouse": "WH-WEST", "batch": "BATCH-4402", "qty_received": 1800, "qty_current": 210, "status": "active", "hold": False},
    "INV-C-4403": {"warehouse": "WH-CENT", "batch": "BATCH-4403", "qty_received": 2800, "qty_current": 340, "status": "active", "hold": False},
    "INV-C-4404": {"warehouse": "WH-CENT", "batch": "BATCH-4404", "qty_received": 2400, "qty_current": 2400, "status": "active", "hold": False},
    "INV-E-4403": {"warehouse": "WH-EAST", "batch": "BATCH-4403", "qty_received": 1500, "qty_current": 275, "status": "active", "hold": False},
    "INV-W-4405": {"warehouse": "WH-WEST", "batch": "BATCH-4405", "qty_received": 3500, "qty_current": 3500, "status": "active", "hold": False},
    "INV-C-4405": {"warehouse": "WH-CENT", "batch": "BATCH-4405", "qty_received": 3500, "qty_current": 3500, "status": "active", "hold": False},
}

# ── Distributors ──────────────────────────────────────────────────────────────
DISTRIBUTORS = {
    "DIST-001": {"name": "AutoParts Northeast", "region": "Northeast USA", "contact": "bob.harris@apne.com", "phone": "+1-617-555-0401"},
    "DIST-002": {"name": "Pacific Auto Supply", "region": "West Coast USA", "contact": "linda.wu@pacsupply.com", "phone": "+1-415-555-0402"},
    "DIST-003": {"name": "MidWest Brake Depot", "region": "Midwest USA", "contact": "tom.riley@mwbd.com", "phone": "+1-312-555-0403"},
    "DIST-004": {"name": "Southern Auto Wholesale", "region": "South USA", "contact": "carlos.m@saw.com", "phone": "+1-214-555-0404"},
    "DIST-005": {"name": "Great Lakes Parts", "region": "Great Lakes", "contact": "ann.schulz@glparts.com", "phone": "+1-313-555-0405"},
    "DIST-006": {"name": "Rocky Mountain AutoParts", "region": "Mountain West", "contact": "derek.k@rmap.com", "phone": "+1-303-555-0406"},
    "DIST-007": {"name": "CanAuto Supply", "region": "Canada", "contact": "sophie.l@canautosupply.ca", "phone": "+1-416-555-0407"},
    "DIST-008": {"name": "MexParts S.A.", "region": "Mexico", "contact": "alejandro.r@mexparts.mx", "phone": "+52-55-5555-0408"},
    "DIST-009": {"name": "Euro Brake Imports", "region": "Western Europe", "contact": "hans.m@ebi.de", "phone": "+49-89-555-0409"},
    "DIST-010": {"name": "Asia Pacific Auto", "region": "APAC", "contact": "kenji.t@apac-auto.jp", "phone": "+81-3-5555-0410"},
    "DIST-011": {"name": "FleetPro Services", "region": "National Fleet", "contact": "rachel.b@fleetpro.com", "phone": "+1-888-555-0411"},
    "DIST-012": {"name": "TruckParts Direct", "region": "Heavy Vehicle", "contact": "mike.d@truckparts.com", "phone": "+1-800-555-0412"},
}

# ── Shipments ─────────────────────────────────────────────────────────────────
SHIPMENTS = {
    "SHIP-8801": {"from": "WH-EAST", "to_dist": "DIST-001", "batch": "BATCH-4401", "qty": 800, "shipped": d(-40), "status": "delivered", "tracking": "FDX-4421001"},
    "SHIP-8802": {"from": "WH-WEST", "to_dist": "DIST-002", "batch": "BATCH-4401", "qty": 1200, "shipped": d(-38), "status": "delivered", "tracking": "UPS-4421002"},
    "SHIP-8803": {"from": "WH-EAST", "to_dist": "DIST-007", "batch": "BATCH-4402", "qty": 600, "shipped": d(-36), "status": "delivered", "tracking": "FDX-4422001"},
    "SHIP-8804": {"from": "WH-WEST", "to_dist": "DIST-002", "batch": "BATCH-4402", "qty": 900, "shipped": d(-35), "status": "delivered", "tracking": "UPS-4422002"},
    "SHIP-8805": {"from": "WH-CENT", "to_dist": "DIST-003", "batch": "BATCH-4403", "qty": 1100, "shipped": d(-30), "status": "delivered", "tracking": "FDX-4423001"},
    "SHIP-8806": {"from": "WH-CENT", "to_dist": "DIST-005", "batch": "BATCH-4403", "qty": 800, "shipped": d(-28), "status": "delivered", "tracking": "UPS-4423002"},
    "SHIP-8807": {"from": "WH-EAST", "to_dist": "DIST-001", "batch": "BATCH-4403", "qty": 500, "shipped": d(-25), "status": "delivered", "tracking": "FDX-4423003"},
    "SHIP-8808": {"from": "WH-WEST", "to_dist": "DIST-006", "batch": "BATCH-4401", "qty": 700, "shipped": d(-33), "status": "delivered", "tracking": "UPS-4421003"},
    "SHIP-8809": {"from": "WH-CENT", "to_dist": "DIST-004", "batch": "BATCH-4402", "qty": 315, "shipped": d(-32), "status": "delivered", "tracking": "FDX-4422003"},
    "SHIP-8810": {"from": "WH-EAST", "to_dist": "DIST-009", "batch": "BATCH-4401", "qty": 280, "shipped": d(-29), "status": "in_transit", "tracking": "DHL-4421004"},
    "SHIP-8811": {"from": "WH-WEST", "to_dist": "DIST-010", "batch": "BATCH-4402", "qty": 490, "shipped": d(-27), "status": "in_transit", "tracking": "FDX-4422004"},
    "SHIP-8812": {"from": "WH-CENT", "to_dist": "DIST-012", "batch": "BATCH-4404", "qty": 0, "shipped": None, "status": "pending", "tracking": None},
}

# ── Customer Incidents ────────────────────────────────────────────────────────
CUSTOMER_INCIDENTS = {
    "INC-2026-0891": {
        "date": d(-5),
        "customer": "FleetOps LLC",
        "product": "BP-2200-F",
        "batch_suspected": "BATCH-4401",
        "complaint": "Premature brake wear — 60% pad loss after 8,000 km (expected 40,000 km)",
        "severity": "CRITICAL",
        "vehicle": "2024 Ford F-250 Fleet",
        "units_affected": 12,
        "status": "open",
    },
    "INC-2026-0892": {
        "date": d(-4),
        "customer": "Northeast Auto Service",
        "product": "BP-2200-F",
        "batch_suspected": "BATCH-4401",
        "complaint": "Abnormal brake dust — grey metallic residue on wheel rims",
        "severity": "HIGH",
        "vehicle": "Multiple vehicles",
        "units_affected": 6,
        "status": "open",
    },
    "INC-2026-0893": {
        "date": d(-2),
        "customer": "Pacific Fleet Management",
        "product": "BP-2200-R",
        "batch_suspected": "BATCH-4402",
        "complaint": "Squealing noise and vibration during braking",
        "severity": "HIGH",
        "vehicle": "2023 Chevy Silverado",
        "units_affected": 4,
        "status": "open",
    },
}

# ── Quality Test Results ──────────────────────────────────────────────────────
QUALITY_TESTS = {
    "QT-2026-441": {
        "batch": "BATCH-4401",
        "test_date": d(-44),
        "tests": {"dimensional": "PASS", "hardness": "PASS", "silica_content": "FAIL (18.3% — spec: ≤9.0%)", "friction_coefficient": "MARGINAL"},
        "result": "FAIL",
        "retested": False,
        "defect_confirmed": True,
    },
}

# ── Regulatory / Recall Context ───────────────────────────────────────────────
RECALL_CONTEXT = {
    "regulation": "FMCSA 49 CFR Part 571 — Federal Motor Vehicle Safety Standards",
    "recall_class": "Class I — Safety Critical",
    "mandatory_notification": "Within 5 business days of confirmation",
    "agencies": ["NHTSA", "FMCSA", "Transport Canada", "EU Type Approval Authority"],
    "potential_fine_per_day": 22591,
}

def get_full_dataset():
    return {
        "suppliers": SUPPLIERS,
        "raw_material_lots": RAW_MATERIAL_LOTS,
        "production_batches": PRODUCTION_BATCHES,
        "warehouses": WAREHOUSES,
        "warehouse_inventory": WAREHOUSE_INVENTORY,
        "distributors": DISTRIBUTORS,
        "shipments": SHIPMENTS,
        "customer_incidents": CUSTOMER_INCIDENTS,
        "quality_tests": QUALITY_TESTS,
        "recall_context": RECALL_CONTEXT,
    }
