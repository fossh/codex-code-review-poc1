"""
Run debug pipeline scripts in order.

MUST HAVE REQUIREMENTS:
- Execute list of scripts sequentially using subprocess
- Pass --db argument to each script
- Order: aws_launch_spot → ssh_wait → write_agents → write_prompt → rsync → sleep 6h
- Same as prod but sleep instead of codex
"""

import subprocess, sys, time, sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

script_dir = Path(__file__).parent
db_path = script_dir.parent / "tmp" / "pipeline.db"

# ---------------------------------------------------------------------------
# Scripts to run in order (matches debug_flow.d2)
# ---------------------------------------------------------------------------

scripts = [
    "002_aws_launch_spot.py",
    "003_ssh_wait.py",
    "004_write_agents.py",
    "005_write_prompt.py",
    "006_rsync_to_ec2.py",
]

# ---------------------------------------------------------------------------
# Run each script with --db argument
# ---------------------------------------------------------------------------

for script in scripts:
    print(f"=== Running {script} ===")
    subprocess.run([sys.executable, str(script_dir / script), "--db", str(db_path)], check=True)

# ---------------------------------------------------------------------------
# Get IP from DB for user to copy
# ---------------------------------------------------------------------------

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
print(f"Download with: uv run .github/codex/008_rsync_from_ec2.py {public_ip} {repo_name} {pr_number}")
time.sleep(21600)

print("=== Debug pipeline complete ===")
