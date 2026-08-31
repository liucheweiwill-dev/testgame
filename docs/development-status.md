# Development status

One line per task, plus the decisions that outlive any single task.

## Where things stand

**Task 001 is at workflow step 4, mid-flight.** SPEC revision 5 is approved; the
implementation of its three changes has not started. The previous Codex session
was interrupted before it wrote anything.

Branch `task/001-domain-core`, five checkpoints, last verified source state
`c9ab88f` — which corresponds to **revision 4**, not revision 5.

Next actions, in order:

1. Send revision 5's three changes to Codex (`codex exec -s workspace-write`,
   Tier 3 so the configured `xhigh` default applies):
   - `settle()` raises `ValueError` for `stake < 1`, plus the two invalid-stake
     scenarios.
   - Every payout formula asserted at stake 7 as well as 10.
   - The `stake = 10**16 + 1` blackjack scenario expecting exactly
     `25000000000000002`.
   - The PUSH property asserts `returned == stake`; a new property pins
     `returned` to one of `0 | stake | stake*2 | stake + stake*3//2`.
2. Claude re-runs all eight gauntlet layers and makes a new checkpoint.
3. **Decide whether to re-run the independent verification.** The last one
   attacked revision 4 at `c9ab88f`; both the SPEC and the source state have
   moved. Either re-run it, or record in EVIDENCE that revision 5's three
   changes were never independently verified. Both are defensible; the choice is
   about how much confidence the report may claim.
4. Codex writes EVIDENCE (step 8).
5. Claude reads EVIDENCE, then reviews the diff line by line (step 9).
6. Human authorises the merge to `main` (step 10).

## Tasks

| Task | Tier | Double-track | Result |
|---|---|---|---|
| 001 domain core | 3 | pending | in progress, step 4 |

## What Task 001 has cost so far

Five SPEC revisions, none of them cosmetic. Each was forced by something that
blocked the work:

- **Revision 2** — the Codex feasibility review raised ten findings, nine
  accepted. It also raised the Tier from 2 to 3 on the §3 structural triggers,
  which the ratchet permits and forbids arguing down.
- **Revision 3** — Codex refused to implement a wrong SPEC. The stake-1
  blackjack scenario said `returned = 1`; `1 * 3 // 2` is `1`, not `0`, so the
  answer is `2`. It left the test RED and reported the contradiction.
- **Revision 4** — lowering vulture's confidence to 60 to make the Cleanup layer
  able to fail also surfaced four findings the tool structurally cannot resolve.
  A whitelist was chosen over dropping vulture, with an admission rule.
- **Revision 5** — the Tier 3 independent verification (`gpt-5.5`, four blind
  inputs, against `c9ab88f`) found no divergence between the code and any
  explicit scenario, and four holes around them. Three fixed, one dismissed.

**The verification found nothing wrong with the code.** All four findings were
things the SPEC failed to say or the gauntlet failed to check. That is the limit
`AGENTS.md` §6 states about the gauntlet, observed rather than asserted.

## Dismissed review findings

**Vulture whitelist entries match by bare name.** The four permitted names
(`CLUBS`, `DIAMONDS`, `HEARTS`, `returned`) would also silence any future unused
item sharing them. This is how vulture whitelists work and cannot be narrowed.
Mitigation is the admission rule in SPEC revision 4 plus review; the four names
are distinctive enough that the practical risk is small. Carry this into every
EVIDENCE report until the layer changes.

## Open findings against the baseline

Not yet fixed in `ai-sw-baseline`; raised by running the workflow rather than
reading it.

**W1 — the workflow never says which branch the SPEC lives on before approval.**
§2 places Codex on a task branch at step 4, but the SPEC is written at step 1.
Here the branch was created at step 1 so that `main` is touched only by the
step 10 merge. That was a judgement call, not a documented rule.

**W2 — EVIDENCE is ordered after verification but naturally written during
implementation.** §2 puts EVIDENCE at step 8, after step 7's verification, which
is correct because it must record the verification result. But the gauntlet
output and the spec-to-test mapping are produced in the implementation session,
so writing EVIDENCE later costs a session that must re-read its own work.

**T4 — a trivial follow-up inside a Tier 3 task costs a full-effort session.**
Correcting one assertion and one test name ran at `xhigh`, because §11 scales
effort by Tier and a Tier is a property of the task, not of the round trip.

**Greenfield Tier triggers.** §3 raises the Tier on "a new module" and "more
than 2 new services/classes". In a greenfield project both fire on the first
task and most early ones, making Tier 3 the default and collapsing the tiering.
The triggers read as though they assume an existing codebase. Task 001 stands at
Tier 3 regardless — fixing a rule because it is inconvenient right now is how
rules erode — but the rule should be fixed before task 002.

## Decisions

**2026-08-28 — Claude runs the gauntlet and makes the checkpoints; Codex writes
code.** Codex's `workspace-write` sandbox refuses writes to `.git` and cannot
execute `uv`, which lives outside the workspace. Rather than relax the sandbox —
the `.git` restriction is a deliberate protection — the roles split. Codex
declined to substitute `.venv` binaries and call them the specified commands,
which is the correct reading of the rule. The split also suits the double track:
neither side can assert an outcome the other did not produce.

**2026-08-28 — The Mutation layer runs in CI only.** mutmut refuses to run
natively on Windows and directs the user to WSL. Every EVIDENCE report written
on a Windows workstation records mutation under "Layers not run as specified —
CI only, not reproduced here", never as skipped.

**2026-08-28 — Two layers could not fail before Task 001 repaired them.**
`mutmut run` exits 0 with survivors, so a results gate was added.
`min_confidence = 80` filtered out vulture's unused-function findings, which
score 60. Both were found by the feasibility review, and both had been passing
green while checking nothing.

**2026-08-28 — Two layers, not three.** `domain` and `web` only. An
`application` layer would have one implementation and one caller. Revisit when a
second front end exists. See `ARCHITECTURE.md`.

**2026-08-28 — Virtual chips do not trigger the Tier 3 "money" rule.** The
bankroll never leaves the process. Recorded in `PROJECT.md`, and filed against
the baseline as imprecise wording: the rule says "money" where it means funds
that can leave the system. If real payments are ever added, this is void.

**2026-08-28 — Dealer soft-17 behaviour is player-selectable.** The only rule
that is configuration rather than constant, alongside the seat count. Every
other rule is fixed, deliberately, to keep the combination space testable.

**2026-08-28 — Bot seats use one threshold, not a basic-strategy table.** A
300-cell table would dominate the mutation signal with trivial lookup mutations
and add no structure.

**2026-08-28 — Bootstrapped from `ai-sw-baseline`, now at general layer
v2.4.1.** This project is also the baseline's first real execution. Defects
found while running `BOOTSTRAP.md` (eight) and its update procedure (one) were
reported back and fixed there across v2.2.0, v2.3.0, v2.4.0 and v2.4.1.
