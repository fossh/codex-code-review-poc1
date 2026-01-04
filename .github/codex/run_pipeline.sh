#!/usr/bin/env bash
# run_pipeline.sh - Run Codex review and post to GitHub
# Called from within the cloned repo on EC2

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP_DIR="${REMOTE_WORKDIR:-.}/.github/tmp"
CODEX_DIR="$REPO_ROOT/.github/codex"

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

CONTEXT_PATH="$TMP_DIR/github_context.json"
TOKEN_PATH="$TMP_DIR/github_token.txt"
AGENTS_PATH="$TMP_DIR/AGENTS.md"
PROMPT_PATH="$TMP_DIR/codex_prompt.txt"
REVIEW_OUT="$TMP_DIR/codex_review.txt"
PAYLOAD_PATH="$TMP_DIR/review_payload.json"
VALIDATION_ERROR_PATH="$TMP_DIR/validation_error.txt"

MAX_ATTEMPTS="${MAX_ATTEMPTS:-2}"

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

log() { printf '[codex-review] %s\n' "$*"; }

# ---------------------------------------------------------------------------
# Step 1: Write AGENTS.md
# ---------------------------------------------------------------------------

log "Writing AGENTS.md"
uv run "$CODEX_DIR/write_agents.py" --output-path "$AGENTS_PATH"
cp "$AGENTS_PATH" "$REPO_ROOT/AGENTS.md"

# ---------------------------------------------------------------------------
# Step 2: Review loop with validation
# ---------------------------------------------------------------------------

VALIDATION_ERROR=""
for ATTEMPT in $(seq 1 "$MAX_ATTEMPTS"); do
    rm -f "$REVIEW_OUT" "$VALIDATION_ERROR_PATH"

    log "Writing prompt (attempt $ATTEMPT)"
    if [[ -n "$VALIDATION_ERROR" ]]; then
        uv run "$CODEX_DIR/write_prompt.py" --output-path "$PROMPT_PATH" --validation-feedback "$VALIDATION_ERROR"
    else
        uv run "$CODEX_DIR/write_prompt.py" --output-path "$PROMPT_PATH"
    fi

    log "Running Codex (attempt $ATTEMPT)"
    cd "$REPO_ROOT"  # Codex reads AGENTS.md from current directory
    if timeout 10m codex exec -m gpt-5.2-codex \
        --config model_reasoning_effort=high \
        --dangerously-bypass-approvals-and-sandbox \
        --skip-git-repo-check \
        < "$PROMPT_PATH" > "$REVIEW_OUT" 2>&1; then
        log "Codex completed"
    else
        VALIDATION_ERROR="Codex execution failed."
        continue
    fi

    log "Validating review output"
    if uv run "$CODEX_DIR/prepare_payload.py" \
        --context-path "$CONTEXT_PATH" \
        --token-path "$TOKEN_PATH" \
        --review-path "$REVIEW_OUT" \
        --payload-path "$PAYLOAD_PATH" \
        --validation-error-path "$VALIDATION_ERROR_PATH"; then
        log "Validation passed"
        break
    fi

    if [[ -f "$VALIDATION_ERROR_PATH" ]]; then
        VALIDATION_ERROR=$(cat "$VALIDATION_ERROR_PATH")
        log "Validation failed: $VALIDATION_ERROR"
    else
        VALIDATION_ERROR="Review output failed validation."
        log "Validation failed"
    fi
done

# ---------------------------------------------------------------------------
# Step 3: Post review to GitHub
# ---------------------------------------------------------------------------

if [[ ! -f "$PAYLOAD_PATH" ]]; then
    log "Codex output failed validation after $MAX_ATTEMPTS attempts; not posting a review."
    exit 1
fi

log "Posting review to GitHub"
uv run "$CODEX_DIR/post_review.py" \
    --context-path "$CONTEXT_PATH" \
    --token-path "$TOKEN_PATH" \
    --payload-path "$PAYLOAD_PATH"

log "Pipeline completed successfully"
