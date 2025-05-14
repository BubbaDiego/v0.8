import sqlite3
import json
import os

DB_PATH = "mother_brain.db"  # 🔧 Change this to your actual DB path if needed
PROFILE_NAME = "comms_seed_profile"

COMMS_CONFIG = {
    "communication": {
        "providers": {
            "email": {
                "enabled": True,
                "smtp": {
                    "server": "smtp.gmail.com",
                    "port": 587,
                    "username": "bubba.diego@gmail.com",
                    "password": "pzix taan afbe igxb",
                    "default_recipient": "bubba.diego@gmail.com"
                }
            },
            "api_config": {
                "coingecko_api_enabled":    "ENABLE",
                "coinmarketcap_api_enabled":"ENABLE",
                "coinpaprika_api_enabled":  "ENABLE",
                "binance_api_enabled":      "DISABLE",
                "cryptocompare_api_enabled":"ENABLE",
                "nomics_api_enabled":       "ENABLE"
            },
            "sms": {
                "enabled": True,
                "carrier_gateway": "txt.att.net",
                "default_recipient": "6199804758"
            },
            "twilio": {
                "enabled": True,
                "account_sid": "ACb606788ada5dccbfeeebed0f440099b3",
                "auth_token": "4a44ade7492e8aac43cb05342f74c492",
                "flow_sid": "FW5b3bf49ee04af4d23a118b613bbc0df2",
                "default_to_phone": "+16199804758",
                "default_from_phone": "+18336913467"
            }
        }
    }
}


def run_seed():
    print("\n🔧 Connecting to DB:", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Ensure `theme_profiles` table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS theme_profiles (
            name TEXT PRIMARY KEY,
            config TEXT
        )
    """)

    # 2. Ensure `system_vars` table exists with id=1
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_vars (
            id INTEGER PRIMARY KEY,
            theme_active_profile TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO system_vars (id, theme_active_profile) VALUES (1, NULL)")

    # 3. Insert or update theme profile
    config_json = json.dumps(COMMS_CONFIG)
    cur.execute("""
        INSERT INTO theme_profiles (name, config)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET config = excluded.config
    """, (PROFILE_NAME, config_json))

    # 4. Set active profile
    cur.execute("""
        UPDATE system_vars SET theme_active_profile = ? WHERE id = 1
    """, (PROFILE_NAME,))

    conn.commit()
    conn.close()

    print("✅ Seed complete. Profile activated:", PROFILE_NAME)


if __name__ == "__main__":
    run_seed()
