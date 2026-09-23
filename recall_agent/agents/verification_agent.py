"""
Verification Agent
Checks whether recall actions have been completed — verifies warehouse holds,
distributor acknowledgements, RMA returns, and shipment diversions.
Generates a completion scorecard and flags gaps for re-planning.
"""

from datetime import datetime
import random


class VerificationAgent:
    NAME = "Verification Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def verify(self, containment_result: dict, logistics_result: dict,
               comm_result: dict) -> dict:
        self._log("Beginning recall verification sweep across all containment and logistics actions.")

        actions        = containment_result["containment_actions"]
        return_orders  = logistics_result["return_orders"]
        wh_transfers   = logistics_result["warehouse_transfers"]
        communications = comm_result["communications"]

        checks = []

        # ── Verify warehouse holds ────────────────────────────────────────────
        wh_hold_actions = [a for a in actions if a["type"] == "INVENTORY_HOLD"]
        for act in wh_hold_actions:
            inv_id  = act["inventory_record"]
            inv     = self.data["warehouse_inventory"].get(inv_id, {})
            held    = inv.get("hold", False) or inv.get("status") == "quarantined"
            checks.append({
                "check_id": f"VER-{act['action_id']}",
                "category": "WAREHOUSE_HOLD",
                "reference": inv_id,
                "description": f"Inventory hold @ {act['warehouse_name']} — batch {act['batch']}",
                "status": "VERIFIED" if held else ("PARTIAL" if containment_result["human_approval_received"] else "PENDING"),
                "units_confirmed": act["units_to_hold"] if held else 0,
                "units_total": act["units_to_hold"],
                "notes": "Quarantine label applied" if held else "Awaiting warehouse confirmation",
            })

        # ── Verify transit holds ──────────────────────────────────────────────
        transit_actions = [a for a in actions if a["type"] == "SHIPMENT_SUSPENSION"]
        for act in transit_actions:
            # Simulate: 80% chance carrier responded
            responded = random.random() < 0.80
            checks.append({
                "check_id": f"VER-{act['action_id']}",
                "category": "TRANSIT_HOLD",
                "reference": act["shipment_id"],
                "description": f"Carrier diversion — tracking {act['tracking']}",
                "status": "VERIFIED" if responded else "ESCALATING",
                "units_confirmed": act["qty"] if responded else 0,
                "units_total": act["qty"],
                "notes": "Carrier confirmed hold" if responded else "No carrier response — escalating to account manager",
            })

        # ── Verify RMA acknowledgements ───────────────────────────────────────
        dist_comms = {c["recipient"]: c for c in communications
                      if c["type"] == "DISTRIBUTOR_RECALL_NOTICE"}
        for ro in return_orders:
            dist_id  = ro["source_id"]
            comm     = dist_comms.get(dist_id, {})
            sent     = comm.get("status") in ("SENT",)
            ack_prob = 0.9 if ro["priority"] == "HIGH" else (0.6 if ro["priority"] == "MEDIUM" else 0.3)
            acked    = sent and random.random() < ack_prob
            checks.append({
                "check_id": f"VER-RMA-{ro['rma_id']}",
                "category": "DISTRIBUTOR_RMA",
                "reference": ro["rma_id"],
                "description": f"RMA acknowledgement — {ro['source_name']}",
                "status": "ACKNOWLEDGED" if acked else ("NOTIFIED" if sent else "NOT_NOTIFIED"),
                "units_confirmed": ro["units_to_return"] if acked else 0,
                "units_total": ro["units_to_return"],
                "notes": f"Expected return: {ro['expected_return_date']}",
            })

        # ── Verify regulatory filings ─────────────────────────────────────────
        reg_comms = [c for c in communications if c["type"] == "REGULATORY_NOTIFICATION"]
        for rc in reg_comms:
            filed = rc["status"] in ("SENT", "QUEUED")
            checks.append({
                "check_id": f"VER-REG-{rc['comm_id']}",
                "category": "REGULATORY_FILING",
                "reference": rc["comm_id"],
                "description": f"Regulatory filing to {rc['recipient_name']}",
                "status": "FILED" if filed else "PENDING",
                "units_confirmed": None,
                "units_total": None,
                "notes": rc["status"],
            })

        # ── Scorecard ─────────────────────────────────────────────────────────
        verified  = [c for c in checks if c["status"] in ("VERIFIED", "ACKNOWLEDGED", "FILED")]
        partial   = [c for c in checks if c["status"] in ("PARTIAL", "NOTIFIED")]
        pending   = [c for c in checks if c["status"] in ("PENDING", "NOT_NOTIFIED")]
        escalating= [c for c in checks if c["status"] == "ESCALATING"]

        total = len(checks)
        completion_pct = round((len(verified) + len(partial) * 0.5) / total * 100, 1) if total else 0

        gaps = []
        for c in pending + escalating:
            gaps.append({
                "gap_id": c["check_id"],
                "category": c["category"],
                "description": c["description"],
                "severity": "HIGH" if c["category"] in ("TRANSIT_HOLD", "REGULATORY_FILING") else "MEDIUM",
                "recommended_action": self._gap_action(c["category"]),
            })

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "verification_checks": checks,
            "scorecard": {
                "total_checks": total,
                "verified": len(verified),
                "partial": len(partial),
                "pending": len(pending),
                "escalating": len(escalating),
                "completion_pct": completion_pct,
            },
            "gaps": gaps,
            "needs_replan": len(gaps) > 0,
            "recall_complete": completion_pct >= 95.0,
        }

        self._log(
            f"Verification complete: {completion_pct}% | {len(gaps)} gaps identified | "
            f"Recall complete: {result['recall_complete']}",
            result,
        )
        return result

    def _gap_action(self, category: str) -> str:
        return {
            "TRANSIT_HOLD":       "Escalate to carrier account manager; file emergency diversion request.",
            "WAREHOUSE_HOLD":     "Call warehouse manager directly; dispatch field inspector.",
            "DISTRIBUTOR_RMA":    "Follow-up call to distributor contact; offer pickup scheduling assistance.",
            "REGULATORY_FILING":  "Submit via certified mail + online portal immediately.",
        }.get(category, "Manual follow-up required.")

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        if data:
            entry["scorecard"] = data.get("scorecard")
            entry["gaps"] = [g["gap_id"] for g in data.get("gaps", [])]
        self.audit.append(entry)
