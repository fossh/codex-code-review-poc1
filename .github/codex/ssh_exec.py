#!/usr/bin/env python3
"""Run a command or script over SSH."""
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


def build_ssh_base(user: str, host: str, identity_file: str) -> list[str]:
    return [
        "ssh",
        "-i",
        identity_file,
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "ConnectTimeout=15",
        "-o",
        "LogLevel=ERROR",
        f"{user}@{host}",
    ]


def build_env_prefix(items: list[str]) -> str:
    pairs = []
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Invalid env item: {item}")
        key, value = item.split("=", 1)
        pairs.append(f"{key}={shlex.quote(value)}")
    return " ".join(pairs)


parser = argparse.ArgumentParser()
parser.add_argument("--host", required=True)
parser.add_argument("--user", required=True)
parser.add_argument("--identity-file", required=True)
parser.add_argument("--command")
parser.add_argument("--script-path")
parser.add_argument("--env", action="append", default=[])
parser.add_argument("--capture-path")
parser.add_argument("--quiet", action="store_true")
args = parser.parse_args()

if bool(args.command) == bool(args.script_path):
    raise SystemExit("Provide exactly one of --command or --script-path")

env_prefix = build_env_prefix(args.env)

if args.command:
    remote_cmd = args.command
    if env_prefix:
        remote_cmd = f"{env_prefix} {remote_cmd}"
    cmd = build_ssh_base(args.user, args.host, args.identity_file) + [remote_cmd]
    result = subprocess.run(cmd, capture_output=True, text=True)
else:
    script = Path(args.script_path).read_text(encoding="utf-8")
    remote_cmd = "bash -s"
    if env_prefix:
        remote_cmd = f"{env_prefix} {remote_cmd}"
    cmd = build_ssh_base(args.user, args.host, args.identity_file) + [remote_cmd]
    result = subprocess.run(cmd, input=script, capture_output=True, text=True)

output = result.stdout + result.stderr

if args.capture_path:
    Path(args.capture_path).write_text(output, encoding="utf-8")

if output and not args.quiet:
    print(output, end="")

if result.returncode != 0:
    raise SystemExit(result.returncode)
