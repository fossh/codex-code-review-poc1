"""
Run codex on remote host.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key, workdir, prompt from DB
- Execute codex via SSH in workdir
"""

import sqlite3, subprocess, tempfile, os
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path
# ---------------------------------------------------------------------------

db_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"

# ---------------------------------------------------------------------------
# Read config from DB
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key IN ('public_ip', 'ssh_private_key', 'workdir', 'prompt')")
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
# Run codex in workdir
# ---------------------------------------------------------------------------

codex_cmd = f"cd {config['workdir']} && codex exec -m gpt-5.2-codex --config model_reasoning_effort=high --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check"

print(f"Running codex in {config['workdir']}...")
subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-i", key_path,
     f"ubuntu@{config['public_ip']}", codex_cmd],
    check=True
)

os.unlink(key_path)
print("Codex execution complete")
