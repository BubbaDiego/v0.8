import pytest
import sqlite3
from alerts.alert_controller import AlertController
from data.data_locker import DataLocker
from data.models import AlertType, Status

@pytest.fixture
def setup_test_db(tmp_path):
    # Create a temporary file-based SQLite database
    db_file = tmp_path / "test_alerts.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # Create minimal positions and alerts tables
    cursor.execute("""
    CREATE TABLE positions (
        id TEXT PRIMARY KEY,
        asset_type TEXT,
        position_type TEXT,
        alert_reference_id TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE alerts (
        id TEXT PRIMARY KEY,
        created_at TEXT,
        alert_type TEXT,
        alert_class TEXT,
        asset_type TEXT,
        trigger_value REAL,
        condition TEXT,
        notification_type TEXT,
        level TEXT,
        last_triggered TEXT,
        status TEXT,
        frequency INTEGER,
        counter INTEGER,
        liquidation_distance REAL,
        travel_percent REAL,
        liquidation_price REAL,
        notes TEXT,
        description TEXT,
        position_reference_id TEXT,
        evaluated_value REAL,
        position_type TEXT
    )
    """)
    conn.commit()
    yield db_file  # Return path to DB
    conn.close()

def test_alert_creation_integration(setup_test_db):
    # Patch DataLocker to use temp DB
    db_path = str(setup_test_db)
    DataLocker._instances = {}  # Clear singleton
    locker = DataLocker.get_instance(db_path)
    controller = AlertController(db_path)

    # Insert fake positions
    conn = locker.get_db_connection()
    cursor = conn.cursor()
    fake_positions = [
        ("pos1", "BTC", "LONG", None),
        ("pos2", "ETH", "LONG", None),
        ("pos3", "SOL", "SHORT", None),
    ]
    cursor.executemany("INSERT INTO positions (id, asset_type, position_type, alert_reference_id) VALUES (?, ?, ?, ?)", fake_positions)
    conn.commit()

    # Override _load_limits with custom config
    controller._load_limits = lambda: {
        "travel_percent_liquid_ranges": {"enabled": True, "low": -20.0},
        "profit_ranges": {"enabled": True, "low": 50.0},
        "heat_index_ranges": {"enabled": True, "low": 7.0},
    }

    # Create alerts
    created_alerts = controller.create_all_position_alerts()

    # Now verify alerts were inserted
    cursor.execute("SELECT alert_type, trigger_value FROM alerts")
    rows = cursor.fetchall()

    assert len(rows) == 9  # 3 positions × 3 alert types = 9 alerts total

    types_seen = [r[0] for r in rows]
    triggers_seen = [r[1] for r in rows]

    # Verify correct types were inserted
    assert AlertType.TRAVEL_PERCENT_LIQUID.value in types_seen
    assert AlertType.PROFIT.value in types_seen
    assert AlertType.HEAT_INDEX.value in types_seen

    # Verify correct trigger values
    assert -20.0 in triggers_seen
    assert 50.0 in triggers_seen
    assert 7.0 in triggers_seen
