# Development status

One line per task, plus the decisions that outlive any single task.

## Tasks

| Task | Tier | Double-track | Result |
|---|---|---|---|
| _none yet_ | | | |

## Decisions

**2026-08-28 — Two layers, not three.** `domain` and `web` only. An
`application` layer would have one implementation and one caller. Revisit when a
second front end exists. See `ARCHITECTURE.md`.

**2026-08-28 — Virtual chips do not trigger the Tier 3 "money" rule.** The
bankroll never leaves the process. Recorded in `PROJECT.md` under
project-specific safety, and filed against the baseline as imprecise wording:
the rule says "money" where it means funds that can leave the system. If real
payments are ever added, this decision is void.

**2026-08-28 — Dealer soft-17 behaviour is player-selectable.** It is the only
rule that is configuration rather than constant, alongside the seat count. Every
other rule is fixed, deliberately, to keep the combination space testable.

**2026-08-28 — Bot seats use one threshold, not a basic-strategy table.** Bots
exist to populate the table. A 300-cell strategy table would dominate the
mutation-testing signal with trivial lookup mutations and add no structure.

**2026-08-28 — The Mutation layer runs in CI only.** mutmut refuses to run
natively on Windows and directs the user to WSL. Since the workstations here are
Windows, mutation is unavailable locally and available in CI on `ubuntu-latest`.
Seven of the eight layers were run locally and passed; mutation was not. Every
EVIDENCE report written on a Windows workstation records mutation under "Layers
not run as specified — not available", not under "skipped".

**2026-08-28 — Bootstrapped from the ai-sw-baseline general layer v2.1.0.**
This project is also the baseline's first real execution; defects found while
running `BOOTSTRAP.md` are reported back to that repository.
