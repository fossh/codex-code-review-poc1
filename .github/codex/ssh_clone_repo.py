"""
Clone repo and checkout PR branch on remote host.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key, repo, pr_number from DB
- Clone repo via SSH
- Checkout PR branch
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

cursor.execute("SELECT key, value FROM config WHERE key IN ('public_ip', 'ssh_private_key', 'repo', 'pr_number')")
config = dict(cursor.fetchall())
conn.close()

# ---------------------------------------------------------------------------
# Write key to temp file
# ---------------------------------------------------------------------------

key_fd, key_path = tempfile.mkstemp()
os.write(key_fd, config["ssh_private_key"].encode())
os.close(key_fd)
os.chmod(key_path, 0o600)

ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-i", key_path, f"ubuntu@{config['public_ip']}"]

# ---------------------------------------------------------------------------
# Clone repo
# ---------------------------------------------------------------------------

print(f"Cloning {config['repo']}...")
subprocess.run(ssh_cmd + [f"git clone https://github.com/{config['repo']}.git /home/ubuntu/repo"], check=True)

# ---------------------------------------------------------------------------
# Checkout PR branch
# ---------------------------------------------------------------------------

print(f"Checking out PR #{config['pr_number']}...")
subprocess.run(ssh_cmd + [f"cd /home/ubuntu/repo && git fetch origin pull/{config['pr_number']}/head:pr && git checkout pr"], check=True)

os.unlink(key_path)
print("Repo cloned and PR checked out")
