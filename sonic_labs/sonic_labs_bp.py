
# sonic_labs_bp.py

from flask import Blueprint, render_template, jsonify, current_app, request
import json
from positions.position_sync_service import PositionSyncService  # noqa: F401
from positions.position_core_service import PositionCoreService  # noqa: F401
from utils.json_manager import JsonType
from core.core_imports import DB_PATH, retry_on_locked
from positions.hedge_manager import HedgeManager

sonic_labs_bp = Blueprint("sonic_labs", __name__, template_folder="templates")

@sonic_labs_bp.route("/hedge_calculator", methods=["GET"])
@retry_on_locked()
def hedge_calculator():
    try:
        positions = PositionService.get_all_positions(DB_PATH)
        long_positions = [p for p in positions if p.get("position_type", "").upper() == "LONG"]
        short_positions = [p for p in positions if p.get("position_type", "").upper() == "SHORT"]

        # Determine default selections from the first detected hedge pair
        hedges = HedgeManager(positions).get_hedges()
        default_long_id = None
        default_short_id = None
        if hedges:
            first = hedges[0]
            pos_map = {p.get("id"): p for p in positions}
            for pid in first.positions:
                pos = pos_map.get(pid)
                if not pos:
                    continue
                ptype = str(pos.get("position_type", "")).upper()
                if ptype == "LONG" and default_long_id is None:
                    default_long_id = pid
                elif ptype == "SHORT" and default_short_id is None:
                    default_short_id = pid
                if default_long_id and default_short_id:
                    break

        dl = current_app.data_locker
        theme_config = dl.system.get_active_theme_profile() or {}
        hedge_mods = dl.modifiers.get_all_modifiers("hedge_modifiers")
        heat_mods = dl.modifiers.get_all_modifiers("heat_modifiers")
        modifiers = {"hedge_modifiers": hedge_mods, "heat_modifiers": heat_mods}


        if not hedge_mods or not heat_mods:
            try:
                json_manager = current_app.json_manager
                fallback = json_manager.load("sonic_sauce.json", json_type=JsonType.SONIC_SAUCE) or {}
                hedge_mods = hedge_mods or fallback.get("hedge_modifiers", {})
                heat_mods = heat_mods or fallback.get("heat_modifiers", {})
                modifiers = {"hedge_modifiers": hedge_mods, "heat_modifiers": heat_mods}
            except Exception:
                pass


        return render_template(
            "hedge_calculator.html",
            theme=theme_config,
            long_positions=long_positions,
            short_positions=short_positions,
            modifiers=modifiers,
            default_long_id=default_long_id,
            default_short_id=default_short_id,
        )
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
