# Contributing Guide

Simple, consistent workflow for small (solo/pair) ML / Python projects.

## 1. Getting Started

1. Run `bash scripts/setup.sh` (creates venv & installs deps)
2. Activate environment: `source .venv/bin/activate`
3. Install any new deps by adding them to `requirements.txt` then `pip install -r requirements.txt`

## 2. Branching

Use short-lived branches:

```text
feature/<short-topic>
fix/<short-topic>
chore/<short-topic>
```

Examples: `feature/ingest-csv`, `fix/null-edge-case`.

## 3. Conventional Commits (Simplified)

Format:

```text
<type>(optional-scope): short imperative summary

[optional longer body explaining Why]

[optional BREAKING CHANGE: description]
```

Types: `feat` | `fix` | `docs` | `test` | `refactor` | `perf` | `chore` | `ci`.

Examples:

```text
feat: add ingestion pipeline skeleton
fix(parser): handle empty input lines
docs: add environment setup section
refactor: extract validation helper from loader
```

Breaking change indicator: either `feat!:` or a `BREAKING CHANGE:` footer.

## 4. Pull Requests (Even When Solo)

1. Ensure tests pass: `pytest -q`
2. Ensure new logic is covered by tests
3. Reference any issue: `Closes #12` (auto-closes on merge)
4. Keep PRs < ~400 LOC when possible
5. Use the PR template checklist

## 5. Tests

- Name files: `tests/test_<module>.py`
- Mirror `src/` structure for clarity
- Prefer fast, deterministic unit tests
- Use fixtures for shared setup (avoid global state)

Minimal example:

```python
# tests/test_example.py
from src.your_project_code.example import add

def test_add():
    assert add(2, 3) == 5
```

## 6. Code Style

This template intentionally starts minimal (no formatter or linter enforced). You may optionally add:

- Ruff (lint + format)
- Mypy (type checking)
- Black (formatting)

If you add tools, update CI accordingly.

## 7. Adding Dependencies

1. Add to `requirements.txt`
2. Re-run `pip install -r requirements.txt`
3. Commit both code and requirement change in same PR

## 8. Releasing

Use GitHub Releases (UI). Tag format suggestion: `vMAJOR.MINOR.PATCH`.

## 9. Documentation

Add internal docs under `docs/`. Consider an ADR (Architecture Decision Record) only when a decision is complex or irreversible.

## 10. Common Tasks

| Task | Command |
|------|---------|
| Run tests | `pytest -q` |
| Run single test | `pytest tests/test_example.py::test_add -q` |
| Install deps | `pip install -r requirements.txt` |
| Update deps (lightweight) | Edit file then reinstall |

## 11. FAQ

**Q: Can I commit directly to main?**  
Prefer a branch + PR so CI runs and history stays readable.

**Q: Large prototype code?**  
Commit early but mark it `chore(prototype): ...` and refactor quickly.

**Q: Data files?**  
Keep large data out of repo. Use storage buckets or DVC if needed (add later only if justified).

---
Thanks for keeping things clean & approachable.
