"""
Upload AGENTS.md to remote host.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key, repo_root from DB
- Upload AGENTS.md via SCP
"""

import sqlite3, subprocess, tempfile, os
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path (hardcoded for all scripts)
# ---------------------------------------------------------------------------

db_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"

# ---------------------------------------------------------------------------
# Read config from DB
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key IN ('public_ip', 'ssh_private_key', 'repo_root')")
config = dict(cursor.fetchall())
conn.close()

# ---------------------------------------------------------------------------
# Write key to temp file
# ---------------------------------------------------------------------------

key_fd, key_path = tempfile.mkstemp()
os.write(key_fd, config["ssh_private_key"].encode())
os.close(key_fd)
os.chmod(key_path, 0o600)

# ---------------------------------------------------------------------------
# Upload AGENTS.md
# ---------------------------------------------------------------------------

local_path = config["repo_root"] + "/AGENTS.md"
remote_path = f"ubuntu@{config['public_ip']}:/home/ubuntu/repo/"

print(f"Uploading AGENTS.md to {config['public_ip']}...")
subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-i", key_path, local_path, remote_path], check=True)

os.unlink(key_path)
print("AGENTS.md uploaded")
