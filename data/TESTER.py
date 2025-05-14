import sqlite3
import os

# ✅ DB Path
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "mother_brain.db"))

def patch_positions_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔍 Check if column already exists
    cursor.execute("PRAGMA table_info(positions);")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "profit" in existing_columns:
        print("✅ Column 'profit' already exists in positions table.")
    else:
        try:
            print("⚙️ Adding missing column 'profit' to positions table...")
            cursor.execute("ALTER TABLE positions ADD COLUMN profit REAL DEFAULT 0.0;")
            conn.commit()
            print("✅ Patch complete: 'profit' column added.")
        except Exception as e:
            print(f"❌ Failed to add column: {e}")

    conn.close()

if __name__ == "__main__":
    print(f"📁 Patching DB: {DB_PATH}")
    patch_positions_table()
