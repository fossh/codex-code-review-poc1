#!/usr/bin/env bash
# remote_clone.sh - Clone PR repository on remote EC2 instance
# Runs via ssh_exec.py with REMOTE_WORKDIR passed as env var

set -euo pipefail

cd "$REMOTE_WORKDIR"

# ---------------------------------------------------------------------------
# Parse PR metadata from github_context.json
# ---------------------------------------------------------------------------

python3 - <<'PY' > .github/tmp/pr_meta.sh
import json
from pathlib import Path

ctx = json.loads(Path(".github/tmp/github_context.json").read_text())
event = ctx.get("event") or {}
pr = event.get("pull_request") or {}

# Extract owner/repo
owner_repo = ctx.get("repository") or ""
if not owner_repo:
    owner = ctx.get("repository_owner") or event.get("repository", {}).get("owner", {}).get("login", "")
    name = event.get("repository", {}).get("name", "")
    owner_repo = f"{owner}/{name}" if owner and name else ""

# Extract PR details
pr_number = pr.get("number") or event.get("number") or ""
base_ref = (pr.get("base") or {}).get("ref") or "dev"
head_sha = (pr.get("head") or {}).get("sha") or ""

def esc(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')

print(f'OWNER_REPO="{esc(owner_repo)}"')
print(f'PR_NUMBER="{esc(pr_number)}"')
print(f'BASE_REF="{esc(base_ref)}"')
print(f'HEAD_SHA="{esc(head_sha)}"')
PY

source .github/tmp/pr_meta.sh

# ---------------------------------------------------------------------------
# Clone or update repository
# ---------------------------------------------------------------------------

TOKEN="$(cat .github/tmp/github_token.txt)"
CLONE_URL="https://x-access-token:${TOKEN}@github.com/${OWNER_REPO}.git"

if [[ ! -d repo/.git ]]; then
    rm -rf repo
    git clone "$CLONE_URL" repo
fi

cd repo
git remote set-url origin "$CLONE_URL"
git fetch origin "$BASE_REF" --depth 50

# ---------------------------------------------------------------------------
# Checkout PR head
# ---------------------------------------------------------------------------

if [[ -n "$PR_NUMBER" ]]; then
    git fetch origin "pull/${PR_NUMBER}/head:pr-head" --depth 50
    git checkout pr-head
elif [[ -n "$HEAD_SHA" ]]; then
    git checkout "$HEAD_SHA"
fi

# Remove token from remote URL for security
git remote set-url origin "https://github.com/${OWNER_REPO}.git"

echo "Repository cloned and checked out successfully"
