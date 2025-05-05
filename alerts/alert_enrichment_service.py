
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.dashboard_service import get_dashboard_context
from utils.calc_services import CalcServices
from utils.console_logger import ConsoleLogger as log
from data.alert import AlertType
from alerts.alert_utils import (
    normalize_alert_type,
    normalize_condition,
    normalize_notification_type,
    normalize_alert_fields
)


class AlertEnrichmentService:
    def __init__(self, data_locker):
        self.data_locker = data_locker
        self.calc_services = CalcServices()

    async def enrich(self, alert):
        """
        Enrich the alert based on its alert_class.
        Dispatches to portfolio, position, or market enrichment as needed.
        """
        try:
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

    async def _enrich_position_type(self, alert):
        """
        Dispatch Position-class alerts to their enrichment method based on alert_type.
        Also attaches wallet info from the position.
        """
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"⚠️ Position not found for alert {alert.id}", source="AlertEnrichment")
            return alert

        # 🧠 Attach wallet info from position
        wallet_id = position.get("wallet_id")
        wallet_name = position.get("wallet_name")
       # alert.wallet_id = wallet_id
      #  alert.wallet_name = wallet_name

        log.debug(f"🔗 Bound wallet to alert {alert.id} → {wallet_name} ({wallet_id})", source="AlertEnrichment")

        if alert.alert_type == AlertType.TravelPercentLiquid:
            return await self._enrich_travel_percent(alert)
        elif alert.alert_type == AlertType.HeatIndex:
            return await self._enrich_heat_index(alert)
        elif alert.alert_type == AlertType.Profit:
            return await self._enrich_profit(alert)
        else:
            log.warning(f"⚠️ Unknown Position alert_type '{alert.alert_type}' for alert {alert.id}",
                        source="AlertEnrichment")
            return alert

    async def _enrich_portfolio(self, alert):
        try:
            context = get_dashboard_context()
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

            value = key_map.get(metric)
            alert.evaluated_value = value

            if value is not None:
                log.success(f"✅ Enriched Portfolio Alert {alert.id} → {metric}={value}", source="AlertEnrichment")
            else:
                log.warning(f"⚠️ Portfolio enrichment metric not found: {metric}", source="AlertEnrichment")

            return alert

        except Exception as e:
            log.error(f"❌ Portfolio enrichment failed for alert {alert.id}: {e}", source="AlertEnrichment")
            return alert

    async def _enrich_travel_percent(self, alert):
        try:
            position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
            if not position:
                log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
                return alert

            entry_price = position.get("entry_price")
            liquidation_price = position.get("liquidation_price")
            position_type = position.get("position_type")

            if not all([entry_price, liquidation_price, position_type]):
                log.error(f"Missing fields in position for alert {alert.id}", source="AlertEnrichment")
                return alert

            current_price_data = self.data_locker.get_latest_price(position.get("asset_type"))
            if not current_price_data:
                log.error(f"Current price not found for asset {position.get('asset_type')}", source="AlertEnrichment")
                return alert

            current_price = current_price_data.get("current_price")

            travel_percent = self.calc_services.calculate_travel_percent(
                position_type=position_type,
                entry_price=entry_price,
                current_price=current_price,
                liquidation_price=liquidation_price
            )

            alert.evaluated_value = travel_percent
            log.success(f"✅ Enriched Travel Percent Alert {alert.id} evaluated_value={travel_percent}", source="AlertEnrichment")
            return alert

        except Exception as e:
            log.error(f"Error enriching Travel Percent for alert {alert.id}: {e}", source="AlertEnrichment")
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
        alert.evaluated_value = position.get("pnl_after_fees_usd")
        log.success(f"✅ Enriched Profit Alert {alert.id} evaluated_value={alert.evaluated_value}", source="AlertEnrichment")
        return alert

    async def _enrich_heat_index(self, alert):
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
            return alert
        alert.evaluated_value = position.get("current_heat_index")
        log.success(f"✅ Enriched HeatIndex Alert {alert.id} evaluated_value={alert.evaluated_value}", source="AlertEnrichment")
        return alert

    async def _determine_value_travel_percent(self, alert):
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
            return None

        current_price_data = self.data_locker.get_latest_price(position.get("asset_type"))
        if not current_price_data:
            log.error(f"Current price not found for asset {position.get('asset_type')}", source="AlertEnrichment")
            return None

        try:
            travel_percent = self.calc_services.calculate_travel_percent(
                position_type=position.get("position_type"),
                entry_price=position.get("entry_price"),
                current_price=current_price_data.get("current_price"),
                liquidation_price=position.get("liquidation_price")
            )
            return travel_percent
        except Exception as e:
            log.error(f"Error calculating Travel Percent for alert {alert.id}: {e}", source="AlertEnrichment")
            return None

    async def _determine_value_price_threshold(self, alert):
        current_price_data = self.data_locker.get_latest_price(alert.asset)
        if not current_price_data:
            log.error(f"Current price not found for asset {alert.asset}", source="AlertEnrichment")
            return None
        return current_price_data.get("current_price")

    async def _determine_value_profit(self, alert):
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
            return None
        return position.get("pnl_after_fees_usd")

    async def _determine_value_heat_index(self, alert):
        position = self.data_locker.get_position_by_reference_id(alert.position_reference_id)
        if not position:
            log.error(f"Position not found for alert {alert.id}", source="AlertEnrichment")
            return None
        return position.get("current_heat_index")
