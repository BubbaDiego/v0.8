import os
import sys
import json
import logging
from flask import Blueprint, request, jsonify, render_template, current_app
from config.config_constants import BASE_DIR, ALERT_LIMITS_PATH, R2VAULT_IMAGE
from pathlib import Path
#from utils.operations_manager import OperationsLogger
from utils.json_manager import JsonManager, JsonType
from sonic_labs.hedge_manager import HedgeManager
from cyclone.cyclone import Cyclone

from alerts.alert_manager import manager as alert_manager

from time import time

# Ensure the current directory is in sys.path so we can import alert_manager.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Create the blueprint with URL prefix '/alerts'
alerts_bp = Blueprint('alerts_bp', __name__, url_prefix='/alerts', template_folder='.')

logger = logging.getLogger("AlertManagerLogger")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def convert_types_in_dict(d):
    if isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            new_d[k] = convert_types_in_dict(v)
        return new_d
    elif isinstance(d, list):
        return [convert_types_in_dict(item) for item in d]
    elif isinstance(d, str):
        if d.strip() == "":
            return None  # Avoid converting empty strings to 0.
        low = d.lower().strip()
        if low in ["true", "on"]:
            return True
        elif low in ["false", "off"]:
            return False
        else:
            try:
                return float(d)
            except ValueError:
                return d
    else:
        return d



def parse_nested_form(form: dict) -> dict:
    updated = {}
    for full_key, value in form.items():
        if isinstance(value, list):
            value = value[-1]
        full_key = full_key.strip()
        keys = []
        part = ""
        for char in full_key:
            if char == "[":
                if part:
                    keys.append(part)
                    part = ""
            elif char == "]":
                if part:
                    keys.append(part)
                    part = ""
            else:
                part += char
        if part:
            keys.append(part)
        current = updated
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                if isinstance(value, str):
                    lower_val = value.lower().strip()
                    if lower_val == "true":
                        v = True
                    elif lower_val == "false":
                        v = False
                    else:
                        try:
                            v = float(value)
                        except ValueError:
                            v = value
                else:
                    v = value
                current[key] = v
            else:
                if key not in current:
                    current[key] = {}
                current = current[key]
    return updated

@alerts_bp.route('/refresh_alerts', methods=['POST'], endpoint="refresh_alerts")
def refresh_alerts():
    from cyclone.cyclone import Cyclone
    import asyncio
    cyc = Cyclone()
    try:
        asyncio.run(cyc.run_alert_updates())
        return jsonify({"success": True, "message": "Alerts refreshed using Cyclone run_alert_updates."})
    except Exception as e:
        logger.error("Error refreshing alerts: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route('/create_all_alerts', methods=['POST'], endpoint="create_all_alerts")
def create_all_alerts():
    add_type = (request.json.get("add_type") or request.form.get("add_type", "all")).lower()
    from cyclone.cyclone import Cyclone
    import asyncio
    cyc = Cyclone()
    messages = []
    try:
        if add_type == "position":
            asyncio.run(cyc.run_create_position_alerts())
            messages.append("Position alerts created.")
        elif add_type == "market":
            asyncio.run(cyc.run_create_market_alerts())
            messages.append("Market alerts created.")
        elif add_type == "system":
            asyncio.run(cyc.run_create_system_alerts())
            messages.append("System alerts created.")
        elif add_type == "all":
            asyncio.run(cyc.run_create_position_alerts())
            asyncio.run(cyc.run_create_market_alerts())
            asyncio.run(cyc.run_create_system_alerts())
            messages.append("All alerts created.")
        else:
            return jsonify({"success": False, "error": "Invalid add type."}), 400
        return jsonify({"success": True, "message": " ".join(messages)})
    except Exception as e:
        logger.error("Error creating alerts: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


def delete_all_data_api(self):
    """
    Non-interactive method to delete all alerts, prices, and positions.
    This method is intended for API use and does not require user confirmation.
    """
    try:
        self.clear_alerts_backend()
        self.clear_prices_backend()
        self.clear_positions_backend()
        self.u_logger.log_cyclone(
            operation_type="Delete All Data",
            primary_text="All alerts, prices, and positions have been deleted via API.",
            source="Cyclone",
            file="cyclone.py"
        )
        print("All alerts, prices, and positions have been deleted via API.")
        return True, "All alerts, prices, and positions have been deleted."
    except Exception as e:
        self.logger.error(f"Error deleting all data via API: {e}", exc_info=True)
        return False, str(e)

@alerts_bp.route('/delete_all_alerts', methods=['POST'], endpoint="delete_all_alerts")
def delete_all_alerts():
    delete_type = (request.json.get("delete_type") or request.form.get("delete_type", "alerts")).lower()
    from cyclone.cyclone import Cyclone
    cyc = Cyclone()
    try:
        if delete_type == "price":
            cyc.clear_prices_backend()
            return jsonify({"success": True, "message": "Price data cleared."})
        elif delete_type == "alerts":
            cyc.clear_alerts_backend()
            return jsonify({"success": True, "message": "Alerts cleared."})
        elif delete_type == "all":
            success, msg = cyc.delete_all_data_api()  # Call the new API method
            if success:
                return jsonify({"success": True, "message": msg})
            else:
                return jsonify({"success": False, "error": msg}), 500
        else:
            return jsonify({"success": False, "error": "Invalid delete type."}), 400
    except Exception as e:
        logger.error("Error deleting alerts: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


def format_alert_config_table(alert_ranges: dict) -> str:
    metrics = [
        "heat_index_ranges", "collateral_ranges", "value_ranges",
        "size_ranges", "leverage_ranges", "liquidation_distance_ranges",
        "travel_percent_liquid_ranges", "travel_percent_profit_ranges", "profit_ranges"
    ]
    html = "<table border='1' style='border-collapse: collapse; width:100%;'>"
    html += "<tr><th>Metric</th><th>Enabled</th><th>Low</th><th>Medium</th><th>High</th></tr>"
    # Reload alert limits from the file using the current JsonManager instance
    json_manager = current_app.json_manager
    alert_data = json_manager.load("alert_limits.json", json_type=JsonType.ALERT_LIMITS)
    for m in metrics:
        data = alert_data.get("alert_ranges", {}).get(m, {})
        enabled = data.get("enabled", False)
        low = data.get("low", "")
        medium = data.get("medium", "")
        high = data.get("high", "")
        html += f"<tr><td>{m}</td><td>{enabled}</td><td>{low}</td><td>{medium}</td><td>{high}</td></tr>"
    html += "</table>"
    return html

def clear_alert_ledger_backend(self):
    """Clear all records from the alert_ledger table."""
    try:
        dl = DataLocker.get_instance()
        cursor = dl.conn.cursor()
        cursor.execute("DELETE FROM alert_ledger")
        dl.conn.commit()
        deleted = cursor.rowcount
        cursor.close()
        self.u_logger.log_cyclone(
            operation_type="Clear Alert Ledger",
            primary_text=f"Cleared {deleted} alert ledger record(s)",
            source="Cyclone",
            file="cyclone.py"
        )
        print(f"Alert ledger cleared. {deleted} record(s) deleted.")
    except Exception as e:
        print(f"Error clearing alert ledger: {e}")


# New route for the Alarm Viewer (default mode)
@alerts_bp.route('/viewer', methods=['GET'], endpoint="alarm_viewer")
def alarm_viewer():
    from data.data_locker import DataLocker
    try:
        from alert_manager import manager
    except ModuleNotFoundError as e:
        logger.error("Error importing alert_manager: %s", e)
        return "Server configuration error.", 500

    data_locker = DataLocker.get_instance()
    json_manager = current_app.json_manager

    config_data = json_manager.load("alert_limits.json", json_type=JsonType.ALERT_LIMITS)
    cooldown_seconds = float(config_data.get("alert_cooldown_seconds", 900))
    call_refractory_seconds = float(config_data.get("call_refractory_period", 1800))

    travel_cfg = config_data["alert_ranges"]["travel_percent_liquid_ranges"]
    profit_cfg = config_data["alert_ranges"]["profit_ranges"]
    price_alerts = config_data["alert_ranges"].get("price_alerts", {})

    positions = data_locker.read_positions()
    now = time()

    for pos in positions:
        asset = pos.get("asset_type", "").upper()
        position_type = pos.get("position_type", "").capitalize() or "Unknown"
        position_id = pos.get("position_id") or pos.get("id") or "unknown"
        asset_full = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana"}.get(asset, asset)

        if asset == "BTC":
            pos["alert_status"] = "green"
        elif asset == "ETH":
            pos["alert_status"] = "yellow"
        elif asset == "SOL":
            pos["alert_status"] = "red"
        else:
            pos["alert_status"] = "unknown"

        pos["travel_low"] = travel_cfg.get("low")
        pos["travel_medium"] = travel_cfg.get("medium")
        pos["travel_high"] = travel_cfg.get("high")
        pos["profit_low"] = profit_cfg.get("low")
        pos["profit_medium"] = profit_cfg.get("medium")
        pos["profit_high"] = profit_cfg.get("high")

        alert_types = []
        details = {}

        try:
            current_travel = float(pos.get("current_travel_percent", 0))
        except:
            current_travel = 0
        if current_travel < 0:
            low_val = float(travel_cfg.get("low", -50))
            medium_val = float(travel_cfg.get("medium", -60))
            high_val = float(travel_cfg.get("high", -75))
            if current_travel <= high_val:
                level = "High"
            elif current_travel <= medium_val:
                level = "Medium"
            elif current_travel <= low_val:
                level = "Low"
            else:
                level = None
            if level:
                alert_types.append("Travel")
                key = f"{asset_full}-{position_type}-{position_id}-travel-{level}"
                last_trigger = manager.last_triggered.get(key, 0)
                remaining = max(0, cooldown_seconds - (now - last_trigger))
                details["Travel Alert"] = f"Remaining cooldown: {remaining:.0f} sec (Level: {level})"
        try:
            profit_val = float(pos.get("profit", 0))
        except:
            profit_val = 0
        if profit_val > 0:
            alert_types.append("Profit")
            key = f"profit-{asset_full}-{position_type}-{position_id}"
            last_trigger = manager.last_triggered.get(key, 0)
            remaining = max(0, cooldown_seconds - (now - last_trigger))
            details["Profit Alert"] = f"Remaining cooldown: {remaining:.0f} sec"

        pos["alert_type"] = ", ".join(alert_types) if alert_types else "None"
        pos["alert_details"] = details

        latest_price = data_locker.get_latest_price(asset)
        pos["current_price"] = latest_price["current_price"] if latest_price else 0.0

        last_call = manager.last_call_triggered.get("all_alerts", 0)
        pos["call_refractory_remaining"] = max(0, call_refractory_seconds - (now - last_call))
        pos["configured_cooldown"] = cooldown_seconds
        pos["configured_call_refractory"] = call_refractory_seconds

    theme_config = current_app.config.get('theme', {})
    return render_template("alert_matrix.html",
                           theme=theme_config,
                           positions=positions)

@alerts_bp.route('/config', methods=['GET'], endpoint="alert_config_page")
def config_page():
    try:
        json_manager = current_app.json_manager
        config_data = json_manager.load("alert_limits.json", json_type=JsonType.ALERT_LIMITS)
        config_data = convert_types_in_dict(config_data)
    except Exception as e:
        op_logger = OperationsLogger(
            log_filename=os.path.join(os.getcwd(), "operations_log.txt")
        )
        op_logger.log("Alert Configuration Failed", source="System",
                      operation_type="Alert Configuration Failed",
                      file_name=str(ALERT_LIMITS_PATH))
        logger.error("Error loading alert limits: %s", str(e))
        return render_template("alert_limits.html", error_message="Error loading alert configuration."), 500

    alert_config = config_data.get("alert_ranges", {})
    price_alerts = alert_config.get("price_alerts", {})
    theme_config = config_data.get("theme_config", {})
    global_alert_config = config_data.get("global_alert_config", {
        "enabled": False,
        "data_fields": {"price": False, "profit": False, "travel_percent": False, "heat_index": False},
        "thresholds": {"price": {"BTC": 0, "ETH": 0, "SOL": 0}, "profit": 0, "travel_percent": 0, "heat_index": 0}
    })

    # Get notifications from the JSON, then force defaults for missing metrics/subkeys.
    notifications = config_data.get("alert_config", {}).get("notifications")
    def fill_notifications_defaults(notif):
        defaults = {
            "low":    {"enabled": False, "notify_by": {"call": False, "sms": False, "email": False}},
            "medium": {"enabled": False, "notify_by": {"call": False, "sms": False, "email": False}},
            "high":   {"enabled": False, "notify_by": {"call": False, "sms": False, "email": False}}
        }
        if not isinstance(notif, dict):
            return defaults
        for level in ["low", "medium", "high"]:
            if level not in notif:
                notif[level] = defaults[level]
            else:
                if "enabled" not in notif[level]:
                    notif[level]["enabled"] = defaults[level]["enabled"]
                if "notify_by" not in notif[level]:
                    notif[level]["notify_by"] = defaults[level]["notify_by"]
                else:
                    for method in ["call", "sms", "email"]:
                        if method not in notif[level]["notify_by"]:
                            notif[level]["notify_by"][method] = defaults[level]["notify_by"][method]
        return notif

    if notifications is None:
        notifications = {}
    for metric in ["heat_index", "travel_percent_liquid", "profit"]:
        notifications[metric] = fill_notifications_defaults(notifications.get(metric, {}))

    alert_cooldown_seconds = config_data.get("alert_cooldown_seconds", 900)
    call_refractory_period = config_data.get("call_refractory_period", 3600)

    return render_template("alert_limits.html",
                           alert_ranges=alert_config,
                           price_alerts=price_alerts,
                           global_alert_config=global_alert_config,
                           notifications=notifications,
                           theme=theme_config,
                           alert_cooldown_seconds=alert_cooldown_seconds,
                           call_refractory_period=call_refractory_period)





@alerts_bp.route('/update_config', methods=['POST'], endpoint="update_alert_config")
def update_alert_config_route():
    op_logger = OperationsLogger(log_filename=os.path.join(os.getcwd(), "operations_log.txt"))
    try:
        flat_form = request.form.to_dict(flat=False)
        logger.debug("POST Data Received:\n%s", json.dumps(flat_form, indent=2))
        nested_update = parse_nested_form(flat_form)
        logger.debug("Parsed Nested Form Data (raw):\n%s", json.dumps(nested_update, indent=2))
        nested_update = convert_types_in_dict(nested_update)
        logger.debug("Parsed Nested Form Data (converted):\n%s", json.dumps(nested_update, indent=2))

        # Ensure defaults for global_alert_config if missing.
        global_update = nested_update.get("global_alert_config", {})
        global_update.setdefault("enabled", False)
        global_update.setdefault("data_fields", {
            "price": False,
            "profit": False,
            "travel_percent": False,
            "heat_index": False
        })
        global_update.setdefault("thresholds", {
            "price": {"BTC": 0, "ETH": 0, "SOL": 0},
            "profit": 0,
            "travel_percent": 0,
            "heat_index": 0
        })
        nested_update["global_alert_config"] = global_update

        # Merge with existing config.
        json_manager = current_app.json_manager
        current_config = json_manager.load("alert_limits.json", json_type=JsonType.ALERT_LIMITS)
        merged_config = json_manager.deep_merge(current_config, nested_update)

        # Ensure timing settings have defaults.
        if not merged_config.get("alert_cooldown_seconds"):
            merged_config["alert_cooldown_seconds"] = 900
        if not merged_config.get("call_refractory_period"):
            merged_config["call_refractory_period"] = 1800

        json_manager.save("alert_limits.json", merged_config, json_type=JsonType.ALERT_LIMITS)
        logger.debug("New Config Loaded After Update:\n%s", json.dumps(merged_config, indent=2))
        return jsonify({"success": True, "message": "Configuration successfully saved to the database!"})
    except Exception as e:
        logger.error("Error updating alert config: %s", str(e))
        op_logger.log("Alert Configuration Failed", source="System",
                      operation_type="Alert Config Failed", file_name=str(ALERT_LIMITS_PATH))
        return jsonify({"success": False, "error": str(e)}), 500


# **NEW**: Test SMS endpoint
@alerts_bp.route('/test_sms', methods=['POST'])
def test_sms():
    """
    Triggers a test SMS using the AlertManager’s send_sms_alert method.
    """
    # Allow overriding the test message via Flask config
    msg = current_app.config.get('TEST_SMS_MESSAGE', 'This is a test SMS alert.')
    # Use a fixed key so it doesn’t collide with real alerts
    success = alert_manager.send_sms_alert(msg, 'test_sms')
    status_code = 200 if success else 500
    return jsonify(success=bool(success),
                   message='SMS sent!' if success else 'SMS failed'), status_code


@alerts_bp.route('/matrix', methods=['GET'], endpoint="alert_matrix")
def alert_matrix():
    from flask import url_for
    from data.data_locker import DataLocker
    from alerts.alert_controller import AlertController
    from sonic_labs.hedge_manager import HedgeManager
    from config.config_constants import BTC_LOGO_IMAGE, ETH_LOGO_IMAGE, SOL_LOGO_IMAGE, OBIVAULT_IMAGE, R2VAULT_IMAGE, LANDOVAULT_IMAGE, VADERVAULT_IMAGE

    # Set up theme configuration if not already set
    theme_config = current_app.config.get('theme')
    if not theme_config:
        theme_config = {
            "border_color": "#ccc",
            "card_header_color": "#007bff",
            "card_header_text_color": "#fff",
            "profiles": {},
            "selected_profile": ""
        }
        current_app.config['theme'] = theme_config

    # Retrieve alerts and positions
    data_locker = DataLocker.get_instance()
    alerts = data_locker.get_alerts()
    positions = data_locker.read_positions()

    # Update alerts with missing position_reference_id using positions data
    for alert in alerts:
        if not alert.get("position_reference_id"):
            for pos in positions:
                if pos.get("alert_reference_id") == alert.get("id"):
                    alert["position_reference_id"] = pos.get("id")
                    break

    # For TRAVELPERCENT alerts, attach the travel_percent from the corresponding position
    for alert in alerts:
        if alert.get("alert_type", "").upper() == "TRAVELPERCENT":
            pos = next((p for p in positions if p.get("id") == alert.get("position_reference_id")), None)
            if pos:
                alert["travel_percent"] = pos.get("travel_percent")
            else:
                alert["travel_percent"] = None

    # Retrieve hedges using HedgeManager
    hedge_manager = HedgeManager(positions)
    hedges = hedge_manager.get_hedges()

    # Load alert configuration ranges
    json_manager = current_app.json_manager
    alert_config = json_manager.load("alert_limits.json", json_type=JsonType.ALERT_LIMITS)
    alert_ranges = alert_config.get("alert_ranges", {})

    # Create asset images dictionary using config constants
    asset_images = {
        "BTC": url_for('static', filename=BTC_LOGO_IMAGE),
        "ETH": url_for('static', filename=ETH_LOGO_IMAGE),
        "SOL": url_for('static', filename=SOL_LOGO_IMAGE)
    }
    # Define a default wallet image (fallback)
    wallet_default = url_for('static', filename=OBIVAULT_IMAGE)

    # Define a wallet-to-image mapping using config constants
    wallet_images = {
        "R2Vault": url_for('static', filename=R2VAULT_IMAGE),
        "ObiVault": url_for('static', filename=OBIVAULT_IMAGE),
        "Landovault": url_for('static', filename=LANDOVAULT_IMAGE),
        "VaderVault": url_for('static', filename=VADERVAULT_IMAGE)
    }

    # For each alert, if wallet_image is missing, use its corresponding position's wallet field
    for alert in alerts:
        if not alert.get("wallet_image"):
            pos = next((p for p in positions if p.get("id") == alert.get("position_reference_id")), None)
            if pos:
                wallet_name = pos.get("wallet", "").strip()
                # Use the mapped wallet image, falling back to OBIVAULT_IMAGE if not found
                alert["wallet_image"] = wallet_images.get(wallet_name, wallet_default)
            else:
                alert["wallet_image"] = wallet_default

        # Also assign asset_image if missing, using asset type from the position
        if not alert.get("asset_image"):
            pos = next((p for p in positions if p.get("id") == alert.get("position_reference_id")), None)
            if pos:
                pos_asset = pos.get("asset_type", "").upper()
                alert["asset_image"] = asset_images.get(pos_asset, url_for('static', filename='images/asset_default.png'))
            else:
                alert["asset_image"] = url_for('static', filename='images/asset_default.png')

    return render_template("alert_matrix.html",
                           theme=theme_config,
                           alerts=alerts,
                           alert_ranges=alert_ranges,
                           hedges=hedges,
                           asset_images=asset_images,
                           wallet_default=wallet_default)


if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(alerts_bp)
    app.json_manager = JsonManager()
    app.run(debug=True, port=5001)
