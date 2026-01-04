"""
Run pipeline scripts in order.

MUST HAVE REQUIREMENTS:
- Execute list of scripts sequentially using subprocess
- Pass --db argument to each script
- Order: aws_launch_spot → ssh_wait → write_agents → write_prompt → rsync → codex
"""

import subprocess, sys

# ---------------------------------------------------------------------------
# Paths (relative, script runs from .github/codex/)
# ---------------------------------------------------------------------------

db_path = "db.sqlite3"

# ---------------------------------------------------------------------------
# Scripts to run in order (matches prod_flow.d2)
# ---------------------------------------------------------------------------

scripts = [
    "002_aws_launch_spot.py",
    "003_ssh_wait.py",
    "004_write_agents.py",
    "005_write_prompt.py",
    "006_rsync_to_ec2.py",
    "007_ssh_run_codex.py",
]

# ---------------------------------------------------------------------------
# Run each script with --db argument
# ---------------------------------------------------------------------------

for script in scripts:
    print(f"=== Running {script} ===")
    subprocess.run([sys.executable, script, "--db", db_path], check=True)

print("=== Pipeline complete ===")

# E2E test change - can be removed
