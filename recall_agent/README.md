# Autonomous Product Recall & Traceability Agent

An AI-powered multi-agent system for autonomous product recall investigation,
containment, coordination, reverse logistics, and verification.

## Scenario

Automotive brake pad manufacturer **BrakeTech Industries LLC** discovers a
defective batch of raw friction compound (excessive silica content: 18% vs 9%
spec) from supplier **FrictionTech Ltd. (SUP-003)**, potentially affecting
**18,700 units** across 4 production batches, 3 warehouses, 10 distributors,
and international shipments.

## Multi-Agent Architecture

| # | Agent | Responsibility |
|---|-------|----------------|
| 1 | **Recall Trigger Agent** | Analyzes quality tests + customer incidents; scores severity |
| 2 | **Traceability Agent** | Traces raw lot → batch → warehouse → distributor graph |
| 3 | **Impact Analysis Agent** | Quantifies scope, financial exposure, distributor risk scores |
| 4 | **Human Approval Gate** | Authorized personnel approve execution before containment |
| 5 | **Containment Agent** | Issues warehouse holds, suspends in-transit shipments, quarantines raw lots |
| 6 | **Communication Agent** | Drafts + dispatches distributor, regulatory, and internal notifications |
| 7 | **Reverse Logistics Agent** | Issues RMAs, plans return routing, assigns return hubs |
| 8 | **Verification Agent** | Verifies completion of all actions; identifies gaps for re-planning |
| 9 | **Audit Agent** | Compiles tamper-evident audit trail with decision chain + SHA-256 hashes |

## Agentic Workflow

```
Detect → Trace → Scope → [Human Approval] → Contain → Communicate
       → Reverse Logistics → Verify → Audit → (Re-plan if gaps)
```

## Dashboard Pages

- **Dashboard** — KPIs, agent workflow visualization, charts (units, financials, progress, batches)
- **Recall Trigger** — Incident analysis, severity scoring, root cause findings
- **Traceability Graph** — Interactive force-directed supply chain graph (ECharts)
- **Impact Analysis** — Financial exposure, recovery analysis, distributor risk scores
- **Containment** — All 21 containment actions with execution status
- **Communications** — 15 notifications across distributors, regulators, internal teams
- **Reverse Logistics** — 10 RMAs, warehouse transfers, disposition plan
- **Verification** — Completion scorecard, gap analysis, re-plan recommendations
- **Audit Trail** — Full decision chain, agent activity log, evidence references

## Quick Start

```bash
cd recall_agent
pip install flask
python app.py
# Open http://localhost:5050
```

## Key Results (Demo Run)

| Metric | Value |
|--------|-------|
| Recall ID | RC-2026-0041 |
| Trigger Level | CRITICAL (Score: 75/100) |
| Units In Scope | 18,700 |
| Batches Affected | 4 (BATCH-4401 through BATCH-4404) |
| Distributors Affected | 10 (across USA, Canada, Mexico, Europe, APAC) |
| Financial Exposure | $1,809,045 |
| Recall Completion | 69.6% (IN_PROGRESS — gaps require re-planning) |
| Decision Steps | 8 (including 1 human approval) |
| Audit Log Entries | 17 |

## File Structure

```
recall_agent/
├── app.py                          # Flask web server
├── orchestrator.py                 # Workflow orchestrator
├── requirements.txt
├── agents/
│   ├── trigger_agent.py            # Recall Trigger Agent
│   ├── traceability_agent.py       # Traceability Agent
│   ├── impact_agent.py             # Impact Analysis Agent
│   ├── containment_agent.py        # Containment Agent
│   ├── communication_agent.py      # Communication Agent
│   ├── reverse_logistics_agent.py  # Reverse Logistics Agent
│   ├── verification_agent.py       # Verification Agent
│   └── audit_agent.py              # Audit Agent
├── data/
│   └── supply_chain_data.py        # Mock supply chain dataset
└── static/
    └── dashboard.html              # Full visualization dashboard
```
