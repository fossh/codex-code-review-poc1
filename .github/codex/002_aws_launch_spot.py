"""
Launch EC2 spot instance from AMI.

MUST HAVE REQUIREMENTS:
- Read config from DB (ami_id, instance_type, key_name, security_group_id, region, aws creds)
- Launch spot instance
- Wait for instance to be running
- Write instance_id and public_ip back to DB
"""

import boto3, sqlite3, sys, time
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path from command line: --db <path>
# ---------------------------------------------------------------------------

db_path = Path(sys.argv[2])

# ---------------------------------------------------------------------------
# Read config from DB
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key IN ('ami_id', 'instance_type', 'key_name', 'security_group_id', 'region', 'aws_access_key_id', 'aws_secret_access_key')")
config = dict(cursor.fetchall())

# ---------------------------------------------------------------------------
# Launch spot instance
# ---------------------------------------------------------------------------

ec2 = boto3.client(
    "ec2",
    region_name=config["region"],
    aws_access_key_id=config["aws_access_key_id"],
    aws_secret_access_key=config["aws_secret_access_key"]
)

response = ec2.run_instances(
    ImageId=config["ami_id"],
    InstanceType=config["instance_type"],
    KeyName=config["key_name"],
    SecurityGroupIds=[config["security_group_id"]],
    MinCount=1,
    MaxCount=1,
    InstanceMarketOptions={"MarketType": "spot", "SpotOptions": {"SpotInstanceType": "one-time"}}
)

instance_id = response["Instances"][0]["InstanceId"]
print(f"Launched spot instance: {instance_id}")

# ---------------------------------------------------------------------------
# Wait for running state
# ---------------------------------------------------------------------------

waiter = ec2.get_waiter("instance_running")
waiter.wait(InstanceIds=[instance_id])
print("Instance is running")

# ---------------------------------------------------------------------------
# Wait for public IP assignment
# ---------------------------------------------------------------------------

time.sleep(2)
desc = ec2.describe_instances(InstanceIds=[instance_id])
if not desc["Reservations"][0]["Instances"][0].get("PublicIpAddress"):
    time.sleep(5)
    desc = ec2.describe_instances(InstanceIds=[instance_id])

public_ip = desc["Reservations"][0]["Instances"][0]["PublicIpAddress"]
print(f"Public IP: {public_ip}")

cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('instance_id', ?)", (instance_id,))
cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('public_ip', ?)", (public_ip,))
conn.commit()
conn.close()

print("Instance info written to DB")
