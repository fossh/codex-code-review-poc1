"""
Download files from EC2 for local testing.

MUST HAVE REQUIREMENTS:
- Read ssh_private_key, public_ip, workdir from DB
- Download workdir from EC2
- Save to tmp/

Usage: uv run 008_rsync_from_ec2.py --db db.sqlite3
"""

import subprocess, tempfile, os, sys, sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative, script runs from .github/codex/)
# ---------------------------------------------------------------------------

db_path = Path(sys.argv[2])
local_dir = Path("tmp")
local_dir.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Read config from DB
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key IN ('public_ip', 'ssh_private_key', 'workdir')")
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
# Download workdir from EC2
# ---------------------------------------------------------------------------

remote_host = f"ubuntu@{config['public_ip']}"
ssh_opts = ["-o", "StrictHostKeyChecking=no", "-i", key_path]

print(f"Downloading {config['workdir']} from {config['public_ip']}...")
subprocess.run(
    ["rsync", "-avz", "-e", f"ssh {' '.join(ssh_opts)}",
     f"{remote_host}:{config['workdir']}/", str(local_dir) + "/"],
    check=True
)

os.unlink(key_path)
print(f"Downloaded to: {local_dir}")
