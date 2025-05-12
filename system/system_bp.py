# 🔌 system_bp.py — Blueprint for SystemCore wallet + theme endpoints

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename

from system.system_core import SystemCore
from wallets.wallet_schema import WalletIn

UPLOAD_FOLDER = os.path.join("static", "uploads", "wallets")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

system_bp = Blueprint("system", __name__, url_prefix="/system")

def get_core():
    return SystemCore(current_app.data_locker)

# 🌐 List meta data
@system_bp.route("/metadata", methods=["GET"])
def system_metadata():
    try:
        core = get_core()
        metadata = core.get_strategy_metadata()
        return jsonify(metadata)
    except Exception as e:
        log.error(f"Failed to fetch system metadata: {e}", source="SystemBP")
        return jsonify({"error": str(e)}), 500


# 🌐 List all wallets
@system_bp.route("/wallets", methods=["GET"])
def list_wallets():
    core = get_core()
    wallets = core.wallets.list_wallets()
    return render_template("wallets/wallet_list.html", wallets=wallets)

# ➕ Add a wallet
@system_bp.route("/wallets/add", methods=["POST"])
def add_wallet():
    try:
        form = request.form
        file = request.files.get("image_file")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        image_path = f"/static/uploads/wallets/{filename}" if filename else form.get("image_path")

        data = WalletIn(
            name=form.get("name"),
            public_address=form.get("public_address"),
            private_address=form.get("private_address"),
            image_path=image_path,
            balance=float(form.get("balance", 0.0)),
            tags=[t.strip() for t in form.get("tags", "").split(",") if t.strip()],
            is_active=form.get("is_active", "off") == "on",
            type=form.get("type", "personal")
        )

        get_core().wallets.create_wallet(data)
        flash("✅ Wallet added!", "success")

    except Exception as e:
        flash(f"❌ Failed to add wallet: {e}", "danger")

    return redirect(url_for("system.list_wallets"))

# 🗑️ Delete wallet
@system_bp.route("/wallets/delete/<name>", methods=["POST"])
def delete_wallet(name):
    try:
        get_core().wallets.delete_wallet(name)
        flash("🗑️ Wallet deleted.", "info")
    except Exception as e:
        flash(f"❌ Delete failed: {e}", "danger")
    return redirect(url_for("system.list_wallets"))

# 💾 Export wallets to JSON
@system_bp.route("/wallets/export", methods=["POST"])
def export_wallets():
    try:
        get_core().wallets.export_wallets()
        flash("💾 Exported to wallets.json", "success")
    except Exception as e:
        flash(f"❌ Export failed: {e}", "danger")
    return redirect(url_for("system.list_wallets"))

# ♻️ Import from JSON
@system_bp.route("/wallets/import", methods=["POST"])
def import_wallets():
    try:
        count = get_core().wallets.import_wallets()
        flash(f"♻️ Imported {count} wallets from JSON", "success")
    except Exception as e:
        flash(f"❌ Import failed: {e}", "danger")
    return redirect(url_for("system.list_wallets"))

# ✏️ Update wallet (from modal)
@system_bp.route("/wallets/update/<name>", methods=["POST"])
def update_wallet(name):
    try:
        form = request.form

        data = WalletIn(
            name=name,
            public_address=form.get("public_address"),
            private_address=form.get("private_address"),
            image_path=form.get("image_path"),
            balance=float(form.get("balance", 0.0)),
            tags=[t.strip() for t in form.get("tags", "").split(",") if t.strip()],
            is_active="is_active" in form,
            type=form.get("type", "personal")
        )

        get_core().wallets.update_wallet(name, data)
        flash(f"💾 Updated wallet '{name}'", "success")
    except Exception as e:
        flash(f"❌ Failed to update wallet '{name}': {e}", "danger")
    return redirect(url_for("system.list_wallets"))

# === 🎨 Theme Profile Routes ===

# 🔍 GET: All saved theme profiles
@system_bp.route("/themes", methods=["GET"])
def list_themes():
    try:
        core = get_core()
        profiles = core.get_all_profiles()
        return jsonify(profiles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 💾 POST: Save or update a theme profile
@system_bp.route("/themes", methods=["POST"])
def save_theme():
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not data:
            return jsonify({"error": "Invalid theme payload"}), 400

        for name, config in data.items():
            get_core().save_profile(name, config)

        return jsonify({"message": "Profile(s) saved."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ❌ DELETE: Remove a theme profile
@system_bp.route("/themes/<name>", methods=["DELETE"])
def delete_theme(name):
    try:
        get_core().delete_profile(name)
        return jsonify({"message": f"Theme '{name}' deleted."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🌟 POST: Set a profile as active
@system_bp.route("/themes/activate/<name>", methods=["POST"])
def activate_theme(name):
    try:
        get_core().set_active_profile(name)
        return jsonify({"message": f"Theme '{name}' set as active."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🎯 GET: Active theme profile
@system_bp.route("/themes/active", methods=["GET"])
def get_active_theme():
    try:
        profile = get_core().get_active_profile()
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 🌗 Get/set theme mode
@system_bp.route("/theme_mode", methods=["GET", "POST"])
def theme_mode():
    core = get_core()
    if request.method == "POST":
        data = request.get_json()
        core.set_theme_mode(data.get("theme_mode"))
        return jsonify(success=True)
    else:
        return jsonify(theme_mode=core.get_theme_mode())


# 🎨 Get/save theme config
@system_bp.route("/theme_config", methods=["GET", "POST"])
@system_bp.route("/theme_config", methods=["GET", "POST"])
def theme_config():
    core = get_core()
    if request.method == "POST":
        config = request.get_json()
        core.save_theme_config(config)
        return jsonify(success=True)
    else:
        return jsonify(config=core.load_theme_config())

