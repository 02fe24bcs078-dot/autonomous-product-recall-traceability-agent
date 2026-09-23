"""
Recall Workflow Orchestrator
Drives the end-to-end agentic recall workflow:
  Detect → Trace → Scope → Contain → Communicate → Reverse Logistics → Verify → Audit
"""

import json
import copy
import random
from datetime import datetime

from data.supply_chain_data import get_full_dataset
from agents.trigger_agent import RecallTriggerAgent
from agents.traceability_agent import TraceabilityAgent
from agents.impact_agent import ImpactAnalysisAgent
from agents.containment_agent import ContainmentAgent
from agents.communication_agent import CommunicationAgent
from agents.reverse_logistics_agent import ReverseLogisticsAgent
from agents.verification_agent import VerificationAgent
from agents.audit_agent import AuditAgent


RECALL_ID = "RC-2026-0041"


def run_recall_workflow(human_approved: bool = True) -> dict:
    """
    Execute the complete autonomous product recall workflow.
    Returns the full results dict (used by the dashboard).
    """
    random.seed(42)   # deterministic demo runs

    # ── Shared state ─────────────────────────────────────────────────────────
    data_store = get_full_dataset()
    audit_log  = []

    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "agent": "ORCHESTRATOR",
        "message": f"Recall workflow initiated. Recall ID: {RECALL_ID}",
    })

    # ── Stage 1: Trigger Detection ────────────────────────────────────────────
    trigger_agent  = RecallTriggerAgent(data_store, audit_log)
    trigger_result = trigger_agent.analyze()

    if not trigger_result["trigger_confirmed"]:
        return {"error": "No recall trigger confirmed.", "recall_id": RECALL_ID}

    # ── Stage 2: Traceability ─────────────────────────────────────────────────
    trace_agent  = TraceabilityAgent(data_store, audit_log)
    trace_result = trace_agent.trace(trigger_result)

    # ── Stage 3: Impact Analysis ──────────────────────────────────────────────
    impact_agent  = ImpactAnalysisAgent(data_store, audit_log)
    impact_result = impact_agent.analyze(trace_result, trigger_result)

    # ── Stage 4: Human Approval Gate ─────────────────────────────────────────
    human_approval_record = {
        "approver": "Jane Mitchell",
        "approver_title": "VP Quality & Regulatory Affairs",
        "timestamp": datetime.now().isoformat(),
        "approved": human_approved,
        "rationale": (
            f"Approved voluntary Class I recall. Trigger score {trigger_result['severity_score']}/100. "
            f"Safety-critical brake system. Estimated exposure ${impact_result['financial_exposure_usd']['total_estimated']:,}. "
            f"Proceeding with full containment and distributor notification."
        ),
        "signature_ref": "e-sign-2026-RC-0041",
    }

    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "agent": "HUMAN APPROVAL",
        "message": f"Human approval {'GRANTED' if human_approved else 'PENDING'} by {human_approval_record['approver']}",
        "approved": human_approved,
    })

    if not human_approved:
        return {
            "recall_id": RECALL_ID,
            "stage": "AWAITING_HUMAN_APPROVAL",
            "trigger": trigger_result,
            "trace": trace_result,
            "impact": impact_result,
            "human_approval": human_approval_record,
        }

    # ── Stage 5: Containment ──────────────────────────────────────────────────
    containment_agent  = ContainmentAgent(data_store, audit_log)
    containment_result = containment_agent.contain(trace_result, impact_result,
                                                   human_approved=True)

    # ── Stage 6: Communications ───────────────────────────────────────────────
    comm_agent  = CommunicationAgent(data_store, audit_log)
    comm_result = comm_agent.communicate(trace_result, impact_result,
                                         trigger_result, RECALL_ID)

    # ── Stage 7: Reverse Logistics ────────────────────────────────────────────
    logistics_agent  = ReverseLogisticsAgent(data_store, audit_log)
    logistics_result = logistics_agent.plan(trace_result, impact_result)

    # ── Stage 8: Verification ─────────────────────────────────────────────────
    verification_agent  = VerificationAgent(data_store, audit_log)
    verification_result = verification_agent.verify(containment_result,
                                                     logistics_result,
                                                     comm_result)

    # ── Stage 9: Audit Trail ──────────────────────────────────────────────────
    audit_agent  = AuditAgent(data_store, audit_log)
    audit_result = audit_agent.compile(
        RECALL_ID, trigger_result, trace_result, impact_result,
        containment_result, comm_result, logistics_result,
        verification_result, human_approval_record,
    )

    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "agent": "ORCHESTRATOR",
        "message": "Recall workflow complete. All agents finished.",
        "recall_status": audit_result["recall_status"],
        "completion_pct": verification_result["scorecard"]["completion_pct"],
    })

    return {
        "recall_id": RECALL_ID,
        "workflow_complete": True,
        "trigger":       trigger_result,
        "trace":         trace_result,
        "impact":        impact_result,
        "human_approval":human_approval_record,
        "containment":   containment_result,
        "communications":comm_result,
        "logistics":     logistics_result,
        "verification":  verification_result,
        "audit":         audit_result,
        "data_store":    data_store,
    }


if __name__ == "__main__":
    results = run_recall_workflow(human_approved=True)
    print(json.dumps({
        "recall_id":       results["recall_id"],
        "trigger_level":   results["trigger"]["trigger_level"],
        "units_in_scope":  results["impact"]["total_units_in_scope"],
        "completion_pct":  results["verification"]["scorecard"]["completion_pct"],
        "recall_status":   results["audit"]["recall_status"],
        "financial_exposure": results["impact"]["financial_exposure_usd"]["total_estimated"],
    }, indent=2))
