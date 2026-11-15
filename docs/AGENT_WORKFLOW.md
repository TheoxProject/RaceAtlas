# RaceAtlas — Autonomous Codex agent workflow (V1.0)

> Detailed operating procedure for the **Coordinator / Developer / Tester** team.
> **`AGENTS.md` is the authoritative project-wide policy.** If these documents appear to conflict, follow the more restrictive safety rule and resolve the inconsistency in the next normal PR. The owner's standing approval covers implementation and **merging the defined V1.0 roadmap**; it does not cover deployment, payments, or unrestricted FFC collection.

## 1. Mission and scope

Deliver RaceAtlas V1.0 incrementally using the approved roadmap in `docs/lot-0/delivery.md` (lots 0–8), the contracts in `contracts/`, and the accepted product rules in `AGENTS.md`. After a lot passes its complete integration gate, the Coordinator may start the next **already defined** lot without requesting another owner approval.

This document grants no authorization to add unrelated features, change the substantive product specification, deploy externally, tag/publish final V1.0, run live recurring FFC harvesting, incur expenses, or alter real user/production data. Those actions require explicit owner approval. If blocked, continue with synthetic/authorized fixtures where safe and record the blocker.

## 2. Roles and boundaries

| Agent | Responsibility | Limits |
|---|---|---|
| **Coordinator / Architect** | Owns roadmap, task breakdown, architecture, interface contracts, GitHub PRs, checkpoints, validation gates, integration and factual progress reports | Does not bypass checks, approvals for restricted operations, permissions, or GitHub protections |
| **Developer** (`.codex/agents/developer.toml`) | Implements bounded tasks, tests locally, commits and pushes coherent increments, provides precise SHA and evidence | Modifies only the agreed scope; does not self-approve final delivery |
| **Tester** (`.codex/agents/tester.toml`) | Independently reviews the **exact frozen commit**, tests behavior and regressions, reports `APPROVE`, `REQUEST CHANGES` or `BLOCKED` | Must not change application source during the review; any new SHA invalidates the verdict |

Subagents typically share the parent Codex worktree, permissions, and sandbox. Their names do **not** confer OS-level isolation. Do not run concurrent writers against the same files or worktree. Independent parallel coding needs separate worktrees, explicit file ownership and stable interfaces. Keep `main` as the stable integration branch; never edit or commit directly on `main`, reset it, force-push, or rewrite published history.

## 3. Start of a lot: reconcile and plan

1. Read `AGENTS.md`, this workflow, the current lot mission, `docs/lot-0/delivery.md`, relevant contracts/fixtures, and `docs/coordination/CURRENT_STATE.md` if present.
2. Check real Git state before acting:
   - `git status --short --branch`
   - `git worktree list`
   - `git branch --show-current`
   - `git rev-parse HEAD`
   - `git fetch origin` and compare with `origin/main` where permitted
   - Check current remote PR head, its base and GitHub Actions status.
3. If resuming, reconcile the checkpoint with GitHub, CI, running processes and local changes. **Never assume a previous command completed merely because it was started.**
4. State the lot, acceptance criteria, dependency assumptions, test plan, source/licensing constraints, and task breakdown. Split an unusually large lot into independently testable PRs **only where that simplifies integration**.
5. Work in a dedicated isolated worktree from the latest verified `origin/main`, on `feature/*` or `fix/*`. Preserve any pre-existing WIP. Do not switch or clean a worktree with uncommitted changes unless they are safely accounted for.
6. Record the task and initial branch/base SHA in the checkpoint.

## 4. GitHub-first execution — publish continuously

1. Create the branch and publish it **as soon as there is a meaningful initial commit**, using `git push -u origin <branch>` (or the equivalent supported Codex Git action).
2. Open a **Draft Pull Request early**, linking the lot, scope, base SHA, acceptance criteria, test matrix and known uncertainties. A Draft PR is for tracking, not authorization to merge incomplete code.
3. Split the lot into coherent, independently testable features and delegate bounded tasks to Developer with explicit file ownership. Require targeted tests, conventional descriptive commits and pushes after meaningful milestones. Avoid noisy commits made only to satisfy a timer.
4. Inspect GitHub Actions after **every push**, including Draft PRs. Match runs to the current PR head, diagnose failures promptly, and route fixes immediately instead of waiting for final delivery. Do not interpret an earlier green CI result as evidence for a later SHA. Keep failure evidence and actual outcomes visible.
5. Maintain the operational checkpoint during development. Publish coherent WIP checkpoints on the **feature branch**, never directly on `main`.
6. At each important completed feature, stop edits and **freeze its exact SHA** for a targeted independent Tester review. Do not run a complete review after every small commit. At the end of the lot, freeze the **final PR head SHA** for a complete independent acceptance review. Do not alter tracked files while claiming that SHA is under review. Independent work may continue in another worktree only with explicit ownership and stable interfaces.
7. If Tester reports defects, route actionable evidence to Developer. After corrections, publish a new SHA and rerun the relevant validations (up to **three targeted correction cycles** before escalation). Even a documentation/checkpoint commit changes the SHA; ensure the Tester verdict and required CI are current for the final PR head.
8. When every merge gate is met, mark Draft PR **Ready for review**, check HEAD/base once more, then **merge autonomously**. Prefer a merge commit for substantial lots and squash only for minor fixes/docs, unless contracts require otherwise.
9. Verify the merge on GitHub, capture the integration SHA on `main`, verify its tree and configured post-merge CI, then record the results. Wait for configured `main` checks before the next dependent lot. Start from the new `origin/main`. Clean up the old worktree/branch only after proving that no uncommitted work would be lost.

Intermediate review is evidence for that feature at that SHA, never approval of a later lot head. The final Tester must inspect the final diff and assess all acceptance criteria. It may explicitly reuse executed evidence for unchanged code when it verifies the relevant trees are identical and runs appropriate checks on changed behavior. Record the original evidence SHA, the unchanged paths, current commands/results and limits. Do not rerun a complete unchanged backend suite merely to change a documentation timestamp, and never relabel a failed or unexecuted test as passing. Required current-head CI and a fresh final-SHA verdict remain mandatory.

If a GitHub connector returns **403**, treat it as a permission restriction. A separately authorized Git CLI or GitHub UI path may be used if available, with the exact SHA rechecked before merging. Never bypass prompts, protections or missing permissions. Do not assert success without verifying the GitHub result.

### CI modes and short reports (owner update, 14 November 2026)

Draft development runs use the exact job name `development`: lint, formatting, contracts, frontend unit/build plus conservative backend seams. Unknown runtime, migration, dependency or shared-fixture changes fall back to full backend. Docs-only may explicitly select no backend; it still runs the static/frontend checks and reports that distinction. Never report a skipped backend as an integrated pass.

Before the final frozen-head merge gate, Coordinator adds `ci:full` and requires the exact job name `integrated` at that SHA, with ALL existing backend/frontend/contracts/migrations/browser checks. Non-Draft PR events and post-merge `main` pushes also use complete integration. A green `development` run cannot satisfy this gate, even if backend selection fell back to full. Keep current-PR-head guards and one-day synthetic failure evidence. Report commands, counts, failures and material limits briefly; avoid replaying whole unchanged suites locally or long repetitive reports. [Implementation guide](readiness/ci-validation.md).

## 5. Mandatory merge gate

**All** conditions must be satisfied:

- The current lot or PR scope meets its observable acceptance criteria, including real integration paths with earlier lots where appropriate.
- Developer handoff records changed files, executed commands, actual test results, exact SHA, and unresolved risks.
- Tester independently returns **`APPROVE` for the exact current PR head SHA**, with reproducible evidence. An in-chat approval counts only when its report can be inspected; an official GitHub review is useful but not automatically required.
- Required GitHub Actions checks, including complete `integrated`, are **green for the same SHA**. Pending, stale or unjustifiably skipped checks do not count.
- No unresolved critical/major regression, security/privacy issue, contractual mismatch, or source-rights violation.
- The PR is mergeable against its current base. If the base changes in a way that could affect behavior, update and repeat necessary checks before merging.
- No restricted action is bundled into the integration (e.g. production deployment, paid resource, live remote migration, unapproved FFC collection).

**Fail or blocked:** keep the PR in Draft, write the findings and next safe action in the checkpoint, and escalate after three failed correction loops. Never merge just to keep the roadmap moving.

## 6. Bounded task brief — Coordinator to Developer

Each task request must contain:

- Task ID, lot, purpose, dependencies and current branch/worktree.
- Explicit scope, non-goals, allowed files and interfaces/data contracts.
- Acceptance criteria with observable examples, including negative cases.
- Exact tests/commands or evidence required, and environment prerequisites.
- Security, provider-rights, privacy and free-tier constraints.
- Expected handoff: files changed, commits/SHA, commands/results, known limitations and unresolved questions.

Avoid rereading the entire repository on every task: pass precise contract paths and previous findings. Use small tasks to limit wasted context, but never weaken integration testing merely to save tokens.

## 7. Independent Tester report

Provide a report with:

- Task / lot / branch / PR URL / **tested SHA** and base SHA.
- Acceptance criteria table: `PASS`, `FAIL` or `BLOCKED`, with evidence for each.
- Exact commands, environment, outputs or concise failure excerpts, and test counts where available.
- Regression, integration, auth/security, PostgreSQL, migration, browser/responsive, and data-handling findings as applicable.
- Findings ordered by severity and reproducible steps.
- Final verdict: **`APPROVE`**, **`REQUEST CHANGES`**, or **`BLOCKED`**.

A successful local test is not a substitute for CI, and successful CI is not a substitute for the independent Tester. Do not run competing writes or share a mutable database between simultaneous test runs unless deliberately isolated.

## 8. Continuity — checkpoint for 5-hour/weekly quota windows

**The project state must survive a conversation or quota interruption.** `docs/coordination/CURRENT_STATE.md` is the short operational checkpoint; GitHub is authoritative for code/PR/CI. Create the file in the active feature branch if it does not exist.

Keep these fields current:

| Field | Required content |
|---|---|
| Last checkpoint | UTC timestamp, current lot, task ID |
| Work location | Worktree path, branch, local SHA and remote PR head SHA |
| GitHub | PR link, Draft/Ready/merged state, base SHA and required CI status |
| Task board | `TODO` / `IN_PROGRESS` / `BLOCKED` / `DONE`, named responsible agent |
| Validation | Last frozen SHA, Tester verdict, local tests and CI results, failures |
| Environment | Python/Node environment, disposable PostgreSQL location/configuration without secrets, known processes |
| Risks / restrictions | Data rights, costs, deployment approval, blocked decisions |
| Resume instruction | **One specific next safe action**, its preconditions and expected confirmation |
| Do-not-repeat | Non-idempotent operations or commands whose outcome remains uncertain |

**Write checkpoints:** after each meaningful task, before a risky/long action, after failures, and before an expected interruption. Commit/push coherent checkpoint updates during development; never claim WIP is validated. During an active frozen SHA review, use the PR description/comment or another non-source note instead of committing a progress-only change; if the SHA changes, obtain fresh Tester approval and CI.

**Quota guidance (not an official Codex threshold):** if reliable remaining-quota data is visible and falls near **15–20%**, avoid starting long tasks and prioritize checkpointing, a coherent commit/push, and clean process handoff. If quota data is not accessible, do not invent percentages; checkpoint on task boundaries. Five hours is a **quota window**, not five guaranteed hours of execution. A weekly quota may still block progress after the five-hour reset.

## 9. Resume protocol — same or new Codex conversation

1. Prefer resuming the **same lot, branch and worktree** when viable; opening a new conversation must not create a second concurrent writer.
2. Read `AGENTS.md`, this file, the lot mission and `CURRENT_STATE.md`.
3. Run `git status --short --branch`, `git worktree list`, `git branch --show-current`, `git rev-parse HEAD`; compare to the remote PR SHA and CI. Preserve uncommitted work.
4. Check whether the last command, test, migration, browser session or subagent is still running, and whether it left side effects. Do not blindly rerun non-idempotent operations.
5. Reuse installed Python/Node tools and caches plus compatible disposable PostgreSQL when practical. Check versions and reproducibility; do not share an unsafe mutable test database between simultaneous runs.
6. Resolve any discrepancy between checkpoint and actual state. **Trust Git, CI and executed test evidence over narrative notes.**
7. Start only the subagents needed to finish the first incomplete bounded task. If the branch head has changed since the last approval, rerun independent review and CI.

**An automatic restart is not guaranteed.** Do not claim work is continuing after the quota is exhausted. Scheduled/automated continuation requires an actually supported and configured Codex scheduling/orchestration capability, no concurrent writer, and available quota. Otherwise stop cleanly with a durable checkpoint for later resumption.

## 10. FFC rights, services, privacy and costs

- Development may use synthetic/authorized fixtures and limited inspection of public race facts, subject to actual provider terms. This is **not** permission for unrestricted bulk extraction, recurring live synchronization, or public republication of a protected database.
- Keep provenance and uncertainty; never infer list identity or eligibility from display order or slug. Missing events must remain `to_verify`, not automatically `cancelled`.
- Do not bypass login, anti-abuse controls, robots restrictions, technical protection or rate limits. No participant personal data, protected images or source dumps in GitHub.
- Do not commit secrets, `.env`, tokens or service credentials. Avoid secrets in terminal logs, checkpoints and PRs.
- Use only free-tier-compatible architecture. Any potentially billable operation or plan change requires owner approval.
- No external deployment (including staging), remote Neon migration, production changes or final `v1.0.0` release/tag without owner approval. An unindexed URL is not access control.

## 11. End-of-lot evidence and V1 release

Once a lot is merged, the Coordinator reports concisely:

- Delivered scope, PR URL, reviewed head SHA and **confirmed merge SHA**.
- Tester verdict and required CI status for the final head SHA.
- Demonstrated end-to-end functionality, commands/tests and residual limitations.
- Checkpoint/roadmap updated and the next lot to be started.

After lot 8, perform comprehensive V1 end-to-end, responsive, security, source-rights, operational and cost-gate validation. A release candidate may be prepared with evidence and blockers; **final publication, production deployment and the `v1.0.0` tag still require the owner's explicit agreement**.

> This workflow governs agent behavior but cannot override GitHub permissions, OS sandbox controls, quotas or deployment/provider restrictions.
