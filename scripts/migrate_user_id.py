import sqlite3
import os

db_path = r"c:\Users\Lenovo\Documents\Arpit-folder\projects\Tradegod\tradegod.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ["strategies", "positions", "signal_logs", "backtest_runs", "broker_accounts", "execution_logs"]
    for t in tables:
        try:
            cursor.execute(f"ALTER TABLE {t} ADD COLUMN user_id INTEGER DEFAULT 1;")
            print(f"Added user_id column to table {t}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower() or "exists" in str(e).lower():
                print(f"Column user_id already exists in {t}")
            else:
                print(f"Notice on {t}: {e}")
                
    conn.commit()
    conn.close()
    print("Migration complete!")
else:
    print("No database file found to migrate.")
