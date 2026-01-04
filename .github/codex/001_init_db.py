"""
Initialize pipeline database from environment variables.

MUST HAVE REQUIREMENTS:
- Create DB at .github/tmp/pipeline.db
- Read GITHUB_CONTEXT, GITHUB_TOKEN, CODEX_CONFIG, PR_NUMBER from env
- Insert all config into DB
"""

import sqlite3, json, os
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path (hardcoded for all scripts)
# ---------------------------------------------------------------------------

db_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Read from environment
# ---------------------------------------------------------------------------

github_context = json.loads(os.environ["GITHUB_CONTEXT"])
github_token = os.environ["GITHUB_TOKEN"]
codex_config = json.loads(os.environ["CODEX_CONFIG"])
pr_number = os.environ["PR_NUMBER"]

# ---------------------------------------------------------------------------
# Create DB and insert config
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY,
        key TEXT UNIQUE NOT NULL,
        value TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS dumps (
        category TEXT,
        name TEXT,
        content TEXT
    )
""")

cursor.execute("INSERT INTO dumps VALUES ('json', 'github', ?)", (json.dumps(github_context),))
cursor.execute("INSERT INTO dumps VALUES ('secret', 'github_token', ?)", (github_token,))

# ---------------------------------------------------------------------------
# Compute workdir: /home/ubuntu/{repo_name}/{pr_number}/
# ---------------------------------------------------------------------------

repo_name = github_context["repository"].split("/")[1]
workdir = f"/home/ubuntu/{repo_name}/{pr_number}"

config_values = [
    ("workdir", workdir),
    ("pr_number", pr_number),
    ("repo", github_context["repository"]),
    ("repo_name", repo_name),
    ("ami_id", codex_config["ami_id"]),
    ("instance_type", codex_config["instance_type"]),
    ("key_name", codex_config["key_name"]),
    ("security_group_id", codex_config["security_group_id"]),
    ("region", codex_config["region"]),
    ("ssh_private_key", codex_config["ssh_private_key"]),
    ("aws_access_key_id", codex_config["aws_access_key_id"]),
    ("aws_secret_access_key", codex_config["aws_secret_access_key"]),
]

cursor.executemany("INSERT INTO config (key, value) VALUES (?, ?)", config_values)
conn.commit()
conn.close()

print(f"DB initialized at {db_path}")
