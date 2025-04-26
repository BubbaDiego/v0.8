#!/usr/bin/env python
"""
cyclone_bp.py
Description:
    Flask blueprint for the Cyclone dashboard and related routes.
    - The main Cyclone view (cyclone.html).
    - A log polling endpoint for real-time console updates.
    - Routes for the various control actions.
Usage:
    Import and register this blueprint in your main application, e.g.:
        from cyclone_bp import cyclone_bp
        app.register_blueprint(cyclone_bp)
"""

import logging
import os
from flask import Blueprint, jsonify, render_template, current_app
from config.config_constants import BASE_DIR

logger = logging.getLogger("CycloneBlueprint")
logger.setLevel(logging.CRITICAL)

cyclone_bp = Blueprint("cyclone", __name__, template_folder=".")

@cyclone_bp.route("/cyclone.html")
def cyclone_dashboard():
    return render_template("cyclone.html")

# --- Full Cycle Update Route ---
import asyncio
from .cyclone import Cyclone

@cyclone_bp.route("/api/run_full_cycle", methods=["POST"], endpoint="run_full_cycle_api")
def run_full_cycle():
    """
    Runs a full cycle of updates by invoking Cyclone's run_cycle() method.
    """
    try:
        cyclone_instance = Cyclone(poll_interval=60)
        # Run one complete cycle synchronously
        asyncio.run(cyclone_instance.run_cycle())
        return jsonify({"message": "Full Cycle Completed."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Other API Endpoints ---

@cyclone_bp.route("/api/cyclone_logs", methods=["GET"])
def api_cyclone_logs():
    """
    Returns the last 50 lines of operations_log.txt as JSON for the Cyclone console.
    """
    try:
        log_file = os.path.join(BASE_DIR, "operations_log.txt")
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Return the last 50 lines
        last_lines = lines[-50:]
        # Strip trailing newlines
        cleaned = [line.rstrip("\n") for line in last_lines]
        return jsonify({"logs": cleaned})
    except Exception as e:
        current_app.logger.exception("Error reading logs for cyclone:", exc_info=True)
        return jsonify({"error": str(e)}), 500

# --- Placeholder Routes for Other Controls ---
@cyclone_bp.route("/api/run_market_updates", methods=["POST"])
def run_market_updates():
    """
    Placeholder for 'Market Updates'.
    """
    return jsonify({"message": "Market Updates Completed (placeholder)."}), 200

@cyclone_bp.route("/api/run_position_updates", methods=["POST"])
def run_position_updates():
    """
    Placeholder for 'Position Updates'.
    """
    return jsonify({"message": "Position Updates Completed (placeholder)."}), 200

@cyclone_bp.route("/api/run_dependent_updates", methods=["POST"])
def run_dependent_updates():
    """
    Placeholder for 'Dependent Updates'.
    """
    return jsonify({"message": "Dependent Updates Completed (placeholder)."}), 200

@cyclone_bp.route("/api/run_alert_evaluations", methods=["POST"])
def run_alert_evaluations():
    """
    Placeholder for 'Alert Evaluations'.
    """
    return jsonify({"message": "Alert Evaluations Completed (placeholder)."}), 200

@cyclone_bp.route("/api/run_system_updates", methods=["POST"])
def run_system_updates():
    """
    Placeholder for 'System Updates'.
    """
    return jsonify({"message": "System Updates Completed (placeholder)."}), 200

import asyncio
from .cyclone import Cyclone
from flask import Blueprint, jsonify

@cyclone_bp.route("/api/clear_all_data", methods=["POST"])
def clear_all_data_api():
    """
    Clears alerts, prices, and positions via Cyclone.
    """
    try:
        # instantiate and run the clear‐all task
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_clear_all_data())
        return jsonify({"message": "All data cleared."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
