# settings/settings_bp.py

import os
import json
from flask import Blueprint, render_template, jsonify, request, current_app
from core.constants import THEME_CONFIG_PATH
from core.logging import log
from utils.route_decorators import route_log_alert

settings_bp = Blueprint(
    'settings_bp',
    __name__,
    url_prefix='/settings',
    template_folder='../templates/settings'  # ✅ Corrected
)

@settings_bp.route("/theme")
@route_log_alert
def theme_setup():
    theme_data = {
        "background": "#f5f5f5",
        "text": "#000",
        "card": "#ffffff",
        "navbar": "#eeeeee"
    }
    return render_template("theme_builder.html", theme=theme_data)

@settings_bp.route("/save_theme_mode", methods=["POST"])
@route_log_alert
def save_theme_mode():
    theme_mode = request.json.get("theme_mode")
    dl = current_app.data_locker
    dl.set_theme_mode(theme_mode)
    return jsonify({"success": True})

@settings_bp.route("/save_theme", methods=["POST"])
@route_log_alert
def save_theme():
    theme_data = request.json
    with open(THEME_CONFIG_PATH, "w") as f:
        json.dump(theme_data, f, indent=2)
    return jsonify({"success": True})

@settings_bp.route("/database")
@route_log_alert
def database_viewer():
    return render_template("db_viewer.html")


@settings_bp.route("/database/datasets")
@route_log_alert
def database_datasets():
    dl = current_app.data_locker
    try:
        return jsonify(dl.get_all_tables_as_dict())
    except Exception as e:
        log.error(f"❌ Error loading tables: {e}", source="DatabaseViewer")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/database/<table_name>")
@route_log_alert
def get_table_data(table_name):
    dl = current_app.data_locker
    try:
        rows = dl.get_table_as_dict(table_name)
        return jsonify(rows)
    except Exception as e:
        log.error(f"❌ Error fetching table {table_name}: {e}", source="DatabaseViewer")
        return jsonify({"error": str(e)}), 500
