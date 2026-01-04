#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Wait for an EC2 instance to reach the requested state.
- Use AWS region ap-south-1.
"""

import argparse
import subprocess

AWS_REGION = "ap-south-1"

parser = argparse.ArgumentParser()
parser.add_argument("--instance-id", required=True)
parser.add_argument("--state", default="instance-running")
parser.add_argument("--aws-access-key-id", required=True)
parser.add_argument("--aws-secret-access-key", required=True)
parser.add_argument("--aws-session-token")
args = parser.parse_args()

env = {
    "AWS_ACCESS_KEY_ID": args.aws_access_key_id,
    "AWS_SECRET_ACCESS_KEY": args.aws_secret_access_key,
}
if args.aws_session_token:
    env["AWS_SESSION_TOKEN"] = args.aws_session_token

cmd = [
    "aws",
    "ec2",
    "wait",
    args.state,
    "--region",
    AWS_REGION,
    "--instance-ids",
    args.instance_id,
]

subprocess.run(cmd, check=True, env=env)
