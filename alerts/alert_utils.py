from threading import Condition

from data.alert import AlertType
from data.alert import NotificationType

from data.alert import Condition



# 🚀 Batch normalizer for full Alert object
def normalize_alert_fields(alert):
    """
    Normalize key enum fields on an Alert object (alert_type, condition, notification_type).
    Accepts either Alert model or dict.
    """
    if isinstance(alert, dict):
        if "alert_type" in alert:
            alert["alert_type"] = normalize_alert_type(alert["alert_type"])
        if "condition" in alert:
            alert["condition"] = normalize_condition(alert["condition"])
        if "notification_type" in alert:
            alert["notification_type"] = normalize_notification_type(alert["notification_type"])
        return alert

    # Assume it's a Pydantic model or similar
    if hasattr(alert, "alert_type") and alert.alert_type:
        alert.alert_type = normalize_alert_type(alert.alert_type)
    if hasattr(alert, "condition") and alert.condition:
        alert.condition = normalize_condition(alert.condition)
    if hasattr(alert, "notification_type") and alert.notification_type:
        alert.notification_type = normalize_notification_type(alert.notification_type)

    return alert

def normalize_condition(condition_input):
    """
    Normalize incoming condition input to Condition Enum.
    """
    if isinstance(condition_input, Condition):
        return condition_input

    if isinstance(condition_input, str):
        cleaned = condition_input.strip().replace("_", "").replace(" ", "").lower()

        mapping = {
            "above": Condition.ABOVE,
            "below": Condition.BELOW,
        }

        if cleaned in mapping:
            return mapping[cleaned]
        else:
            raise ValueError(f"Invalid condition string: {condition_input}")

    raise TypeError(f"Invalid condition input: {type(condition_input)}")


def normalize_alert_type(alert_type_input):
    """
    Normalize incoming alert_type input:
    - If already an AlertType Enum, return as-is
    - If string, try to convert to AlertType Enum
    """
    from data.alert import AlertType

    if isinstance(alert_type_input, AlertType):
        return alert_type_input

    if isinstance(alert_type_input, str):
        cleaned = alert_type_input.strip().replace("_", "").replace(" ", "").lower()

        mapping = {
            "pricethreshold": AlertType.PriceThreshold,
            "profit": AlertType.Profit,
            "travelpercentliquid": AlertType.TravelPercentLiquid,
            "heatindex": AlertType.HeatIndex,
            "totalvalue": AlertType.TotalValue,
            "totalsize": AlertType.TotalSize,
            "avgleverage": AlertType.AvgLeverage,
            "avgtravelpercent": AlertType.AvgTravelPercent,
            "valuetocollateralratio": AlertType.ValueToCollateralRatio,
            "totalheat": AlertType.TotalHeat
        }

        if cleaned in mapping:
            return mapping[cleaned]
        else:
            raise ValueError(
                f"Invalid alert_type string: {alert_type_input}. "
                f"Expected one of: {list(mapping.keys())}"
            )

    raise TypeError(f"Invalid alert_type input: {type(alert_type_input)}")




def normalize_notification_type(notification_input):
    """
    Normalize incoming notification_type input to NotificationType Enum.
    """
    if isinstance(notification_input, NotificationType):
        return notification_input

    if isinstance(notification_input, str):
        cleaned = notification_input.strip().replace("_", "").replace(" ", "").lower()

        mapping = {
            "sms": NotificationType.SMS,
            "email": NotificationType.EMAIL,
            "phonecall": NotificationType.PHONECALL,
        }

        if cleaned in mapping:
            return mapping[cleaned]
        else:
            raise ValueError(f"Invalid notification_type string: {notification_input}")

    raise TypeError(f"Invalid notification_type input: {type(notification_input)}")

def log_alert_summary(alert):
    """
    Print a clean, emoji-annotated summary of a created alert.
    """
    from utils.console_logger import ConsoleLogger as log

    alert_type = getattr(alert, "alert_type", None)
    alert_class = getattr(alert, "alert_class", None)
    trigger_value = getattr(alert, "trigger_value", None)

    if isinstance(alert, dict):
        alert_type = alert.get("alert_type")
        alert_class = alert.get("alert_class")
        trigger_value = alert.get("trigger_value")

    log.info(
        f"📦 Alert Created → 🧭 Class: {alert_class} | 🏷️ Type: {alert_type} | 🎯 Trigger: {trigger_value}",
        source="CreateAlert"
    )
