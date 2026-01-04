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
    "aws_launch_spot.py",
    "ssh_wait.py",
    "002_write_agents.py",
    "003_write_prompt.py",
    "rsync_to_ec2.py",
    "ssh_run_codex.py",
]

# ---------------------------------------------------------------------------
# Run each script
# ---------------------------------------------------------------------------

script_dir = Path(__file__).parent

for script in scripts:
    print(f"=== Running {script} ===")
    subprocess.run([sys.executable, str(script_dir / script)], check=True)

print("=== Pipeline complete ===")
