"""
Communication Agent
Drafts and dispatches recall notifications to distributors, regulators,
internal teams, and customers. Tracks communication status.
"""

from datetime import datetime


NOTIFICATION_TEMPLATES = {
    "distributor": """
URGENT PRODUCT RECALL NOTICE — {recall_id}

Dear {contact_name},

{company_name} is initiating an IMMEDIATE voluntary recall of Heavy Duty Brake Pads
(Product Codes: BP-2200-F, BP-2200-R, BP-2200-HV) from production batches {batches}.

DEFECT DESCRIPTION:
A supplier quality deviation has been identified: excessive silica content (18%+ vs
9% specification) in raw friction compound from lot(s) {raw_lots}. This may result
in accelerated brake pad wear, reduced braking efficiency, and potential safety risk.

IMMEDIATE ACTIONS REQUIRED:
1. Place a HOLD on all inventory of the above product codes received since {start_date}
2. Do NOT ship any remaining stock to customers
3. Complete the enclosed distributor recall acknowledgement form within 24 hours
4. Contact us at recalls@company.com or +1-800-RECALL-1

Serial/Lot identification: Any unit with date code {date_range} on packaging.

We sincerely apologise for this inconvenience. Customer safety is our highest priority.

{company_name} Recall Management Team
Recall Coordinator: {coordinator}
Direct Line: +1-800-555-9999
""",
    "regulator": """
NHTSA / FMCSA VOLUNTARY RECALL NOTIFICATION

Manufacturer: BrakeTech Industries LLC
NHTSA Recall Number: [PENDING]
Date of Notification: {date}
Recall Classification: Class I — Safety Critical

SUBJECT VEHICLES / COMPONENTS:
Heavy Duty Brake Pads — BP-2200-F, BP-2200-R, BP-2200-HV
Production batches: {batches}
Approximate units: {total_units}

DESCRIPTION OF DEFECT:
Excessive silica content detected in raw friction compound (FrictionTech FC-99).
Silica content measured at 18.3% against specification of ≤9.0%.
Potential consequence: Premature wear resulting in reduced stopping distance.

REMEDY:
Free replacement of all affected brake pads at authorized service centers.

OWNER NOTIFICATION: Letters to be mailed within 30 days of this filing.

Contact: recall-compliance@braketech.com
""",
    "internal_alert": """
[INTERNAL — RECALL MANAGEMENT SYSTEM]
RECALL INITIATED: {recall_id}
Trigger Level: {trigger_level}
Batches: {batches}
Units in scope: {total_units}
Financial exposure: ${exposure:,}

IMMEDIATE ACTIONS:
- Quality team: Retain all physical samples from batches {batches}
- Procurement: Issue Supplier Corrective Action Request to SUP-003 (FrictionTech)
- Legal: Brief counsel on regulatory timeline obligations
- Customer Service: Activate hotline protocol RC-7
- Finance: Reserve ${exposure:,} for recall costs

Recall Coordinator assigned: Jane Mitchell (jmitchell@braketech.com)
""",
}


class CommunicationAgent:
    NAME = "Communication Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def communicate(self, trace_result: dict, impact_result: dict,
                    trigger_result: dict, recall_id: str) -> dict:
        self._log(f"Generating recall communications for {recall_id}.")

        batches      = ", ".join(trace_result["affected_batches"])
        raw_lots     = ", ".join(trigger_result["suspect_raw_lots"])
        total_units  = impact_result["total_units_in_scope"]
        exposure     = impact_result["financial_exposure_usd"]["total_estimated"]
        distributors = self.data["distributors"]
        dist_detail  = trace_result["affected_distributor_detail"]
        today        = datetime.now().strftime("%Y-%m-%d")

        communications = []

        # ── Distributor notifications ────────────────────────────────────────
        for dist_id, dist in dist_detail.items():
            info = distributors[dist_id]
            msg = NOTIFICATION_TEMPLATES["distributor"].format(
                recall_id=recall_id,
                contact_name=info["contact"].split("@")[0].replace(".", " ").title(),
                company_name=info["name"],
                batches=batches,
                raw_lots=raw_lots,
                start_date="2026-06-15",
                date_range="2026-07 / 2026-08",
                coordinator="Jane Mitchell",
            )
            communications.append({
                "comm_id": f"COMM-{dist_id}-001",
                "type": "DISTRIBUTOR_RECALL_NOTICE",
                "recipient": dist_id,
                "recipient_name": info["name"],
                "channel": "email",
                "to": info["contact"],
                "subject": f"URGENT: Product Recall Notice — {recall_id}",
                "body": msg.strip(),
                "status": "QUEUED",
                "priority": impact_result["distributor_risk_scores"].get(
                    dist_id, {}).get("priority", "MEDIUM"),
                "sent_at": None,
            })

        # ── Regulatory notifications ──────────────────────────────────────────
        for agency in self.data["recall_context"]["agencies"]:
            reg_msg = NOTIFICATION_TEMPLATES["regulator"].format(
                date=today, batches=batches, total_units=total_units)
            communications.append({
                "comm_id": f"COMM-REG-{agency.replace(' ', '_')}",
                "type": "REGULATORY_NOTIFICATION",
                "recipient": agency,
                "recipient_name": agency,
                "channel": "certified_mail+portal",
                "subject": f"Voluntary Recall Notification — {recall_id}",
                "body": reg_msg.strip(),
                "status": "DRAFT",
                "priority": "CRITICAL",
                "sent_at": None,
            })

        # ── Internal alert ────────────────────────────────────────────────────
        int_msg = NOTIFICATION_TEMPLATES["internal_alert"].format(
            recall_id=recall_id,
            trigger_level=trigger_result["trigger_level"],
            batches=batches,
            total_units=total_units,
            exposure=exposure,
        )
        communications.append({
            "comm_id": f"COMM-INT-001",
            "type": "INTERNAL_ALERT",
            "recipient": "ALL_INTERNAL_TEAMS",
            "recipient_name": "Internal (Quality, Procurement, Legal, CS, Finance)",
            "channel": "internal_system+email",
            "subject": f"RECALL INITIATED — {recall_id}",
            "body": int_msg.strip(),
            "status": "SENT",
            "priority": "CRITICAL",
            "sent_at": datetime.now().isoformat(),
        })

        # Mark HIGH priority dist comms as sent (simulated auto-send)
        for comm in communications:
            if comm["type"] == "DISTRIBUTOR_RECALL_NOTICE" and comm["priority"] == "HIGH":
                comm["status"] = "SENT"
                comm["sent_at"] = datetime.now().isoformat()

        sent  = [c for c in communications if c["status"] == "SENT"]
        queued= [c for c in communications if c["status"] == "QUEUED"]
        draft = [c for c in communications if c["status"] == "DRAFT"]

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "recall_id": recall_id,
            "communications": communications,
            "summary": {
                "total_communications": len(communications),
                "sent": len(sent),
                "queued": len(queued),
                "draft": len(draft),
                "distributor_notices": sum(1 for c in communications if c["type"] == "DISTRIBUTOR_RECALL_NOTICE"),
                "regulatory_filings": sum(1 for c in communications if c["type"] == "REGULATORY_NOTIFICATION"),
                "internal_alerts": sum(1 for c in communications if c["type"] == "INTERNAL_ALERT"),
            },
        }

        self._log(
            f"Communications generated: {len(communications)} total | "
            f"{len(sent)} sent | {len(queued)} queued | {len(draft)} draft.",
            result,
        )
        return result

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        if data:
            entry["comm_summary"] = data.get("summary")
        self.audit.append(entry)
