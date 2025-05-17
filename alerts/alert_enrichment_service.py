
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.fuzzy_wuzzy import fuzzy_match_enum
from data.alert import AlertType
from utils.json_manager import JsonManager  # ensure this is at the top
import asyncio
import re
from dashboard.dashboard_service import get_dashboard_context
from utils.travel_percent_logger import log_travel_percent_comparison
from calc_core.calculation_core import CalculationCore
from alerts.alert_utils import normalize_alert_fields
from data.alert import AlertType
from core.logging import log



class AlertEnrichmentService:
    def __init__(self, data_locker):
        self.data_locker = data_locker
        self.core = CalculationCore(data_locker)

    async def enrich(self, alert):
        """
        Enrich the alert based on its alert_class.
        Dispatches to portfolio, position, or market enrichment as needed.
        """
        try:
            if not alert:
                log.error("❌ Enrichment failed: alert is None", source="AlertEnrichment")
                return alert

            if not alert.alert_class:
                log.warning(f"⚠️ Skipping enrichment: missing alert_class on {alert.id}", source="AlertEnrichment")
                return alert

            if not alert.alert_type:
                log.warning(f"⚠️ Skipping enrichment: missing alert_type on {alert.id}", source="AlertEnrichment")
                return alert

            normalize_alert_fields(alert)

            if alert.alert_class == "Portfolio":
                log.debug(f"🚦 Portfolio enrichment dispatched for alert {alert.id}", source="AlertEnrichment")
                return await self._enrich_portfolio(alert)

            elif alert.alert_class == "Position":
                return await self._enrich_position_type(alert)

            elif alert.alert_class == "Market":
                return await self._enrich_price_threshold(alert)

            else:
                log.warning(f"⚠️ Unknown alert_class '{alert.alert_class}' for alert {alert.id}",
                            source="AlertEnrichment")
                return alert

        except Exception as e:
            log.error(f"❌ Exception during enrichment of alert {alert.id}: {e}", source="AlertEnrichment")
            return alert

    async def _enrich_portfolio(self, alert):
        try:
            context = get_dashboard_context(self.data_locker)
            if not context:
                raise RuntimeError("Dashboard context returned None")

            totals = context.get("totals", {})
            metric = (alert.description or "").strip().lower()

            key_map = {
                "total_value": totals.get("total_value"),
                "total_collateral": totals.get("total_collateral"),
                "total_size": totals.get("total_size"),
                "avg_leverage": totals.get("avg_leverage"),
                "avg_travel_percent": totals.get("avg_travel_percent"),
                "value_to_collateral_ratio": (
                    totals.get("total_value") / totals.get("total_collateral")
                    if totals.get("total_collateral") else None
                ),
                "total_heat": totals.get("avg_heat_index")
            }

            # 🧠 Aliases allow resilient matching
            aliases = {
                "total_heat": ["avg_heat_index", "heat_index", "heat"],
                "value_to_collateral_ratio": ["vcr", "collateral_ratio", "valuecollateral"],
                "avg_travel_percent": ["travel", "travel_percent", "avgtravel"]
            }

            json_mgr = JsonManager()
            resolved_key = json_mgr.resolve_key_fuzzy(metric, key_map, aliases=aliases)
            value = key_map.get(resolved_key)

            alert.evaluated_value = value

            # 🔍 ConsoleLogger v2 structured logging
            log.debug(f"🔍 Metric requested: '{metric}'", source="AlertEnrichment")
            log.debug(f"🔑 Resolved key: '{resolved_key}'", source="AlertEnrichment")
            log.debug("📦 Available keys in map", source="AlertEnrichment", payload={"keys": list(key_map.keys())})

            if value is not None:
                log.success(f"✅ Enriched Portfolio Alert {alert.id} → {resolved_key}={value}", source="AlertEnrichment")
            else:
                log.warning("⚠️ No matching key for enrichment", source="AlertEnrichment", payload={
                    "requested_metric": metric,
                    "available_keys": list(key_map.keys()),
                    "resolved_key": resolved_key
                })

            return alert

        except Exception as e:
            log.error(f"❌ Portfolio enrichment failed for alert {alert.id}: {e}", source="AlertEnrichment")
            return alert

    async def _enrich_position_type(self, alert):
        try:
            #alert_type_enum = fuzzy_match_enum(str(alert.alert_type), AlertType)

            raw_type = str(alert.alert_type)
            cleaned = raw_type.split('.')[-1]  # Strip enum wrapper
            alert_type_enum = fuzzy_match_enum(cleaned, AlertType)

            if not alert_type_enum:
                log.warning(f"⚠️ Unable to fuzzy-match alert type: {alert.alert_type}", source="AlertEnrichment")
                return alert

            alert.alert_type = alert_type_enum
            alert_type_str = alert_type_enum.name.lower()
            log.debug(f"📌 Matched alert type: {alert_type_str}", source="AlertEnrichment")

            if alert_type_str == "profit":
                log.debug(f"🧭 Routing to _enrich_profit for alert {alert.id}", source="AlertEnrichment")
                return await self._enrich_profit(alert)
            elif alert_type_str == "heatindex":
                log.debug(f"🧭 Routing to _enrich_heat_index for alert {alert.id}", source="AlertEnrichment")
                return await self._enrich_heat_index(alert)
            elif alert_type_str == "travelpercentliquid":
                log.debug(f"🧭 Routing to _enrich_travel_percent for alert {alert.id}", source="AlertEnrichment")
                return await self._enrich_travel_percent(alert)
            else:
                log.warning(f"⚠️ Unsupported matched alert type: {alert_type_str}", source="AlertEnrichment")
                return alert

        except Exception as e:
            log.error(f"❌ Fuzzy match error during enrichment of alert {alert.id}: {e}", source="AlertEnrichment")
            return alert

    async def _enrich_travel_percent(self, alert):
        from utils.travel_percent_logger import log_travel_percent_comparison

        try:
            position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
            if not position:
                log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
                return alert

            entry_price = position.get("entry_price")
            liquidation_price = position.get("liquidation_price")
            position_type = position.get("position_type")

            if not all([entry_price, liquidation_price, position_type]):
                alert.notes = (alert.notes or "") + " 🔸 TravelPercent defaulted due to missing price fields.\n"
                alert.evaluated_value = 0.0
                log.warning(f"⚠️ TravelPercent inputs missing for alert {alert.id}. Using default 0.0",
                            source="AlertEnrichment")
                return alert

            current_price_data = self.data_locker.get_latest_price(position.get("asset_type"))
            if not current_price_data:
                alert.notes = (alert.notes or "") + " 🔸 TravelPercent defaulted due to missing market price.\n"
                alert.evaluated_value = 0.0
                log.warning(f"⚠️ Market price not found for asset {position.get('asset_type')} → defaulting",
                            source="AlertEnrichment")
                return alert

            current_price = current_price_data.get("current_price")

            travel_percent = self.calc_services.calculate_travel_percent(
                position_type=position_type,
                entry_price=entry_price,
                current_price=current_price,
                liquidation_price=liquidation_price
            )

            # Jupiter-provided travel_percent (simulated from position data)
            jupiter_value = 43.5#position.get("travel_percent")

            log.info(f"🛰 Logging drift | Jupiter={jupiter_value}", source="TravelLogger")

            if jupiter_value is not None:
                log_travel_percent_comparison(
                    alert_id=alert.id,
                    jupiter_value=jupiter_value,
                    calculated_value=travel_percent,
                    format="csv"
                )

            if travel_percent is None:
                travel_percent = 0.0
                alert.notes = (alert.notes or "") + " 🔸 TravelPercent calc returned None → defaulted.\n"
                log.warning(f"⚠️ Travel calc failed for alert {alert.id} → default 0.0", source="AlertEnrichment")
            else:
                log.success(f"✅ Enriched Travel Percent Alert {alert.id} evaluated_value={travel_percent}",
                            source="AlertEnrichment")

            alert.evaluated_value = travel_percent

            # ✅ Inject wallet
            wallet_name = position.get("wallet_name")
            wallet = self.data_locker.get_wallet_by_name(wallet_name) if wallet_name else None
            return alert

        except Exception as e:
            log.error(f"Error enriching Travel Percent for alert {alert.id}: {e}", source="AlertEnrichment")
            alert.evaluated_value = 0.0
            alert.notes = (alert.notes or "") + " 🔸 TravelPercent exception → defaulted.\n"
            return alert

    async def _enrich_price_threshold(self, alert):
        current_price_data = self.data_locker.get_latest_price(alert.asset)
        if not current_price_data:
            log.error(f"Current price not found for asset {alert.asset}", source="AlertEnrichment")
            return alert
        alert.evaluated_value = current_price_data.get("current_price")
        log.success(f"✅ Enriched PriceThreshold Alert {alert.id} evaluated_value={alert.evaluated_value}", source="AlertEnrichment")
        return alert

    async def _enrich_profit(self, alert):
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
            return alert

        pnl = position.get("pnl_after_fees_usd") or 0.0
        alert.evaluated_value = pnl

        # ✅ Inject wallet metadata
        wallet_name = position.get("wallet_name")
        wallet = self.data_locker.get_wallet_by_name(wallet_name) if wallet_name else None
        log.success(f"✅ Enriched Profit Alert {alert.id} → {pnl}", source="AlertEnrichment")
        return alert

    async def _enrich_heat_index(self, alert):
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
            return alert

        heat = position.get("current_heat_index")

        if heat is None:
            heat = 5.0  # ← ✅ Default fallback value
            alert.notes = (alert.notes or "") + " 🔸 Default heat index applied (5.0).\n"
            log.warning(f"⚠️ No heat_index for position {position.get('id')} on alert {alert.id} → using default 5.0",
                        source="AlertEnrichment")
        else:
            log.success(f"✅ Enriched HeatIndex Alert {alert.id} evaluated_value={heat}", source="AlertEnrichment")

        # ✅ Inject wallet
        wallet_name = position.get("wallet_name")
        wallet = self.data_locker.get_wallet_by_name(wallet_name) if wallet_name else None
        alert.evaluated_value = heat
        return alert

    async def enrich_all(self, alerts):
        """
        Asynchronously enrich a list of alerts using asyncio.gather.
        Returns a list of enriched alerts.
        """
        if not isinstance(alerts, list):
            log.error("❌ enrich_all() expected a list of alerts", source="AlertEnrichment")
            return []

        log.info(f"🚀 Starting enrichment for {len(alerts)} alerts", source="AlertEnrichment")

        # 🧠 Normalize all alerts before enriching
        alerts = [normalize_alert_fields(alert) for alert in alerts]

        enriched_alerts = await asyncio.gather(*(self.enrich(alert) for alert in alerts))

        log.success(f"✅ Enriched {len(enriched_alerts)} alerts", source="AlertEnrichment")
        return enriched_alerts

