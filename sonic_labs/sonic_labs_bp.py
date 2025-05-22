
# sonic_labs_bp.py

from flask import Blueprint, render_template, jsonify, current_app, request
import json
from positions.position_sync_service import PositionSyncService  # noqa: F401
from positions.position_core_service import PositionCoreService  # noqa: F401
from utils.json_manager import JsonType
from core.core_imports import DB_PATH, retry_on_locked

sonic_labs_bp = Blueprint("sonic_labs", __name__, template_folder="templates")

@sonic_labs_bp.route("/hedge_calculator", methods=["GET"])
@retry_on_locked()
def hedge_calculator():
    try:
        positions = PositionService.get_all_positions(DB_PATH)
        long_positions = [p for p in positions if p.get("position_type", "").upper() == "LONG"]
        short_positions = [p for p in positions if p.get("position_type", "").upper() == "SHORT"]

        dl = current_app.data_locker
        theme_config = dl.system.get_active_theme_profile() or {}
        modifiers = dl.modifiers.get_all_modifiers("hedge_modifiers")

        if not modifiers:
            try:
                json_manager = current_app.json_manager
                modifiers = json_manager.load("sonic_sauce.json", json_type=JsonType.SONIC_SAUCE)
            except Exception:
                modifiers = {}

        return render_template("hedge_calculator.html",
                               theme=theme_config,
                               long_positions=long_positions,
                               short_positions=short_positions,
                               modifiers=modifiers)
    except Exception as e:
        current_app.logger.error(f"Error rendering Hedge Calculator: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@sonic_labs_bp.route("/sonic_sauce", methods=["GET"])
def get_sonic_sauce():
    try:
        json_manager = current_app.json_manager
        modifiers = json_manager.load("sonic_sauce.json", json_type=JsonType.SONIC_SAUCE)
        return jsonify(modifiers), 200
    except Exception as e:
        current_app.logger.error(f"Error loading sonic sauce: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@sonic_labs_bp.route("/sonic_sauce", methods=["POST"])
def update_sonic_sauce():
    try:
        data = request.get_json()
        json_manager = current_app.json_manager
        json_manager.save("sonic_sauce.json", data, json_type=JsonType.SONIC_SAUCE)
        return jsonify({"success": True}), 200
    except Exception as e:
        current_app.logger.error(f"Error saving sonic sauce: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
