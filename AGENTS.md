# RaceAtlas — Instructions for Codex

## Project

RaceAtlas is a cycling-race discovery and planning web app. V1 covers the 12 departments of Auvergne-Rhône-Alpes, France, with extension to other regions later. The public interface offers a map and calendar, with optional accounts for personally saved races.

Target architecture (do not scaffold without an assigned task): React + Vite, Python Flask + SQLAlchemy, Neon PostgreSQL, MapLibre GL JS, Render, and GitHub Actions scheduled imports.

## Three-agent orchestration

- The **Coordinator / Architect** is the main Codex thread. For a sufficiently bounded, owner-approved implementation task, it spawns the project-scoped `developer` subagent, waits for a stable commit, and delegates verification of that exact SHA to `tester`. It routes defects back to Developer, up to 3 correction cycles, before escalating.
- `developer` and `tester` are configured in `.codex/agents/*.toml`. Follow the detailed handoff and gate in `docs/AGENT_WORKFLOW.md`.
- Subagents share the parent workspace and sandbox, not separate worktrees by default. Start work in a dedicated **Codex worktree for the feature**; do not concurrently edit the same files. Tester is instructed not to modify source, but this is not an OS-level sandbox guarantee.
- **Do not start developing features merely because these instructions are present.** Await the owner's feature brief or explicit go-ahead. No coordinator mission prompt is included here.

## Git and collaboration rules

- `main` is the stable integration branch. No agent may edit, commit, merge, reset or force-push `main` or rewrite shared history. Only the repository owner authorizes merges and deployments.
- Feature/fix code uses its own Codex worktree and `feature/*` or `fix/*` branch. Prefer one pull request per independently testable feature and logical, descriptive commits. Do not force-push.
- Coordinator specifies scope, interfaces, acceptance criteria and ownership of files. Developer works only in that scope; Tester independently examines the specified SHA and reports reproducible findings. Never claim another agent acted without observable output.
- Execute relevant tests and provide exact commands, actual outcomes, and blockers. Never claim a check passed unless run. Preserve test evidence in the handoff.
- Never commit secrets, `.env`, tokens, credentials, user data, production dumps or downloaded raw provider datasets. Ask before destructive commands, live schema migrations, permission changes, production resource changes, or paid operations.
- No broad live import automation or public release without owner's explicit permission.

## FFC data: development policy

The owner approves implementing FFC ingestion and developing against small factual examples of publicly visible race metadata, subject to the data provider's terms and applicable rights. This is **not** proof of permission to mass-extract or republish a protected database. Prefer synthetic/authorized fixtures for comprehensive tests; keep source references, links, fetch timestamps and respect limits. Do not bypass logins, technical protection or rate limits. If source terms restrict a requested data use, report the blocker and use fixtures or an authorized source rather than circumventing restrictions. An unindexed Render URL is still publicly reachable; test staging with actual authentication. Do not expose personal participant data or protected media/documents without rights.

## V1 product invariants (summary)

- One interactive map view with **Altitude** topographic 2.5D and **Summit** 3D terrain modes, plus one **monthly calendar** view; no separate listing page.
- Markers at **commune center**, not an invented start point; cache geocoding. Missing coordinates remain visible in a clearly identified unlocated-races panel.
- Disciplines: Road, Gravel, MTB and Cyclo-cross. A time trial (CLM) is a Road event type, not its own discipline.
- Category filters support OR and AND. AND requires all selected categories to be accepted by **one specific race/entry list**, not a combination of separate races. Generic `Access` expands to Access 1–4, generic `Open` to Open 1–3; preserve raw source labels.
- Map Year / Month / Week controls; opening date range is the current calendar year. Calendar is monthly with All Races / My Races switch.
- Saved race statuses: Interested, Planned, Registered, Completed, stored per specific race/entry list; Registered is user-declared, not FFC-verified.
- Weekly FFC synchronization is designed to be idempotent/auditable and resilient to source gaps. Disappeared races are 'to verify', not automatically canceled; don't invent details.
- Modern sport design: navy `#111F37` and orange `#F97316`, responsive for desktop/mobile.

## Definition of done

1. Assigned scope and acceptance criteria met.
2. Relevant tests/lint/build actually run, or limitations precisely stated.
3. Source rights, secrets and production controls respected.
4. Developer provides commit SHA, files changed, tests and known risks.
5. Tester independently reports verdict for **that SHA**.
6. Coordinator compiles evidence and requests owner permission before merging into `main` or deploying.

These rules direct behavior but do not replace Git branch protections, credentials restrictions or OS permissions.
