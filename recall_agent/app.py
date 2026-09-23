"""
Flask web server — serves the Recall Agent dashboard.
Runs the full workflow on first request and caches results.
"""

import json
import os
import sys

from flask import Flask, jsonify, render_template_string, send_from_directory

# Make sure recall_agent package is importable
sys.path.insert(0, os.path.dirname(__file__))
from orchestrator import run_recall_workflow

app = Flask(__name__, static_folder="static")

_RESULTS_CACHE = None


def get_results():
    global _RESULTS_CACHE
    if _RESULTS_CACHE is None:
        _RESULTS_CACHE = run_recall_workflow(human_approved=True)
    return _RESULTS_CACHE


@app.route("/")
def dashboard():
    with open(os.path.join(os.path.dirname(__file__), "static", "dashboard.html"), encoding="utf-8") as f:
        return f.read()


@app.route("/api/results")
def api_results():
    r = get_results()
    # Strip data_store raw dict; expose only the fields the dashboard needs
    payload = {k: v for k, v in r.items() if k != "data_store"}
    # Pass through subset of data_store needed for trigger / comms detail pages
    ds = r.get("data_store", {})
    payload["data_store"] = {
        "customer_incidents": ds.get("customer_incidents", {}),
        "recall_context":     ds.get("recall_context", {}),
    }
    return jsonify(payload)


@app.route("/api/graph")
def api_graph():
    r = get_results()
    return jsonify(r["trace"]["genealogy_graph"])


@app.route("/api/run", methods=["POST"])
def api_run():
    global _RESULTS_CACHE
    _RESULTS_CACHE = None   # force re-run
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("Starting Recall Agent Dashboard on http://localhost:5050")
    app.run(debug=False, port=5050)
