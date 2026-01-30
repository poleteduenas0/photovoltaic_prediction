# Getting Started

## 1. Environment Setup

Run the provided setup script:

```bash
bash scripts/setup.sh
source .venv/bin/activate
```

## 2. Project Layout

See the top-level README for structure overview. Core code lives in `src/`; tests in `tests/`.

## 3. Adding Code

If you are building an entire app, place your main application code in `src/your_project_code/`. This folder is intended for your project's core logic and functionality. Create modules inside `src/your_project_code/` (e.g., `src/your_project_code/ingest.py`). Add corresponding tests under `tests/` (e.g., `tests/test_ingest.py`).

## 4. Running Tests

```bash
pytest -q
```

## 5. Conventional Commits

Follow the simplified conventional commit rules outlined in `README.md` / `CONTRIBUTING.md`.

## 6. Using GitHub

1. Create an Issue (bug or feature) using templates
2. Create a branch `feature/<topic>` or `fix/<topic>`
3. Commit changes (small, focused commits)
4. Open a Pull Request (even if solo) to get CI run
5. Merge after green tests & self-review

## 7. Optional Enhancements

Add linters, type checking, coverage, or Dependabot only when justified by project scope.

---
Stay lean: automate only after repetition proves the need.
