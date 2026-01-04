"""
Execute Codex CLI with the prompt.

MUST HAVE REQUIREMENTS:
- Read repo_root and prompt from config
- Run codex CLI in repo directory
- Codex handles reviewing and posting to GitHub
"""

import sqlite3, argparse, subprocess

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--db-path", required=True)
db_path = parser.parse_args().db_path

# ---------------------------------------------------------------------------
# Read from config
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT key, value FROM config WHERE key IN ('repo_root', 'prompt')")
config = dict(cursor.fetchall())
conn.close()

# ---------------------------------------------------------------------------
# Run Codex CLI (Codex handles everything including posting review)
# ---------------------------------------------------------------------------

subprocess.run(
    ["codex", "exec", "--prompt", config["prompt"]],
    cwd=config["repo_root"],
    timeout=600
)

print("Codex execution complete")
