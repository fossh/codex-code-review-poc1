#!/usr/bin/env python3
"""MUST HAVE REQUIREMENTS
- Accept all inputs via CLI args; do not read env vars.
- Write github_context.json, github_token.txt, auth.json, id_rsa under --out-dir.
"""

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--out-dir", required=True)
parser.add_argument("--github-context")
parser.add_argument("--github-context-path")
parser.add_argument("--github-token")
parser.add_argument("--github-token-path")
parser.add_argument("--codex-auth-json")
parser.add_argument("--codex-auth-json-path")
parser.add_argument("--codex-id-rsa")
parser.add_argument("--codex-id-rsa-path")
args = parser.parse_args()

out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

# Prefer direct values; fall back to reading the provided file paths.
if args.github_context is None:
    github_context = Path(args.github_context_path).read_text(encoding="utf-8")
else:
    github_context = args.github_context

if args.github_token is None:
    github_token = Path(args.github_token_path).read_text(encoding="utf-8")
else:
    github_token = args.github_token

if args.codex_auth_json is None:
    codex_auth = Path(args.codex_auth_json_path).read_text(encoding="utf-8")
else:
    codex_auth = args.codex_auth_json

if args.codex_id_rsa is None:
    codex_id_rsa = Path(args.codex_id_rsa_path).read_text(encoding="utf-8")
else:
    codex_id_rsa = args.codex_id_rsa

(out_dir / "github_context.json").write_text(github_context, encoding="utf-8")
(out_dir / "github_token.txt").write_text(github_token, encoding="utf-8")
(out_dir / "auth.json").write_text(codex_auth, encoding="utf-8")
id_rsa_path = out_dir / "id_rsa"
id_rsa_path.write_text(codex_id_rsa, encoding="utf-8")
id_rsa_path.chmod(0o600)
