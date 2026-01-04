"""
Rsync AGENTS.md, prompt.txt, and auth.json to EC2.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key, workdir, codex_auth_json from DB
- Create remote workdir and ~/.codex/ via SSH
- Upload AGENTS.md and prompt.txt to workdir
- Upload auth.json to /home/ubuntu/.codex/auth.json
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

cursor.execute("SELECT key, value FROM config WHERE key IN ('public_ip', 'ssh_private_key', 'workdir', 'codex_auth_json')")
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
# Create remote directories
# ---------------------------------------------------------------------------

print(f"Creating remote workdir: {config['workdir']}")
subprocess.run(["ssh"] + ssh_opts + [remote_host, f"mkdir -p {config['workdir']} ~/.codex"], check=True)

# ---------------------------------------------------------------------------
# Write auth.json locally
# ---------------------------------------------------------------------------

auth_json_path = local_tmp / "auth.json"
with open(auth_json_path, "w") as f:
    f.write(config["codex_auth_json"])

# ---------------------------------------------------------------------------
# Rsync files to EC2
# ---------------------------------------------------------------------------

print(f"Syncing AGENTS.md and prompt.txt to {config['public_ip']}:{config['workdir']}")
for local_file in [local_tmp / "AGENTS.md", local_tmp / "prompt.txt"]:
    subprocess.run(
        ["rsync", "-avz", "-e", f"ssh {' '.join(ssh_opts)}",
         str(local_file), f"{remote_host}:{config['workdir']}/"],
        check=True
    )

# ---------------------------------------------------------------------------
# Rsync auth.json to ~/.codex/
# ---------------------------------------------------------------------------

print(f"Syncing auth.json to {config['public_ip']}:~/.codex/")
subprocess.run(
    ["rsync", "-avz", "-e", f"ssh {' '.join(ssh_opts)}",
     str(auth_json_path), f"{remote_host}:/home/ubuntu/.codex/auth.json"],
    check=True
)

os.unlink(key_path)
print("Rsync complete")
