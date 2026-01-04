#!/usr/bin/env bash
# remote_codex.sh - Run Codex review on remote EC2 instance
# Runs via ssh_exec.py with REMOTE_WORKDIR passed as env var

set -euo pipefail

source "$REMOTE_WORKDIR/.github/tmp/pr_meta.sh"
cd "$REMOTE_WORKDIR/repo"

# ---------------------------------------------------------------------------
# Find codex binary
# ---------------------------------------------------------------------------

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
CODEX_BIN="$(command -v codex || true)"

if [[ -z "$CODEX_BIN" && -x /usr/local/bin/codex ]]; then
    CODEX_BIN="/usr/local/bin/codex"
fi

if [[ -z "$CODEX_BIN" ]]; then
    echo "codex not found in PATH" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Run Codex with prompt
# ---------------------------------------------------------------------------

timeout 10m "$CODEX_BIN" exec -m gpt-5.2-codex \
    --config model_reasoning_effort=high \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check \
    < "$REMOTE_WORKDIR/.github/tmp/codex_prompt.txt"
