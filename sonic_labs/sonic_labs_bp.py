
# sonic_labs_bp.py

from flask import Blueprint, jsonify, current_app, request, render_template
import json
from positions.position_sync_service import PositionSyncService  # noqa: F401
from positions.position_core_service import PositionCoreService  # noqa: F401
from core.core_imports import retry_on_locked
from calc_core.calc_services import CalcServices
from app.system_bp import hedge_calculator_page, hedge_report_page

sonic_labs_bp = Blueprint("sonic_labs", __name__, template_folder="templates")

@sonic_labs_bp.route("/hedge_calculator", methods=["GET"])
@retry_on_locked()
def hedge_calculator():
    """Delegate to the system blueprint implementation."""
    return hedge_calculator_page()


@sonic_labs_bp.route("/hedge_report", methods=["GET"])
@retry_on_locked()
def hedge_report():
    """Delegate to the system blueprint implementation for hedge report."""
    return hedge_report_page()

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


@sonic_labs_bp.route("/hedge_labs", methods=["GET"])
@retry_on_locked()
def hedge_labs_page():
    """Render the Hedge Labs UI."""
    dl = current_app.data_locker
    hedges = dl.hedges.get_hedges() or []
    theme_config = dl.system.get_active_theme_profile() or {}
    return render_template(
        "hedge_labs.html",
        hedges=hedges,
        theme=theme_config,
    )


@sonic_labs_bp.route("/api/hedges", methods=["GET"])
@retry_on_locked()
def api_get_hedges():
    """Return current hedges as JSON."""
    hedges = current_app.data_locker.hedges.get_hedges() or []
    data = [
        {
            "id": h.id,
            "positions": h.positions,
            "total_long_size": h.total_long_size,
            "total_short_size": h.total_short_size,
            "total_heat_index": h.total_heat_index,
        }
        for h in hedges
    ]
    return jsonify({"hedges": data})


@sonic_labs_bp.route("/api/link_hedges", methods=["POST"])
@retry_on_locked()
def api_link_hedges():
    """Link hedges using HedgeCore."""
    try:
        from hedge_core.hedge_core import HedgeCore

        core = HedgeCore(current_app.data_locker)
        groups = core.link_hedges()
        return jsonify({"linked": len(groups)})
    except Exception as e:
        current_app.logger.error(f"Error linking hedges: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@sonic_labs_bp.route("/api/unlink_hedges", methods=["POST"])
@retry_on_locked()
def api_unlink_hedges():
    """Unlink all hedges."""
    try:
        from hedge_core.hedge_core import HedgeCore

        core = HedgeCore(current_app.data_locker)
        core.unlink_hedges()
        return jsonify({"unlinked": True})
    except Exception as e:
        current_app.logger.error(f"Error unlinking hedges: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@sonic_labs_bp.route("/api/test_calcs", methods=["GET"])
@retry_on_locked()
def api_test_calcs():
    """Run basic calculation tests and return results."""
    try:
        from calc_core.calculation_core import CalculationCore

        dl = current_app.data_locker
        positions = dl.positions.get_all_positions() or []
        core = CalculationCore(dl)
        totals = core.calculate_totals(positions)
        return jsonify({"totals": totals})
    except Exception as e:
        current_app.logger.error(f"Error running test calcs: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@sonic_labs_bp.route("/api/hedge_positions", methods=["GET"])
@retry_on_locked()
def api_get_hedge_positions():
    """Return position data for a specific hedge."""
    hedge_id = request.args.get("hedge_id")
    if not hedge_id:
        return jsonify({"error": "hedge_id required"}), 400

    dl = current_app.data_locker
    hedges = dl.hedges.get_hedges() or []
    hedge = next((h for h in hedges if str(h.id) == hedge_id), None)
    if not hedge:
        return jsonify({"error": "Hedge not found"}), 404

    pos_list = []
    for pid in hedge.positions:
        pos = dl.positions.get_position_by_id(pid)
        if pos:
            pos_list.append(dict(pos))

    return jsonify({"positions": pos_list})


@sonic_labs_bp.route("/api/evaluate_hedge", methods=["GET"])
@retry_on_locked()
def api_evaluate_hedge():
    """Evaluate hedge positions at a specific price."""
    hedge_id = request.args.get("hedge_id")
    price = request.args.get("price")
    if not hedge_id or price is None:
        return jsonify({"error": "hedge_id and price required"}), 400

    try:
        price = float(price)
    except ValueError:
        return jsonify({"error": "invalid price"}), 400

    dl = current_app.data_locker
    hedges = dl.hedges.get_hedges() or []
    hedge = next((h for h in hedges if str(h.id) == hedge_id), None)
    if not hedge:
        return jsonify({"error": "Hedge not found"}), 404

    calc = CalcServices()
    results = {}
    eval_positions = []

    for pid in hedge.positions:
        pos = dl.positions.get_position_by_id(pid)
        if not pos:
            continue
        eval_data = calc.evaluate_at_price(pos, price)
        ptype = str(pos.get("position_type", "")).lower()
        results[ptype] = {
            "id": pid,
            **{k: round(v, 6) if isinstance(v, float) else v for k, v in eval_data.items()},
        }
        pos_copy = dict(pos)
        pos_copy.update(eval_data)
        eval_positions.append(pos_copy)

    totals = calc.calculate_totals(eval_positions)

    return jsonify({"long": results.get("long"), "short": results.get("short"), "totals": totals})
