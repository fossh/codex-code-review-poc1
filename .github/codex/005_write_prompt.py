"""
Generate prompt from Jinja2 template.

MUST HAVE REQUIREMENTS:
- Read github context for base ref
- Render prompt.txt.j2 template
- Write prompt.txt to local .github/tmp/
- Store prompt in DB
"""

import sqlite3, json, sys
from pathlib import Path
from jinja2 import Template

# ---------------------------------------------------------------------------
# Paths (relative, script runs from .github/codex/)
# ---------------------------------------------------------------------------

db_path = Path(sys.argv[2])
local_prompt_path = Path("tmp/prompt.txt")
local_prompt_path.parent.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Read from database
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)

cursor = conn.execute("SELECT content FROM dumps WHERE category = 'json' AND name = 'github'")
github_raw = cursor.fetchone()[0]
github_ctx = json.loads(github_raw.decode() if isinstance(github_raw, bytes) else github_raw)

cursor = conn.execute("SELECT content FROM dumps WHERE category = 'secret' AND name = 'github_token'")
token_raw = cursor.fetchone()[0]
github_token = (token_raw.decode() if isinstance(token_raw, bytes) else token_raw).strip()

cursor = conn.execute("SELECT value FROM config WHERE key = 'pr_number'")
pr_number = cursor.fetchone()[0]

# ---------------------------------------------------------------------------
# Extract variables
# ---------------------------------------------------------------------------

owner = github_ctx["repository_owner"]
repo = github_ctx["repository"].split("/")[1]
base_ref = github_ctx.get("base_ref", "main")
head_sha = github_ctx.get("event", {}).get("pull_request", {}).get("head", {}).get("sha", github_ctx.get("sha", ""))

# ---------------------------------------------------------------------------
# Render template
# ---------------------------------------------------------------------------

template_path = Path("templates/prompt.txt.j2")
template = Template(template_path.read_text())

prompt = template.render(
    owner=owner,
    repo=repo,
    pr_number=pr_number,
    base_ref=base_ref,
    head_sha=head_sha,
    github_token=github_token
)

# ---------------------------------------------------------------------------
# Write prompt.txt locally and store in DB
# ---------------------------------------------------------------------------

local_prompt_path.write_text(prompt)

conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('prompt', ?)", [prompt])
conn.commit()
conn.close()

print(f"prompt.txt written to: {local_prompt_path}")
