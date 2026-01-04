"""
Download files from EC2 for local testing.

MUST HAVE REQUIREMENTS:
- Read ssh_private_key from .env (CODEX_SSH_PRIVATE_KEY)
- Download workdir from EC2
- Save to .github/tmp/

Usage: uv run rsync_from_ec2.py <public_ip> <repo_name> <pr_number>
"""

import subprocess, tempfile, os, sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------

public_ip = sys.argv[1]
repo_name = sys.argv[2]
pr_number = sys.argv[3]

# ---------------------------------------------------------------------------
# Load .env for SSH key
# ---------------------------------------------------------------------------

env_path = Path(__file__).parent.parent.parent / ".env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key, val = line.split("=", 1)
        os.environ[key.strip()] = val.strip().strip("'\"")

ssh_private_key = os.environ["CODEX_SSH_PRIVATE_KEY"]

# ---------------------------------------------------------------------------
# Write key to temp file
# ---------------------------------------------------------------------------

key_fd, key_path = tempfile.mkstemp()
os.write(key_fd, ssh_private_key.encode())
os.close(key_fd)
os.chmod(key_path, 0o600)

# ---------------------------------------------------------------------------
# Download workdir from EC2
# ---------------------------------------------------------------------------

workdir = f"/home/ubuntu/{repo_name}/{pr_number}/"
local_dir = Path(__file__).parent.parent / "tmp"
local_dir.mkdir(parents=True, exist_ok=True)

remote_host = f"ubuntu@{public_ip}"
ssh_opts = ["-o", "StrictHostKeyChecking=no", "-i", key_path]

print(f"Downloading {workdir} from {public_ip}...")
subprocess.run(
    ["rsync", "-avz", "-e", f"ssh {' '.join(ssh_opts)}",
     f"{remote_host}:{workdir}", str(local_dir) + "/"],
    check=True
)

os.unlink(key_path)
print(f"Downloaded to: {local_dir}")
