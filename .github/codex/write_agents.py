#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Write the Codex review AGENTS.md content to --output-path.
- Do not read environment variables.
"""

import argparse
from pathlib import Path

AGENTS_TEXT = """## Codex Review Agent

You are running a pull-request code review. Focus on correctness, security, and missing tests.

### Context
- PR metadata is in `.github/tmp/github_context.json`.
- If no git repo exists, clone it using the repo info in the context file.
- A GitHub token for cloning private repos is in `.github/tmp/github_token.txt`.

### Expectations
- Review only the changes in this PR. If git history is available, use `git diff` against the base ref.
- Call out bugs, risky behavior changes, and missing tests first.
- Keep the review concise and actionable.

### Output Format
- Start with a one-line overall verdict.
- Then list findings as short bullets grouped by severity: `Blocking`, `Risk`, `Nit`.
- End with a brief testing note (what was or was not validated).
- Do not include code fences or markdown headings.

### Structured Output
- Output only a JSON object between lines `BEGIN_REVIEW_JSON` and `END_REVIEW_JSON`.
- JSON schema:
  {
    "event": "COMMENT" | "REQUEST_CHANGES" | "APPROVE",
    "body": "Verdict line + grouped bullets + testing note",
    "comments": [
      {"path": "relative/path.ext", "line": 123, "body": "Inline comment text"}
    ]
  }
- For every finding in the body, include a matching inline comment pointing to the relevant changed line.
- If you cannot anchor a finding to a changed line, omit that finding from the body.
"""

parser = argparse.ArgumentParser()
parser.add_argument("--output-path", required=True)
args = parser.parse_args()

# Single write to keep the script tiny and predictable.
Path(args.output_path).write_text(AGENTS_TEXT, encoding="utf-8")
