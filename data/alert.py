from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

# === Enums ===

class AlertType(str, Enum):
    # 🔥 Position-level alert types
    HeatIndex = "HeatIndex"                       # 🔥 Measures position risk exposure
    Profit = "Profit"                             # 💰 Monitors realized or unrealized PnL
    TravelPercentLiquid = "TravelPercentLiquid"   # ✈️ Distance to liquidation in %

    # 📈 Market-level alert types
    PriceThreshold = "PriceThreshold"             # 📈 Triggers when price crosses a value

    # 🧮 Portfolio-level alert types
    TotalValue = "TotalValue"                     # 💼 Portfolio USD value (sum of all positions)
    TotalSize = "TotalSize"                       # 📊 Total open position size
    AvgLeverage = "AvgLeverage"                   # 🧷 Average leverage across positions
    AvgTravelPercent = "AvgTravelPercent"         # 🚦 Mean liquidation travel % across portfolio
    ValueToCollateralRatio = "ValueToCollateralRatio"  # ⚖️ Risk ratio: value vs. collateral
    TotalHeat = "TotalHeat"                       # 🌡 Composite portfolio heat index

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

# === Main Alert Model ===

class Alert(BaseModel):
    id: str
    alert_type: AlertType                        # 👀 What are we monitoring?
    alert_class: Optional[str] = "Unknown"       # 🧭 Where it belongs (Position, Portfolio, Market)
    asset: Optional[str] = None
    trigger_value: Optional[float] = None
    condition: Condition
    evaluated_value: Optional[float] = 0.0
    position_reference_id: Optional[str] = None
    position_type: Optional[str] = None
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
