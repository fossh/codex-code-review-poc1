"""
Initialize SQLite database with config table.

MUST HAVE REQUIREMENTS:
- Create config table with key (unique) and value columns
- Let SQLite handle primary key automatically
"""

import sqlite3, argparse

# ---------------------------------------------------------------------------
# Parse arguments and initialize database
# ---------------------------------------------------------------------------

args = argparse.ArgumentParser()
args.add_argument("--db-path", required=True)
db_path = args.parse_args().db_path

conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, value TEXT)")
conn.commit()
conn.close()

print(f"Database initialized: {db_path}")
