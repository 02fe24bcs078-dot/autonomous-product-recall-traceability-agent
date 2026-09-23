"""
Audit Agent
Compiles the complete, immutable, evidence-backed audit trail of the recall.
Generates structured audit report with decision chain, timestamps,
approvals, and regulatory evidence package.
"""

from datetime import datetime
import hashlib
import json


def _hash(data: dict) -> str:
    """Simple SHA-256 fingerprint of a dict for tamper-evidence simulation."""
    raw = json.dumps(data, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()[:16].upper()


class AuditAgent:
    NAME = "Audit Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def compile(self, recall_id: str, trigger_r: dict, trace_r: dict,
                impact_r: dict, containment_r: dict, comm_r: dict,
                logistics_r: dict, verification_r: dict,
                human_approval_record: dict) -> dict:

        self._log(f"Compiling complete audit trail for {recall_id}.")

        # ── Decision chain ────────────────────────────────────────────────────
        decision_chain = [
            {
                "step": 1,
                "agent": "Recall Trigger Agent",
                "decision": f"Recall trigger CONFIRMED — Level: {trigger_r['trigger_level']}",
                "basis": f"Severity score {trigger_r['severity_score']}/100; "
                         f"{trigger_r['open_incidents']} open incidents; "
                         f"{trigger_r['failed_quality_tests']} failed QA tests",
                "timestamp": trigger_r["timestamp"],
                "hash": _hash(trigger_r),
                "automated": True,
            },
            {
                "step": 2,
                "agent": "Traceability Agent",
                "decision": f"Traced {len(trace_r['affected_batches'])} affected batches "
                            f"across {len(trace_r['affected_distributors'])} distributors",
                "basis": f"Suspect raw lots: {', '.join(trigger_r['suspect_raw_lots'])}",
                "timestamp": trace_r["timestamp"],
                "hash": _hash({"batches": trace_r["affected_batches"], "qty": trace_r["quantity_summary"]}),
                "automated": True,
            },
            {
                "step": 3,
                "agent": "Impact Analysis Agent",
                "decision": f"Recall scope: {impact_r['total_units_in_scope']} units | "
                            f"Financial exposure: ${impact_r['financial_exposure_usd']['total_estimated']:,}",
                "basis": f"Safety risk: {impact_r['safety_risk_level']} | "
                         f"Regulatory: {impact_r['regulatory_obligations']['regulation']}",
                "timestamp": impact_r["timestamp"],
                "hash": _hash(impact_r["financial_exposure_usd"]),
                "automated": True,
            },
            {
                "step": 4,
                "agent": "HUMAN APPROVAL",
                "decision": f"Recall execution APPROVED by {human_approval_record['approver']}",
                "basis": human_approval_record["rationale"],
                "timestamp": human_approval_record["timestamp"],
                "hash": _hash(human_approval_record),
                "automated": False,
                "approver": human_approval_record["approver"],
                "approver_title": human_approval_record["approver_title"],
                "signature_ref": human_approval_record.get("signature_ref", "e-sign-2026-RC-0041"),
            },
            {
                "step": 5,
                "agent": "Containment Agent",
                "decision": f"{containment_r['summary']['total_actions']} containment actions; "
                            f"{containment_r['summary']['executed']} executed",
                "basis": "Post-approval automated containment execution",
                "timestamp": containment_r["timestamp"],
                "hash": _hash(containment_r["summary"]),
                "automated": True,
            },
            {
                "step": 6,
                "agent": "Communication Agent",
                "decision": f"{comm_r['summary']['total_communications']} communications; "
                            f"{comm_r['summary']['sent']} sent",
                "basis": "Distributor + regulatory + internal notifications dispatched",
                "timestamp": comm_r["timestamp"],
                "hash": _hash(comm_r["summary"]),
                "automated": True,
            },
            {
                "step": 7,
                "agent": "Reverse Logistics Agent",
                "decision": f"{logistics_r['summary']['total_rma_issued']} RMAs issued; "
                            f"{logistics_r['summary']['total_units_in_reverse_flow']} units in reverse flow",
                "basis": "Return routing based on distributor location and risk priority",
                "timestamp": logistics_r["timestamp"],
                "hash": _hash(logistics_r["summary"]),
                "automated": True,
            },
            {
                "step": 8,
                "agent": "Verification Agent",
                "decision": f"Recall completion: {verification_r['scorecard']['completion_pct']}% | "
                            f"Gaps: {len(verification_r['gaps'])}",
                "basis": f"Verified: {verification_r['scorecard']['verified']} checks | "
                         f"Pending: {verification_r['scorecard']['pending']}",
                "timestamp": verification_r["timestamp"],
                "hash": _hash(verification_r["scorecard"]),
                "automated": True,
            },
        ]

        # ── Agent log entries (from shared audit_log) ─────────────────────────
        agent_logs = [{"seq": i+1, **entry} for i, entry in enumerate(self.audit)]

        # ── Evidence references ───────────────────────────────────────────────
        evidence = [
            {"ref": "QT-2026-441",     "type": "Quality Test Report",     "description": "Failed silica content test — BATCH-4401"},
            {"ref": "INC-2026-0891",   "type": "Customer Complaint",      "description": "Premature wear — FleetOps LLC — CRITICAL"},
            {"ref": "INC-2026-0892",   "type": "Customer Complaint",      "description": "Abnormal dust — Northeast Auto Service — HIGH"},
            {"ref": "INC-2026-0893",   "type": "Customer Complaint",      "description": "Squealing — Pacific Fleet Management — HIGH"},
            {"ref": "RML-1003",        "type": "Raw Material COA",        "description": "FrictionTech cert FT-2026-0812 — FAIL"},
            {"ref": "RML-1004",        "type": "Raw Material COA",        "description": "FrictionTech cert FT-2026-0819 — FAIL"},
            {"ref": human_approval_record["signature_ref"], "type": "Human Approval", "description": f"Signed by {human_approval_record['approver']}"},
        ]

        # ── Overall recall status ─────────────────────────────────────────────
        recall_status = "IN_PROGRESS"
        if verification_r["recall_complete"]:
            recall_status = "CLOSED"
        elif verification_r["scorecard"]["completion_pct"] > 80:
            recall_status = "SUBSTANTIALLY_COMPLETE"

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "recall_id": recall_id,
            "recall_status": recall_status,
            "recall_initiated": trigger_r["timestamp"],
            "recall_class": impact_r["recall_class"],
            "total_units_in_scope": impact_r["total_units_in_scope"],
            "financial_exposure": impact_r["financial_exposure_usd"]["total_estimated"],
            "completion_pct": verification_r["scorecard"]["completion_pct"],
            "decision_chain": decision_chain,
            "agent_activity_log": agent_logs,
            "evidence_references": evidence,
            "open_gaps": verification_r["gaps"],
            "regulatory_obligations": impact_r["regulatory_obligations"],
            "audit_integrity": {
                "total_log_entries": len(agent_logs),
                "decision_steps": len(decision_chain),
                "audit_hash": _hash({"chain": [d["hash"] for d in decision_chain]}),
                "generated_at": datetime.now().isoformat(),
            },
        }

        self._log(f"Audit trail compiled. Status: {recall_status} | "
                  f"Completion: {verification_r['scorecard']['completion_pct']}%")
        return result

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        self.audit.append(entry)
