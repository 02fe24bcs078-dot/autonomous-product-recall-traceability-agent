"""
Traceability Agent
Traces the full product genealogy from raw material lots → production batches
→ warehouse inventory → shipments. Builds a directed graph of relationships.
"""

from datetime import datetime
from collections import defaultdict


class TraceabilityAgent:
    NAME = "Traceability Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def trace(self, trigger_result: dict) -> dict:
        self._log("Beginning full supply-chain genealogy trace.")

        suspect_lots   = trigger_result["suspect_raw_lots"]
        batches        = self.data["production_batches"]
        inventory      = self.data["warehouse_inventory"]
        shipments      = self.data["shipments"]
        distributors   = self.data["distributors"]

        # ── Step 1: find all batches that used a suspect lot ─────────────────
        affected_batches = {}
        for batch_id, batch in batches.items():
            used = [lot for lot in batch["raw_materials"] if lot in suspect_lots]
            if used:
                affected_batches[batch_id] = {**batch, "contaminated_lots": used}

        # ── Step 2: find all inventory records for affected batches ──────────
        affected_inventory = {}
        for inv_id, inv in inventory.items():
            if inv["batch"] in affected_batches:
                affected_inventory[inv_id] = inv

        # ── Step 3: find all shipments for affected batches ──────────────────
        affected_shipments = {}
        for ship_id, ship in shipments.items():
            if ship["batch"] in affected_batches:
                affected_shipments[ship_id] = ship

        # ── Step 4: find all distributors that received affected products ────
        affected_distributors = {}
        for ship in affected_shipments.values():
            dist_id = ship["to_dist"]
            if dist_id not in affected_distributors:
                affected_distributors[dist_id] = {
                    **distributors[dist_id],
                    "shipments": [],
                    "total_units": 0,
                }
            affected_distributors[dist_id]["shipments"].append(ship)
            affected_distributors[dist_id]["total_units"] += ship["qty"]

        # ── Step 5: build genealogy graph nodes + edges ──────────────────────
        graph = self._build_graph(suspect_lots, affected_batches,
                                   affected_inventory, affected_shipments,
                                   affected_distributors)

        # ── Step 6: quantity summary ─────────────────────────────────────────
        total_produced  = sum(b["qty_units"] for b in affected_batches.values())
        total_in_wh     = sum(i["qty_current"] for i in affected_inventory.values())
        total_shipped   = sum(s["qty"] for s in affected_shipments.values())
        in_transit_qty  = sum(s["qty"] for s in affected_shipments.values() if s["status"] == "in_transit")
        delivered_qty   = sum(s["qty"] for s in affected_shipments.values() if s["status"] == "delivered")

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "suspect_raw_material_lots": suspect_lots,
            "affected_batches": list(affected_batches.keys()),
            "affected_batch_detail": affected_batches,
            "affected_inventory_records": list(affected_inventory.keys()),
            "affected_inventory_detail": affected_inventory,
            "affected_shipments": list(affected_shipments.keys()),
            "affected_shipment_detail": affected_shipments,
            "affected_distributors": list(affected_distributors.keys()),
            "affected_distributor_detail": affected_distributors,
            "quantity_summary": {
                "total_units_produced": total_produced,
                "total_units_in_warehouse": total_in_wh,
                "total_units_shipped": total_shipped,
                "in_transit": in_transit_qty,
                "delivered_to_distributors": delivered_qty,
                "accounted_for": total_in_wh + total_shipped,
                "unaccounted": total_produced - (total_in_wh + total_shipped),
            },
            "genealogy_graph": graph,
        }

        self._log(f"Trace complete: {len(affected_batches)} batches, {len(affected_distributors)} distributors, "
                  f"{total_produced} total units in scope.", result)
        return result

    # ── graph builder ─────────────────────────────────────────────────────────
    def _build_graph(self, suspect_lots, batches, inventory, shipments, distributors):
        nodes = []
        edges = []

        # Supplier node
        nodes.append({"id": "SUP-003", "label": "FrictionTech Ltd.", "type": "supplier", "status": "flagged"})

        # Raw lot nodes
        for lot_id in suspect_lots:
            lot = self.data["raw_material_lots"][lot_id]
            nodes.append({"id": lot_id, "label": f"{lot_id}\n{lot['material']}", "type": "raw_lot", "status": "defective"})
            edges.append({"from": "SUP-003", "to": lot_id, "label": "supplied"})

        # Batch nodes
        for batch_id, batch in batches.items():
            nodes.append({"id": batch_id, "label": f"{batch_id}\n{batch['product_name']}\n{batch['qty_units']} units",
                          "type": "batch", "status": "affected"})
            for lot_id in batch["contaminated_lots"]:
                edges.append({"from": lot_id, "to": batch_id, "label": "used in"})

        # Warehouse inventory nodes
        warehouses_seen = {}
        for inv_id, inv in inventory.items():
            wh_id = inv["warehouse"]
            if wh_id not in warehouses_seen:
                wh = self.data["warehouses"][wh_id]
                nodes.append({"id": wh_id, "label": f"{wh['name']}\n{wh['location']}", "type": "warehouse", "status": "affected"})
                warehouses_seen[wh_id] = True
            edges.append({"from": inv["batch"], "to": wh_id, "label": f"stored ({inv['qty_current']} units)"})

        # Distributor nodes
        for dist_id, dist in distributors.items():
            nodes.append({"id": dist_id, "label": f"{dist['name']}\n{dist['region']}", "type": "distributor", "status": "notified"})
            for ship in dist["shipments"]:
                wh_id = ship.get("from")
                if wh_id:
                    edges.append({"from": wh_id, "to": dist_id, "label": f"shipped {ship['qty']} ({ship['status']})"})

        return {"nodes": nodes, "edges": edges}

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        if data:
            entry["summary"] = {k: v for k, v in data.items() if k in ("quantity_summary", "affected_batches", "affected_distributors")}
        self.audit.append(entry)
