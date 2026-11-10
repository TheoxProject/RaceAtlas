# RaceAtlas — Project Instructions for Codex

## Project
RaceAtlas is a web application for discovering and planning cycling races. V1 covers the 12 departments of Auvergne-Rhône-Alpes, France; other regions may follow. The interface is public for browsing, with optional accounts for saved races and personal tracking.

Planned stack (do not scaffold until assigned): React + Vite, Python Flask + SQLAlchemy, Neon PostgreSQL, MapLibre GL JS, Render, and GitHub Actions for scheduled imports.

## Universal working rules
- Only work on the explicitly assigned task. If scope or acceptance criteria are unclear, report the ambiguity rather than implementing unrelated features.
- Treat `main` as stable. Do not edit, commit, reset, force-push, or merge into `main` as an agent. Feature code belongs in a dedicated worktree and `feature/*` or `fix/*` branch. The repository owner authorizes integration.
- Keep commits small, logically coherent, and descriptive (e.g. `feat(map): add race markers`). Prefer one pull request per independently testable feature. Do not rewrite published history or force-push.
- Do not silently overwrite other agents' changes. Use Git branches, pull requests, and written handoffs. Never assume concurrent Codex chats share task context.
- Keep changes minimal and explain important technical choices and trade-offs. Avoid unnecessary frameworks, dependencies, or speculative infrastructure.
- Do not claim a test passed unless it was executed. Report the exact command and its outcome; if it could not run, state why.
- Add or update automated tests for changed behavior where practical. Regression tests are especially important for import idempotency, date handling, filtering semantics, authentication, and persistence.
- Never commit secrets, credentials, `.env` files, personal data, or production data. Never expose API keys or database credentials in logs or responses.
- Do not deploy publicly, enable paid services, modify live databases, or import/publish actual FFC data without explicit authorization from the repository owner. Use synthetic or duly authorized fixtures during development.
- Ask for approval before destructive commands, schema changes affecting stored data, permissions changes, or changes to security-sensitive configuration.

## Roles and handoffs

### Coordinator / Architect (local project)
- Define the scope, technical boundaries, interfaces, task dependencies, acceptance criteria, and Git branch names.
- Delegate bounded tasks to Developer and independent verification to Tester via explicit task briefs; keep a concise written record of decisions, branch/commit identifiers, and results.
- Review tests and changes before recommending a pull-request merge. Never claim another agent has acted unless there is an observable result.
- Do not modify application code or merge/deploy unless the repository owner explicitly requests it.

### Developer (isolated worktree)
- Implement only the assigned functionality in a dedicated feature/fix branch. Include tests and documentation relevant to that change.
- Produce coherent commits and a pull request when ready; identify changed files, test results, assumptions, known limitations, and the commit SHA for Tester.
- Address verified defects on the same feature branch and request retesting.

### Tester (independent worktree)
- Inspect and test the exact commit or pull request supplied by the Coordinator/Developer, not an assumed current version of `main`.
- Run relevant checks, examine edge cases, and report reproducible findings with severity, steps, expected/observed results, and the tested commit SHA.
- Do not modify application source code or merge branches. Submit defects to Developer for correction; if a check cannot run, mark it as unverified.

## V1 product invariants (summary)
- One interactive map view with Altitude (topographic 2.5D) and Summit (3D terrain) modes, plus one monthly calendar view. Do not add a separate list page unless requested.
- Map markers represent the center of the event's commune, not a claimed exact start line. Cache geocoding; missing locations must remain visible in a clearly labeled exception list.
- The primary disciplines are Road, Gravel, MTB, and Cyclo-cross. Time trials (CLM) are a Road event type, not an independent discipline.
- Category filters support OR and AND. AND means that a single race/entry list admits all selected categories, not that categories can be combined across different races of one event. Generic `Access` means Access 1–4; generic `Open` means Open 1–3. Preserve raw source labels.
- The map has Year / Month / Week temporal controls and opens on the current calendar year. The calendar has a monthly view and an optional My Races mode for authenticated users.
- Saved race statuses: Interested, Planned, Registered, Completed; tracking is per specific race/entry list. Changes to saved events appear in in-app notifications. Do not assume user-entered registration has been verified by FFC.
- Weekly FFC synchronization must be idempotent, auditable, and resilient to missing events. A vanished source entry is 'to verify', not automatically canceled. Do not invent event details.
- Visual direction: modern, sporty, navy (`#111F37`) and orange (`#F97316`); responsive desktop/mobile layouts.

## Definition of done for each task
1. Scope and acceptance criteria are addressed without unrelated changes.
2. Relevant tests/lint/build are run if available; otherwise limitations are explicit.
3. No secrets or unauthorized third-party data are added.
4. Developer provides a commit/PR reference and brief handoff.
5. Tester reports independently on that exact revision.
6. Coordinator requests owner approval before integration into `main` or deployment.

This document supplies shared rules, not a replacement for a task-specific brief or for technical permission controls.
