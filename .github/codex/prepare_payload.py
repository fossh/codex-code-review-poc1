#!/usr/bin/env python3
"""Build a GitHub review payload from Codex output."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--context-path", required=True)
parser.add_argument("--token-path", required=True)
parser.add_argument("--review-path", required=True)
parser.add_argument("--payload-path", required=True)
parser.add_argument("--validation-error-path", required=True)
args = parser.parse_args()


error_path = Path(args.validation_error_path)


def fail(message: str) -> None:
    error_path.write_text(str(message), encoding="utf-8")
    raise SystemExit(message)


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def parse_repo_info(context: dict) -> tuple[str, str]:
    repo_full = context.get("repository")
    owner = ""
    repo = ""
    if isinstance(repo_full, str) and "/" in repo_full:
        owner, repo = repo_full.split("/", 1)
    event = context.get("event") or {}
    if not owner:
        owner = context.get("repository_owner") or event.get("repository", {}).get("owner", {}).get(
            "login", ""
        )
    if not repo:
        repo = event.get("repository", {}).get("name", "")
    if not owner or not repo:
        raise ValueError("Unable to determine repository owner/name from context.")
    return owner, repo


def parse_pr_info(context: dict) -> tuple[int, str, str, str]:
    event = context.get("event") or {}
    pr = event.get("pull_request") or {}
    pr_number = pr.get("number") or event.get("number")
    if not pr_number:
        raise ValueError("Unable to determine pull request number from context.")
    base_sha = (pr.get("base") or {}).get("sha") or ""
    head_sha = (pr.get("head") or {}).get("sha") or context.get("sha") or ""
    head_repo = (pr.get("head") or {}).get("repo") or {}
    head_clone_url = head_repo.get("clone_url") or ""
    return int(pr_number), base_sha, head_sha, head_clone_url


def ensure_commit(sha: str, fallback_url: str | None = None) -> None:
    if not sha:
        return
    try:
        subprocess.run(
            ["git", "cat-file", "-e", sha],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["git", "fetch", "--no-tags", "origin", sha],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            if not fallback_url:
                raise
            subprocess.run(
                ["git", "fetch", "--no-tags", fallback_url, sha],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def build_positions(diff_text: str) -> dict[str, dict[int, int]]:
    positions: dict[str, dict[int, int]] = {}
    current_path = None
    position = 0
    new_line = None
    diff_re = re.compile(r"^diff --git a/(.+) b/(.+)$")
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for raw in diff_text.splitlines():
        diff_match = diff_re.match(raw)
        if diff_match:
            current_path = None
            position = 0
            new_line = None
            b_path = diff_match.group(2)
            if b_path == "/dev/null":
                continue
            current_path = b_path
            positions.setdefault(current_path, {})
            continue

        if current_path is None:
            continue

        if raw.startswith("@@ "):
            position += 1
            hunk_match = hunk_re.match(raw)
            new_line = int(hunk_match.group(1)) if hunk_match else None
            continue

        if raw.startswith("+++ ") or raw.startswith("--- "):
            continue

        if raw.startswith("\\"):
            position += 1
            continue

        prefix = raw[:1]
        if prefix in (" ", "+", "-"):
            position += 1
            if prefix in (" ", "+") and new_line is not None:
                positions[current_path][new_line] = position
                new_line += 1
            continue

    return positions


def extract_review_json(raw_text: str) -> dict:
    start_token = "BEGIN_REVIEW_JSON"
    end_token = "END_REVIEW_JSON"
    start = raw_text.rfind(start_token)
    if start == -1:
        raise ValueError("Missing BEGIN_REVIEW_JSON marker in codex output.")
    start += len(start_token)
    end = raw_text.find(end_token, start)
    if end == -1:
        raise ValueError("Missing END_REVIEW_JSON marker in codex output.")
    json_text = raw_text[start:end].strip()
    if not json_text:
        raise ValueError("Empty JSON block in codex output.")
    json_text = json_text.replace("***", "")
    first_brace = json_text.find("{")
    last_brace = json_text.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        raise ValueError("No JSON object found inside review block.")
    json_text = json_text[first_brace : last_brace + 1]
    return json.loads(json_text)


try:
    context = load_json(args.context_path)
    token = read_text(args.token_path).strip()
    raw_review = read_text(args.review_path)
    review = extract_review_json(raw_review)
except Exception as exc:
    fail(str(exc))

owner, repo = parse_repo_info(context)
pr_number, base_sha, head_sha, head_clone_url = parse_pr_info(context)

if head_clone_url and head_clone_url.startswith("https://"):
    auth_head_clone_url = head_clone_url.replace(
        "https://", f"https://x-access-token:{token}@"
    )
else:
    auth_head_clone_url = ""

ensure_commit(base_sha)
ensure_commit(head_sha, fallback_url=auth_head_clone_url or None)

if base_sha and head_sha:
    diff_args = ["git", "diff", "--no-color", "--unified=3", f"{base_sha}...{head_sha}"]
else:
    diff_args = ["git", "diff", "--no-color", "--unified=3", "HEAD~1...HEAD"]

diff_text = subprocess.check_output(diff_args, text=True)
positions = build_positions(diff_text)
file_positions_cache: dict[str, dict[int, int]] = {}


def position_for(path: str, line: int) -> int | None:
    pos = positions.get(path, {}).get(line)
    if pos:
        return pos
    if path in file_positions_cache:
        return file_positions_cache[path].get(line)
    if base_sha and head_sha:
        file_args = [
            "git",
            "diff",
            "--no-color",
            "--unified=10000",
            f"{base_sha}...{head_sha}",
            "--",
            path,
        ]
    else:
        file_args = [
            "git",
            "diff",
            "--no-color",
            "--unified=10000",
            "HEAD~1...HEAD",
            "--",
            path,
        ]
    try:
        file_diff = subprocess.check_output(file_args, text=True)
    except subprocess.CalledProcessError:
        file_diff = ""
    file_positions_cache[path] = build_positions(file_diff).get(path, {})
    return file_positions_cache[path].get(line)


raw_event = str(review.get("event", "COMMENT")).upper()
event = raw_event if raw_event in {"COMMENT", "REQUEST_CHANGES", "APPROVE"} else "COMMENT"

body = str(review.get("body", "")).strip()
if not body:
    fail("Review body is empty after parsing JSON.")

raw_comments = review.get("comments") or []
api_comments = []


def candidate_paths(value: str) -> list[str]:
    candidates = []
    if value:
        candidates.append(value)
    if value.startswith("./"):
        candidates.append(value[2:])
    if value.startswith("/"):
        candidates.append(value[1:])
    if value.startswith("a/") or value.startswith("b/"):
        candidates.append(value[2:])
    if value.startswith("github/"):
        candidates.append("." + value)
    if value.startswith(".github/"):
        candidates.append(value[1:])
    return [c for c in candidates if c]


for entry in raw_comments:
    if not isinstance(entry, dict):
        continue
    path = str(entry.get("path", "")).strip().strip("`\"")
    body_text = str(entry.get("body", "")).strip()
    try:
        line = int(entry.get("line"))
    except (TypeError, ValueError):
        continue
    if not path or not body_text:
        continue
    matched = False
    for candidate in candidate_paths(path):
        position = position_for(candidate, line)
        if not position:
            continue
        api_comments.append({"path": candidate, "position": position, "body": body_text})
        matched = True
        break
    if not matched:
        continue

findings = [
    line.strip()
    for line in body.splitlines()
    if line.strip().startswith("-") and "none" not in line.lower()
]
if findings and not raw_comments:
    fail("Findings present but no inline comments were provided.")
if raw_comments and not api_comments:
    fail("Inline comments could not be mapped to diff positions.")

payload: dict[str, object] = {"body": body, "event": event}
if head_sha:
    payload["commit_id"] = head_sha
if api_comments:
    payload["comments"] = api_comments

Path(args.payload_path).write_text(json.dumps(payload), encoding="utf-8")
