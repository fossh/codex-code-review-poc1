#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Accept every needed configuration via CLI arguments; do not read environment variables directly.
- Delegate AWS, SSH, Git, and GitHub work to helper scripts under .github/codex using `uv run`.
- Keep the review loop idempotent and log progress with a `[codex-review]` prefix.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import textwrap
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

agents_path = tmp_dir / "AGENTS.md"
prompt_path = tmp_dir / "codex_prompt.txt"
review_out = tmp_dir / "codex_review.txt"
payload_path = tmp_dir / "review_payload.json"
validation_error_path = tmp_dir / "validation_error.txt"

remote_workdir = f"{REMOTE_BASE_DIR}/{args.session_name}"
prompt_remote = f"{remote_workdir}/.github/tmp/codex_prompt.txt"

pr_number = (args.pr_number or "").strip()
existing_instance_id = (args.existing_instance_id or "").strip()
aws_session_token = (args.aws_session_token or "").strip()

aws_auth_args = [
    "--aws-access-key-id",
    args.aws_access_key_id,
    "--aws-secret-access-key",
    args.aws_secret_access_key,
]
if aws_session_token:
    aws_auth_args += ["--aws-session-token", aws_session_token]

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
    )

    if existing_instance_id:
        instance_id = existing_instance_id
        log(f"Using existing instance: {instance_id}")
        run_tool(
            "aws_wait_instance.py",
            ["--instance-id", instance_id, *aws_auth_args],
        )
    else:
        log(f"Launching instance in ap-south-1 with AMI {args.ami_id}")
        aws_run_args = [
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
            *aws_auth_args,
        ]
        launch_result = run_tool(
            "aws_run_instance.py",
            aws_run_args,
            capture_output=True,
            check=True,
        )
        instance_id = launch_result.stdout.strip()
        if not instance_id:
            raise SystemExit("Failed to launch EC2 instance.")
        should_terminate = True
        run_tool("aws_wait_instance.py", ["--instance-id", instance_id, *aws_auth_args])

    public_ip = ""
    for _ in range(30):
        ip_op = run_tool(
            "aws_get_public_ip.py",
            ["--instance-id", instance_id, *aws_auth_args],
            capture_output=True,
            check=False,
        )
        if ip_op.returncode == 0:
            candidate = ip_op.stdout.strip()
            if candidate and candidate != "None":
                public_ip = candidate
                break
        time.sleep(5)

    if not public_ip:
        raise SystemExit(f"Failed to obtain public IP for {instance_id}")

    ssh_conn_args[1] = public_ip

    log(f"Waiting for ssh on {public_ip}")
    run_tool(
        "ssh_wait.py",
        ["--host", public_ip, "--user", SSH_USER, "--identity-file", str(ssh_key_path)],
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
    )

    run_tool("write_agents.py", ["--output-path", str(agents_path)])
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
    )

    clone_script = tmp_dir / "remote_clone.sh"
    clone_script.write_text(textwrap.dedent("""
        set -euo pipefail
        cd "$REMOTE_WORKDIR"

        python3 - <<'PY'
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
        PY

        source .github/tmp/pr_meta.sh

        TOKEN="$(cat .github/tmp/github_token.txt)"
        CLONE_URL="https://x-access-token:${TOKEN}@github.com/${OWNER_REPO}.git"

        if [[ ! -d repo/.git ]]; then
            rm -rf repo
            git clone "$CLONE_URL" repo
        fi

        cd repo
        git remote set-url origin "$CLONE_URL"
        git fetch origin "$BASE_REF" --depth 5
        if [[ -n "$PR_NUMBER" ]]; then
            git fetch origin "pull/${PR_NUMBER}/head:pr-head" --depth 5
            git checkout pr-head
        elif [[ -n "$HEAD_SHA" ]]; then
            git checkout "$HEAD_SHA"
        fi
        git remote set-url origin "https://github.com/${OWNER_REPO}.git"
    """), encoding="utf-8")

    run_tool(
        "ssh_exec.py",
        [
            "--host",
            public_ip,
            "--user",
            SSH_USER,
            "--identity-file",
            str(ssh_key_path),
            "--script-path",
            str(clone_script),
            "--env",
            f"REMOTE_WORKDIR={remote_workdir}",
        ],
    )

    codex_script = tmp_dir / "remote_codex.sh"
    codex_script.write_text(textwrap.dedent("""
        set -euo pipefail
        source "$REMOTE_WORKDIR/.github/tmp/pr_meta.sh"
        cd "$REMOTE_WORKDIR/repo"

        export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
        CODEX_BIN="$(command -v codex || true)"
        if [[ -z "$CODEX_BIN" && -x /usr/local/bin/codex ]]; then
            CODEX_BIN="/usr/local/bin/codex"
        fi
        if [[ -z "$CODEX_BIN" ]]; then
            echo "codex not found in PATH" >&2
            exit 1
        fi

        timeout 10m "$CODEX_BIN" exec -m gpt-5.2-codex \
            --config model_reasoning_effort=high \
            --dangerously-bypass-approvals-and-sandbox \
            --skip-git-repo-check \
            < "$REMOTE_WORKDIR/.github/tmp/codex_prompt.txt"
    """), encoding="utf-8")

    validation_error = ""
    for attempt in range(1, args.max_attempts + 1):
        if review_out.exists():
            review_out.unlink()
        if validation_error_path.exists():
            validation_error_path.unlink()

        prompt_args = ["--output-path", str(prompt_path)]
        if validation_error:
            prompt_args += ["--validation-feedback", validation_error]
        run_tool("write_prompt.py", prompt_args)

        run_tool(
            "scp_put.py",
            [
                "--source",
                str(prompt_path),
                "--destination",
                prompt_remote,
                "--host",
                public_ip,
                "--user",
                SSH_USER,
                "--identity-file",
                str(ssh_key_path),
            ],
        )

        log(f"Codex attempt {attempt}")
        codex_result = run_tool(
            "ssh_exec.py",
            [
                "--host",
                public_ip,
                "--user",
                SSH_USER,
                "--identity-file",
                str(ssh_key_path),
                "--script-path",
                str(codex_script),
                "--env",
                f"REMOTE_WORKDIR={remote_workdir}",
                "--capture-path",
                str(review_out),
            ],
            check=False,
        )

        if codex_result.returncode != 0:
            validation_error = f"Codex review failed with status {codex_result.returncode}."
            continue

        if not review_out.exists() or not review_out.read_text(encoding="utf-8").strip():
            validation_error = "Codex produced no output."
            continue

        prepare_result = run_tool(
            "prepare_payload.py",
            [
                "--context-path",
                str(context_path),
                "--token-path",
                str(token_path),
                "--review-path",
                str(review_out),
                "--payload-path",
                str(payload_path),
                "--validation-error-path",
                str(validation_error_path),
            ],
            check=False,
        )

        if prepare_result.returncode == 0 and payload_path.exists():
            break

        if validation_error_path.exists():
            validation_error = validation_error_path.read_text(encoding="utf-8").strip()
        else:
            validation_error = "Review output failed validation."

    if not payload_path.exists():
        raise SystemExit("Codex output failed validation; not posting a review.")

    run_tool(
        "post_review.py",
        [
            "--context-path",
            str(context_path),
            "--token-path",
            str(token_path),
            "--payload-path",
            str(payload_path),
        ],
    )
    log("Review posted successfully")
finally:
    if should_terminate and instance_id:
        log(f"Terminating instance: {instance_id}")
        run_tool(
            "aws_terminate_instance.py",
            ["--instance-id", instance_id, *aws_auth_args],
            check=False,
        )
