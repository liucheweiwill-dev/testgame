# Development status

One line per task, plus the decisions that outlive any single task.

## Where things stand

**Task 001 is merged.** Authorised by Will on 2026-08-31 and merged with
`--no-ff` at `e2b6640`; the verified source state was `3fd7521` on
`task/001-domain-core`. Nothing was pushed — this repository has no remote.

SPEC revision 6, seven gauntlet layers run, three independent verification
rounds, EVIDENCE written and reviewed, diff reviewed line by line.

**Task 002 has not started.** Read "Logged for task 002" before writing its
SPEC. The baseline is now at v2.5.1, which fixed every finding this project has
raised — the greenfield Tier triggers among them, so task 002 is no longer Tier
3 by construction.

## Tasks

| Task | Tier | Double-track | Result |
|---|---|---|---|
| 001 domain core | 3 | both | merged `e2b6640`, 2026-08-31 |

## The result worth keeping

**Three independent verification rounds never once found the code diverging from
what the SPEC said.** Every accepted finding across all three was something the
SPEC failed to state or the gauntlet failed to check.

| Round | Target | Contract | Findings | Accepted |
|---|---|---|---|---|
| 1 | `c9ab88f` | revision 4 | 4 | 3 → revision 5 |
| 2 | `569f154` | revision 5 | 4 | 2 → revision 6 |
| 3 | `3fd7521` | revision 6 | 7 | 0 — no divergence |

That is the limit `AGENTS.md` §6 states about the gauntlet, observed rather than
asserted: it turns the constraints the SPEC expresses into executable evidence,
and can say nothing about whether the SPEC expresses what matters.

**The sharper version came from step 9.** EVIDENCE classified the Mutation layer
as `CI only`. This repository has no git remote — no CI exists, and WSL has no
distribution — so mutation has never run anywhere, on any machine, and neither
has the results gate task 001 added in revision 2 to make that layer capable of
failing at all. The gauntlet was green, the Spec→Test mapping cited 58 tests and
every one of them existed, and three verification rounds found no divergence —
and the report still asserted something false about where the work had been
checked. The line-by-line diff review caught it. Nothing else did, and all three
verification rounds had that `PROJECT.md` row in front of them as a blind input.

The gauntlet cannot show the SPEC expresses everything that matters. It also
cannot show that the gauntlet's own description of itself is true.

## What Task 001 cost

Six SPEC revisions, none cosmetic. Each was forced by something that blocked the
work:

- **Revision 2** — the Codex feasibility review raised ten findings, nine
  accepted, and raised the Tier from 2 to 3 on the §3 structural triggers, which
  the ratchet permits and forbids arguing down.
- **Revision 3** — Codex refused to implement a wrong SPEC. The stake-1
  blackjack scenario said `returned = 1`; `1 * 3 // 2` is `1`, not `0`, so the
  answer is `2`. It left the test RED and reported the contradiction.
- **Revision 4** — lowering vulture's confidence to 60 to make the Cleanup layer
  able to fail surfaced four findings the tool structurally cannot resolve. A
  whitelist was chosen over dropping vulture, with an admission rule.
- **Revision 5** — verification round 1 found `stake` had no lower bound, every
  payout formula asserted only at stake 10, and nothing enforcing "no float
  touches a stake".
- **Revision 6** — verification round 2 found `stake`'s domain only half
  enforced (`stake=1.5` returned `returned=3.5` with every layer green) and a
  natural never pinned to ten-value cards.

## Logged for task 002

Round 3's seven findings were logged and not acted on, under the termination
rule below. In rough priority:

1. **A `bool` stake leaks through the PUSH path.** `settle(20, 20, stake=True)`
   returns `Settlement(PUSH, returned=True)`. Only PUSH leaks it — the win and
   blackjack paths coerce to real `int`s through arithmetic. `True == 1` so no
   arithmetic is wrong and the `isinstance(returned, int)` property passes,
   because `bool` subclasses `int`. **A template renders it as `True`, not `1`.**
   Whichever task builds the web layer meets this first.
2. **Invalid `DealerRule` silently behaves as S17.** A string where the enum
   belongs runs H17 as S17 rather than raising.
3. **`Shoe`'s runtime input domain is unpinned.** `Shoe(decks=True, seed=42)`
   gives 52 cards; `Shoe(decks=6, seed="42")` accepts a string seed.
4. **`Settlement`'s `frozen=True` is untested.** Removing it would pass tests,
   types, lint, coverage and properties.
5. **The stdlib-only import test is static-only.** `importlib.import_module`
   evades it, so Must NOT 1 is enforced against static imports alone.
6. **The shoe property generates decks 1–4**, while scenarios cover 6. A defect
   specific to 5, or above 6, would pass.
7. **`is_bust` is declared in the SPEC's API with no scenario row anywhere.**
   Found during the diff review, same class as the above. Tests cover it; the
   contract never pinned it.

## Dismissed review findings

Carry all three into every EVIDENCE report until the underlying layer changes.

**Vulture whitelist entries match by bare name.** The four permitted names
(`CLUBS`, `DIAMONDS`, `HEARTS`, `returned`) would also silence any future unused
item sharing them. This is how vulture whitelists work and cannot be narrowed.
Mitigation is revision 4's admission rule plus review. **Raised independently in
rounds 1 and 2**, which raises its standing as a known limitation without
changing the reason for dismissal.

**Stale scaffold `.pyc` files under `__pycache__`.** `__pycache__/` is
gitignored, nothing scaffold-related is tracked, and `import domain.scaffold`
raises `ModuleNotFoundError` — since PEP 3147 a `__pycache__` `.pyc` is not
importable without its source. Must NOT 6 concerns what survives in the
repository.

**CI skips changed-line coverage on a push to `main`.** The workflow states the
reason directly above the condition: a push to `main` has no changed-line base,
so the layer is skipped rather than silently degraded into an overall-coverage
check. Residual nuance: CI would not independently enforce that layer on a merge
commit; the pre-merge workstation run is what establishes it. Moot while no CI
exists at all.

## Baseline findings from task 001 — fixed in v2.5.0 and v2.5.1

Task 001 was this baseline's first end-to-end run. Eleven defects surfaced by
running the workflow rather than reading it, and all eleven are fixed in general
layer **v2.5.0**, adopted here on 2026-08-31. One line each is enough to
remember why the rules now read as they do.

| Finding | What it was | Fixed in |
|---|---|---|
| W1 | The workflow never said which branch the SPEC lives on before approval | §2 step 1, §12 |
| W2 | EVIDENCE ordered after verification but naturally written during implementation | §6 |
| W3 | `CLAUDE.md` contradicted §12 on whether checkpoint commits need authorisation | `CLAUDE.md` |
| W4 | `CI only` asserted that a CI exists, and nothing verified it | §5 |
| W5 | The verification loop had no termination rule | §11 |
| W6 | The verifier received the gauntlet table as a blind input but was never asked to doubt it | §11 |
| W7 | Step 10 ordered the status update before the merge it describes | §2 step 10, §12 |
| Greenfield triggers | §3's structural triggers fire on every early task in a new project | §3 |
| T4 | A trivial follow-up inside a Tier 3 task cost a full-effort session | §11 |
| E1 | The Codex hash directory is deleted on update, and a missing CLI reports success | `SETUP.md` §1, §5 |
| E2 | The builder cannot run the formatter it is judged by | `SETUP.md` §4 |
| "money" wording | §3's Tier 3 trigger said "money" where it meant funds that can leave the system — it fired on this project's play chips | §3, in **v2.5.1** |

Two of these change how task 002 is run, so read them before writing its SPEC:

- **The greenfield triggers no longer fire by construction.** §3 now measures
  change against the architecture the project has already committed to, so task
  002 is not automatically Tier 3 the way task 001 was. A trigger that does fire
  still cannot be argued down — that remains the ratchet.
- **Verification now terminates**, on a round that finds no divergence, and the
  rule has to be set before the round runs rather than after reading its
  findings.

**Two more came from running the update procedure itself**, at v2.5.0 and again
at v2.5.1. Both are fixed in `BOOTSTRAP.md`, with no general-layer version bump,
because nothing that gets copied into a project changed:

- **The overwrite had no leak check at all.** It replaced the three
  general-layer files unconditionally, on the stated assumption that they hold no
  project content. A project that had edited one lost the edit silently — the
  exact failure the procedure's own closing note warns about, and which it gave
  no way to detect, because it compared nothing.
- **The obvious form of that check fails towards merging.** A CRLF working tree
  on one side and LF blobs on the other is enough to make a plain `diff` report
  every line of every file as changed while nothing has leaked. Read naively it
  says "everything leaked", and the reader's next move is the merge
  `BOOTSTRAP.md` forbids.

An earlier version of this file described the second as *the procedure's own
check* being line-ending sensitive. That was wrong — there was no check to be
sensitive, which made the finding larger than it was first filed as. Recorded
here rather than silently rewritten.

## Open findings against the baseline

**No convention for versioning a `BOOTSTRAP.md`-only change.** That file is
never copied into a project and carries no version header, so a fix to it moves
no general-layer version. v2.4.1 marked one in its commit title anyway while the
general layer stayed at v2.4.0 — which is why this file once said "now at general
layer v2.4.1" while these files said v2.4.0. The two BOOTSTRAP fixes above
deliberately did not repeat that, and the gap is still unfixed.

## Decisions

**2026-08-31 — Verification terminates when a round finds no divergence.**
Contract-completeness findings from that round are logged and triaged, and a
revision that closes a contract gap without fixing a code defect does not re-open
the requirement. Set before round 3 ran, not after seeing its result. Without a
rule of this shape the loop does not terminate — see W5.

**2026-08-31 — The Mutation layer is `not available`, not `CI only`.** It is
configured, cannot run on this Windows workstation, and there is no CI or WSL to
run it elsewhere. It becomes `CI only` the moment a remote exists and the
workflow actually runs, and not before. Superseded the 2026-08-28 decision below.

**2026-08-31 — Claude makes small mechanical corrections to Codex-owned files
rather than spending a round trip, and records each one.** Two `ruff format` runs
on `tests/test_settlement.py`, and one stale `CI only` phrase in EVIDENCE that
Codex missed while correcting four other sections. Each is whitespace or an
internal-consistency fix, never a new claim. The alternative is a full `xhigh`
session per line, which is T4.

**2026-08-28 — Claude runs the gauntlet and makes the checkpoints; Codex writes
code.** Codex's `workspace-write` sandbox refuses writes to `.git` and cannot
execute `uv`, which lives outside the workspace. Rather than relax the sandbox —
the `.git` restriction is a deliberate protection — the roles split. Codex
declined to substitute `.venv` binaries and call them the specified commands,
which is the correct reading of the rule. The split also suits the double track:
neither side can assert an outcome the other did not produce.

**2026-08-28 — Two layers could not fail before Task 001 repaired them.**
`mutmut run` exits 0 with survivors, so a results gate was added. `min_confidence
= 80` filtered out vulture's unused-function findings, which score 60. Both were
found by the feasibility review, and both had been passing green while checking
nothing. The mutation gate remains unproven — see W4.

**2026-08-28 — Two layers, not three.** `domain` and `web` only. An `application`
layer would have one implementation and one caller. Revisit when a second front
end exists. See `ARCHITECTURE.md`.

**2026-08-28 — Virtual chips do not trigger the Tier 3 "money" rule.** The
bankroll never leaves the process. Recorded in `PROJECT.md`, and filed against
the baseline as imprecise wording: the rule says "money" where it means funds
that can leave the system. If real payments are ever added, this is void.

**2026-08-28 — Dealer soft-17 behaviour is player-selectable.** The only rule
that is configuration rather than constant, alongside the seat count. Every other
rule is fixed, deliberately, to keep the combination space testable.

**2026-08-28 — Bot seats use one threshold, not a basic-strategy table.** A
300-cell table would dominate the mutation signal with trivial lookup mutations
and add no structure.

**2026-08-28 — Bootstrapped from `ai-sw-baseline`; updated to general layer
v2.5.1 on 2026-08-31.** This project is also the baseline's first real
execution. Defects found while running `BOOTSTRAP.md` (eight) and its update
procedure (three) were reported back and fixed there across v2.2.0, v2.3.0,
v2.4.0, v2.4.1 and the update-procedure repair that followed v2.5.1. Task 001's full run added eleven more, fixed in v2.5.0, and
the "money" wording it had been reading narrowly was fixed in v2.5.1.
