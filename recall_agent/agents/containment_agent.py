"""
Containment Agent
Places inventory holds, suspends shipments, and generates warehouse/distributor
quarantine instructions. Requires human approval before executing critical holds.
"""

from datetime import datetime


class ContainmentAgent:
    NAME = "Containment Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def contain(self, trace_result: dict, impact_result: dict,
                human_approved: bool = False) -> dict:

        self._log("Building containment plan for all affected supply-chain nodes.")

        affected_inv   = trace_result["affected_inventory_detail"]
        affected_ships = trace_result["affected_shipment_detail"]
        dist_risk      = impact_result["distributor_risk_scores"]
        warehouses     = self.data["warehouses"]
        raw_lots       = self.data["raw_material_lots"]

        # ── Action 1: Warehouse inventory holds ───────────────────────────────
        wh_holds = []
        for inv_id, inv in affected_inv.items():
            wh = warehouses[inv["warehouse"]]
            hold_action = {
                "action_id": f"HOLD-{inv_id}",
                "type": "INVENTORY_HOLD",
                "warehouse": inv["warehouse"],
                "warehouse_name": wh["name"],
                "manager": wh["manager"],
                "phone": wh["phone"],
                "inventory_record": inv_id,
                "batch": inv["batch"],
                "units_to_hold": inv["qty_current"],
                "status": "PENDING_APPROVAL" if not human_approved else "EXECUTED",
                "instructions": (
                    f"Immediately quarantine all units of batch {inv['batch']} "
                    f"in warehouse {wh['name']}. Move to quarantine zone Q-RED. "
                    f"Apply RECALL HOLD labels. Do NOT ship."
                ),
            }
            wh_holds.append(hold_action)
            # Update data store to reflect hold
            if human_approved:
                self.data["warehouse_inventory"][inv_id]["hold"] = True
                self.data["warehouse_inventory"][inv_id]["status"] = "quarantined"

        # ── Action 2: Suspend in-transit shipments ────────────────────────────
        transit_holds = []
        for ship_id, ship in affected_ships.items():
            if ship["status"] == "in_transit":
                transit_holds.append({
                    "action_id": f"TRANSIT-HOLD-{ship_id}",
                    "type": "SHIPMENT_SUSPENSION",
                    "shipment_id": ship_id,
                    "tracking": ship["tracking"],
                    "destination_dist": ship["to_dist"],
                    "qty": ship["qty"],
                    "status": "PENDING_APPROVAL" if not human_approved else "EXECUTED",
                    "instructions": (
                        f"Contact carrier immediately for shipment {ship['tracking']}. "
                        f"Request diversion to nearest holding facility. "
                        f"Do NOT deliver to distributor {ship['to_dist']}."
                    ),
                })

        # ── Action 3: Block pending shipments ────────────────────────────────
        pending_blocks = []
        for ship_id, ship in affected_ships.items():
            if ship["status"] == "pending":
                pending_blocks.append({
                    "action_id": f"BLOCK-{ship_id}",
                    "type": "SHIPMENT_BLOCK",
                    "shipment_id": ship_id,
                    "status": "EXECUTED",   # no approval needed for pending
                    "instructions": f"Cancel shipment {ship_id} to {ship['to_dist']} immediately.",
                })

        # ── Action 4: Quarantine remaining raw material lots ──────────────────
        raw_holds = []
        in_stock_lots = {k: v for k, v in raw_lots.items()
                         if v.get("lot_quality") == "FAIL" and v["status"] == "in_stock"}
        for lot_id, lot in in_stock_lots.items():
            raw_holds.append({
                "action_id": f"RAW-HOLD-{lot_id}",
                "type": "RAW_MATERIAL_QUARANTINE",
                "lot_id": lot_id,
                "material": lot["material"],
                "supplier": lot["supplier"],
                "qty_kg": lot["qty_kg"],
                "status": "EXECUTED",
                "instructions": f"Move lot {lot_id} to quarantine cage. Tag as DEFECTIVE. Notify supplier SUP-003.",
            })

        # ── Action 5: Distributor notification queue ──────────────────────────
        dist_notifications = []
        for dist_id, risk in dist_risk.items():
            priority = risk["priority"]
            dist_notifications.append({
                "action_id": f"NOTIFY-{dist_id}",
                "type": "DISTRIBUTOR_HOLD_REQUEST",
                "distributor": dist_id,
                "distributor_name": risk["name"],
                "priority": priority,
                "units_at_risk": risk["units_at_risk"],
                "status": "PENDING",
                "channel": "email+phone",
            })
        # Sort by risk priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        dist_notifications.sort(key=lambda x: priority_order.get(x["priority"], 3))

        all_actions = wh_holds + transit_holds + pending_blocks + raw_holds + dist_notifications
        executed    = [a for a in all_actions if a["status"] == "EXECUTED"]
        pending     = [a for a in all_actions if a["status"] in ("PENDING_APPROVAL", "PENDING")]

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "human_approval_received": human_approved,
            "approval_required_for": [a["action_id"] for a in pending],
            "containment_actions": all_actions,
            "summary": {
                "warehouse_holds": len(wh_holds),
                "transit_holds": len(transit_holds),
                "pending_shipment_blocks": len(pending_blocks),
                "raw_material_quarantines": len(raw_holds),
                "distributor_notifications": len(dist_notifications),
                "total_actions": len(all_actions),
                "executed": len(executed),
                "pending_approval": len(pending),
            },
            "units_immediately_containable": sum(
                a["units_to_hold"] for a in wh_holds
            ),
        }

        self._log(
            f"Containment plan ready: {len(all_actions)} actions | "
            f"{len(executed)} auto-executed | {len(pending)} await human approval.",
            result,
        )
        return result

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        if data:
            entry["summary"] = data.get("summary")
            entry["approval_required"] = data.get("approval_required_for")
        self.audit.append(entry)
