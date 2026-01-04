"""
Rsync AGENTS.md and prompt.txt to EC2 workdir.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key, workdir from DB
- Create remote workdir via SSH
- Upload AGENTS.md and prompt.txt to workdir
"""

import sqlite3, subprocess, tempfile, os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

db_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"
local_tmp = Path(__file__).parent.parent / "tmp"

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

ssh_opts = ["-o", "StrictHostKeyChecking=no", "-i", key_path]
remote_host = f"ubuntu@{config['public_ip']}"

# ---------------------------------------------------------------------------
# Create remote workdir
# ---------------------------------------------------------------------------

print(f"Creating remote workdir: {config['workdir']}")
subprocess.run(["ssh"] + ssh_opts + [remote_host, f"mkdir -p {config['workdir']}"], check=True)

# ---------------------------------------------------------------------------
# Rsync files to EC2
# ---------------------------------------------------------------------------

files_to_sync = [
    local_tmp / "AGENTS.md",
    local_tmp / "prompt.txt",
]

print(f"Syncing files to {config['public_ip']}:{config['workdir']}")
for local_file in files_to_sync:
    subprocess.run(
        ["rsync", "-avz", "-e", f"ssh {' '.join(ssh_opts)}",
         str(local_file), f"{remote_host}:{config['workdir']}/"],
        check=True
    )

os.unlink(key_path)
print("Rsync complete")
