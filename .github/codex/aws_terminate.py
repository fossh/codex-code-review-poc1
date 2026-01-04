"""
Terminate EC2 instance.

MUST HAVE REQUIREMENTS:
- Read instance_id, region, aws creds from DB
- Terminate instance
"""

import boto3, sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path (hardcoded for all scripts)
# ---------------------------------------------------------------------------

db_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"

# ---------------------------------------------------------------------------
# Read config from DB
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key IN ('instance_id', 'region', 'aws_access_key_id', 'aws_secret_access_key')")
config = dict(cursor.fetchall())
conn.close()

# ---------------------------------------------------------------------------
# Terminate instance
# ---------------------------------------------------------------------------

ec2 = boto3.client(
    "ec2",
    region_name=config["region"],
    aws_access_key_id=config["aws_access_key_id"],
    aws_secret_access_key=config["aws_secret_access_key"]
)

ec2.terminate_instances(InstanceIds=[config["instance_id"]])

print(f"Terminated instance: {config['instance_id']}")
