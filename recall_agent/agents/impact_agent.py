"""
Impact Analysis Agent
Quantifies the recall scope: units at risk, financial exposure, regulatory
obligations, and risk-scores each affected node in the supply chain.
"""

from datetime import datetime


UNIT_COST_USD    = 42.50   # avg selling price per brake pad unit
INSTALLATION_COST = 180.0  # average labour cost per vehicle
UNITS_PER_VEHICLE = 4

SEVERITY_WEIGHT = {"CRITICAL": 1.0, "HIGH": 0.7, "MEDIUM": 0.4}


class ImpactAnalysisAgent:
    NAME = "Impact Analysis Agent"

    def __init__(self, data_store: dict, audit_log: list):
        self.data  = data_store
        self.audit = audit_log

    def analyze(self, trace_result: dict, trigger_result: dict) -> dict:
        self._log("Starting impact analysis and financial exposure calculation.")

        qty    = trace_result["quantity_summary"]
        dist_d = trace_result["affected_distributor_detail"]
        incidents = self.data["customer_incidents"]
        ctx    = self.data["recall_context"]

        total_units = qty["total_units_produced"]
        in_wh       = qty["total_units_in_warehouse"]
        shipped     = qty["total_units_shipped"]
        in_transit  = qty["in_transit"]
        delivered   = qty["delivered_to_distributors"]

        # ── Financial exposure ────────────────────────────────────────────────
        product_cost      = total_units * UNIT_COST_USD
        replacement_cost  = total_units * UNIT_COST_USD
        labor_cost        = (total_units / UNITS_PER_VEHICLE) * INSTALLATION_COST
        logistics_cost    = total_units * 3.20          # return shipping estimate
        regulatory_fine   = ctx["potential_fine_per_day"] * 5   # 5-day window
        total_exposure    = replacement_cost + labor_cost + logistics_cost + regulatory_fine

        # ── Recovery probability by location ─────────────────────────────────
        recovery = {
            "warehouse_stock":    {"units": in_wh,      "recovery_pct": 98, "effort": "LOW"},
            "in_transit":         {"units": in_transit,  "recovery_pct": 90, "effort": "MEDIUM"},
            "delivered_to_dist":  {"units": delivered,   "recovery_pct": 75, "effort": "HIGH"},
        }
        weighted_recovery = sum(
            v["units"] * v["recovery_pct"] / 100 for v in recovery.values()
        )
        overall_recovery_pct = round(weighted_recovery / total_units * 100, 1) if total_units else 0

        # ── Risk-score each distributor ───────────────────────────────────────
        dist_risk = {}
        for dist_id, dist in dist_d.items():
            ship_count   = len(dist["shipments"])
            units        = dist["total_units"]
            in_transit_f = any(s["status"] == "in_transit" for s in dist["shipments"])
            score = min(100, units // 10 + ship_count * 5 + (20 if in_transit_f else 0))
            dist_risk[dist_id] = {
                "name": dist["name"],
                "units_at_risk": units,
                "risk_score": score,
                "priority": "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW",
                "in_transit": in_transit_f,
            }

        # ── Customer impact ───────────────────────────────────────────────────
        total_customer_units = sum(inc["units_affected"] for inc in incidents.values())
        vehicles_potentially_affected = delivered // UNITS_PER_VEHICLE

        # ── Safety risk classification ────────────────────────────────────────
        safety_risk = "CRITICAL"   # brake system = life-safety
        recall_class = ctx["recall_class"]

        result = {
            "agent": self.NAME,
            "timestamp": datetime.now().isoformat(),
            "total_units_in_scope": total_units,
            "safety_risk_level": safety_risk,
            "recall_class": recall_class,
            "quantity_breakdown": {
                "warehouse_stock": in_wh,
                "in_transit": in_transit,
                "delivered_to_distributors": delivered,
            },
            "financial_exposure_usd": {
                "product_replacement": round(replacement_cost),
                "labor_installation": round(labor_cost),
                "return_logistics": round(logistics_cost),
                "regulatory_fines": round(regulatory_fine),
                "total_estimated": round(total_exposure),
            },
            "recovery_analysis": recovery,
            "estimated_overall_recovery_pct": overall_recovery_pct,
            "distributor_risk_scores": dist_risk,
            "customer_impact": {
                "confirmed_complaint_units": total_customer_units,
                "vehicles_potentially_affected": vehicles_potentially_affected,
                "complaint_count": len(incidents),
            },
            "regulatory_obligations": {
                "regulation": ctx["regulation"],
                "agencies": ctx["agencies"],
                "deadline": ctx["mandatory_notification"],
            },
            "affected_batch_count": len(trace_result["affected_batches"]),
            "affected_distributor_count": len(dist_d),
        }

        self._log(
            f"Impact analysis complete. Total scope: {total_units} units | "
            f"Financial exposure: ${total_exposure:,.0f} | Recovery est.: {overall_recovery_pct}%",
            result,
        )
        return result

    def _log(self, message: str, data: dict = None):
        entry = {"timestamp": datetime.now().isoformat(), "agent": self.NAME, "message": message}
        if data:
            entry["financial_exposure"] = data.get("financial_exposure_usd")
            entry["recovery_pct"] = data.get("estimated_overall_recovery_pct")
        self.audit.append(entry)
