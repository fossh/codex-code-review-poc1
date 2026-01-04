"""
Generate AGENTS.md from Jinja2 template.

MUST HAVE REQUIREMENTS:
- Read repo_root, github context, and token from database
- Render agents.md.j2 template with context
- Write AGENTS.md to repo root
"""

import sqlite3, argparse, json
from pathlib import Path
from jinja2 import Template

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--db-path", required=True)
db_path = parser.parse_args().db_path

# ---------------------------------------------------------------------------
# Read from database
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)

cursor = conn.execute("SELECT value FROM config WHERE key = 'repo_root'")
repo_root = cursor.fetchone()[0]

cursor = conn.execute("SELECT value FROM config WHERE key = 'pr_number'")
pr_number = cursor.fetchone()[0]

cursor = conn.execute("SELECT content FROM dumps WHERE category = 'json' AND name = 'github'")
github_ctx = json.loads(cursor.fetchone()[0])

cursor = conn.execute("SELECT content FROM dumps WHERE category = 'secret' AND name = 'github_token'")
github_token = cursor.fetchone()[0].strip()

# ---------------------------------------------------------------------------
# Render template
# ---------------------------------------------------------------------------

template_path = Path(__file__).parent / "templates" / "agents.md.j2"
template = Template(template_path.read_text())

agents_content = template.render(
    owner=github_ctx["repository_owner"],
    repo=github_ctx["repository"].split("/")[1],
    pr_number=pr_number,
    commit_sha=github_ctx["sha"],
    github_token=github_token
)

# ---------------------------------------------------------------------------
# Write AGENTS.md to repo
# ---------------------------------------------------------------------------

agents_path = f"{repo_root}/AGENTS.md"
with open(agents_path, "w") as f:
    f.write(agents_content)

conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('agents_md', ?)", [agents_content])
conn.commit()
conn.close()

print(f"AGENTS.md written to: {agents_path}")
