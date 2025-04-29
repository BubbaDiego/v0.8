from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

# --- Enums ---

class AlertType(str, Enum):
    PriceThreshold = "PriceThreshold"
    HeatIndex = "HeatIndex"
    Profit = "Profit"
    TravelPercentLiquid = "TravelPercentLiquid"

class Condition(str, Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"

class AlertLevel(str, Enum):
    NORMAL = "Normal"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Status(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class NotificationType(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    PHONECALL = "PHONECALL"

# --- Main Alert Model ---

class Alert(BaseModel):
    id: str
    alert_type: AlertType
    asset: str
    trigger_value: float
    condition: Condition
    evaluated_value: Optional[float] = 0.0
    position_reference_id: Optional[str] = None
    position_type: Optional[str] = None  # ✅ Now officially supported
    notification_type: Optional[NotificationType] = NotificationType.SMS
    level: Optional[AlertLevel] = AlertLevel.NORMAL
    last_triggered: Optional[datetime] = None
    status: Optional[Status] = Status.ACTIVE
    frequency: Optional[int] = 1
    counter: Optional[int] = 0
    liquidation_distance: Optional[float] = 0.0
    travel_percent: Optional[float] = 0.0
    liquidation_price: Optional[float] = 0.0
    notes: Optional[str] = ""
    description: Optional[str] = ""
