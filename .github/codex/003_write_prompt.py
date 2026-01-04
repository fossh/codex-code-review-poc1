"""
Generate prompt from Jinja2 template.

MUST HAVE REQUIREMENTS:
- Read github context for base ref
- Render prompt.txt.j2 template
- Write prompt to config table
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
# Read github context
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT content FROM dumps WHERE category = 'json' AND name = 'github'")
github_ctx = json.loads(cursor.fetchone()[0])

# ---------------------------------------------------------------------------
# Render template
# ---------------------------------------------------------------------------

template_path = Path(__file__).parent / "templates" / "prompt.txt.j2"
template = Template(template_path.read_text())

prompt = template.render(
    base_ref=github_ctx.get("base_ref", "main")
)

# ---------------------------------------------------------------------------
# Store prompt
# ---------------------------------------------------------------------------

conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('prompt', ?)", [prompt])
conn.commit()
conn.close()

print("Prompt written to config")
