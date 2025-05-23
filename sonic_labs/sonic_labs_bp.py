
# sonic_labs_bp.py

from flask import Blueprint, jsonify, current_app, request
import json
from positions.position_sync_service import PositionSyncService  # noqa: F401
from positions.position_core_service import PositionCoreService  # noqa: F401
from core.core_imports import retry_on_locked
from app.system_bp import hedge_calculator_page

sonic_labs_bp = Blueprint("sonic_labs", __name__, template_folder="templates")

@sonic_labs_bp.route("/hedge_calculator", methods=["GET"])
@retry_on_locked()
def hedge_calculator():
    """Delegate to the system blueprint implementation."""
    return hedge_calculator_page()

@sonic_labs_bp.route("/sonic_sauce", methods=["GET"])
def get_sonic_sauce():
    try:
        dl = current_app.data_locker
        hedge_mods = dl.modifiers.get_all_modifiers("hedge_modifiers")
        heat_mods = dl.modifiers.get_all_modifiers("heat_modifiers")
        return jsonify({"hedge_modifiers": hedge_mods, "heat_modifiers": heat_mods}), 200
    except Exception as e:
        current_app.logger.error(f"Error loading sonic sauce: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@sonic_labs_bp.route("/sonic_sauce", methods=["POST"])
def update_sonic_sauce():
    try:
        data = request.get_json() or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid payload"}), 400
        dl = current_app.data_locker
        for group, mods in data.items():
            if not isinstance(mods, dict):
                continue
            for key, value in mods.items():
                dl.modifiers.set_modifier(key, float(value), group=group)
        return jsonify({"success": True}), 200
    except Exception as e:
        current_app.logger.error(f"Error saving sonic sauce: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
