# AGML GitHub Template

Lean, opinionated repository template for the Alimak Group Machine Learning Department. It balances simplicity (solo / pair contributors) with enough structure to keep work legible, testable, and easy to onboard.

> Use GitHub Projects (not in-repo roadmap files) to track roadmap, issues, releases, iterations. This repo only carries lightweight process & quality scaffolding.

## Quick Start

1. Create a new repo from this template (Use this template button)
2. Clone it
3. Run the setup script (creates venv, installs dependencies, editable install):

```bash
bash scripts/setup.sh
```

1. Start coding inside `src/` and add/modify tests in `tests/`
1. Run tests locally:

```bash
pytest -q
```

1. Commit using the conventional style (see below) and push; CI will auto-run if tests exist.

## Repository Structure

```
├── .github/                # Issue / PR templates, workflows
│   ├── ISSUE_TEMPLATE/     # Bug & feature templates
│   ├── pull_request_template.md
│   └── workflows/ci.yml    # Conditional test runner
├── docs/                   # Additional documentation (getting started, decisions)
├── scripts/                # Utility scripts (environment setup, maintenance)
├── src/                    # Source code (importable modules)
├── tests/                  # Pytest tests (mirrors src structure)
├── CONTRIBUTING.md         # How to work with this project
├── requirements.txt        # Runtime + dev dependencies (minimal initially)
├── pyproject.toml          # Minimal packaging metadata (editable install)
└── README.md               # This file
```

## Minimal Local Workflow

1. Create / activate virtual environment (script does this)
2. Add dependencies to `requirements.txt`
3. Implement feature in a short-lived branch (`feature/short-description`)
4. Add / update tests (aim for failing test first when practical)
5. Run `pytest -q`
6. Commit with conventional message
7. Open Pull Request (even if solo) to get CI evidence + history

## Conventional Commit Style (Simplified)

Format:

```text
<type>(optional-scope): short imperative summary

[Body - optional]

[Footer - BREAKING CHANGE: description]
```
Allowed `<type>` values:
`feat` new user feature
`fix` bug fix
`docs` documentation only
`test` tests only
`refactor` internal change w/o behavior change
`perf` performance improvement
`chore` build / tooling / infra (no src logic)
`ci` CI related change

Examples:

```text
feat: add ingestion pipeline skeleton
fix(parser): handle empty input lines
docs: clarify environment setup steps
refactor: extract common validation helper
chore: bump numpy to 2.x

feat!: remove legacy config support
fix(parser)!: change default parsing behavior
feat!: migrate to new API
BREAKING CHANGE: The old API endpoints are no longer supported.
```


Mark breaking changes with either `!` after the type or a `BREAKING CHANGE:` footer.

## Testing Guidelines

- Tests live under `tests/` mirroring the `src/` structure
- Name files `test_*.py`
- Keep tests isolated & fast (<1s preferred)
- Use pytest fixtures for shared setup instead of ad-hoc helper scripts

## CI Behavior

- Workflow triggers on pushes & PRs to main / master
- If no Python test files exist in `tests/`, the test job is skipped automatically
- Python versions: 3.11 & 3.12 (adjust in `ci.yml` if needed)
- Extend by adding steps (lint, type-check) later without breaking simplicity

## Documentation

Put lightweight internal docs into `docs/`:

- `getting-started.md` – environment + first-run
- `decisions/` – Architecture Decision Records (ADRs) when design choices matter (optional)

## Using GitHub Projects

1. Create (or link) a GitHub Project board for planning
2. Use issues (from templates) for tasks & bugs
3. Link PRs to issues using `Fixes #<issue-number>` or `Closes #<issue-number>`
4. Track milestones / releases directly in GitHub (no extra local files)

## Extending This Template (Optional Enhancements)

Add later only if needed (a minimal `pyproject.toml` already exists – extend it only when publishing or adding tooling):

| Need | Add |
|------|-----|
| Static lint | Ruff / Flake8 and step in CI |
| Type checking | mypy + CI step |
| Packaging metadata | Extend existing `pyproject.toml` |
| Coverage | `coverage.py` + upload to Codecov |
| Dependency updates | `dependabot.yml` |

## License

Add a suitable license file if code will be shared externally (none included by default).

---
Happy building! Keep it small, explicit, and well-tested.
