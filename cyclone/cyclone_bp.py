import asyncio
import logging
import os
import threading
from flask import Blueprint, jsonify, render_template, current_app
from config.config_constants import BASE_DIR
from cyclone.cyclone_engine import Cyclone

# --- Setup Blueprint ---
cyclone_bp = Blueprint("cyclone", __name__, template_folder=".", url_prefix="/cyclone")
logger = logging.getLogger("CycloneBlueprint")
logger.setLevel(logging.INFO)

# --- Helper functions ---

def run_in_background(coro_func):
    def wrapper():
        asyncio.run(coro_func())
    thread = threading.Thread(target=wrapper)
    thread.start()

# --- Dashboard View (Optional) ---
@cyclone_bp.route("/dashboard", methods=["GET"])
def cyclone_dashboard():
    return render_template("cyclone.html")

# --- API Endpoints ---

@cyclone_bp.route("/run_market_updates", methods=["POST"])
def run_market_updates():
    try:
        run_in_background(lambda: Cyclone(poll_interval=60).run_market_updates())
        return jsonify({"message": "Market Updates Started."}), 202
    except Exception as e:
        logger.error(f"Market Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_position_updates", methods=["POST"])
def run_position_updates():
    try:
        run_in_background(lambda: asyncio.run(Cyclone(poll_interval=60).position_runner.update_positions_from_jupiter()))
        return jsonify({"message": "Position Updates Started."}), 202
    except Exception as e:
        logger.error(f"Position Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_dependent_updates", methods=["POST"])
def run_dependent_updates():
    try:
        run_in_background(lambda: Cyclone(poll_interval=60).run_enrich_positions())
        return jsonify({"message": "Dependent Updates Started."}), 202
    except Exception as e:
        logger.error(f"Dependent Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_alert_evaluations", methods=["POST"])
def run_alert_evaluations():
    try:
        run_in_background(lambda: Cyclone(poll_interval=60).run_alert_updates())
        return jsonify({"message": "Alert Evaluations Started."}), 202
    except Exception as e:
        logger.error(f"Alert Evaluations Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_system_updates", methods=["POST"])
def run_system_updates():
    try:
        run_in_background(lambda: Cyclone(poll_interval=60).run_system_updates())
        return jsonify({"message": "System Updates Started."}), 202
    except Exception as e:
        logger.error(f"System Updates Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/run_full_cycle", methods=["POST"])
def run_full_cycle():
    try:
        run_in_background(lambda: Cyclone(poll_interval=60).run_cycle())
        return jsonify({"message": "Full Cycle Started."}), 202
    except Exception as e:
        logger.error(f"Full Cycle Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/clear_all_data", methods=["POST"])
def clear_all_data():
    try:
        run_in_background(lambda: Cyclone(poll_interval=60).run_clear_all_data())
        return jsonify({"message": "Clear All Data Started."}), 202
    except Exception as e:
        logger.error(f"Clear All Data Error: {e}")
        return jsonify({"error": str(e)}), 500

@cyclone_bp.route("/cyclone_logs", methods=["GET"])
def api_cyclone_logs():
    try:
        log_file = os.path.join(BASE_DIR, "monitor", "operations_log.txt")
        if not os.path.exists(log_file):
            return jsonify({"logs": []})
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last_lines = lines[-50:]
        cleaned = [line.rstrip("\n") for line in last_lines]
        return jsonify({"logs": cleaned})
    except Exception as e:
        current_app.logger.exception("Error reading Cyclone logs:", exc_info=True)
        return jsonify({"error": str(e)}), 500
