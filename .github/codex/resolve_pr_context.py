#!/usr/bin/env python3
"""Ensure github_context.json contains pull_request data."""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def request_json(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-cli-review-bot",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-path", required=True)
    parser.add_argument("--token")
    parser.add_argument("--token-path")
    parser.add_argument("--pr-number")
    args = parser.parse_args()

    token = args.token
    if token is None:
        if args.token_path is None:
            raise SystemExit("Missing token input.")
        token = Path(args.token_path).read_text(encoding="utf-8").strip()

    path = Path(args.context_path)
    ctx = json.loads(path.read_text(encoding="utf-8"))
    event = ctx.get("event") or {}
    pr = event.get("pull_request")
    if pr:
        return

    repo = ctx.get("repository")
    if not repo:
        owner = ctx.get("repository_owner") or event.get("repository", {}).get("owner", {}).get(
            "login", ""
        )
        name = event.get("repository", {}).get("name", "")
        repo = f"{owner}/{name}" if owner and name else ""

    if not repo:
        raise SystemExit("Unable to determine repository from context.")

    api_url = ctx.get("api_url") or "https://api.github.com"
    pr_number = (args.pr_number or "").strip()
    pr_data = None

    if pr_number:
        pr_data = request_json(f"{api_url}/repos/{repo}/pulls/{pr_number}", token)
    else:
        ref_name = ctx.get("ref_name") or ctx.get("ref", "").split("/")[-1]
        if not ref_name:
            raise SystemExit("Unable to determine ref name for PR lookup.")
        owner = repo.split("/", 1)[0]
        prs = request_json(
            f"{api_url}/repos/{repo}/pulls?state=open&head={owner}:{ref_name}", token
        )
        if prs:
            pr_data = prs[0]

    if not pr_data:
        raise SystemExit("Unable to resolve pull request for workflow_dispatch run.")

    event["pull_request"] = pr_data
    ctx["event"] = event
    path.write_text(json.dumps(ctx), encoding="utf-8")


if __name__ == "__main__":
    main()
