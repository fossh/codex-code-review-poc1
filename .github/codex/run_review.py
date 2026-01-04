#!/usr/bin/env python3
"""Run the Codex PR review flow end-to-end."""
from __future__ import annotations

import argparse
import shlex
import subprocess
import time
from pathlib import Path


REMOTE_BASE_DIR = "/home/ubuntu/codex-work"
SSH_USER = "ubuntu"
MAX_ATTEMPTS_DEFAULT = 2


def run_tool(script: str, args: list[str], capture_output: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["uv", "run", f".github/codex/{script}", *args]
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=True)


def log(message: str) -> None:
    print(f"[codex-review] {message}")


def ensure_file(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing required file: {path}")


parser = argparse.ArgumentParser()
parser.add_argument("--tmp-dir", required=True)
parser.add_argument("--context-path", required=True)
parser.add_argument("--token-path", required=True)
parser.add_argument("--auth-path", required=True)
parser.add_argument("--ssh-key-path", required=True)
parser.add_argument("--pr-number")
parser.add_argument("--session-name", required=True)
parser.add_argument("--instance-name", required=True)
parser.add_argument("--ami-id", required=True)
parser.add_argument("--instance-type", required=True)
parser.add_argument("--subnet-id", required=True)
parser.add_argument("--security-group-ids", required=True)
parser.add_argument("--key-name", required=True)
parser.add_argument("--aws-access-key-id", required=True)
parser.add_argument("--aws-secret-access-key", required=True)
parser.add_argument("--aws-session-token")
parser.add_argument("--existing-instance-id")
parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS_DEFAULT)
args = parser.parse_args()


tmp_dir = Path(args.tmp_dir)
tmp_dir.mkdir(parents=True, exist_ok=True)

context_path = Path(args.context_path)
token_path = Path(args.token_path)
auth_path = Path(args.auth_path)
ssh_key_path = Path(args.ssh_key_path)

ensure_file(context_path)
ensure_file(token_path)
ensure_file(auth_path)
ensure_file(ssh_key_path)
ssh_key_path.chmod(0o600)

pr_number = (args.pr_number or "").strip()
existing_instance_id = (args.existing_instance_id or "").strip()
aws_session_token = (args.aws_session_token or "").strip() or None

agents_path = tmp_dir / "AGENTS.md"
prompt_path = tmp_dir / "codex_prompt.txt"
review_out = tmp_dir / "codex_review.txt"
payload_path = tmp_dir / "review_payload.json"
validation_error_path = tmp_dir / "validation_error.txt"

remote_workdir = f"{REMOTE_BASE_DIR}/{args.session_name}"
prompt_remote = f"{remote_workdir}/.github/tmp/codex_prompt.txt"

instance_id = ""
should_terminate = False

try:
    run_tool(
        "resolve_pr_context.py",
        [
            "--context-path",
            str(context_path),
            "--token-path",
            str(token_path),
            "--pr-number",
            pr_number,
        ],
        check=True,
    )

    if existing_instance_id:
        instance_id = existing_instance_id
        log(f"Using existing instance: {instance_id}")
        run_tool(
            "aws_wait_instance.py",
            [
                "--instance-id",
                instance_id,
                "--aws-access-key-id",
                args.aws_access_key_id,
                "--aws-secret-access-key",
                args.aws_secret_access_key,
                "--aws-session-token",
                aws_session_token or "",
            ],
            check=True,
        )
    else:
        log(f"Launching instance in ap-south-1 with AMI {args.ami_id}")
        launch_result = run_tool(
            "aws_run_instance.py",
            [
                "--ami-id",
                args.ami_id,
                "--instance-type",
                args.instance_type,
                "--subnet-id",
                args.subnet_id,
                "--security-group-ids",
                args.security_group_ids,
                "--key-name",
                args.key_name,
                "--session-name",
                args.session_name,
                "--instance-name",
                args.instance_name,
                "--aws-access-key-id",
                args.aws_access_key_id,
                "--aws-secret-access-key",
                args.aws_secret_access_key,
                "--aws-session-token",
                aws_session_token or "",
            ],
            capture_output=True,
            check=True,
        )
        instance_id = launch_result.stdout.strip()
        should_terminate = True
        run_tool(
            "aws_wait_instance.py",
            [
                "--instance-id",
                instance_id,
                "--aws-access-key-id",
                args.aws_access_key_id,
                "--aws-secret-access-key",
                args.aws_secret_access_key,
                "--aws-session-token",
                aws_session_token or "",
            ],
            check=True,
        )

    public_ip = ""
    for _ in range(30):
        ip_result = run_tool(
            "aws_get_public_ip.py",
            [
                "--instance-id",
                instance_id,
                "--aws-access-key-id",
                args.aws_access_key_id,
                "--aws-secret-access-key",
                args.aws_secret_access_key,
                "--aws-session-token",
                aws_session_token or "",
            ],
            capture_output=True,
            check=False,
        )
        if ip_result.returncode == 0:
            public_ip = ip_result.stdout.strip()
            if public_ip and public_ip != "None":
                break
        time.sleep(5)

    if not public_ip or public_ip == "None":
        raise SystemExit(f"Failed to obtain public IP for {instance_id}")

    log(f"Waiting for ssh on {public_ip}")
    run_tool(
        "ssh_wait.py",
        [
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
        ],
        check=True,
    )

    mkdir_cmd = f"mkdir -p ~/.codex {shlex.quote(remote_workdir)}/.github/tmp"
    run_tool(
        "ssh_exec.py",
        [
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
            "--command",
            mkdir_cmd,
        ],
        check=True,
    )

    run_tool(
        "scp_put.py",
        [
            "--source",
            str(auth_path),
            "--destination",
            "~/.codex/auth.json",
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
        ],
        check=True,
    )

    run_tool(
        "scp_put.py",
        [
            "--source",
            str(context_path),
            "--destination",
            f"{remote_workdir}/.github/tmp/github_context.json",
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
        ],
        check=True,
    )

    run_tool(
        "scp_put.py",
        [
            "--source",
            str(token_path),
            "--destination",
            f"{remote_workdir}/.github/tmp/github_token.txt",
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
        ],
        check=True,
    )

    run_tool("write_agents.py", ["--output-path", str(agents_path)], check=True)
    run_tool(
        "scp_put.py",
        [
            "--source",
            str(agents_path),
            "--destination",
            f"{remote_workdir}/AGENTS.md",
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
        ],
        check=True,
    )

    clone_script = tmp_dir / "remote_clone.sh"
    clone_script.write_text(
        """set -euo pipefail
cd "$REMOTE_WORKDIR"

python3 - <<'PY' > .github/tmp/pr_meta.sh
import json
from pathlib import Path

ctx = json.loads(Path(".github/tmp/github_context.json").read_text())
event = ctx.get("event") or {}
pr = event.get("pull_request") or {}

owner_repo = ctx.get("repository") or ""
if not owner_repo:
    owner = ctx.get("repository_owner") or event.get("repository", {}).get("owner", {}).get("login", "")
    name = event.get("repository", {}).get("name", "")
    owner_repo = f"{owner}/{name}" if owner and name else ""

pr_number = pr.get("number") or event.get("number")
base_ref = (pr.get("base") or {}).get("ref") or "dev"
head_sha = (pr.get("head") or {}).get("sha") or ""

def esc(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')

print(f'OWNER_REPO="{esc(owner_repo)}"')
print(f'PR_NUMBER="{esc(pr_number or "")}"')
print(f'BASE_REF="{esc(base_ref)}"')
print(f'HEAD_SHA="{esc(head_sha)}"')
