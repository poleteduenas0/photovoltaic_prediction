# Copilot Prompts: Documentation & Tests

These prompts are designed to be pasted into **Copilot Chat** in **Visual Studio Code** (ideally with `@workspace` context) to (1) scan your repository and create/update documentation/READMEs, and (2) create/update tests to maximize coverage **without changing business logic**.  
Each prompt includes **“ask-before-creating-files”** behavior and proposes alternatives where possible.

---

## Index

- [Repository Documentation & READMEs](#repository-documentation--readmes)
- [Tests Overhaul for Coverage & Edge Cases](#tests-overhaul-for-coverage--edge-cases)

- [Repository Documentation & READMEs — No Context Provided](#repository-documentation--readmes--no-context-provided)
- [Tests Overhaul for Coverage & Edge Cases — No Context Provided](#tests-overhaul-for-coverage--edge-cases--no-context-provided)

---

## Repository Documentation & READMEs

```text
#workspace #git
[Task: Documentation Overhaul Focused by Provided Context]

Context from me (scope, changes, priorities, style expectations):
<PASTE YOUR CONTEXT HERE
    Examples:
    - What changed recently and why
    - Files/modules/packages most affected
    - Intended audience (internal/external), tone (concise/teaching), and preferred docstring style (Google/NumPy/reST/JSDoc)
    - Sections I care most about (quickstart, env vars, architecture, troubleshooting, release notes)
    - Diagrams allowed? (Mermaid yes/no, Recomended: yes)
>

Goals:
- Focus first on areas mentioned in my context to update READMEs, docs, and inline docstrings/comments WITHOUT changing code behavior.
- Add/refresh sections: project overview, install, configuration/env vars, usage examples (CLI/API), architecture overview, troubleshooting, known limitations; for monorepos—ensure each package has a minimal README pointing to the root.
- Keep edits minimal, safe, and consistent with existing style and tooling.

Guardrails:
- Ask me BEFORE creating any new file/dir (e.g., docs/architecture.md). For each request, include: exact path/name, purpose, outline (H2/H3), a short stub/preview, justification, and an ALTERNATIVE that avoids creating a file (e.g., add a section to an existing README).
- Do NOT rename/move files, change public APIs, or alter licensing. No new dependencies/services without prior approval and a no-new-dependency alternative.
- Respect existing docstring/comment style. If mixed/unclear, propose a standard and ask before applying.

Process & Output Format:
0) Read my context; list inferred priorities and unknowns.
1) Targeted scan: inventory current docs footprint in the modules/packages I named (and immediate dependencies).
2) Plan & batched questions: propose a concise plan; bundle all clarifying questions to minimize back-and-forth.
3) Proposed changes (no file creation yet): show unified diffs for README/docs updates and inline docstrings/comments; include a short rationale per diff.
4) File Creation Requests (if needed): provide path, outline, short stub, justification, plus an alternative.
5) After approval: apply changes; show final diffs; propose conventional commit messages (e.g., docs: update README for <module>; docs: add NumPy-style docstrings in <pkg>).

Deliverables:
- Diffs for updated READMEs/docs and inline docstrings/comments.
- Optional ToC for long docs (ask first if large).
- Commit message suggestions.

Begin with Step 0 and Step 1 based on my context above.

```

## Tests Overhaul for Coverage & Edge Cases

```text
#workspace #git
[Task: Tests Expansion Focused by Provided Context]

Context from me (scope, changes, priorities, constraints):
<PASTE YOUR CONTEXT HERE
    Examples:
    - What modules/functions/classes changed and expected behaviors
    - Edge cases, failure modes, or regressions I’m worried about
    - Runtime constraints (CI time), flakiness concerns, external services to avoid/mocking policy
    - Coverage target (e.g., 90% lines + meaningful branch coverage) for the affected areas
    - Frameworks in use (pytest/jest/junit/…), fixtures policy, property-based tests allowed? (only if already available)
>

Goals:
- Expand and improve tests for the areas I named to maximize coverage of lines/branches/critical paths and to validate edge/boundary/error cases, concurrency/IO/time as applicable.
- Do NOT change the business logic of existing tests. You may add parametrizations, assertions, fixtures/utilities, or refactor structure, but keep the intent of what is validated intact. If a test is objectively wrong, PAUSE and ask with justification.
- Do NOT change production code unless a confirmed bug is found; if found, pause and ask.

Guardrails:
- Ask BEFORE creating any new files (new test modules, fixtures, golden/snapshot data). For each request: path, purpose, outline/skeleton, a short draft, justification, and an alternative that avoids creating a file (e.g., extend an existing test file via parametrization).
- Ask BEFORE adding/changing dev dependencies (e.g., hypothesis, coverage plugins). Provide rationale, impact, and a no-new-dependency alternative.
- Keep test runtime reasonable; if heavy tests are needed, mark appropriately per repo conventions.

Process & Output Format:
0) Read my context; list inferred priorities, risk areas, and unknowns.
1) Targeted test scan & coverage baseline: describe current frameworks/fixtures in the affected areas; identify critical gaps; estimate current vs. target coverage for those modules.
2) Plan & batched questions: propose a prioritized plan to reach my stated target with minimal disruption; bundle questions (runtime limits, integration/E2E boundaries, mocking strategy).
3) Proposed diffs to existing tests (no new files yet): add parametrizations, more assertions, boundary/error cases, and concurrency/time cases if relevant—while preserving test intent. Show unified diffs with a short rationale per change.
4) File Creation Requests (if needed): present path, outline or code skeleton, short draft, justification, and an alternative that avoids a new file.
5) Coverage & follow-up: explain how to run coverage locally with existing tools/config; estimate expected coverage gains per module after changes. Then propose conventional commit messages (e.g., test: expand edge cases for <module>; test: parametrize <function> scenarios).

Deliverables:
- Test plan and batched questions.
- Diffs enhancing existing tests (no business-logic changes to what they validate unless explicitly approved).
- Any file creation or dependency change requests (with alternatives).
- Coverage run instructions and expected improvements.

Begin with Step 0 and Step 1 based on my context above.

```

## Repository Documentation & READMEs — No Context Provided

```text
[Task: Repository Documentation & READMEs Overhaul]

Goals:
- Inventory all documentation across the repo (README(s), docs/, wiki references, package-level READMEs).
- Improve/standardize READMEs: add project overview, quickstart, installation, configuration/env vars, usage examples, CLI/API examples, architecture overview, dependency graph summary, troubleshooting, known limitations, release/compatibility matrix, badges, and contribution pointers.
- Add or update inline docstrings and comments without changing semantics.
- If present: generate/refresh API docs sections from source (include usage snippets).
- For monorepos: ensure each package/module has a minimal README with usage and links up to the root.

Constraints:
- Do not change code behavior. Inline docs only.
- Ask before creating any new files (e.g., /docs/architecture.md), and provide an alternative (e.g., fold into root README).
- Follow repo’s docstring style (Google / NumPy / reST / JSDoc / XML doc). If unclear, propose and ask.
- Do not rename/move files, change public APIs, or alter licensing without explicit approval.
- Don’t add new dependencies or services. If you believe one is needed, ask first with rationale and a no-new-dependency alternative.

Process:
1) Repo scan & inventory:
   - Map languages, frameworks, modules/packages, and current docs footprint.
   - Identify missing or outdated sections.

2) Plan & questions:
   - Present a concise plan to update docs.
   - Batch any questions (docstyle, preferred sections, glossary, audience level, diagrams allowed?).

3) Propose diffs (no file creation yet):
   - For each README/doc to be updated, show unified diffs.
   - For inline docstrings/comments: list files with proposed patches.
   - Include short rationale per diff.

4) File Creation Requests (if needed):
   - For each new file, propose: exact path (e.g., docs/architecture.md), outline (H2/H3 headings), and a short content preview or stub.
   - Justify why a new file is preferable and offer an alternative (e.g., new section in existing README).

5) After approval:
   - Apply changes, show final diffs, and propose conventional commit messages (e.g., docs: improve root README; docs: add module docstrings).

Deliverables:
- Updated READMEs and docs diffs.
- Inline docstrings/comments diffs.
- Optional: generated Tables of Contents for long docs.
- Optional: badge suggestions (build, test coverage, code style) without adding services unless accepted.

Begin with Step 1: Repo scan & inventory. Then provide Step 2 with a plan and batched questions.

```

## Tests Overhaul for Coverage & Edge Cases — No Context Provided

```text
[Task: Tests Overhaul for Coverage & Edge Cases]

Goals:
- Inventory current test layout, frameworks, fixtures, utilities, and CI integration.
- Improve and expand tests to maximize coverage (lines/branches/functions) and capture edge cases, concurrency, IO, time, error paths, and boundary conditions.
- Do NOT modify the business logic of existing tests; you may refactor structure, add parametrizations, add more assertions, introduce better fixtures/utilities, or switch test utilities—but do not change the “if/then” logic of what the test is verifying unless strictly required (e.g., the test is objectively wrong). If you believe a change is required, ask first with justification.
- Do not change production code unless a confirmed bug is found; if found, pause and ask.

Constraints:
- Ask before creating new files (e.g., new test module, fixtures, golden files).
- Ask before adding/changing dev dependencies (property-based testing, coverage tools).
- Prefer in-place enhancements: parametrization, hypothesis/property-based cases (if already available), mocks/fakes, boundary-value tests, negative tests, and concurrency tests (if applicable).
- Keep test runtime reasonable; mark heavy tests appropriately (e.g., @slow) if conventions exist.
- Do not rename/move files or alter CI config without explicit approval.

Process:
1) Repo test scan & coverage baseline:
   - Describe existing frameworks (e.g., pytest/jest/junit/xUnit/go test).
   - Identify untested/under-tested modules and critical paths.
   - Propose a target coverage (default suggestion: 85–95% lines and meaningful branch coverage), and list the highest-value areas to focus first.

2) Plan & questions (batched):
   - Confirm coverage target, test runtime constraints, integration/e2e boundaries, and whether to include property-based or fuzz tests.
   - Ask before proposing any new files or dev dependencies.

3) Propose diffs to existing tests:
   - Add parametrizations and additional assertions.
   - Cover error handling, boundary values, and edge cases.
   - Keep test “intent” the same (no change to business logic of what is validated).
   - Show unified diffs and rationales.

4) File Creation Requests (if needed):
   - For each new test file/fixture/util, propose path, outline, draft, justification, and an alternative (e.g., put new tests into existing file via parametrization).
   - Do the same before introducing data files (golden/snapshot) or mocks.

5) Coverage report & follow-ups:
   - Explain how to generate a coverage report locally using existing tools/configs.
   - After approval and application, report expected coverage improvements per module.

Deliverables:
- Test plan and batched questions.
- Diffs to existing tests (no logic changes to what they validate unless approved).
- Optional new test files/fixtures requests with justification and alternatives.
- Coverage run instructions and expected gains.
- Conventional commit messages (e.g., test: expand edge cases for module X; test: add parametrized cases for Y).

Begin with Step 1: repo test scan & coverage baseline. Then present Step 2 with a plan and batched questions.

```