"""
Run debug pipeline scripts in order.

MUST HAVE REQUIREMENTS:
- Execute list of scripts sequentially using subprocess
- Order: aws_launch_spot → ssh_wait → write_agents → write_prompt → rsync → sleep 6h
- Same as prod but sleep instead of codex
"""

import subprocess, sys, time
from pathlib import Path

# ---------------------------------------------------------------------------
# Scripts to run in order (matches debug_flow.d2)
# ---------------------------------------------------------------------------

scripts = [
    "aws_launch_spot.py",
    "ssh_wait.py",
    "002_write_agents.py",
    "003_write_prompt.py",
    "rsync_to_ec2.py",
]

# ---------------------------------------------------------------------------
# Run each script
# ---------------------------------------------------------------------------

script_dir = Path(__file__).parent

for script in scripts:
    print(f"=== Running {script} ===")
    subprocess.run([sys.executable, str(script_dir / script)], check=True)

# ---------------------------------------------------------------------------
# Get IP from DB for user to copy
# ---------------------------------------------------------------------------

import sqlite3
db_path = script_dir.parent / "tmp" / "pipeline.db"
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT value FROM config WHERE key = 'public_ip'")
public_ip = cursor.fetchone()[0]
cursor = conn.execute("SELECT value FROM config WHERE key = 'repo_name'")
repo_name = cursor.fetchone()[0]
cursor = conn.execute("SELECT value FROM config WHERE key = 'pr_number'")
pr_number = cursor.fetchone()[0]
conn.close()

# ---------------------------------------------------------------------------
# Sleep 6 hours to keep GitHub token active
# ---------------------------------------------------------------------------

print("=== Sleeping 6 hours (token active for local testing) ===")
print(f"EC2 IP: {public_ip}")
print(f"Download with: uv run .github/codex/rsync_from_ec2.py {public_ip} {repo_name} {pr_number}")
time.sleep(21600)

print("=== Debug pipeline complete ===")
