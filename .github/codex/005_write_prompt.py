"""
Generate prompt from Jinja2 template.

MUST HAVE REQUIREMENTS:
- Read github context for base ref
- Render prompt.txt.j2 template
- Write prompt.txt to local .github/tmp/
- Store prompt in DB
"""

import sqlite3, json
from pathlib import Path
from jinja2 import Template

# ---------------------------------------------------------------------------
# DB and output paths
# ---------------------------------------------------------------------------

db_path = Path(__file__).parent.parent / "tmp" / "pipeline.db"
local_prompt_path = Path(__file__).parent.parent / "tmp" / "prompt.txt"

# ---------------------------------------------------------------------------
# Read github context
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT content FROM dumps WHERE category = 'json' AND name = 'github'")
github_raw = cursor.fetchone()[0]
github_ctx = json.loads(github_raw.decode() if isinstance(github_raw, bytes) else github_raw)

# ---------------------------------------------------------------------------
# Render template
# ---------------------------------------------------------------------------

template_path = Path(__file__).parent / "templates" / "prompt.txt.j2"
template = Template(template_path.read_text())

prompt = template.render(
    base_ref=github_ctx.get("base_ref", "main")
)

# ---------------------------------------------------------------------------
# Write prompt.txt locally and store in DB
# ---------------------------------------------------------------------------

local_prompt_path.write_text(prompt)

conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('prompt', ?)", [prompt])
conn.commit()
conn.close()

print(f"prompt.txt written to: {local_prompt_path}")
