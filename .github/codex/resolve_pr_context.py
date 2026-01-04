#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Ensure github_context.json includes event.pull_request data.
- Fetch PR data via GitHub API when missing, using CLI-provided token.
"""

import argparse
import json
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--context-path", required=True)
parser.add_argument("--token")
parser.add_argument("--token-path")
parser.add_argument("--pr-number")
args = parser.parse_args()

if args.token is None:
    token = Path(args.token_path).read_text(encoding="utf-8").strip()
else:
    token = args.token

path = Path(args.context_path)
ctx = json.loads(path.read_text(encoding="utf-8"))
event = ctx["event"]

# Exit early when pull_request is already present.
pr_existing = event["pull_request"] if "pull_request" in event else None
if pr_existing:
    raise SystemExit(0)

repo_full = ctx["repository"]
if not repo_full:
    owner = ctx["repository_owner"] or event["repository"]["owner"]["login"]
    name = event["repository"]["name"]
    repo_full = f"{owner}/{name}"

api_url = ctx["api_url"] if ctx["api_url"] else "https://api.github.com"
pr_number = (args.pr_number or "").strip()

if pr_number:
    url = f"{api_url}/repos/{repo_full}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-cli-review-bot",
        },
    )
    with urllib.request.urlopen(req) as resp:
        pr_data = json.loads(resp.read().decode("utf-8"))
else:
    ref_name = ctx["ref_name"] if ctx["ref_name"] else ctx["ref"].split("/")[-1]
    owner = repo_full.split("/", 1)[0]
    url = f"{api_url}/repos/{repo_full}/pulls?state=open&head={owner}:{ref_name}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-cli-review-bot",
        },
    )
    with urllib.request.urlopen(req) as resp:
        prs = json.loads(resp.read().decode("utf-8"))
    pr_data = prs[0] if prs else None

if not pr_data:
    raise SystemExit("Unable to resolve pull request for workflow_dispatch run.")

event["pull_request"] = pr_data
ctx["event"] = event
path.write_text(json.dumps(ctx), encoding="utf-8")
