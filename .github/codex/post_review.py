#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Post the validated payload to the GitHub reviews API for the given PR.
- Consume only CLI args (context, token, payload paths) and avoid other I/O.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--context-path", required=True)
parser.add_argument("--token-path", required=True)
parser.add_argument("--payload-path", required=True)
args = parser.parse_args()


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def parse_repo_info(context: dict) -> tuple[str, str]:
    repo_full = context.get("repository")
    owner = ""
    repo = ""
    if isinstance(repo_full, str) and "/" in repo_full:
        owner, repo = repo_full.split("/", 1)
    event = context.get("event") or {}
    if not owner:
        owner = context.get("repository_owner") or event.get("repository", {}).get("owner", {}).get(
            "login", ""
        )
    if not repo:
        repo = event.get("repository", {}).get("name", "")
    if not owner or not repo:
        raise ValueError("Unable to determine repository owner/name from context.")
    return owner, repo


def parse_pr_number(context: dict) -> int:
    event = context.get("event") or {}
    pr = event.get("pull_request") or {}
    pr_number = pr.get("number") or event.get("number")
    if not pr_number:
        raise ValueError("Unable to determine pull request number from context.")
    return int(pr_number)


context = load_json(args.context_path)
token = read_text(args.token_path).strip()
payload = load_json(args.payload_path)

owner, repo = parse_repo_info(context)
pr_number = parse_pr_number(context)
api_url = context.get("api_url") or "https://api.github.com"
url = f"{api_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
    "User-Agent": "codex-cli-review-bot",
    "X-GitHub-Api-Version": "2022-11-28",
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="POST",
)

try:
    with urllib.request.urlopen(request) as response:
        if response.status not in (200, 201):
            raise SystemExit(f"GitHub API returned status {response.status}: {response.read()}")
except urllib.error.HTTPError as exc:
    message = exc.read().decode("utf-8", errors="replace")
    raise SystemExit(f"GitHub API error: {exc.code} {message}") from exc

comment_count = len(payload.get("comments", [])) if isinstance(payload, dict) else 0
print(f"Posted review to {owner}/{repo} PR #{pr_number} with {comment_count} comments")
