"""
Run pipeline scripts in order.

MUST HAVE REQUIREMENTS:
- Execute list of scripts sequentially using subprocess
- Order: aws_launch_spot → ssh_wait → write_agents → write_prompt → rsync → codex → poweroff
"""

import subprocess, sys
from pathlib import Path

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
# Run each script
# ---------------------------------------------------------------------------

script_dir = Path(__file__).parent

for script in scripts:
    print(f"=== Running {script} ===")
    subprocess.run([sys.executable, str(script_dir / script)], check=True)

print("=== Pipeline complete ===")
