#!/usr/bin/env python3
"""Terminate an EC2 instance."""
from __future__ import annotations

import argparse
import subprocess

AWS_REGION = "ap-south-1"


def build_env(access_key: str, secret_key: str, session_token: str | None) -> dict[str, str]:
    env = {
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
    }
    if session_token:
        env["AWS_SESSION_TOKEN"] = session_token
    return env


parser = argparse.ArgumentParser()
parser.add_argument("--instance-id", required=True)
parser.add_argument("--aws-access-key-id", required=True)
parser.add_argument("--aws-secret-access-key", required=True)
parser.add_argument("--aws-session-token")
args = parser.parse_args()

cmd = [
    "aws",
    "ec2",
    "terminate-instances",
    "--region",
    AWS_REGION,
    "--instance-ids",
    args.instance_id,
]

subprocess.run(
    cmd,
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    env=build_env(args.aws_access_key_id, args.aws_secret_access_key, args.aws_session_token),
)
