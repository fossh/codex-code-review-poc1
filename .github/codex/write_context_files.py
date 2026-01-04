#!/usr/bin/env python3
"""Write GitHub/Codex context files from provided inputs."""
from __future__ import annotations

import argparse
from pathlib import Path


def read_value(text: str | None, path: str | None, name: str) -> str:
    if text is not None:
        return text
    if path is None:
        raise SystemExit(f"Missing {name} value.")
    return Path(path).read_text(encoding="utf-8")


def main() -> None:
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

    github_context = read_value(args.github_context, args.github_context_path, "github context")
    github_token = read_value(args.github_token, args.github_token_path, "github token")
    codex_auth = read_value(args.codex_auth_json, args.codex_auth_json_path, "codex auth json")
    codex_id_rsa = read_value(args.codex_id_rsa, args.codex_id_rsa_path, "codex id rsa")

    (out_dir / "github_context.json").write_text(github_context, encoding="utf-8")
    (out_dir / "github_token.txt").write_text(github_token, encoding="utf-8")
    (out_dir / "auth.json").write_text(codex_auth, encoding="utf-8")
    id_rsa_path = out_dir / "id_rsa"
    id_rsa_path.write_text(codex_id_rsa, encoding="utf-8")
    id_rsa_path.chmod(0o600)


if __name__ == "__main__":
    main()
