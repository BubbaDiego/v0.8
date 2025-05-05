# cyclone/cyclone_portfolio_service.py

from datetime import datetime
from uuid import uuid4

from data.data_locker import DataLocker
from data.alert import AlertType, Condition
from utils.console_logger import ConsoleLogger as log
from alerts.alert_utils import log_alert_summary


class CyclonePortfolioService:
    def __init__(self):
        self.dl = DataLocker.get_instance()

    async def create_portfolio_alerts(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.info("Creating portfolio alerts", source="CyclonePortfolio")

        metrics = [
            (AlertType.TotalValue, "total_value", 50000),
            (AlertType.TotalSize, "total_size", 1.0),
            (AlertType.AvgLeverage, "avg_leverage", 2.0),
            (AlertType.AvgTravelPercent, "avg_travel_percent", 10.0),
            (AlertType.ValueToCollateralRatio, "value_to_collateral_ratio", 1.2),
            (AlertType.TotalHeat, "total_heat", 25.0),
        ]

        created = 0
        for alert_type, metric_desc, trigger_value in metrics:
            try:
                alert = {
                    "id": str(uuid4()),
                    "created_at": now,
                    "alert_type": alert_type.value,
                    "alert_class": "Portfolio",
                    "asset": "PORTFOLIO",
                    "asset_type": "ALL",
                    "trigger_value": trigger_value,
                    "condition": Condition.ABOVE.value,
                    "notification_type": "SMS",
                    "level": "Normal",
                    "last_triggered": None,
                    "status": "Active",
                    "frequency": 1,
                    "counter": 0,
                    "liquidation_distance": 0.0,
                    "travel_percent": 0.0,
                    "liquidation_price": 0.0,
                    "notes": "Auto-generated portfolio alert",
                    "description": metric_desc,
                    "position_reference_id": None,
                    "evaluated_value": 0.0,
                    "position_type": None
                }

                self.dl.create_alert(alert)
                log_alert_summary(alert)
                created += 1
            except Exception as e:
                log.error(f"Failed to create portfolio alert for {metric_desc}: {e}", source="CyclonePortfolio")

        log.success(f"✅ Created {created} portfolio alerts.", source="CyclonePortfolio")
