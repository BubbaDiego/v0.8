import sqlite3
import os

DB_PATH = r"C:\v0.8\data\mother_brain.db"

def ensure_theme_tables(db_path):
    if not os.path.exists(db_path):
        print(f"❌ DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- Create theme_profiles table if missing ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS theme_profiles (
            name TEXT PRIMARY KEY,
            config TEXT
        )
    """)
    print("✅ Table ensured: theme_profiles")

    # --- Add theme_active_profile column if missing ---
    cursor.execute("PRAGMA table_info(system_vars);")
    columns = [row[1] for row in cursor.fetchall()]
    if "theme_active_profile" not in columns:
        cursor.execute("ALTER TABLE system_vars ADD COLUMN theme_active_profile TEXT")
        print("✅ Column added: system_vars.theme_active_profile")
    else:
        print("✅ Column already exists: system_vars.theme_active_profile")

    conn.commit()
    conn.close()
    print("🎨 Theme migration complete.")

if __name__ == "__main__":
    ensure_theme_tables(DB_PATH)
