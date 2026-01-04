"""
Power off EC2 instance via SSH.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key from DB
- Execute poweroff command via SSH
"""

import sqlite3, subprocess, tempfile, os, sys
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path from command line: --db <path>
# ---------------------------------------------------------------------------

db_path = Path(sys.argv[2])

# ---------------------------------------------------------------------------
# Read config from DB
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key IN ('public_ip', 'ssh_private_key')")
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
# Power off instance
# ---------------------------------------------------------------------------

print(f"Powering off {config['public_ip']}...")
subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-i", key_path,
     f"ubuntu@{config['public_ip']}", "sudo poweroff"],
    check=False  # poweroff may disconnect before returning
)

os.unlink(key_path)
print("Poweroff command sent")
