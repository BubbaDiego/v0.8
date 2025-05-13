# 🔌 system_bp.py — Blueprint for SystemCore wallet + theme endpoints

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
#from config.alert_limits_json import legacy_alert_limits  # Simulating legacy load

from system.system_core import SystemCore
from data.dl_thresholds import DLThresholdManager
from data.models import AlertThreshold
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

def theme_config():
    core = get_core()

    if request.method == "GET":
        try:
            profiles = core.get_all_profiles()
            return jsonify(profiles)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == "POST":
        try:
            payload = request.get_json()
            if not isinstance(payload, dict):
                return jsonify({"error": "Invalid theme config"}), 400

            for name, config in payload.items():
                core.save_profile(name, config)

            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500



@system_bp.route("/seed_demo_thresholds", methods=["POST", "GET"])
def seed_demo_thresholds():
    from datetime import datetime, timezone
    from uuid import uuid4
    from data.models import AlertThreshold

    db = current_app.data_locker.db
    dl_mgr = DLThresholdManager(db)

    def notify_str(n):  # takes {"call": T, "sms": F, ...} and returns "SMS,Voice"
        mapping = {"call": "Voice", "sms": "SMS", "email": "Email"}
        return ",".join(name for key, name in mapping.items() if n.get(key))

    now = datetime.now(timezone.utc).isoformat()

    definitions = [
        # Position alerts
        ("Profit", "Position", "profit", "profit_ranges"),
        ("HeatIndex", "Position", "heat_index", "heat_index_ranges"),
        ("TravelPercentLiquid", "Position", "travel_percent_liquid", "travel_percent_liquid_ranges"),
        ("LiquidationDistance", "Position", "liquidation_distance", "liquidation_distance_ranges"),

        # Portfolio alerts
        ("TotalValue", "Portfolio", "total_value", "portfolio"),
        ("TotalSize", "Portfolio", "total_size", "portfolio"),
        ("AvgLeverage", "Portfolio", "avg_leverage", "portfolio"),
        ("AvgTravelPercent", "Portfolio", "avg_travel_percent", "portfolio"),
        ("ValueToCollateralRatio", "Portfolio", "value_to_collateral_ratio", "portfolio"),
        ("TotalHeat", "Portfolio", "total_heat_index", "portfolio"),

        # Market
        ("PriceThreshold", "Market", "current_price", "price_alerts"),
    ]



    created = 0
    for alert_type, alert_class, metric_key, legacy_key in definitions:
        if alert_class == "Market":
            low, med, high = 30000, 40000, 50000
        elif legacy_key in legacy_alert_limits:
            raw = legacy_alert_limits[legacy_key]
            low, med, high = raw["low"], raw["medium"], raw["high"]
        else:
            low, med, high = 10, 25, 50  # fallback

        def level_notify(level):
            if legacy_key not in legacy_alert_limits.get("notifications", {}):
                return ""
            return notify_str(legacy_alert_limits["notifications"][legacy_key].get(level, {}).get("notify_by", {}))

        threshold = AlertThreshold(
            id=str(uuid4()),
            alert_type=alert_type,
            alert_class=alert_class,
            metric_key=metric_key,
            condition="ABOVE",
            low=low,
            medium=med,
            high=high,
            enabled=True,
            low_notify=level_notify("low"),
            medium_notify=level_notify("medium"),
            high_notify=level_notify("high"),
            last_modified=now
        )

        dl_mgr.insert(threshold)
        created += 1

    return jsonify({"status": "seeded", "count": created})


@system_bp.route("/alert_thresholds", methods=["GET"])
def list_alert_thresholds():
    db = current_app.data_locker.db
    thresholds = DLThresholdManager(db).get_all()

    grouped = {}

    for t in thresholds:
        for level in ["low", "medium", "high"]:
            # ✅ Notify list for checkbox rendering
            notify_field = f"{level}_notify"
            raw = getattr(t, notify_field, "") or ""
            notify_list = [v.strip() for v in raw.split(",") if v.strip()]
            setattr(t, f"{notify_field}_list", notify_list)

            # ✅ Value field (e.g. t.low_val, t.medium_val)
            value_field = getattr(t, level, None)
            setattr(t, f"{level}_val", value_field)

        grouped.setdefault(t.alert_class, []).append(t)

    return render_template("system/alert_thresholds.html", grouped_thresholds=grouped)




# === POST: Update a threshold (AJAX) ===
@system_bp.route("/alert_thresholds/update/<id>", methods=["POST"])
def update_alert_threshold(id):
    try:
        data = request.json
        fields = {
            "low": float(data["low"]),
            "medium": float(data["medium"]),
            "high": float(data["high"]),
            "enabled": bool(data["enabled"]),
            "low_notify": ",".join(data.get("low_notify", [])),
            "medium_notify": ",".join(data.get("medium_notify", [])),
            "high_notify": ",".join(data.get("high_notify", []))
        }
        db = current_app.data_locker.db
        DLThresholdManager(db).update(id, fields)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@system_bp.route("/alert_thresholds/export", methods=["GET"])
def export_alert_thresholds():
    db = current_app.data_locker.db
    thresholds = DLThresholdManager(db).get_all()
    data = [t.to_dict() for t in thresholds]

    return jsonify(data)

@system_bp.route("/alert_thresholds/import", methods=["POST"])
def import_alert_thresholds():
    try:
        payload = request.get_json()
        if not isinstance(payload, list):
            return jsonify({"success": False, "error": "Expected a list of thresholds"}), 400

        db = current_app.data_locker.db
        dl_mgr = DLThresholdManager(db)

        count = 0
        for t in payload:
            if "id" not in t:
                continue
            dl_mgr.update(t["id"], t)  # update existing
            count += 1

        return jsonify({"success": True, "updated": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
