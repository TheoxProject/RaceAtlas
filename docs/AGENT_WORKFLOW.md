# RaceAtlas — autonomous Codex agent workflow

This document defines the team's working protocol, not a feature implementation request.

## Team

- **Coordinator / Architect:** the main Codex session. Owns the plan, contracts, task boundaries, acceptance criteria, delegated agent selection, evidence gathering and final recommendation. Does not merge or deploy.
- **Developer:** a project-scoped `developer` subagent defined in `.codex/agents/developer.toml`. Implements only an approved, bounded task in the current isolated feature/fix worktree.
- **Tester:** a project-scoped `tester` subagent defined in `.codex/agents/tester.toml`. Independently reviews/tests an exact, stable commit; never modifies application code.

Codex subagents share the parent workspace, permissions, MCP tools and sandbox; role instructions do not implement a technical permission boundary. A Codex worktree belongs to the parent session, **not automatically to each subagent**. Start the coordinating session from an isolated worktree and keep `main` read-only. Do not allow parallel edits in the same worktree.

## Workflow for each approved feature

1. **Plan:** Coordinator defines scope, dependencies, file ownership, interfaces, acceptance tests, branch name (`feature/...`, `fix/...`), and safety constraints. It must not initiate a feature unless the user has assigned or approved that feature. A planning-only task may stop here.
2. **Isolate:** Start the coordinating Codex session in a dedicated app worktree based on `main`; verify `git status` and current branch. If on `main`, do read-only planning only and require a feature worktree before any code changes.
3. **Delegate build:** Coordinator spawns `developer` with one bounded task. Developer implements, tests, makes coherent commits where permitted, and returns the exact commit SHA, changed files, actual test outcomes and risks.
4. **Freeze revision:** Coordinator ensures Developer has stopped changing code, records the SHA, then spawns `tester` to independently review exactly that SHA. Tester may run safe checks but does not edit application code.
5. **Correct:** If Tester requests changes, Coordinator relays the defect evidence to Developer, waits for a new commit, then requests a complete retest of the new SHA. Limit correction cycles to **3**; escalate remaining blockers to the user instead of looping forever.
6. **Gate:** A feature is ready for owner review only if required checks pass, no confirmed critical/major defect remains, unknown checks are identified, and the revision SHA matches the handoff. Prepare a pull request or suggested PR content without merging automatically.
7. **Approve:** Owner alone authorizes merge to `main`, changes to production resources, publicly available deployments, or enabling scheduled live data imports.

Parallel subagents are useful for **independent reading and analysis**. Do not spawn Developer and Tester as concurrent editors of the same worktree. Allow Tester to independently examine a finished commit after Developer stops.

## Task brief, from Coordinator to Developer

- Task ID and purpose:
- Current isolated worktree / branch:
- Explicit scope and non-goals:
- Allowed files / components:
- Interface or data contract:
- Acceptance criteria (observable):
- Commands or tests to run:
- Data/security/licensing restrictions:
- Expected output: changed files, test evidence, commit SHA, risks

## Tester report

- Task / target branch / tested SHA:
- Exact commands and test results:
- Criterion-by-criterion PASS / FAIL / BLOCKED:
- Findings with severity and reproduction steps:
- Regressions / security / privacy considerations:
- Final verdict: APPROVE / REQUEST CHANGES / BLOCKED

## FFC data and deployment policy

The owner has approved building the FFC import and validating behavior with factual, publicly visible race examples during development. This **does not grant rights belonging to third parties** or authorize bulk copying against a provider's terms. Maintain provenance and links, limit requests, avoid access restrictions, and do not reproduce images, documents or personal participant data without the necessary rights. If the source terms disallow the planned use, mark the ingestion as blocked and proceed with fixture-backed development until permission or another lawful source exists. Never describe an unindexed Render URL as private: staging requires actual access controls. Separately request owner approval before broad live harvesting, enabling automatic weekly synchronization against a provider, public redistribution or public deployment.

## Security and quality

Do not commit credentials, use destructive Git commands, force-push, modify live Neon databases, enable paid services, or deploy without explicit approval. The Coordinator must report what is implemented versus planned, and evidence for any successful checks. The default end state is a reviewed branch/PR, **not a merge**.
