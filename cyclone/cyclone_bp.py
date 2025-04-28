#!/usr/bin/env python
"""
cyclone_bp.py
Description:
    Flask blueprint for Cyclone API routes.
    - Handles Market Updates, Position Updates, Clear All Data, Full Cycle, etc.
"""

import asyncio
import logging
import os
from flask import Blueprint, jsonify, render_template, current_app
from config.config_constants import BASE_DIR
from cyclone.cyclone import Cyclone  # Your core logic

# --- Setup Blueprint ---
cyclone_bp = Blueprint("cyclone", __name__, template_folder=".", url_prefix="/cyclone")
logger = logging.getLogger("CycloneBlueprint")
logger.setLevel(logging.INFO)

# --- Dashboard View ---
@cyclone_bp.route("/dashboard", methods=["GET"])
def cyclone_dashboard():
    return render_template("cyclone.html")  # Optional, if you have cyclone.html

# --- Actual API Endpoints ---
@cyclone_bp.route("/run_market_updates", methods=["POST"])
def run_market_updates():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_market_updates())
        return jsonify({"message": "Market Updates Completed."}), 200
    except Exception as e:
        logger.error(f"Market Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_position_updates", methods=["POST"])
def run_position_updates():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_position_updates())
        return jsonify({"message": "Position Updates Completed."}), 200
    except Exception as e:
        logger.error(f"Position Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_dependent_updates", methods=["POST"])
def run_dependent_updates():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_enrich_positions())
        return jsonify({"message": "Dependent Updates Completed."}), 200
    except Exception as e:
        logger.error(f"Dependent Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_alert_evaluations", methods=["POST"])
def run_alert_evaluations():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_alert_updates())
        return jsonify({"message": "Alert Evaluations Completed."}), 200
    except Exception as e:
        logger.error(f"Alert Evaluations Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_system_updates", methods=["POST"])
def run_system_updates():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_system_updates())
        return jsonify({"message": "System Updates Completed."}), 200
    except Exception as e:
        logger.error(f"System Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_full_cycle", methods=["POST"], endpoint="run_full_cycle_api")
def run_full_cycle():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_cycle())
        return jsonify({"message": "Full Cycle Completed."}), 200
    except Exception as e:
        logger.error(f"Full Cycle Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/clear_all_data", methods=["POST"], endpoint="clear_all_data_api")
def clear_all_data():
    try:
        cyclone = Cyclone(poll_interval=60)
        asyncio.run(cyclone.run_clear_all_data())
        return jsonify({"message": "All Data Cleared."}), 200
    except Exception as e:
        logger.error(f"Clear All Data Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Optional: Log Fetching (for console) ---
@cyclone_bp.route("/cyclone_logs", methods=["GET"])
def api_cyclone_logs():
    try:
        log_file = os.path.join(BASE_DIR, "operations_log.txt")
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last_lines = lines[-50:]
        cleaned = [line.rstrip("\n") for line in last_lines]
        return jsonify({"logs": cleaned})
    except Exception as e:
        current_app.logger.exception("Error reading Cyclone logs:", exc_info=True)
        return jsonify({"error": str(e)}), 500
