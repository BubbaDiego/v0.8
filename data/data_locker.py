#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sqlite3
import logging
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4
from config.config_constants import DB_PATH


from alerts.alert_utils import (
    normalize_alert_type,
    normalize_condition,
    normalize_notification_type
)


class DataLocker:
    """
    A synchronous DataLocker that manages database interactions using sqlite3.
    Stores:
      - Prices in the 'prices' table.
      - Positions in the 'positions' table.
      - Alerts in the 'alerts' table.
      - System variables (timestamps, balance vars, and strategy performance data) in the 'system_vars' table.
      - Brokers in the 'brokers' table.
      - Wallets in the 'wallets' table.
      - Aggregated positions snapshots in the 'positions_totals_history' table.
    """

    _instance: Optional['DataLocker'] = None

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = DB_PATH
        self.db_path = db_path
        self.logger = logging.getLogger("DataLockerLogger")
        self.conn = None
        self._initialize_database()

    class DictRow(sqlite3.Row):
        def get(self, key, default=None):
            try:
                return self[key]
            except KeyError:
                return default

    def _initialize_database(self):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()

            # Create system_vars table (if needed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_vars (
                    id INTEGER PRIMARY KEY,
                    last_update_time_positions DATETIME,
                    last_update_positions_source TEXT,
                    last_update_time_prices DATETIME,
                    last_update_prices_source TEXT,
                    last_update_time_jupiter DATETIME
                )
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO system_vars (
                    id,
                    last_update_time_positions,
                    last_update_positions_source,
                    last_update_time_prices,
                    last_update_prices_source,
                    last_update_time_jupiter
                )
                VALUES (1, NULL, NULL, NULL, NULL, NULL)
            """)

            # Add new columns for Jupiter updates if missing
            cursor.execute("PRAGMA table_info(system_vars)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            if "last_update_time_jupiter" not in existing_cols:
                cursor.execute("""
                    ALTER TABLE system_vars
                    ADD COLUMN last_update_time_jupiter DATETIME
                """)
                self.logger.info("Added 'last_update_time_jupiter' column to 'system_vars' table.")
            if "last_update_jupiter_source" not in existing_cols:
                cursor.execute("""
                    ALTER TABLE system_vars
                    ADD COLUMN last_update_jupiter_source TEXT
                """)
                self.logger.info("Added 'last_update_jupiter_source' column to 'system_vars' table.")

            cursor.execute("PRAGMA table_info(system_vars)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            if "theme_mode" not in existing_cols:
                cursor.execute("ALTER TABLE system_vars ADD COLUMN theme_mode TEXT DEFAULT 'light'")
                self.logger.info("Added 'theme_mode' column to 'system_vars' table.")

            # Add additional balance columns if missing
            cursor.execute("PRAGMA table_info(system_vars)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            for col, sql in [
                ("total_brokerage_balance",
                 "ALTER TABLE system_vars ADD COLUMN total_brokerage_balance REAL DEFAULT 0.0"),
                ("total_wallet_balance", "ALTER TABLE system_vars ADD COLUMN total_wallet_balance REAL DEFAULT 0.0"),
                ("total_balance", "ALTER TABLE system_vars ADD COLUMN total_balance REAL DEFAULT 0.0")
            ]:
                if col not in existing_cols:
                    cursor.execute(sql)
                    self.logger.info(f"Added '{col}' column to 'system_vars' table.")

            # NEW: Create position_alert_map table to support multiple alerts per position.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS position_alert_map (
                    id TEXT PRIMARY KEY,
                    position_id TEXT NOT NULL,
                    alert_id TEXT NOT NULL,
                    FOREIGN KEY(position_id) REFERENCES positions(id),
                    FOREIGN KEY(alert_id) REFERENCES alerts(id)
                )
            """)

            # NEW: Add columns for strategy performance persistence
            cursor.execute("PRAGMA table_info(system_vars)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            if "strategy_start_value" not in existing_cols:
                cursor.execute("ALTER TABLE system_vars ADD COLUMN strategy_start_value REAL DEFAULT 0.0")
               # self.logger.info("Added 'strategy_start_value' column to 'system_vars' table.")
            if "strategy_description" not in existing_cols:
                cursor.execute("ALTER TABLE system_vars ADD COLUMN strategy_description TEXT DEFAULT ''")
               # self.logger.info("Added 'strategy_description' column to 'system_vars' table.")

            # Create prices table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id TEXT PRIMARY KEY,
                    asset_type TEXT,
                    current_price REAL,
                    previous_price REAL,
                    last_update_time DATETIME,
                    previous_update_time DATETIME,
                    source TEXT
                )
            """)

            # Create positions table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    asset_type TEXT,
                    position_type TEXT,
                    entry_price REAL,
                    liquidation_price REAL,
                    travel_percent REAL,  -- Unified column name for travel percent
                    value REAL,
                    collateral REAL,
                    size REAL,
                    leverage REAL,
                    wallet_name TEXT,
                    last_updated DATETIME,
                    alert_reference_id TEXT,
                    hedge_buddy_id TEXT,
                    current_price REAL,
                    liquidation_distance REAL,
                    heat_index REAL,
                    current_heat_index REAL,
                    pnl_after_fees_usd REAL
                )
            """)

            # Create alerts table if it doesn't exist
            # Inside _initialize_database() in DataLocker, update the alerts table creation:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    created_at DATETIME,
                    alert_type TEXT,
                    alert_class TEXT,
                    asset_type TEXT,
                    trigger_value REAL,
                    condition TEXT,
                    notification_type TEXT,
                    level TEXT,
                    last_triggered DATETIME,
                    status TEXT,
                    frequency INTEGER,
                    counter INTEGER,
                    liquidation_distance REAL,
                    travel_percent REAL,
                    liquidation_price REAL,
                    notes TEXT,
                    description TEXT,
                    position_reference_id TEXT,
                    evaluated_value REAL
                )
            """)

            # Now, check if 'position_type' column exists in alerts table:
            cursor.execute("PRAGMA table_info(alerts)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            if "position_type" not in existing_cols:
                cursor.execute("ALTER TABLE alerts ADD COLUMN position_type TEXT")
                self.logger.info("Added 'position_type' column to 'alerts' table.")

            # Create new ledger table for update ledger (alert ledger)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_ledger (
                    id TEXT PRIMARY KEY,
                    alert_id TEXT,
                    modified_by TEXT,
                    reason TEXT,
                    before_value TEXT,
                    after_value TEXT,
                    timestamp DATETIME
                )
            """)

            # Create brokers table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brokers (
                    name TEXT PRIMARY KEY,
                    image_path TEXT,
                    web_address TEXT,
                    total_holding REAL DEFAULT 0.0
                )
            """)

            # Create wallets table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    name TEXT PRIMARY KEY,
                    public_address TEXT,
                    private_address TEXT,
                    image_path TEXT,
                    balance REAL DEFAULT 0.0
                )
            """)

            # Create portfolio_entries table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_entries (
                    id TEXT PRIMARY KEY,
                    snapshot_time DATETIME,
                    total_value REAL NOT NULL
                )
            """)

            # Create positions_totals_history table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions_totals_history (
                    id TEXT PRIMARY KEY,
                    snapshot_time DATETIME,
                    total_size REAL,
                    total_value REAL,
                    total_collateral REAL,
                    avg_leverage REAL,
                    avg_travel_percent REAL,
                    avg_heat_index REAL
                )
            """)
            self.conn.commit()
           # self.logger.debug("Database initialization complete.")
        except sqlite3.Error as e:
            self.logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> 'DataLocker':
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def _init_sqlite_if_needed(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
          #  self.logger.debug(f"Created directory for DB: {db_dir}")
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.row_factory = self.DictRow

    def get_db_connection(self) -> sqlite3.Connection:
        self._init_sqlite_if_needed()
        return self.conn

    def add_position_alert_mapping(self, position_id: str, alert_id: str) -> None:
        """Adds a mapping record linking a position to an alert."""
        cursor = self.conn.cursor()
        sql = """
            INSERT INTO position_alert_map (id, position_id, alert_id)
            VALUES (?, ?, ?)
        """
        mapping_id = str(uuid4())
        cursor.execute(sql, (mapping_id, position_id, alert_id))
        self.conn.commit()
        cursor.close()

    def has_alert_mapping(self, position_id: str, alert_type: str) -> bool:
        """
        Checks whether an alert of a specific type already exists for a position,
        by joining the alerts table with the mapping table.
        """
        cursor = self.conn.cursor()
        sql = """
            SELECT a.id FROM alerts a
            JOIN position_alert_map pam ON a.id = pam.alert_id
            WHERE pam.position_id = ? AND a.alert_type = ?
        """
        cursor.execute(sql, (position_id, alert_type))
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    def get_theme_mode(self) -> str:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("SELECT theme_mode FROM system_vars WHERE id = 1 LIMIT 1")
        row = cursor.fetchone()
        return row["theme_mode"] if row and "theme_mode" in row and row["theme_mode"] else "light"

    def set_theme_mode(self, mode: str):
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE system_vars SET theme_mode = ? WHERE id = 1", (mode,))
        self.conn.commit()

    # ----------------------------------------------------------------
    # Strategy Performance Data Persistence
    # ----------------------------------------------------------------

    def set_strategy_performance_data(self, start_value: float, description: str):
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE system_vars
               SET strategy_start_value = ?,
                   strategy_description = ?
            WHERE id = 1
        """, (start_value, description))
        self.conn.commit()
       # self.logger.debug(f"Updated strategy performance data: start_value={start_value}, description={description}")

    def get_strategy_performance_data(self) -> dict:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT strategy_start_value, strategy_description
            FROM system_vars
            WHERE id = 1
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {
                "strategy_start_value": row["strategy_start_value"] or 0.0,
                "strategy_description": row["strategy_description"] or ""
            }
        else:
            return {"strategy_start_value": 0.0, "strategy_description": ""}

    # ----------------------------------------------------------------
    # PRICES
    # ----------------------------------------------------------------

    def insert_price(self, price_dict: dict):
        try:
            self._init_sqlite_if_needed()
            if "id" not in price_dict:
                price_dict["id"] = str(uuid4())
            if "asset_type" not in price_dict:
                price_dict["asset_type"] = "BTC"
            if "current_price" not in price_dict:
                price_dict["current_price"] = 1.0
            if "previous_price" not in price_dict:
                price_dict["previous_price"] = 0.0
            if "last_update_time" not in price_dict:
                price_dict["last_update_time"] = datetime.now().isoformat()
            if "previous_update_time" not in price_dict:
                price_dict["previous_update_time"] = None
            if "source" not in price_dict:
                price_dict["source"] = "Manual"
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO prices (
                    id,
                    asset_type,
                    current_price,
                    previous_price,
                    last_update_time,
                    previous_update_time,
                    source
                )
                VALUES (
                    :id, :asset_type, :current_price, :previous_price,
                    :last_update_time, :previous_update_time, :source
                )
            """, price_dict)
            self.conn.commit()
            self.logger.debug(f"Inserted price row with ID={price_dict['id']}")
        except Exception as e:
            self.logger.exception(f"Unexpected error in insert_price: {e}")
            raise

    def get_prices(self, asset_type: Optional[str] = None) -> List[dict]:
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            if asset_type:
                cursor.execute("""
                    SELECT *
                      FROM prices
                     WHERE asset_type=?
                     ORDER BY last_update_time DESC
                """, (asset_type,))
            else:
                cursor.execute("""
                    SELECT *
                      FROM prices
                     ORDER BY last_update_time DESC
                """)
            rows = cursor.fetchall()
            price_list = [dict(r) for r in rows]
            self.logger.debug(f"Retrieved {len(price_list)} price rows.")
            return price_list
        except sqlite3.Error as e:
            self.logger.error(f"Database error in get_prices: {e}", exc_info=True)
            return []
        except Exception as e:
            self.logger.exception(f"Unexpected error in get_prices: {e}")
            return []

    def read_prices(self) -> List[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM prices ORDER BY last_update_time DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def get_latest_price(self, asset_type: str) -> Optional[dict]:
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT *
                  FROM prices
                 WHERE asset_type=?
                 ORDER BY last_update_time DESC
                 LIMIT 1
            """, (asset_type,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Database error in get_latest_price: {e}", exc_info=True)
            return None
        except Exception as ex:
            self.logger.exception(f"Unexpected error in get_latest_price: {ex}")
            return None

    def delete_price(self, price_id: str):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM prices WHERE id=?", (price_id,))
            self.conn.commit()
            self.logger.debug(f"Deleted price row ID={price_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error in delete_price: {e}", exc_info=True)
            raise
        except Exception as ex:
            self.logger.exception(f"Unexpected error in delete_price: {ex}")
            raise

    def get_portfolio_history(self) -> List[dict]:

        def get_portfolio_history(self):
            return [
                {"snapshot_time": "2025-04-24T10:00:00Z", "total_value": 1000, "total_collateral": 800},
                {"snapshot_time": "2025-04-24T11:00:00Z", "total_value": 1100, "total_collateral": 850},
                {"snapshot_time": "2025-04-24T12:00:00Z", "total_value": 950, "total_collateral": 780}
            ]

        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
              FROM positions_totals_history
             ORDER BY snapshot_time ASC
        """)
        rows = cursor.fetchall()
        portfolio_history = [dict(row) for row in rows]
        self.logger.debug(f"Fetched {len(portfolio_history)} portfolio snapshots.")
        return portfolio_history

    def get_latest_portfolio_snapshot(self) -> Optional[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
              FROM positions_totals_history
             ORDER BY snapshot_time DESC
             LIMIT 1
        """)
        row = cursor.fetchone()
        latest_snapshot = dict(row) if row else None
        self.logger.debug("Retrieved latest portfolio snapshot." if latest_snapshot else "No portfolio snapshot found.")
        return latest_snapshot

    def record_portfolio_snapshot(self, totals: dict):
        self.record_positions_totals_snapshot(totals)
        self.logger.debug("Recorded portfolio snapshot via record_portfolio_snapshot.")

    def initialize_alert_data(self, alert_data: dict = None) -> dict:
        from data.models import Status, AlertLevel
        from uuid import uuid4
        from datetime import datetime

        defaults = {
            "id": str(uuid4()),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "alert_type": "",
            "alert_class": "",
            "asset_type": "BTC",
            "trigger_value": 0.0,
            "condition": "ABOVE",
            "notification_type": "Email",
            "level": AlertLevel.NORMAL.value,  # New default for alert level
            "last_triggered": None,
            "status": Status.ACTIVE.value,
            "frequency": 1,
            "counter": 0,
            "liquidation_distance": 0.0,
            "travel_percent": 0.0,  # Updated key for travel percent
            "liquidation_price": 0.0,
            "notes": "",
            "description": "",
            "position_reference_id": None,
            "evaluated_value": 0.0
        }
        if alert_data is None:
            alert_data = {}

        for key, default_val in defaults.items():
            if key not in alert_data or alert_data.get(key) is None:
                alert_data[key] = default_val
            elif key == "position_reference_id":
                value = alert_data.get(key)
                if isinstance(value, str) and value.strip() == "":
                    self.logger.error("initialize_alert_data: position_reference_id is empty for a position alert")
        return alert_data

    # ----------------------------------------------------------------
    # ALERTS
    # ----------------------------------------------------------------
    from alerts.alert_utils import (
        normalize_alert_type,
        normalize_condition,
        normalize_notification_type
    )

    def create_alert(self, alert_obj) -> bool:
        try:
            self.logger.debug("[DataLocker] Starting create_alert process.")

            if not isinstance(alert_obj, dict):
                alert_dict = alert_obj.to_dict()
                self.logger.debug("Converted alert object to dict.")
            else:
                alert_dict = alert_obj
                self.logger.debug("Alert object is already a dict.")

            # Normalize critical fields
            if "alert_type" in alert_dict:
                alert_dict["alert_type"] = normalize_alert_type(alert_dict["alert_type"]).value
            if "condition" in alert_dict:
                alert_dict["condition"] = normalize_condition(alert_dict["condition"]).value
            if "notification_type" in alert_dict:
                alert_dict["notification_type"] = normalize_notification_type(alert_dict["notification_type"]).value

            # Initialize defaults
            alert_dict = self.initialize_alert_data(alert_dict)

            # Correct SQL to include asset
            cursor = self.conn.cursor()
            sql = """
                INSERT INTO alerts (
                    id,
                    created_at,
                    alert_type,
                    alert_class,
                    asset,
                    asset_type,
                    trigger_value,
                    condition,
                    notification_type,
                    level,
                    last_triggered,
                    status,
                    frequency,
                    counter,
                    liquidation_distance,
                    travel_percent,
                    liquidation_price,
                    notes,
                    description,
                    position_reference_id,
                    evaluated_value,
                    position_type
                ) VALUES (
                    :id, :created_at, :alert_type, :alert_class, :asset, :asset_type,
                    :trigger_value, :condition, :notification_type, :level,
                    :last_triggered, :status, :frequency, :counter, :liquidation_distance,
                    :travel_percent, :liquidation_price, :notes, :description,
                    :position_reference_id, :evaluated_value, :position_type
                )
            """
            cursor.execute(sql, alert_dict)
            self.conn.commit()
            cursor.close()

            self.logger.debug(f"Alert created successfully with ID={alert_dict['id']}")
            return True

        except sqlite3.IntegrityError as ie:
            self.logger.error(f"IntegrityError creating alert: {ie}", exc_info=True)
            return False
        except Exception as ex:
            self.logger.exception(f"Unexpected error creating alert: {ex}")
            raise

    def get_alert(self, alert_id: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE id=?", (alert_id,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return dict(row)
        return None

    # --- New Method to Get Alert Limits ---
    def get_alert_limits(self):
        try:
            alert_limits_path = os.path.join(self.db_path, "..", "alert_limits.json")
            alert_limits_path = os.path.abspath(alert_limits_path)  # Always use absolute path
            with open(alert_limits_path, "r") as f:
                data = json.load(f)

            return {
                "call_refractory_period": float(data.get("call_refractory_period", 1800)),  # default 30 min
                "call_refractory_start": None,  # Optional, you can wire this later
                "snooze_countdown": float(data.get("alert_config", {}).get("snooze_countdown", 300)),
                # 5 min default
                "snooze_start": None
            }

        except Exception as e:
            print(f"[ERROR] Failed to load alert_limits.json: {e}")
            # Return safe fallback if file missing or corrupt
            return {
                "call_refractory_period": 1800,
                "call_refractory_start": None,
                "snooze_countdown": 300,
                "snooze_start": None
            }

    def get_position_by_reference_id(self, ref_id: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE id=?", (ref_id,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def get_current_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def serialize_sql_values(self, values):
        result = []
        for v in values:
            if hasattr(v, "value"):  # Enum
                result.append(v.value)
            elif hasattr(v, "to_dict"):  # Object
                result.append(str(v.to_dict()))
            else:
                result.append(str(v) if not isinstance(v, (str, int, float)) else v)
        return result

    def update_alert_conditions(self, alert_id: str, update_fields: dict) -> int:
        try:
            cursor = self.conn.cursor()
            set_clause = ", ".join(f"{key}=?" for key in update_fields.keys())
            values = self.serialize_sql_values(update_fields.values())
            values.append(alert_id)
            sql = f"UPDATE alerts SET {set_clause} WHERE id=?"
            self.logger.debug("Executing SQL: %s with values: %s", sql, values)
            cursor.execute(sql, values)
            self.conn.commit()
            num_updated = cursor.rowcount
            self.logger.info("Alert %s updated, rows affected: %s", alert_id, num_updated)
            return num_updated
        except Exception as ex:
            self.logger.error("Error updating alert conditions for %s: %s", alert_id, ex, exc_info=True)
            raise

    def get_alerts(self) -> List[dict]:
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM alerts")
            rows = cursor.fetchall()
            alert_list = [dict(r) for r in rows]
            self.logger.debug(f"Fetched {len(alert_list)} alerts.")
            return alert_list
        except sqlite3.Error as e:
            self.logger.error(f"Database error in get_alerts: {e}", exc_info=True)
            return []
        except Exception as ex:
            self.logger.exception(f"Unexpected error in get_alerts: {ex}")
            return []

    def update_alert_status(self, alert_id: str, new_status: str):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE alerts
                   SET status=?
                 WHERE id=?
            """, (new_status, alert_id))
            self.conn.commit()
            self.logger.debug(f"Alert {alert_id} => status={new_status}")
        except sqlite3.Error as e:
            self.logger.error(f"DB error update_alert_status: {e}", exc_info=True)
            raise
        except Exception as ex:
            self.logger.exception(f"Error updating alert status: {ex}")
            raise

    def delete_alert(self, alert_id: str):
        try:
            self._init_sqlite_if_needed()
            self.logger.debug(f"Preparing to delete alert with id: {alert_id}")
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
            self.conn.commit()
            self.logger.debug(f"Deleted alert with id: {alert_id} successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error while deleting alert {alert_id}: {e}", exc_info=True)
            raise
        except Exception as ex:
            self.logger.exception(f"Unexpected error while deleting alert {alert_id}: {ex}")
            raise

    # ----------------------------------------------------------------
    # Insert/Update Price
    # ----------------------------------------------------------------

    def insert_or_update_price(self, asset_type: str, current_price: float, source: str, timestamp: Optional[datetime] = None):
        self._init_sqlite_if_needed()
        if timestamp is None:
            timestamp = datetime.now()
        price_dict = {
            "id": str(uuid4()),
            "asset_type": asset_type,
            "current_price": current_price,
            "previous_price": 0.0,
            "last_update_time": timestamp.isoformat(),
            "previous_update_time": None,
            "source": source
        }
        self.insert_price(price_dict)

    # APIs use this shit
    def update_price(self, price_id: str, current_price: float, last_update_time: str) -> int:
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE prices SET current_price = ?, last_update_time = ? WHERE id = ?",
                (current_price, last_update_time, price_id)
            )
            self.conn.commit()
            self.logger.debug(
                f"Updated price {price_id}: current_price={current_price}, last_update_time={last_update_time}")
            return cursor.rowcount
        except Exception as ex:
            self.logger.exception(f"Error updating price {price_id}: {ex}")
            raise

    # ----------------------------------------------------------------
    # POSITIONS
    # ----------------------------------------------------------------

    def create_position(self, pos_dict: dict) -> None:
        """
        Creates a new position record in the database.
        Enforces that current_price must exist and be reasonable.
        """
        import logging
        logger = logging.getLogger(__name__)

        # -- ENFORCEMENT BLOCK --

        asset_type = pos_dict.get('asset_type')
        current_price = pos_dict.get('current_price', 0.0)

        if current_price in (None, 0, 0.0):
            logger.debug(f"[CREATE_POSITION] No current_price for {asset_type}, attempting to fetch latest price...")
            latest_price_data = self.get_latest_price(asset_type)

            if latest_price_data and 'current_price' in latest_price_data:
                pos_dict['current_price'] = float(latest_price_data['current_price'])
                logger.debug(f"[CREATE_POSITION] Set current_price for {asset_type} to {pos_dict['current_price']}")
            else:
                # Fallback to entry_price if no market price available
                fallback_price = pos_dict.get('entry_price', 0.0)
                pos_dict['current_price'] = fallback_price
                logger.warning(
                    f"[CREATE_POSITION] No live price for {asset_type}; fallback to entry_price={fallback_price}")

        # Force float
        pos_dict['current_price'] = float(pos_dict.get('current_price', 0.0))

        # FINAL ASSERTION (absolute enforcement)
        assert pos_dict[
                   'current_price'] > 0.0, f"[CREATE_POSITION] Cannot create position with invalid current_price for {asset_type}"

        # -- NORMAL INSERT BLOCK --

        try:
            cursor = self.conn.cursor()
            cursor.execute(
            """
            INSERT
            INTO
            positions(
                id, asset_type, position_type, entry_price, current_price, liquidation_price,
                collateral, size, leverage, value, last_updated,
                wallet_name, alert_reference_id, hedge_buddy_id, pnl_after_fees_usd
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                pos_dict.get('id'),
                pos_dict.get('asset_type'),
                pos_dict.get('position_type'),
                pos_dict.get('entry_price'),
                pos_dict.get('current_price'),
                pos_dict.get('liquidation_price'),
                pos_dict.get('collateral'),
                pos_dict.get('size'),
                pos_dict.get('leverage'),
                pos_dict.get('value'),
                pos_dict.get('last_updated'),
                pos_dict.get('wallet_name'),
                pos_dict.get('alert_reference_id'),
                pos_dict.get('hedge_buddy_id'),
                pos_dict.get('pnl_after_fees_usd')
            )
            )
            self.conn.commit()
            logger.info(f"[CREATE_POSITION] Successfully created position for {asset_type}")
        except Exception as e:
            logger.error(f"[CREATE_POSITION] Failed to insert position: {e}", exc_info=True)
            raise

    def get_positions(self) -> List[dict]:
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM positions")
            rows = cursor.fetchall()
            results = [dict(r) for r in rows]
            self.logger.debug(f"Fetched {len(results)} positions.")
            return results
        except sqlite3.Error as e:
            self.logger.error(f"DB error get_positions: {e}", exc_info=True)
            return []
        except Exception as ex:
            self.logger.exception(f"Error get_positions: {ex}")
            return []

    def read_positions(self) -> List[dict]:
        return self.get_positions()

    def delete_position(self, position_id: str):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM positions WHERE id=?", (position_id,))
            self.conn.commit()
            self.logger.debug(f"Deleted position ID={position_id}")
        except sqlite3.Error as e:
            self.logger.error(f"DB error delete_position: {e}", exc_info=True)
            raise
        except Exception as ex:
            self.logger.exception(f"Error delete_position: {ex}")
            raise

    def delete_all_positions(self):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM positions")
            self.conn.commit()
            self.logger.debug("Deleted all positions.")
        except Exception as ex:
            self.logger.exception(f"Error in delete_all_positions: {ex}")
            raise

    # ----------------------------------------------------------------
    # GET / SET last update times (system_vars table)
    # ----------------------------------------------------------------

    def set_last_update_times(self, positions_dt=None, positions_source=None, prices_dt=None, prices_source=None, jupiter_dt=None):
        current = self.get_last_update_times() or {}
        new_positions_dt = positions_dt.isoformat() if positions_dt else current.get("last_update_time_positions", None)
        new_prices_dt = prices_dt.isoformat() if prices_dt else current.get("last_update_time_prices", None)
        new_jupiter_dt = jupiter_dt.isoformat() if jupiter_dt else current.get("last_update_time_jupiter", None)

        cursor = self.conn.cursor()
        if current:
            cursor.execute("""
                UPDATE system_vars
                   SET last_update_time_positions = ?,
                       last_update_positions_source = ?,
                       last_update_time_prices = ?,
                       last_update_prices_source = ?,
                       last_update_time_jupiter = ?
                 WHERE id = 1
            """, (new_positions_dt, positions_source, new_prices_dt, prices_source, new_jupiter_dt))
        else:
            cursor.execute("""
                INSERT INTO system_vars 
                    (id, last_update_time_positions, last_update_positions_source,
                     last_update_time_prices, last_update_prices_source, last_update_time_jupiter)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (new_positions_dt, positions_source, new_prices_dt, prices_source, new_jupiter_dt))
        self.conn.commit()
        cursor.close()

    def get_last_update_times(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT last_update_time_positions, last_update_positions_source,
                   last_update_time_prices, last_update_prices_source,
                   last_update_time_jupiter
              FROM system_vars
             WHERE id = 1
             LIMIT 1
        """)
        row = cursor.fetchone()
        cursor.close()
        if row is not None:
            return dict(row)
        else:
            return {}

    # ----------------------------------------------------------------
    # WALLET & BROKER
    # ----------------------------------------------------------------

    def read_wallets(self) -> List[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM wallets")
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "name": r["name"],
                "public_address": r["public_address"],
                "private_address": r["private_address"],
                "image_path": r["image_path"],
                "balance": float(r["balance"])
            })
        return results

    def update_wallet(self, wallet_name, wallet_dict):
        self._init_sqlite_if_needed()
        query = """
            UPDATE wallets 
               SET name = ?,
                   public_address = ?,
                   private_address = ?,
                   image_path = ?,
                   balance = ?
             WHERE name = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (
            wallet_dict.get("name"),
            wallet_dict.get("public_address"),
            wallet_dict.get("private_address"),
            wallet_dict.get("image_path"),
            wallet_dict.get("balance"),
            wallet_name
        ))
        self.conn.commit()

    def delete_positions_for_wallet(self, wallet_name: str):
        self._init_sqlite_if_needed()
        self.logger.info(f"Deleting positions for wallet: {wallet_name}")
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM positions WHERE wallet_name IS NOT NULL")
        self.conn.commit()
        cursor.close()

    def update_position(self, position_id: str, size: float, collateral: float):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            query = """
            UPDATE positions
               SET size=?,
                   collateral=?
             WHERE id=?
            """
            cursor.execute(query, (size, collateral, position_id))
            self.conn.commit()
        except Exception as ex:
            self.logger.exception(f"Error updating position {position_id}: {ex}")
            raise

    def create_wallet(self, wallet_dict: dict):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO wallets (name, public_address, private_address, image_path, balance)
                VALUES (?,?,?,?,?)
            """, (
                wallet_dict.get("name"),
                wallet_dict.get("public_address"),
                wallet_dict.get("private_address"),
                wallet_dict.get("image_path"),
                wallet_dict.get("balance", 0.0)
            ))
            self.conn.commit()
        except Exception as ex:
            self.logger.exception(f"Error creating wallet: {ex}")
            raise

    def create_broker(self, broker_dict: dict):
        self._init_sqlite_if_needed()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO brokers (name, image_path, web_address, total_holding)
                VALUES (?,?,?,?)
            """, (
                broker_dict.get("name"),
                broker_dict.get("image_path"),
                broker_dict.get("web_address"),
                broker_dict.get("total_holding", 0.0)
            ))
            self.conn.commit()
        except sqlite3.Error as ex:
            self.logger.error(f"DB error create_broker: {ex}", exc_info=True)
            raise

    def read_brokers(self) -> List[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM brokers")
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "name": r["name"],
                "image_path": r["image_path"],
                "web_address": r["web_address"],
                "total_holding": float(r["total_holding"])
            })
        return results

    def read_positions_raw(self) -> List[Dict]:
        self._init_sqlite_if_needed()
        results: List[Dict] = []
        try:
            self.logger.debug("Reading positions raw...")
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM positions")
            rows = cursor.fetchall()
            for row in rows:
                results.append(dict(row))
            self.logger.debug(f"Fetched {len(results)} raw positions.")
            return results
        except Exception as ex:
            self.logger.error(f"Error reading raw positions: {ex}", exc_info=True)
            return []

    def record_positions_totals_snapshot(self, totals: dict):
        try:
            self._init_sqlite_if_needed()
            snapshot_id = str(uuid4())
            snapshot_time = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO positions_totals_history (
                    id, snapshot_time, total_size, total_value, total_collateral,
                    avg_leverage, avg_travel_percent, avg_heat_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                snapshot_time,
                totals.get("total_size", 0.0),
                totals.get("total_value", 0.0),
                totals.get("total_collateral", 0.0),
                totals.get("avg_leverage", 0.0),
                totals.get("avg_travel_percent", 0.0),
                totals.get("avg_heat_index", 0.0)
            ))
            self.conn.commit()
            self.logger.debug(f"Recorded positions totals snapshot with ID={snapshot_id}.")
        except Exception as e:
            self.logger.exception(f"Error recording positions totals snapshot: {e}")
            raise

    def update_position_size(self, position_id: str, new_size: float):
        try:
            self._init_sqlite_if_needed()
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE positions
                   SET size=?
                 WHERE id=?
            """, (new_size, position_id))
            self.conn.commit()
            self.logger.debug(f"Updated position {position_id} => size={new_size}")
        except sqlite3.Error as ex:
            self.logger.error(f"DB error in update_position_size: {ex}", exc_info=True)
            raise
        except Exception as ex:
            self.logger.exception(f"Error update_position_size: {ex}")
            raise

    def create_alert_instance(self, alert_obj) -> None:
        """
        Creates an alert in the database from an alert object.
        The alert object is expected to halert_manager.pyave a `to_dict()` method
        that returns a dictionary compatible with the alerts table.
        """
        try:
            alert_dict = alert_obj.to_dict()
            # Ensure an ID is present
            if not alert_dict.get("id"):
                alert_dict["id"] = str(uuid4())
            self.create_alert(alert_dict)
        except Exception as e:
            self.logger.exception(f"Error creating alert instance: {e}")
            raise


    # ----------------------------------------------------------------
    # PORTFOLIO ENTRIES CRUD
    # ----------------------------------------------------------------

    def add_portfolio_entry(self, entry: dict):
        self._init_sqlite_if_needed()
        if "id" not in entry:
            entry["id"] = str(uuid4())
        if "snapshot_time" not in entry:
            entry["snapshot_time"] = datetime.now().isoformat()
        if "total_value" not in entry:
            raise ValueError("total_value is required for a portfolio entry")
        cursor = self.conn.cursor()
        cursor.execute("""
             INSERT INTO portfolio_entries (id, snapshot_time, total_value)
             VALUES (:id, :snapshot_time, :total_value)
         """, entry)
        self.conn.commit()
        self.logger.debug(f"Inserted portfolio entry with ID={entry['id']}")

    def get_portfolio_entries(self) -> List[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
             SELECT * FROM portfolio_entries
             ORDER BY snapshot_time ASC
         """)
        rows = cursor.fetchall()
        entries = [dict(row) for row in rows]
        self.logger.debug(f"Retrieved {len(entries)} portfolio entries.")
        return entries

    def get_portfolio_entry_by_id(self, entry_id: str) -> Optional[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
             SELECT * FROM portfolio_entries
             WHERE id = ?
             LIMIT 1
         """, (entry_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_portfolio_entry(self, entry_id: str, updated_fields: dict):
        self._init_sqlite_if_needed()
        set_clause = ", ".join([f"{key}=:{key}" for key in updated_fields.keys()])
        updated_fields["id"] = entry_id
        cursor = self.conn.cursor()
        cursor.execute(f"""
             UPDATE portfolio_entries
                SET {set_clause}
              WHERE id=:id
         """, updated_fields)
        self.conn.commit()
        self.logger.debug(f"Updated portfolio entry {entry_id} with fields {updated_fields}")

    def delete_portfolio_entry(self, entry_id: str):
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
             DELETE FROM portfolio_entries
             WHERE id = ?
         """, (entry_id,))
        self.conn.commit()
        self.logger.debug(f"Deleted portfolio entry with ID={entry_id}")

    def get_wallet_by_name(self, wallet_name: str) -> Optional[dict]:
        self._init_sqlite_if_needed()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name,
                   public_address,
                   private_address,
                   image_path,
                   balance
              FROM wallets
             WHERE name=?
             LIMIT 1
        """, (wallet_name,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "name": row["name"],
            "public_address": row["public_address"],
            "private_address": row["private_address"],
            "image_path": row["image_path"],
            "balance": row["balance"]
        }



    def clear_alerts(self):
        """
        Delete all rows from the alerts table.
        """
        self._init_sqlite_if_needed()
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM alerts")
            self.conn.commit()
            cursor.close()
            self.logger.info("Cleared all alerts from database.")
        except Exception as e:
            self.logger.error(f"Error clearing alerts: {e}", exc_info=True)
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            self.logger.debug("Database connection closed.")

from data.data_locker import DataLocker

def main():
    print("🛠 Initializing database...")
    locker = DataLocker()  # Will auto-call _initialize_database()
    print("✅ Initialization complete.")

if __name__ == "__main__":
    main()
