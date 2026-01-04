#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Poll SSH connectivity until the remote host accepts logins.
- Accept host/user/identity details via CLI arguments and do not read environment variables.
"""
from __future__ import annotations

import argparse
import subprocess
import time


def ssh_args(user: str, host: str, identity_file: str) -> list[str]:
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
        "echo",
        "ready",
    ]


parser = argparse.ArgumentParser()
parser.add_argument("--host", required=True)
parser.add_argument("--user", required=True)
parser.add_argument("--identity-file", required=True)
parser.add_argument("--retries", type=int, default=30)
parser.add_argument("--delay", type=int, default=5)
args = parser.parse_args()

for _ in range(args.retries):
    result = subprocess.run(ssh_args(args.user, args.host, args.identity_file))
    if result.returncode == 0:
        raise SystemExit(0)
    time.sleep(args.delay)

raise SystemExit("SSH not ready after retries.")
