import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
from flask import current_app

from flask import Blueprint, jsonify, render_template, render_template_string
from data.data_locker import DataLocker

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
ALERT_MONITOR_DIR = os.path.join(APP_DIR, 'alert_monitor')
TEMPLATE_PATH = os.path.join(ALERT_MONITOR_DIR, 'alert_monitor.html')



alerts_bp = Blueprint(
    'alerts_bp',
    __name__,
    url_prefix='/alerts',
    template_folder=ALERT_MONITOR_DIR,
    static_folder=ALERT_MONITOR_DIR,
    static_url_path='/alerts/static'
)




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


@alerts_bp.route('/create_all', methods=['POST'])
def create_all_alerts():
    """
    Create sample alerts for testing purposes.
    """
    try:
        data_locker = current_app.data_locker
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
            data_locker.alerts.create_alert(alert)  # ✅ Use create_alert (not save_alert!)

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
        data_locker = current_app.data_locker
        data_locker.alerts.clear_all_alerts()
        log.success("All alerts deleted successfully.", source="AlertsBP")
        return jsonify({"success": True, "message": "All alerts cleared."})
    except Exception as e:
        logger.error(f"Error deleting alerts: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@alerts_bp.route('/alert_config_page', methods=['GET'])
def alert_config_page():
    """Render the alert limits configuration page."""
    # ❗ Alert thresholds are stored in the database via the DataLocker
    # interface. For now we simply render the template with empty
    # placeholders so the page loads without relying on JSON files.
    return render_template(
        "alert_limits.html",
        price_alerts={},
        global_alert_config={},
    )


@alerts_bp.route('/monitor_page', methods=['GET'])
def monitor_page():
    print("🧪 Rendering from:", TEMPLATE_PATH)
    if not os.path.exists(TEMPLATE_PATH):
        return "Template file not found", 404
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        html = f.read()
    return render_template("alert_monitor.html")



@alerts_bp.route('/monitor', methods=['GET'])
def monitor_data():
    """
    API endpoint that returns all alerts for the monitor UI.
    """
    try:
        data_locker = current_app.data_locker
        alert_list = data_locker.alerts.get_all_alerts()
        logger.info(f"Fetched {len(alert_list)} alerts for monitor", extra={"source": "AlertsBP"})
        return jsonify({"alerts": alert_list})
    except Exception as e:
        logger.error(f"Failed to load alerts for monitor: {e}", exc_info=True)
        return jsonify({"alerts": [], "error": str(e)}), 500

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
