# SPEC — 003 mutation gate (Tier 3), revision 2

## Goal

Make the Mutation layer's verdict deterministic and make the gate that produces
it something the gauntlet actually checks.

The layer currently fails on a `timeout`, which is a property of the runner's
speed rather than of the code, so an identical tree passes or fails depending on
which machine CI gets. `main` is red for that reason now. A timed-out mutant is
retried with a larger budget and judged on the retry; only then can it count as
caught.

The gate itself moves out of the workflow into a tested module, and every layer
that should have been watching it — types, lint, coverage, mutation — is pointed
at it.

Nothing under `src/domain` changes.

## Background — the rule this fixes is one this project wrote

SPEC 002 revision 2 ruled that every non-`killed` status fails the layer, on the
reasoning that a mutant nobody tested is not a mutant the tests caught. Three CI
runs on an identical `src/` and `tests/` show what that costs:

| Run | mutations/second | Result |
|---|---|---|
| `33485359092` | 10.09 | 129 killed, 0 timeout |
| `33488038604` | 10.13 | 129 killed, 0 timeout |
| `33490174020` | **4.71** | 128 killed, **1 timeout** |

Nothing about the code changed; the verdict did.

**But forgiving timeouts outright is worse.** The feasibility review showed that
a gate which treats every timeout as a kill returns green when *all* mutants time
out — the layer would report success having proved nothing. A timeout means the
process exceeded mutmut's heuristic clock. That is consistent with a mutant that
hangs, and equally consistent with a busy runner. The status alone cannot tell
them apart, so the gate must make them tell themselves apart.

## Design

**Retry decides what the clock could not.** Timed-out mutants are re-run with a
larger time budget:

- killed on retry → counts as killed. It was slow, not undetected.
- times out again on a larger budget → counts as killed. A mutant that will not
  finish is a mutant whose behaviour visibly diverged.
- any other status on retry → that status, classified normally.

This turns an ambiguous status into a decided one instead of tolerating it.

**Mechanism to verify before building.** Whether mutmut 3.7.0 can raise the
budget for a single invocation — `timeout_multiplier` and `timeout_constant` are
configuration, and it is not established that either can be overridden per run —
must be confirmed against the installed source. **If it cannot, stop and report
rather than substituting a weaker scheme**; that is a SPEC revision, not an
implementation detail. A retry at the same budget on a second run is not this
design and must not be shipped as if it were.

**The gate becomes a tested module.** `tools/mutation_gate.py` reads
`mutmut results` output, classifies, orchestrates the retry, and exits. It has
unit tests. The point is not tidiness: this gate has been wrong three times — it
exited 0 with survivors, it had no CI to run in, and it failed on timeouts — and
none of those was catchable, because **the gate has never had a test**.

## Scenarios

### Status vocabulary

Verified against installed mutmut 3.7.0. These are the exact strings; unknown
process exit codes are normalised to `suspicious`.

| Status | Gate verdict |
|---|---|
| `survived` | fail |
| `no tests` | fail |
| `not checked` | fail |
| `skipped` | fail |
| `suspicious` | fail |
| `caught by type check` | fail |
| `segfault` | fail |
| `check was interrupted by user` | fail |
| `timeout` | retry, then classify by the retry result |
| anything else | **fail**, naming the unrecognised status |

`killed` is not printed by `mutmut results` unless `--all` is passed, and the
gate does not pass it.

The last row is what stops this happening a fourth time. A gate that ignores what
it does not understand shrinks silently as its tool grows new outcomes.

### Parsing

`mutmut results` prints exactly four leading spaces, then `<mutant key>: <status>`.
It emits no header and no blank lines. The deprecation warning goes to stderr via
`warnings.warn`, not to the stdout the gate reads.

| Input line | Expected |
|---|---|
| `    domain.x.y__mutmut_1: survived` | parsed, status `survived` |
| a non-blank line with no `: ` separator | **fail**, naming the malformed line |
| an unexpected header line | **fail**, as malformed |
| a blank line | ignored |

The gate does not depend on result ordering.

### Exit behaviour

| Situation | Exit | Prints |
|---|---|---|
| no non-killed results, mutants were run | `0` | a count of mutants run |
| only timeouts, all resolved as killed by retry | `0` | the timeouts and their retry outcome |
| one `survived` | `1` | that line |
| a `timeout` and a `survived` | `1` | **both** — the survivor as the failure, the timeout as a note |
| `mutmut run` or `mutmut results` exits non-zero | `1` | the producer's failure |
| empty output **and** zero mutants generated | `1` | that no mutants were generated |

The mixed row and the last row are the two that matter. The mixed row fails if
timeouts were implemented by discarding a whole result set. The last row closes a
fail-open hole: empty output is what the gate sees when everything was killed
*and* what it sees when the producer crashed before printing, so the gate must
check that a non-zero number of mutants actually ran.

### The gate is covered by the gauntlet it serves

Configuration alone does not do this. `mypy src` ignores the configured `files`
because a CLI target was given, and `vulture src tests` overrides the configured
`paths`. The **commands** must change.

| Layer | Required change |
|---|---|
| Types | command includes `tools` |
| Cleanup | vulture command includes `tools` |
| Changed-line coverage | `--cov` includes `tools`, so new gate lines are measured |
| Mutation | `source_paths` includes `tools`, so the gate is mutated too |
| Tests | `tests/test_mutation_gate.py` runs in the normal suite |

Both `PROJECT.md` and `.github/workflows/gauntlet.yml` change together; they
currently state the commands twice and must not drift.

### The deprecation is gone

| Check | Expected |
|---|---|
| `[tool.mutmut]` | uses `source_paths`, not `paths_to_mutate` |
| CI Mutation step stderr | no `paths_to_mutate is deprecated` warning |

## Must NOT

1. **No change under `src/domain`.** This task touches the gauntlet only.
2. **No status other than `timeout` gets special handling**, and `timeout` gets a
   retry rather than forgiveness. An unrecognised status fails.
3. **The gate is not made to pass by loosening it.** If parsing cannot classify
   reliably, or the retry budget cannot be raised, stop and report.
4. **No new dependency.** Standard library only.
5. **The gate is not exempt from the gauntlet it gates.** If any of the five
   layers above cannot be pointed at `tools/`, say which and why, in EVIDENCE.
6. **A retry is not a re-roll.** Retrying at the same budget, or retrying a
   non-timeout status, is forbidden — that is how a flaky gate becomes a gate
   that passes on the second attempt.

## Failure model (Tier 3)

Every way this change can hurt is a wrong verdict from the thing that judges the
tests. Each mode names the check that catches it.

| Failure mode | Check |
|---|---|
| Unknown status silently ignored, gate shrinks as mutmut grows | the unrecognised-status scenario, a literal `: banana` fixture |
| Producer crash read as "all killed" | the zero-mutants-generated scenario, plus propagating the producer's exit code |
| Malformed line skipped instead of failing | the malformed-line scenarios |
| A timeout hides a survivor in the same run | the mixed-status scenario, asserting both are reported and the exit is 1 |
| Retry masks a genuinely undetected mutant | retry only applies to `timeout`; any other retry status is classified normally |
| Retry at an unchanged budget, so it is a re-roll | Must NOT 6, and EVIDENCE must state the budget used for each pass |
| The gate itself is untested or unchecked | the five-layer coverage table; the gate is mutated by its own layer |
| Mutation scope drifts and stops covering `src/domain` | the mutant count is reported and compared against the previous run |

## Files to edit

```
tools/mutation_gate.py              new — classification, retry, exit code
tests/test_mutation_gate.py         new — its unit tests
pyproject.toml                      source_paths rename; mutation and vulture scope
.github/workflows/gauntlet.yml      the four layer commands, and the Mutation step
PROJECT.md                          the same four commands, kept in step
docs/development-status.md          Claude writes this at step 10
```

## Do not modify

```
src/                                 no product change belongs in this task
uv.lock                              no new dependency is approved
AGENTS.md  CLAUDE.md  SETUP.md       general layer
ARCHITECTURE.md                      the dependency contract
docs/001-domain-core/                closed
docs/002-gauntlet-repair/            closed
tests/test_cards.py  tests/test_hand.py  tests/test_shoe.py
tests/test_settlement.py  tests/test_domain_dependencies.py
tests/test_hand_properties.py  tests/test_shoe_properties.py
tests/test_settlement_properties.py
                                     tasks 001 and 002 left these as evidence
```

## Setup plan

- **No new dependencies.**
- **Files the gauntlet adds:** `mutants/`, already ignored.
- **Checkpoints:** the two AGENTS.md §12 requires.
- Branch `task/003-mutation-gate`, created from `main` at step 1 per §12.
- **Mutation is CI only, so this task cannot be verified without pushing.**
  Pushing the branch and opening a pull request are outward-facing acts on a
  public repository and are **separately authorised by the human when they
  happen**; approving this SPEC is not that authorisation.

## Acceptance tests

Every row of every scenario table is a named unit test in
`tests/test_mutation_gate.py`, driven by literal `mutmut results` text, except
the CI rows.

- **The mixed row.** A `timeout` beside a `survived` exits 1 and reports both.
- **Unrecognised status.** A literal `: banana` line exits 1 naming it.
- **Malformed line.** A non-blank line without `: ` exits 1 naming it.
- **Zero mutants generated.** Empty results with no mutants exits 1.
- **Producer failure.** A non-zero exit from `mutmut run` or `mutmut results`
  propagates as a non-zero gate exit.
- **Subprocess-level control:** invoke the gate as the workflow invokes it, with
  a stubbed producer emitting one `survived` line, and assert the process exits
  non-zero. Unit tests alone do not prove the wiring in the workflow is right.
- **CI:** the Mutation step completes with no deprecation warning, and the gate
  is included in Types, Cleanup, coverage and mutation. Record the run id.

**What these cannot show**, and EVIDENCE must say so: they prove the gate
classifies text correctly against mutmut 3.7.0's current vocabulary and output
shape, neither of which mutmut publishes as a contract. A format change should
surface through the malformed-line and unrecognised-status rules rather than
passing silently — that is why both fail closed.

## Commands to run

The full gauntlet from `PROJECT.md`, with the four amended commands. Mutation is
CI only.

**Merge through a pull request.** Changed-line coverage is skipped on a push to
`main`, and this task adds new measured lines.

## Risk notes

- **Tier 3 by ratchet.** Revision 1 proposed Tier 2, arguing `tools/` is test
  infrastructure rather than product structure. The feasibility review rejected
  that: §3's "a new module" trigger is explicit, and v2.5.0's narrowing exempts
  greenfield structure created by construction, not tooling. Codex raised the
  Tier and the ratchet forbids arguing back. Independent verification therefore
  applies.
- **Verifying "no longer flaky" empirically is impossible.** No number of green
  runs proves a timing-dependent failure is gone. That is why the fix is a
  classification-and-retry change with unit tests rather than a threshold tweak:
  the question becomes decidable.
- **This is the third defect in this one gate**, and the second time its own
  correction introduced the next one — revision 1 of this SPEC would have shipped
  a gate that returns green when every mutant times out. Prefer failing loudly
  when surprised over assuming the surprise cannot happen.
- **The retry adds wall-clock time to every CI run** that has a timeout, which is
  most likely to be exactly the slow runners already under contention.

## Human approval

Revision 1: superseded, never approved.
Revision 2: **approved by Will, 2026-09-01**.

## Revisions

**Revision 2** — the Codex feasibility review raised nine findings. All nine are
accepted; two changed decisions the human had already made and were taken back to
them.

- **Tier 2 → Tier 3**, by the ratchet. A failure model and independent
  verification are added.
- **Forgiving `timeout` outright was unsafe.** As revision 1 was written, a run
  in which *every* mutant timed out would have reported success. Timed-out
  mutants are now retried on a larger budget and judged on the retry, and the
  mechanism must be verified before it is built rather than assumed.
- **Two status spellings were wrong and two statuses were missing.** It is
  `no tests` and `not checked`, not the hyphenated forms, and `segfault` and
  `check was interrupted by user` were absent. A misspelling in this table is a
  misclassification.
- **Pointing the layers at `tools/` needs command changes, not configuration.**
  `mypy src` ignores the configured `files`, and `vulture src tests` overrides
  the configured `paths`. Revision 1 would have added a gate that no layer
  actually checked — the exact shape of the defect this task exists to fix.
- **Changed-line coverage would not have measured it either**, since `--cov=src`
  excludes `tools/`, so new lines could contribute nothing and leave the
  threshold green.
- **Mutation would not have mutated the gate**, leaving the new judge unjudged.
- **Empty output was a fail-open hole**: it is what the gate sees when everything
  was killed and when the producer crashed before printing. The gate now requires
  a non-zero mutant count and propagates the producer's exit status.
- **Two scenarios contradicted each other** on whether a timeout is printed
  alongside a survivor, and "CI on `main` after merge is green" was listed as a
  pre-merge acceptance criterion, which EVIDENCE cannot demonstrate before the
  merge exists.
- The `source_paths` rename was confirmed correct, and the assumed output shape
  was confirmed correct.

**Revision 1** — initial. Written after CI run `33490174020` failed on `main`
with a single timeout at 4.71 mutations/second, against an identical tree that
had passed 129/129 twice at ~10/s.
