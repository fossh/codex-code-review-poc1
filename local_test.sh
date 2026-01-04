#!/usr/bin/env bash
# local_test.sh - Download GHA context from EC2 and run pipeline locally
#
# Prerequisites:
#   1. Run debug-setup workflow first (it uploads context to EC2 and sleeps)
#   2. Set EC2_IP env var or update .env with correct instance ID
#   3. Have SSH key at ~/.ssh/codex-key (or set SSH_KEY_PATH)

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DEBUG_DIR="$SCRIPT_DIR/.local-debug"
SSH_KEY_PATH="${SSH_KEY_PATH:-$SCRIPT_DIR/.tmp/codex-key}"
SSH_USER="ubuntu"
REMOTE_WORKDIR="/home/$SSH_USER/codex-debug"

# ---------------------------------------------------------------------------
# Get EC2 IP
# ---------------------------------------------------------------------------

if [[ -z "${EC2_IP:-}" ]]; then
    source "$SCRIPT_DIR/.env"
    export AWS_DEFAULT_REGION=ap-south-1
    EC2_IP=$(aws ec2 describe-instances \
        --instance-ids "$CODEX_EXISTING_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
fi

echo "[local-test] EC2 IP: $EC2_IP"

# ---------------------------------------------------------------------------
# SSH options
# ---------------------------------------------------------------------------

SSH_OPTS="-i $SSH_KEY_PATH -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

# ---------------------------------------------------------------------------
# Step 1: Download from EC2
# ---------------------------------------------------------------------------

echo "[local-test] Downloading context from EC2..."
mkdir -p "$LOCAL_DEBUG_DIR/.github/tmp"

rsync -avz -e "ssh $SSH_OPTS" \
    "$SSH_USER@$EC2_IP:$REMOTE_WORKDIR/.github/tmp/" \
    "$LOCAL_DEBUG_DIR/.github/tmp/"

rsync -avz -e "ssh $SSH_OPTS" \
    "$SSH_USER@$EC2_IP:$REMOTE_WORKDIR/repo/" \
    "$LOCAL_DEBUG_DIR/repo/"

echo "[local-test] Downloaded to $LOCAL_DEBUG_DIR"

# ---------------------------------------------------------------------------
# Step 2: Run pipeline locally
# ---------------------------------------------------------------------------

echo "[local-test] Running pipeline locally..."

cd "$LOCAL_DEBUG_DIR/repo"

CODEX_DIR="$SCRIPT_DIR/.github/codex"
TMP_DIR="$LOCAL_DEBUG_DIR/.github/tmp"
CONTEXT_PATH="$TMP_DIR/github_context.json"
TOKEN_PATH="$TMP_DIR/github_token.txt"
AGENTS_PATH="$TMP_DIR/AGENTS.md"
PROMPT_PATH="$TMP_DIR/codex_prompt.txt"
REVIEW_OUT="$TMP_DIR/codex_review.txt"
PAYLOAD_PATH="$TMP_DIR/review_payload.json"

# Write AGENTS.md
echo "[local-test] Writing AGENTS.md"
uv run "$CODEX_DIR/write_agents.py" --output-path "$AGENTS_PATH"
cp "$AGENTS_PATH" ./AGENTS.md

# Write prompt
echo "[local-test] Writing prompt"
uv run "$CODEX_DIR/write_prompt.py" --output-path "$PROMPT_PATH"

echo "[local-test] Prompt written to: $PROMPT_PATH"
echo "--- PROMPT PREVIEW ---"
head -30 "$PROMPT_PATH"
echo "--- END PREVIEW ---"

# Run Codex
echo "[local-test] Running Codex..."
if timeout 10m codex exec \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check \
    < "$PROMPT_PATH" > "$REVIEW_OUT" 2>&1; then
    echo "[local-test] Codex completed"
else
    echo "[local-test] Codex failed with status $?"
    echo "--- CODEX OUTPUT ---"
    cat "$REVIEW_OUT"
    echo "--- END OUTPUT ---"
    exit 1
fi

echo "--- CODEX OUTPUT ---"
cat "$REVIEW_OUT"
echo "--- END OUTPUT ---"

# Prepare payload
echo "[local-test] Preparing payload..."
if uv run "$CODEX_DIR/prepare_payload.py" \
    --context-path "$CONTEXT_PATH" \
    --token-path "$TOKEN_PATH" \
    --review-path "$REVIEW_OUT" \
    --payload-path "$PAYLOAD_PATH"; then
    echo "[local-test] Payload prepared"
else
    echo "[local-test] Payload preparation failed"
    exit 1
fi

echo "--- PAYLOAD ---"
cat "$PAYLOAD_PATH"
echo "--- END PAYLOAD ---"

# Post review (optional - uncomment to actually post)
echo ""
echo "[local-test] Ready to post review. Run this to post:"
echo "  uv run $CODEX_DIR/post_review.py --context-path $CONTEXT_PATH --token-path $TOKEN_PATH --payload-path $PAYLOAD_PATH"
echo ""

# Uncomment to auto-post:
# echo "[local-test] Posting review..."
# uv run "$CODEX_DIR/post_review.py" \
#     --context-path "$CONTEXT_PATH" \
#     --token-path "$TOKEN_PATH" \
#     --payload-path "$PAYLOAD_PATH"
# echo "[local-test] Review posted!"

echo "[local-test] Done!"
