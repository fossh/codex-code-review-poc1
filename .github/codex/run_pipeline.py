"""
Run pipeline scripts in order.

MUST HAVE REQUIREMENTS:
- Execute list of scripts sequentially using subprocess
"""

import subprocess, sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Scripts to run in order
# ---------------------------------------------------------------------------

scripts = [
    "001_init_db.py",
    "002_write_agents.py",
    "003_write_prompt.py",
    "aws_launch_spot.py",
    "ssh_wait.py",
    "ssh_clone_repo.py",
    "scp_upload_agents.py",
    "ssh_run_codex.py",
    "aws_terminate.py",
]

# ---------------------------------------------------------------------------
# Run each script
# ---------------------------------------------------------------------------

script_dir = Path(__file__).parent

for script in scripts:
    print(f"=== Running {script} ===")
    subprocess.run([sys.executable, str(script_dir / script)], check=True)

print("=== Pipeline complete ===")
