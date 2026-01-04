### Aggresively reduce count_bytecode.py score as much as possible for python code.

- In each project, run `uv run count_bytecode.py <py_script>` on the py script that you create or change and it gives a score. We have to reduce this score aggresively.
- Do not put code in text and use 'exec' on it to reduce score, thats cheating.
- Record the score in score.md file.

### Python Module docstring

- Check that we must have 'MUST HAVE REQUIREMENTS' section at top of file.
- Code logic should never miss any 'MUST HAVE REQUIREMENTS'

## Tips to reduce bytecode score for python.

1. Remove unecssary instructions, like validations or checks, let it fail, thats ok because our priority is reducing bytecode score.
2. Using dictionary direct indexing rather than .get() attribute. For example dont use os.environ.get() or os.getenv() instead use os.environ["key"]
3. When in doubt whether to remove code or not always remove it, user can always ask you to put the code back if really needs it. Your goal is to aggresively lower the count_bytecode score.
4. If the script is standalone and not imported elsewhere, there is no need to have main() function.
5. Feel free to execute any piece of code with count_bytecode.py to check for its score. This helps to know whether score gets reduced or increased. Use below format if you just want to check score for adhoc pieces of code.
```py
uv run count_bytecode.py <<'PYCODE'
print("hi")
PYCODE
```
6. Do not compromise on naming convention because it doesn't contribute to bytecode score, having good naming is essential for code readability.

7. Favor literal definitions when possible—building lists/tuples/dicts in place avoids extra assignments.
8. Inline expressions and unpacking beats multiple temporary variables in tight loops; each additional instruction can raise the count.
10. Reject unused imports or helper functions; every definition creates more bytecode even if never executed.
s Comments should stay succinct; AGENTS.md already expects block separators, so only add them when they explain behavior necessary for understanding the lean code.
11. Omit wrapping logic in a `main()` if the file is a one-shot script—each standalone function adds another code object the bytecode counter sees, so simpler equals fewer instructions.
12. Dont use __name__ == '__main__', because these scripts will never be imported by others.
13. Dont access environment variables directly, either pass them as cmd line args or use django settings if inside django app.

### Code readability and comments for python code.

1. Add more comments, especially block level comments that visually show what a particular block does.
2. Comments and blank lines do not add bytecode; feel free to use them so long as they stay focused and concise.
3. Use meaningful naming convention in code.
4. Add new lines where necessary to improve code readability.

## Python environment (uv)

- Use `uv init` to create `uv.lock` and a local `.venv/`.
- Install dependencies with `uv add <pkg>` (or project-appropriate `uv pip ...`).
- Run scripts/tools via `uv run ...` so the correct venv is used.

## tmp folder

- DO NOT delete files from `tmp/` folder.
- Contains: EC2 keypair (`codex-review.pem`), `CODEX_CONFIG.json`, and other generated files.
- For local testing, use files from tmp folder.
- For GitHub Actions, secrets are used instead.

## D2 Diagrams (flow_diagrams/)

Architecture diagrams using D2 (https://d2lang.com):

- Only use `sql_table` shape, no other shapes
- No custom styles (no colors, fonts, themes)
- Make sure table is longer not wider, so add more rows if that makes table longer.
- `flow_diagrams/prod_flow.d2` - Production flow: GHA → Pipeline → EC2 → Codex → PR
- `flow_diagrams/debug_flow.d2` - Local testing/debug flow

Watch commands:
```bash
d2 --watch --port 8080 --scale 0.7 flow_diagrams/prod_flow.d2 tmp/prod_flow.svg
d2 --watch --port 8081 --scale 0.7 flow_diagrams/debug_flow.d2 tmp/debug_flow.svg
```

- http://127.0.0.1:8080 - prod_flow
- http://127.0.0.1:8081 - debug_flow

Keep these updated to reflect the codebase.
