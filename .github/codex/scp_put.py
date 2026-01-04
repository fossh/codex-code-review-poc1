#!/usr/bin/env python3
"""Copy a local file to a remote host via scp."""
from __future__ import annotations

import argparse
import subprocess


def build_scp_cmd(source: str, user: str, host: str, dest: str, identity_file: str) -> list[str]:
    return [
        "scp",
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
        source,
        f"{user}@{host}:{dest}",
    ]


parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True)
parser.add_argument("--destination", required=True)
parser.add_argument("--host", required=True)
parser.add_argument("--user", required=True)
parser.add_argument("--identity-file", required=True)
args = parser.parse_args()

subprocess.run(
    build_scp_cmd(args.source, args.user, args.host, args.destination, args.identity_file),
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
