"""
Download pipeline.db from EC2 for local testing.

MUST HAVE REQUIREMENTS:
- Read public_ip, ssh_private_key from environment or .env
- Download pipeline.db from EC2 context path
- Save to .github/tmp/pipeline.db

Usage: uv run rsync_from_ec2.py <repo_name> <pr_number>
"""

import subprocess, tempfile, os, sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------

repo_name = sys.argv[1]
pr_number = sys.argv[2]

# ---------------------------------------------------------------------------
# Load .env for SSH credentials
# ---------------------------------------------------------------------------

env_path = Path(__file__).parent.parent.parent / ".env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key, val = line.split("=", 1)
        os.environ[key.strip()] = val.strip().strip("'\"")

public_ip = os.environ["CODEX_EC2_IP"]
ssh_private_key = os.environ["CODEX_SSH_PRIVATE_KEY"]

# ---------------------------------------------------------------------------
# Write key to temp file
# ---------------------------------------------------------------------------

key_fd, key_path = tempfile.mkstemp()
os.write(key_fd, ssh_private_key.encode())
os.close(key_fd)
os.chmod(key_path, 0o600)

# ---------------------------------------------------------------------------
# Download pipeline.db from EC2
# ---------------------------------------------------------------------------

ec2_path = f"/home/ubuntu/context/{repo_name}/{pr_number}/pipeline.db"
local_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"
local_path.parent.mkdir(parents=True, exist_ok=True)

remote_host = f"ubuntu@{public_ip}"
ssh_opts = ["-o", "StrictHostKeyChecking=no", "-i", key_path]

print(f"Downloading {ec2_path} from {public_ip}...")
subprocess.run(
    ["rsync", "-avz", "-e", f"ssh {' '.join(ssh_opts)}",
     f"{remote_host}:{ec2_path}", str(local_path)],
    check=True
)

os.unlink(key_path)
print(f"Downloaded to: {local_path}")
