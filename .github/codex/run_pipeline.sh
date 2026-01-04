#!/usr/bin/env bash
# run_pipeline.sh - Orchestrate Codex code review pipeline
# Sources .env for configuration, calls Python scripts sequentially with CLI args

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP_DIR="$REPO_ROOT/.github/tmp"
CODEX_DIR="$REPO_ROOT/.github/codex"

# Source .env for credentials and EC2 configuration
if [[ -f "$REPO_ROOT/.env" ]]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
fi

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

CONTEXT_PATH="$TMP_DIR/github_context.json"
TOKEN_PATH="$TMP_DIR/github_token.txt"
AUTH_PATH="$TMP_DIR/auth.json"
SSH_KEY_PATH="$TMP_DIR/id_rsa"
AGENTS_PATH="$TMP_DIR/AGENTS.md"
PROMPT_PATH="$TMP_DIR/codex_prompt.txt"
REVIEW_OUT="$TMP_DIR/codex_review.txt"
PAYLOAD_PATH="$TMP_DIR/review_payload.json"
VALIDATION_ERROR_PATH="$TMP_DIR/validation_error.txt"

# Remote configuration
SSH_USER="ubuntu"
REMOTE_BASE_DIR="/home/$SSH_USER/codex-work"
REMOTE_WORKDIR="$REMOTE_BASE_DIR/${SESSION_NAME:-codex-session}"
PROMPT_REMOTE="$REMOTE_WORKDIR/.github/tmp/codex_prompt.txt"

# Review loop configuration
MAX_ATTEMPTS="${MAX_ATTEMPTS:-2}"

# ---------------------------------------------------------------------------
# Helper function
# ---------------------------------------------------------------------------

log() {
    printf '[codex-review] %s\n' "$*"
}

# ---------------------------------------------------------------------------
# Step 1: Resolve PR context
# ---------------------------------------------------------------------------

log "Resolving PR context"
uv run "$CODEX_DIR/resolve_pr_context.py" \
    --context-path "$CONTEXT_PATH" \
    --token-path "$TOKEN_PATH" \
    --pr-number "${PR_NUMBER:-}"

# ---------------------------------------------------------------------------
# Step 2: Get public IP for existing instance
# ---------------------------------------------------------------------------

log "Getting public IP for instance: $CODEX_EXISTING_INSTANCE_ID"
PUBLIC_IP=$(uv run "$CODEX_DIR/aws_get_public_ip.py" \
    --instance-id "$CODEX_EXISTING_INSTANCE_ID" \
    --aws-access-key-id "$AWS_ACCESS_KEY_ID" \
    --aws-secret-access-key "$AWS_SECRET_ACCESS_KEY")
log "Instance public IP: $PUBLIC_IP"

# ---------------------------------------------------------------------------
# Step 3: Wait for SSH connectivity
# ---------------------------------------------------------------------------

log "Waiting for SSH on $PUBLIC_IP"
uv run "$CODEX_DIR/ssh_wait.py" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH"

# ---------------------------------------------------------------------------
# Step 4: Create remote directories
# ---------------------------------------------------------------------------

log "Creating remote directories"
uv run "$CODEX_DIR/ssh_exec.py" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH" \
    --command "mkdir -p ~/.codex $REMOTE_WORKDIR/.github/tmp"

# ---------------------------------------------------------------------------
# Step 5: Upload files to remote
# ---------------------------------------------------------------------------

log "Uploading auth.json"
uv run "$CODEX_DIR/scp_put.py" \
    --source "$AUTH_PATH" \
    --destination "~/.codex/auth.json" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH"

log "Uploading github_context.json"
uv run "$CODEX_DIR/scp_put.py" \
    --source "$CONTEXT_PATH" \
    --destination "$REMOTE_WORKDIR/.github/tmp/github_context.json" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH"

log "Uploading github_token.txt"
uv run "$CODEX_DIR/scp_put.py" \
    --source "$TOKEN_PATH" \
    --destination "$REMOTE_WORKDIR/.github/tmp/github_token.txt" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH"

# ---------------------------------------------------------------------------
# Step 6: Write and upload AGENTS.md
# ---------------------------------------------------------------------------

log "Writing AGENTS.md"
uv run "$CODEX_DIR/write_agents.py" --output-path "$AGENTS_PATH"

uv run "$CODEX_DIR/scp_put.py" \
    --source "$AGENTS_PATH" \
    --destination "$REMOTE_WORKDIR/AGENTS.md" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH"

# ---------------------------------------------------------------------------
# Step 7: Clone repository on remote
# ---------------------------------------------------------------------------

log "Cloning PR repo on remote"
uv run "$CODEX_DIR/ssh_exec.py" \
    --host "$PUBLIC_IP" \
    --user "$SSH_USER" \
    --identity-file "$SSH_KEY_PATH" \
    --script-path "$CODEX_DIR/remote_clone.sh" \
    --env "REMOTE_WORKDIR=$REMOTE_WORKDIR"

# ---------------------------------------------------------------------------
# Step 8: Review loop with validation feedback
# ---------------------------------------------------------------------------

VALIDATION_ERROR=""
for ATTEMPT in $(seq 1 "$MAX_ATTEMPTS"); do
    rm -f "$REVIEW_OUT" "$VALIDATION_ERROR_PATH"

    # Write prompt (with optional feedback)
    log "Writing prompt (attempt $ATTEMPT)"
    if [[ -n "$VALIDATION_ERROR" ]]; then
        uv run "$CODEX_DIR/write_prompt.py" \
            --output-path "$PROMPT_PATH" \
            --validation-feedback "$VALIDATION_ERROR"
    else
        uv run "$CODEX_DIR/write_prompt.py" --output-path "$PROMPT_PATH"
    fi

    # Upload prompt
    uv run "$CODEX_DIR/scp_put.py" \
        --source "$PROMPT_PATH" \
        --destination "$PROMPT_REMOTE" \
        --host "$PUBLIC_IP" \
        --user "$SSH_USER" \
        --identity-file "$SSH_KEY_PATH"

    # Run Codex on remote
    log "Running Codex (attempt $ATTEMPT)"
    if ! uv run "$CODEX_DIR/ssh_exec.py" \
        --host "$PUBLIC_IP" \
        --user "$SSH_USER" \
        --identity-file "$SSH_KEY_PATH" \
        --script-path "$CODEX_DIR/remote_codex.sh" \
        --env "REMOTE_WORKDIR=$REMOTE_WORKDIR" \
        --capture-path "$REVIEW_OUT"; then
        VALIDATION_ERROR="Codex execution failed on remote."
        continue
    fi

    # Validate and prepare payload
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

    # Read validation error for next attempt
    if [[ -f "$VALIDATION_ERROR_PATH" ]]; then
        VALIDATION_ERROR=$(cat "$VALIDATION_ERROR_PATH")
        log "Validation failed: $VALIDATION_ERROR"
    else
        VALIDATION_ERROR="Review output failed validation."
        log "Validation failed"
    fi
done

# ---------------------------------------------------------------------------
# Step 9: Post review to GitHub
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
