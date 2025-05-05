import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import logging
import asyncio
from flask import Blueprint, request, jsonify, render_template, current_app
from markupsafe import Markup
from alerts.alert_service_manager import AlertServiceManager
from utils.json_manager import JsonManager, JsonType
from dashboard.dashboard_view_model import DashboardViewModel
from config.config_constants import ALERT_LIMITS_PATH
from utils.console_logger import ConsoleLogger as log
from data.data_locker import DataLocker
from time import time

# --- Blueprint Setup ---
alerts_bp = Blueprint('alerts_bp', __name__, url_prefix='/alerts', template_folder='.')

# --- Logger Setup ---
logger = logging.getLogger("AlertsBPLogger")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# --- Utilities ---

def convert_types_in_dict(d):
    if isinstance(d, dict):
        return {k: convert_types_in_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_types_in_dict(i) for i in d]
    elif isinstance(d, str):
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
    return d

# --- Routes ---

@alerts_bp.route('/refresh', methods=['POST'])
def refresh_alerts():
    """
    Reevaluate all alerts and process notifications.
    """
    try:
        service = AlertServiceManager.get_instance()
        asyncio.run(service.process_all_alerts())
        log.success("Alerts refreshed successfully.", source="AlertsBP")
        return jsonify({"success": True, "message": "Alerts refreshed."})
    except Exception as e:
        logger.error(f"Error refreshing alerts: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@alerts_bp.route('/test_sms', methods=['POST'])
def test_sms():
    """
    Trigger a test SMS via NotificationService.
    """
    try:
        service = AlertServiceManager.get_instance()
        msg = current_app.config.get('TEST_SMS_MESSAGE', 'This is a test SMS alert.')
        result = service.notification_service.send_alert(msg, 'test_sms')
        return jsonify(success=bool(result),
                       message='SMS sent!' if result else 'SMS failed'), (200 if result else 500)
    except Exception as e:
        logger.error(f"Error sending test SMS: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@alerts_bp.route('/monitor', methods=['GET'])
def monitor_alerts():
    #from alerts.dashboard_view_model import DashboardViewModel
    dashboard = DashboardViewModel()
    return jsonify({"alerts": dashboard.get_alerts()})

@alerts_bp.route('/create_all', methods=['POST'])
def create_all_alerts():
    """
    Create sample alerts for testing purposes.
    """
    try:
        data_locker = DataLocker.get_instance()
        sample_alerts = [
            {
                "id": "alert-sample-1",
                "alert_type": "PriceThreshold",
                "alert_class": "Market",
                "asset_type": "BTC",
                "trigger_value": 60000,
                "condition": "ABOVE",
                "notification_type": "SMS",
                "level": "Normal",
                "last_triggered": None,
                "status": "Active",
                "frequency": 1,
                "counter": 0,
                "liquidation_distance": 0.0,
                "travel_percent": -10.0,
                "liquidation_price": 50000,
                "notes": "Sample BTC price alert",
                "description": "Test alert for BTC above 60k",
                "position_reference_id": None,
                "evaluated_value": 59000
            }
        ]

        for alert in sample_alerts:
            data_locker.create_alert(alert)  # ✅ Use create_alert (not save_alert!)

        log.success("Sample alerts created successfully.", source="AlertsBP")
        return jsonify({"success": True, "message": "Sample alerts created."})
    except Exception as e:
        logger.error(f"Error creating sample alerts: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route('/delete_all', methods=['POST'])
def delete_all_alerts():
    """
    Delete all alerts from the database.
    """
    try:
        data_locker = DataLocker.get_instance()
        data_locker.clear_alerts()
        log.success("All alerts deleted successfully.", source="AlertsBP")
        return jsonify({"success": True, "message": "All alerts cleared."})
    except Exception as e:
        logger.error(f"Error deleting alerts: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route('/config', methods=['GET'])
def config_page():
    """
    Display the alert configuration editor.
    """
    try:
        json_manager = current_app.json_manager
        config_data = json_manager.load("alert_limitsz.json", json_type=JsonType.ALERT_LIMITS)
        config_data = convert_types_in_dict(config_data)
    except Exception as e:
        logger.error(f"Error loading config: {e}", exc_info=True)
        return render_template("alert_limits.html", error_message="Failed to load configuration."), 500

    return render_template("alert_limits.html",
                           alert_ranges=config_data.get("alert_ranges", {}),
                           price_alerts=config_data.get("alert_ranges", {}).get("price_alerts", {}),
                           global_alert_config=config_data.get("global_alert_config", {}),
                           notifications=config_data.get("alert_config", {}).get("notifications", {}),
                           theme=config_data.get("theme_config", {}))

@alerts_bp.route('/alert_config_page', methods=['GET'])
def alert_config_page():
    return "🚫 Alert Limits Page has been disabled.", 410


# Matrix view route
@alerts_bp.route('/alert_matrix', methods=['GET'])
def alert_matrix_page():
    try:
        data_locker = DataLocker.get_instance()
        alerts = data_locker.get_alerts()
        positions = data_locker.read_positions()
        json_manager = current_app.json_manager
        alert_config = json_manager.load("alert_limitsz.json", json_type=JsonType.ALERT_LIMITS)
        theme_config = current_app.config.get('theme', {})

        for alert in alerts:
            alert["cooldown_remaining"] = 0  # can extend later

        return render_template("alert_matrix.html",
                               theme=theme_config,
                               alerts=alerts,
                               alert_ranges=alert_config.get("alert_ranges", {}),
                               hedges=[],
                               asset_images={},
                               wallet_default="")
    except Exception as e:
        logger.error(f"Error loading alert matrix: {e}", exc_info=True)
        return "Error loading alert matrix", 500


@alerts_bp.route('/update_config', methods=['POST'])
def update_config():
    """
    Save updated alert configuration.
    """
    try:
        flat_form = request.form.to_dict(flat=False)
        nested_update = _parse_nested_form(flat_form)
        nested_update = convert_types_in_dict(nested_update)

        json_manager = current_app.json_manager
        current_config = json_manager.load("alert_limitsz.json", json_type=JsonType.ALERT_LIMITS)
        merged_config = json_manager.deep_merge(current_config, nested_update)

        if not merged_config.get("alert_cooldown_seconds"):
            merged_config["alert_cooldown_seconds"] = 900
        if not merged_config.get("call_refractory_period"):
            merged_config["call_refractory_period"] = 1800

        json_manager.save("alert_limitsz.json", merged_config, json_type=JsonType.ALERT_LIMITS)
        log.success("Alert configuration updated successfully.", source="AlertsBP")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error updating alert config: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@alerts_bp.route('/matrix', methods=['GET'])
def alert_matrix():
    """
    Display the Alert Matrix (visuals for current alerts).
    """
    try:
        data_locker = DataLocker.get_instance()
        alerts = data_locker.get_alerts()
        positions = data_locker.read_positions()
        json_manager = current_app.json_manager
        alert_config = json_manager.load("alert_limitsz.json", json_type=JsonType.ALERT_LIMITS)
        theme_config = current_app.config.get('theme', {})

        now = time()

        for alert in alerts:
            alert["cooldown_remaining"] = 0  # Placeholder if you want per-alert cooldowns

        return render_template("alert_matrix.html",
                               theme=theme_config,
                               alerts=alerts,
                               alert_ranges=alert_config.get("alert_ranges", {}),
                               hedges=[],  # Could load hedges if needed
                               asset_images={},  # You can define asset image mapping
                               wallet_default="")
    except Exception as e:
        logger.error(f"Error building alert matrix: {e}", exc_info=True)
        return "Matrix load error", 500

@alerts_bp.route('/monitor_page', methods=['GET'])
def monitor_page():
    import os
    from flask import current_app
    path = os.path.join(current_app.template_folder, 'alert_monitor.html')
    print(f"🧪 CHECKING TEMPLATE PATH: {path}")
    exists = os.path.exists(path)
    print(f"🧪 EXISTS? {exists}")
    return render_template("alert_monitor.html")


@alerts_bp.route('/monitor_page_debug', methods=['GET'])
def monitor_page_debug():
    from markupsafe import Markup
    html = """
      <!DOCTYPE html>
      <html>
      <head>
          <title>💥 Debug Monitor Page</title>
          <style>
              body {
                  font-family: monospace;
                  padding: 2rem;
                  background: #1e1e1e;
                  color: #00ffae;
              }
          </style>
      </head>
      <body>
          <h1>✅ DEBUG: Template rendering is working!</h1>
          <script>
              alert("🚀 DEBUG TEMPLATE WORKS!");
              console.log("🧠 JS loaded inside alert_monitor.html");
          </script>
      </body>
      </html>
      """
    return Markup(html)


# --- Internal helpers ---

def _parse_nested_form(form: dict) -> dict:
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
