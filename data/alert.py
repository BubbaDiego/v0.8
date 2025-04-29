from enum import Enum
from pydantic import BaseModel
from typing import Optional

class AlertType(str, Enum):
    PriceThreshold = "PriceThreshold"
    Profit = "Profit"
    TravelPercentLiquid = "TravelPercentLiquid"
    HeatIndex = "HeatIndex"

class Condition(str, Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"

class NotificationType(str, Enum):
    SMS = "SMS"
    EMAIL = "Email"
    PHONECALL = "PhoneCall"

class AlertLevel(str, Enum):
    NORMAL = "Normal"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Status(str, Enum):
    Active = "Active"
    Inactive = "Inactive"
    Triggered = "Triggered"

# ✅ Now add Alert BaseModel
class Alert(BaseModel):
    id: str
    alert_type: AlertType
    asset: str
    trigger_value: float
    condition: Condition
    evaluated_value: float = 0.0
    level: AlertLevel = AlertLevel.NORMAL
    status: Status = Status.Active
    last_triggered: Optional[str] = None
    position_reference_id: Optional[str] = None
    notification_type: NotificationType = NotificationType.SMS
