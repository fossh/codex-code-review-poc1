"""
Generate AGENTS.md from Jinja2 template.

MUST HAVE REQUIREMENTS:
- Read workdir, pr_number, github context, token from database
- Render agents.md.j2 template with context
- Write AGENTS.md to local .github/tmp/
- Store content in DB
"""

import sqlite3, json, sys
from pathlib import Path
from jinja2 import Template

# ---------------------------------------------------------------------------
# Paths (relative, script runs from .github/codex/)
# ---------------------------------------------------------------------------

db_path = Path(sys.argv[2])
local_agents_path = Path("tmp/AGENTS.md")
local_agents_path.parent.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Read from database
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)

cursor = conn.execute("SELECT value FROM config WHERE key = 'pr_number'")
pr_number = cursor.fetchone()[0]

cursor = conn.execute("SELECT content FROM dumps WHERE category = 'json' AND name = 'github'")
github_raw = cursor.fetchone()[0]
github_ctx = json.loads(github_raw.decode() if isinstance(github_raw, bytes) else github_raw)

cursor = conn.execute("SELECT content FROM dumps WHERE category = 'secret' AND name = 'github_token'")
token_raw = cursor.fetchone()[0]
github_token = (token_raw.decode() if isinstance(token_raw, bytes) else token_raw).strip()

# ---------------------------------------------------------------------------
# Render template
# ---------------------------------------------------------------------------

template_path = Path("templates/agents.md.j2")
template = Template(template_path.read_text())

agents_content = template.render(
    owner=github_ctx["repository_owner"],
    repo=github_ctx["repository"].split("/")[1],
    pr_number=pr_number,
    commit_sha=github_ctx["sha"],
    github_token=github_token
)

# ---------------------------------------------------------------------------
# Write AGENTS.md locally and store in DB
# ---------------------------------------------------------------------------

local_agents_path.write_text(agents_content)

conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('agents_md', ?)", [agents_content])
conn.commit()
conn.close()

print(f"AGENTS.md written to: {local_agents_path}")
