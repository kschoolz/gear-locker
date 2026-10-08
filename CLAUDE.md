# Working rules for this repo
I'm practicing schema/API design and AI-assisted coding. Keep me in control.

1. DESIGN.md is the source of truth. Implement exactly what its current stage says.
   If the code would differ from it, stop and tell me before writing code.
2. Do only what I asked. No extra endpoints, files, dependencies or refactors.
3. One bounded step at a time (~40 lines). Larger → propose a split and wait.
4. State assumptions in ≤3 bullets before code. Never invent requirements; ask.
5. Never write or change files in migrations/. I write the SQL.
6. After edits: list files changed, run `uv run pytest -q`, show the result.
7. Never commit or push. I do git.

## Tech
- FastAPI, sqlite3 from the standard library, raw SQL (no ORM).
- Every connection runs `PRAGMA foreign_keys = ON`.
- Status codes and errors exactly as in DESIGN.md. Errors return {"error": "<code>", "message": "..."}.
- Tests use FastAPI's TestClient with a fresh temporary database per test.
