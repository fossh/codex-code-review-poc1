"""
Wait for SSH to be ready on remote host.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key from DB
- Try SSH connection up to 30 times
- Exit 0 when ready, exit 1 on timeout
"""

import sqlite3, subprocess, time, tempfile, os
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
# Wait for SSH
# ---------------------------------------------------------------------------

print(f"Waiting for SSH on {config['public_ip']}...")

for i in range(30):
    result = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", "-i", key_path, f"ubuntu@{config['public_ip']}", "echo ready"],
        capture_output=True
    )
    if result.returncode == 0:
        print("SSH ready")
        os.unlink(key_path)
        exit(0)
    print(f"Attempt {i+1}/30...")
    time.sleep(10)

os.unlink(key_path)
print("SSH timeout")
exit(1)
