"""
Reverse Logistics Agent
Plans and tracks the return movement of recalled products from distributors
and customers back through the supply chain to disposal/replacement.
"""

from datetime import datetime, timedelta
import uuid


RETURN_HUB = {
    "HUB-EAST": {"name": "East Return Processing Hub", "location": "Newark, NJ", "capacity_units": 10000},
    "HUB-WEST": {"name": "West Return Processing Hub", "location": "Reno, NV",   "capacity_units": 8000},
    "HUB-INTL": {"name": "International Returns Depot", "location": "JFK Airport, NY", "capacity_units": 5000},
}

REGION_TO_HUB = {
    "Northeast USA": "HUB-EAST",
    "West Coast USA": "HUB-WEST",
    "Midwest USA":   "HUB-EAST",
    "South USA":     "HUB-EAST",
    "Great Lakes":   "HUB-EAST",
    "Mountain West": "HUB-WEST",
    "Canada":        "HUB-EAST",
    "Mexico":        "HUB-WEST",
    "Western Europe":"HUB-INTL",
    "APAC":          "HUB-INTL",
    "National Fleet":"HUB-EAST",
    "Heavy Vehicle": "HUB-EAST",
}


class ReverseLogisticsAgent:
    NAME = "Reverse Logistics Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def plan(self, trace_result: dict, impact_result: dict) -> dict:
        self._log("Building reverse logistics plan for all affected product units.")

        dist_detail   = trace_result["affected_distributor_detail"]
        dist_risk     = impact_result["distributor_risk_scores"]
        distributors  = self.data["distributors"]
        inv_detail    = trace_result["affected_inventory_detail"]
        warehouses    = self.data["warehouses"]

        return_orders = []
        today = datetime.now()

        # ── Return Orders from Distributors ──────────────────────────────────
        for dist_id, dist in dist_detail.items():
            info      = distributors[dist_id]
            region    = info["region"]
            hub_id    = REGION_TO_HUB.get(region, "HUB-EAST")
            hub       = RETURN_HUB[hub_id]
            units     = dist["total_units"]
            priority  = dist_risk.get(dist_id, {}).get("priority", "MEDIUM")

            # Expected return window based on region + priority
            lead_days = 3 if priority == "HIGH" else (7 if priority == "MEDIUM" else 14)
            expected  = (today + timedelta(days=lead_days)).strftime("%Y-%m-%d")

            rma_id = f"RMA-{dist_id}-{today.strftime('%Y%m%d')}"
            return_orders.append({
                "rma_id": rma_id,
                "type": "DISTRIBUTOR_RETURN",
                "source_id": dist_id,
                "source_name": info["name"],
                "source_contact": info["contact"],
                "units_to_return": units,
                "return_hub": hub_id,
                "hub_name": hub["name"],
                "hub_location": hub["location"],
                "priority": priority,
                "status": "RMA_ISSUED",
                "expected_return_date": expected,
                "carrier_assigned": self._assign_carrier(region),
                "pickup_scheduled": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "tracking": f"RL-{rma_id}",
                "units_received": 0,
                "units_pending": units,
                "disposition": "PENDING",
            })

        # ── Transfer Orders from Warehouses (quarantined stock) ───────────────
        warehouse_transfers = []
        for inv_id, inv in inv_detail.items():
            wh_id = inv["warehouse"]
            wh    = warehouses[wh_id]
            units = inv["qty_current"]
            if units == 0:
                continue
            transfer_id = f"TFR-{inv_id}-{today.strftime('%Y%m%d')}"
            warehouse_transfers.append({
                "transfer_id": transfer_id,
                "type": "WAREHOUSE_QUARANTINE_TRANSFER",
                "source_warehouse": wh_id,
                "source_name": wh["name"],
                "batch": inv["batch"],
                "units": units,
                "status": "SCHEDULED",
                "expected_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "destination": "QUARANTINE_ZONE_Q-RED",
                "disposition": "AWAITING_DESTRUCTION_OR_REWORK",
            })

        # ── Disposition plan ─────────────────────────────────────────────────
        total_return_units = sum(r["units_to_return"] for r in return_orders)
        total_wh_units     = sum(t["units"] for t in warehouse_transfers)

        disposition_plan = {
            "confirmed_defective_destroy": round(total_return_units * 0.85),
            "rework_possible": round(total_return_units * 0.10),
            "insufficient_evidence_investigate": round(total_return_units * 0.05),
            "warehouse_destroy": total_wh_units,
        }

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "return_orders": return_orders,
            "warehouse_transfers": warehouse_transfers,
            "return_hubs": RETURN_HUB,
            "summary": {
                "total_rma_issued": len(return_orders),
                "total_warehouse_transfers": len(warehouse_transfers),
                "total_units_to_return": total_return_units,
                "total_warehouse_units_to_quarantine": total_wh_units,
                "total_units_in_reverse_flow": total_return_units + total_wh_units,
            },
            "disposition_plan": disposition_plan,
            "estimated_completion_days": 21,
        }

        self._log(
            f"Reverse logistics plan: {len(return_orders)} RMAs issued | "
            f"{total_return_units + total_wh_units} total units in reverse flow.",
            result,
        )
        return result

    def _assign_carrier(self, region: str) -> str:
        if "Europe" in region or "APAC" in region:
            return "DHL Express International"
        if "Canada" in region:
            return "Purolator / FedEx Cross-Border"
        if "Mexico" in region:
            return "Estafeta / FedEx MX"
        return "FedEx Ground (Domestic)"

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        if data:
            entry["summary"] = data.get("summary")
        self.audit.append(entry)
