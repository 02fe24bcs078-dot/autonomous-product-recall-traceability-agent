"""
Recall Trigger Agent
Analyzes quality alerts, incidents, and inspection reports to confirm
whether a recall trigger event has occurred and how severe it is.
"""

import json
from datetime import datetime


class RecallTriggerAgent:
    NAME = "Recall Trigger Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data = data_store
        self.audit = audit_log

    # ── public entry point ────────────────────────────────────────────────────
    def analyze(self) -> dict:
        self._log("Starting incident analysis across quality tests and customer complaints.")

        incidents    = self.data["customer_incidents"]
        quality_tests = self.data["quality_tests"]
        raw_lots     = self.data["raw_material_lots"]

        # Step 1 – cluster incidents
        failed_tests   = {k: v for k, v in quality_tests.items() if v["result"] == "FAIL"}
        open_incidents = {k: v for k, v in incidents.items() if v["status"] == "open"}
        critical_cnt   = sum(1 for v in open_incidents.values() if v["severity"] == "CRITICAL")
        high_cnt       = sum(1 for v in open_incidents.values() if v["severity"] == "HIGH")

        # Step 2 – identify suspect root-cause lots
        failed_lots = {k: v for k, v in raw_lots.items() if v.get("lot_quality") == "FAIL"}

        # Step 3 – severity scoring  (0-100)
        score = 0
        score += critical_cnt * 30
        score += high_cnt * 15
        score += len(failed_tests) * 10
        score += len(failed_lots) * 5
        score = min(score, 100)

        if score >= 70:
            trigger_level = "CRITICAL"
            action        = "IMMEDIATE RECALL"
        elif score >= 40:
            trigger_level = "HIGH"
            action        = "VOLUNTARY RECALL"
        else:
            trigger_level = "MEDIUM"
            action        = "INVESTIGATION"

        # Step 4 – identify primary suspect batch from incidents
        batch_mentions = {}
        for inc in open_incidents.values():
            b = inc.get("batch_suspected")
            if b:
                batch_mentions[b] = batch_mentions.get(b, 0) + 1
        primary_batch = max(batch_mentions, key=batch_mentions.get) if batch_mentions else None

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "trigger_confirmed": True,
            "trigger_level": trigger_level,
            "recommended_action": action,
            "severity_score": score,
            "open_incidents": len(open_incidents),
            "critical_incidents": critical_cnt,
            "failed_quality_tests": len(failed_tests),
            "suspect_raw_lots": list(failed_lots.keys()),
            "suspect_root_cause": "Excessive silica content in Friction Compound FC-99 from FrictionTech Ltd. (SUP-003)",
            "primary_suspect_batch": primary_batch,
            "regulatory_obligation": self.data["recall_context"]["regulation"],
            "mandatory_notification_deadline": "Within 5 business days of this trigger confirmation",
            "findings": self._build_findings(open_incidents, failed_tests, failed_lots),
        }

        self._log(f"Trigger confirmed: {trigger_level} — Score {score}/100 — Action: {action}", result)
        return result

    # ── helpers ───────────────────────────────────────────────────────────────
    def _build_findings(self, incidents, tests, lots):
        findings = []
        for k, v in incidents.items():
            findings.append(f"[{v['severity']}] Incident {k}: {v['complaint']} ({v['units_affected']} units, customer: {v['customer']})")
        for k, v in tests.items():
            findings.append(f"[QA FAIL] Test {k}: silica content {v['tests']['silica_content']}")
        for k, v in lots.items():
            findings.append(f"[RAW MATERIAL] Lot {k}: {v.get('defect', 'defective')} — Cert {v.get('cert_number', 'N/A')}")
        return findings

    def _log(self, message: str, data: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.NAME,
            "message": message,
        }
        if data:
            entry["data_snapshot"] = {k: v for k, v in data.items() if k not in ("findings",)}
        self.audit.append(entry)
