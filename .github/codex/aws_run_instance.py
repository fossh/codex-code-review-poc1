#!/usr/bin/env python3
"""Launch an EC2 instance and print its instance id."""
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
parser.add_argument("--ami-id", required=True)
parser.add_argument("--instance-type", required=True)
parser.add_argument("--subnet-id", required=True)
parser.add_argument("--security-group-ids", required=True)
parser.add_argument("--key-name", required=True)
parser.add_argument("--session-name", required=True)
parser.add_argument("--instance-name", required=True)
parser.add_argument("--aws-access-key-id", required=True)
parser.add_argument("--aws-secret-access-key", required=True)
parser.add_argument("--aws-session-token")
args = parser.parse_args()

security_group_ids = " ".join(args.security_group_ids.replace(",", " ").split())
security_group_ids_comma = ",".join(security_group_ids.split())

run_args = [
    "aws",
    "ec2",
    "run-instances",
    "--region",
    AWS_REGION,
    "--image-id",
    args.ami_id,
    "--instance-type",
    args.instance_type,
]

if args.key_name and args.key_name != "None":
    run_args.extend(["--key-name", args.key_name])

run_args.extend(
    [
        "--tag-specifications",
        "ResourceType=instance,Tags=["
        f"{{Key=Name,Value={args.instance_name}}},"
        f"{{Key=Session,Value={args.session_name}}}"
        "]",
        "--network-interfaces",
        "DeviceIndex=0,AssociatePublicIpAddress=true,"
        f"SubnetId={args.subnet_id},Groups={security_group_ids_comma}",
        "--query",
        "Instances[0].InstanceId",
        "--output",
        "text",
    ]
)

result = subprocess.run(
    run_args,
    check=True,
    capture_output=True,
    text=True,
    env=build_env(args.aws_access_key_id, args.aws_secret_access_key, args.aws_session_token),
)

instance_id = result.stdout.strip()
if not instance_id:
    raise SystemExit("aws ec2 run-instances returned empty instance id")

print(instance_id)
