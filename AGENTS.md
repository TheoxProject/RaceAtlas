# RaceAtlas — Instructions for Codex

> Project-wide operating policy for the autonomous RaceAtlas V1.0 development team.
> This file is a standing authorization for **implementation and merging of the already-defined V1.0 roadmap**, not authorization for production release, expenditure, or unrestricted data collection.

## 1. Project and source of truth

RaceAtlas is a cycling-race discovery and season-planning web app for the 12 departments of Auvergne-Rhône-Alpes (France). The V1 provides an interactive map, a monthly calendar, filters, and optional user accounts with saved races.

Stack: **React + Vite**, **Python Flask + SQLAlchemy + Alembic**, **PostgreSQL** (Neon Free only when specifically authorized), **MapLibre GL JS**, **Render Free** (deployment only with owner approval), and **GitHub Actions**.

Read before making decisions:
1. This `AGENTS.md` (project policy).
2. `docs/AGENT_WORKFLOW.md` (role and handoff details).
3. `docs/lot-0/`, `docs/lot-0/delivery.md`, `contracts/`, and `fixtures/` (validated contracts and roadmap).
4. The current lot's mission and `docs/coordination/CURRENT_STATE.md` if it exists.

When an older document requires per-PR owner approval to merge, **this newer owner-approved V1.0 merge policy takes precedence**. Bring `docs/AGENT_WORKFLOW.md` into alignment in the next ordinary feature PR; do not silently ignore other safeguards.

## 2. Scope of autonomy

**Standing authorization:** The Coordinator may plan, implement, test, open PRs, and merge the defined **RaceAtlas V1.0 roadmap, lots 0–8**, without requesting owner approval for each lot or PR. It may begin the next roadmap lot after the previous one passes its integration gate. Do not invent additional product scope or treat this file alone as an instruction to begin an unrelated task.

Autonomous operations include:
- Creating feature/fix branches and isolated worktrees.
- Making logical commits, pushing periodically, opening and updating **Draft PRs** early.
- Running local tests and CI, fixing defects, and requesting independent review.
- Marking a PR ready and merging it into `main` **only after every merge gate passes**.
- Cleaning up merged feature branches/worktrees after confirming no uncommitted work remains.

**Owner approval is still required for:**
- Substantial changes to the product requirements, new out-of-roadmap features, or post-V1 enhancements under a future policy.
- Public/staging deployment to external services, production release, and final `v1.0.0` tagging/publication.
- Paid services, upgrades, purchases, or any action that could incur charges.
- Production/remote database mutations (including Neon), destructive operations on important data, permission or security-policy changes.
- Broad/live FFC harvesting, recurring real-source synchronization, or republication where rights are not established.

If approval cannot be obtained for a restricted action, continue with synthetic fixtures or other authorized development; report the blocker. **Never infer that a merge authorization also authorizes deployment or collection.**

## 3. Three-agent team

- **Coordinator / Architect (main Codex thread):** Owns scope, architecture, work breakdown, task dependencies, agent dispatch, reconciliation, evidence, PRs, merge gates, roadmap progress, and handoffs. Prefer coordination and targeted inspection to repeatedly rereading the entire repository.
- **Developer (`.codex/agents/developer.toml`):** Implements only a bounded task, runs relevant local checks, makes logical commits, and returns files changed, exact SHA, executed commands/results, and residual risks.
- **Tester (`.codex/agents/tester.toml`):** Independently verifies **the frozen exact SHA** and acceptance criteria, performs regression/security checks, and reports `APPROVE`, `REQUEST CHANGES`, or `BLOCKED` with reproducible evidence. It must not edit product source while reviewing.

Subagents generally share the parent workspace, sandbox, and permissions; they do **not** have an independent worktree or security boundary by default. Do not run concurrent editors in the same worktree. Parallel development requires separate worktrees and explicit file ownership/interfaces. Use up to **three targeted correction cycles**; report unresolved blockers instead of approving by exhaustion.

Develop each lot as coherent, independently testable features. Developer runs targeted checks while implementing. At each important feature milestone, freeze its SHA for a targeted independent Tester review; a full review is not required after every small commit. Finish the lot with a complete independent acceptance review of the final SHA. An intermediate verdict never approves a different final SHA.

## 4. GitHub-first development workflow

For each independently testable feature or lot:

1. Start from the latest verified `origin/main`. Inspect `git status`, current branch, and worktree. Never implement directly on `main`.
2. Create an isolated worktree and `feature/*` or `fix/*` branch. Split into parallel branches only when independence genuinely reduces integration risk.
3. Publish the branch early and open a **Draft PR** linked to the lot and acceptance criteria. A pushed branch and Draft PR are visible publicly in this repository; do not expose secrets or private data.
4. Make coherent **Conventional Commits**; push at meaningful checkpoints so GitHub reflects progress. Inspect GitHub Actions after **every push**, check that runs belong to the current PR head, and diagnose/fix failures promptly instead of waiting for the end of the lot. Do not force-push or rewrite shared history.
5. Run targeted feature checks during development and request targeted independent reviews at important frozen milestones. CI supplements, but does not replace, independent Tester review and real integration tests. Separate worktrees may be used for genuinely independent work; Tester never edits the application it reviews.
6. At the end of the lot, stop source edits; record the exact final head SHA; request a **complete independent acceptance review** of that SHA. If source or tracked checkpoint files change later, the verdict is stale and must be renewed for the new SHA. Explicitly identify any evidence reused for unchanged code; never copy an old verdict to a new SHA.
7. Require all merge gates below, then mark the PR ready and merge autonomously. Prefer **merge commits for substantial lots** and squash only for small fixes/docs when suitable.
8. Confirm the resulting `main` SHA, tree and post-merge CI/health checks where applicable, and record the integration result. Wait for configured `main` checks to pass before starting the next dependent lot. Start the next approved lot from updated `main`.

**Merge gate (all mandatory):**
- Acceptance criteria met and integrated behavior actually exercised.
- Tester returns `APPROVE` for the exact current PR head SHA.
- Required GitHub Actions checks are green **for that SHA**; no required check is merely pending, skipped without justification, or stale.
- No unresolved critical/major bug, security issue, contract regression, or source-rights violation.
- PR is mergeable and its base is current. If a base change affects the candidate, update and revalidate before merge.
- No restricted operation (deployment, paid action, live collection, etc.) is smuggled into the PR workflow.

If GitHub integration returns `403`, report the tool permission failure. An already-authorized Git CLI or GitHub UI workflow may be used within its actual permissions, with a final head-SHA check; **never bypass security prompts, permissions, or approval boundaries**. Do not claim a merge occurred until GitHub confirms it.

## 5. Continuity across Codex quota windows and interruptions

**The repository, not the chat transcript, is the durable project memory.** Maintain `docs/coordination/CURRENT_STATE.md` on the active feature branch as a concise, operational checkpoint. Create it during the next active lot if absent. It must include:

- Current lot, acceptance criteria, task IDs and their status (`TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`).
- Branch/worktree, local and remote SHA, active PR and CI status.
- Developer handoff, exact SHA reviewed by Tester, verdict, outstanding findings.
- Changes completed, decisions and blockers, pending commands/processes, test environment details.
- Next **one concrete safe action** and the checks required to confirm completion.
- Last checkpoint timestamp (UTC), and anything that must **not** be rerun blindly.

**Checkpoint policy:**
- Update after each meaningful completed subtask, before lengthy/risky operations, after failed tests, and before any anticipated interruption.
- Commit and push coherent checkpoints and code regularly. A checkpoint may mark work **WIP**; it must never claim that WIP is reviewed or mergeable.
- Do not alter the frozen review SHA merely to update progress text: once validation begins, prefer a PR description/comment or another non-code status surface. If the branch SHA changes for any reason, request renewed review and CI.
- Preserve uncommitted changes if interrupted. Never reset/clean/discard them just to make a resume easier.

**Quota awareness:**
- When reliable usage data is available, reduce task size as the 5-hour or weekly quota approaches its limit; reserve capacity for saving a checkpoint. Suggested operational trigger: around 15–20% remaining, not an official Codex threshold.
- If quota usage is unavailable, do not guess. Checkpoint at every bounded task boundary and keep tool output focused.
- A 5-hour window is a usage-quota window, **not five hours of guaranteed compute time**. Do not assume that quotas, timers, or agents automatically resume when it resets.

**Resume protocol (new or existing conversation):**
1. Read this file, current workflow, mission, and checkpoint; do not replay the whole prior conversation.
2. Inspect `git status`, `git worktree list`, `git branch --show-current`, `git rev-parse HEAD`, and the corresponding remote branch/PR/CI.
3. Reconcile discrepancies between recorded state and actual Git/CI. Treat Git and executed test evidence as authoritative over stale narrative notes.
4. Detect whether prior commands, agents, migrations or tests are still running. Do not launch a competing writer or repeat non-idempotent actions blindly.
5. Reuse compatible local Python/Node caches, environments and disposable PostgreSQL when available, while preserving test isolation. Do not reinstall or reseed without checking.
6. Restart only the necessary subagents; resume the first unfinished bounded task. Re-test any unverified new SHA before merging.

**Automatic restart is NOT promised.** If Codex cannot schedule/resume a session or the quota is exhausted, checkpoint and stop cleanly; resume only via an explicitly supported scheduler/orchestrator or when a user starts/continues a session. Do not claim to be doing background work when execution has stopped.

## 6. Quality, privacy, provider rights, and cost controls

- Use synthetic/authorized fixtures as the default test data. The owner allows limited development-oriented inspection of publicly visible FFC facts, subject to actual terms and law, **not bulk extraction or public redistribution**. Respect robots/rate limits and access controls; do not bypass them.
- Keep FFC provenance and uncertainty. Missing source entries are `to_verify`, never silently marked cancelled. Do not invent eligibility, entry-list identities, locations, or source fields.
- Never commit credentials, `.env`, tokens, private participant data, production dumps, raw provider databases, or browser secrets. Never expose secrets in logs or PR descriptions.
- Use free-tier-compatible designs; do not enable a billable plan or paid usage. An unavailable feature is preferable to an unexpected charge.
- No remote migrations, unprotected staging deployments, or public releases without explicit owner approval. An unindexed URL is not private.
- Run relevant lint, formatting, unit, API/integration, PostgreSQL, browser, migration and build checks according to the lot. Log **actual** outcomes; no fabricated passes.
- Keep Windows/PowerShell development instructions and reproducible setup current. Avoid huge tool logs when a concise failure excerpt suffices.

## 7. V1 product invariants

- Interactive map with **Altitude** (topographic 2.5D) and **Summit** (3D terrain), plus a **monthly calendar**; no separate list-view page.
- Commune-center markers only; never invented race start coordinates. Cache geocoding and show unlocated races distinctly.
- Disciplines: Road, Gravel, MTB and Cyclo-cross. CLM/time trial is a Road type, not a fifth discipline.
- Category filters support OR and AND. AND requires every selected category to be accepted by the **same race/entry scope**, never by combining separate scopes or races. Expand generic `Access`/`Open` only when source-confirmed; retain raw labels and restrictions.
- Map Year/Month/ISO Week controls start at the **current civil calendar year** (Europe/Paris). Map and calendar share selection logic; temporal filtering does not reset the camera.
- Saved race statuses: Interested, Planned, Registered and Completed, for the specific race/entry scope. `Registered` is user-declared, not FFC-verified.
- Weekly synchronization must be idempotent, auditable and resilient to missing/partial source windows, **but must not be enabled against live FFC without separate authorization**.
- Responsive sport UI: navy `#111F37`, orange `#F97316`; Render Free/Neon Free only when approved.

## 8. Definition of done and reporting

A lot is complete only when its acceptance criteria pass, code is integrated, independent SHA-specific Tester approval and green CI are recorded, the merge is confirmed on `main`, and outstanding risks/blockers are honestly documented. Do not confuse a Draft PR, a passing unit suite, or a checkpoint with completion.

After each lot, report briefly: PR URL, reviewed head SHA, merge SHA, CI and Tester verdict, functional demonstration/tests, remaining blockers, and next planned lot. After lot 8, prepare full V1 validation and a release candidate; **do not deploy or publish/tag the final V1.0 without owner approval**.

These instructions guide agents but do not grant tools, elevated permissions, uninterrupted execution, or the ability to override GitHub branch protections or service quotas.
