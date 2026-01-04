#!/usr/bin/env python3
"""Write the Codex prompt file."""
from __future__ import annotations

import argparse
from pathlib import Path


PROMPT_TEXT = """You are running a PR code review. Read .github/tmp/github_context.json for PR metadata.
Follow the instructions in AGENTS.md. Review only the PR diff against the base branch.
You must output only a valid JSON object wrapped between lines BEGIN_REVIEW_JSON and END_REVIEW_JSON.
JSON schema:
{
  "event": "COMMENT" | "REQUEST_CHANGES" | "APPROVE",
  "body": "One-line verdict, then bullets grouped by severity (Blocking, Risk, Nit), then a testing note.",
  "comments": [
    {"path": "relative/path.ext", "line": 123, "body": "Inline comment text"}
  ]
}
Use paths relative to repo root. "line" is the line number in the new file (right side).
Only include inline comments for lines that appear in the PR diff; omit uncertain ones.
For every finding you mention in the body, include a corresponding inline comment that points to the relevant line.
If you cannot anchor a finding to a changed line, omit that finding from the body.
Do not include markdown headings or code fences. No text outside the JSON block. Output exactly one JSON block.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--validation-feedback")
    args = parser.parse_args()

    content = PROMPT_TEXT
    if args.validation_feedback:
        content += f"\nValidation feedback: {args.validation_feedback}\n"
        content += "Fix the issues and output a single valid JSON block with proper commas and quotes.\n"

    Path(args.output_path).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
