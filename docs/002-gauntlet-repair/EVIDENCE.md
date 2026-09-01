# Evidence Report — 002 gauntlet repair (Tier 2)

## Verified source state

Approved contract: `docs/002-gauntlet-repair/SPEC.md`, revision 3, approved by
Will on 2026-09-01.

Verified source state: commit `0309bb6` on branch
`task/002-gauntlet-repair`. This is the pre-Cleanup checkpoint for the review
fixes. Cleanup then ran clean on that same tree.

## Roles

`dual-agent`. Codex built the change and wrote this report. Claude ran the
checks that can run on the workstation and made the checkpoints; CI ran the
Mutation layer and the complete CI gauntlet. Codex did not execute or reproduce
the supplied results.

## Double-track

`both`. Claude completed the step 9 line-by-line diff review after the original
step 8 report. The review found two problems, both now fixed and recorded below.

## Step 9 line-by-line diff review

Both review findings had passed all eight gauntlet layers and a 129/129
mutation run. Their discovery is therefore evidence of limits in the automated
checks, not merely a record of subsequent fixes.

### Finding 1 — structural import check could pass while checking nothing

`_repository_root()` walked `__file__`'s parents looking for a component named
`mutants`. If the repository itself was located beneath a component with that
name, a normal run could match the outer component. `DOMAIN_ROOT` would then
point at a directory with no `src/domain`; `rglob` would find no modules; and
the test would pass after inspecting zero modules.

Neither automated layer could expose that fail-open path. The gauntlet only
observed a passing test, while Mutation scopes its mutations to `src/domain`
and therefore never mutates the test's own repository-resolution logic. This
has the same shape as task 001's false `CI only` claim: the green result was a
symptom of nothing being checked rather than evidence that the intended thing
was checked.

The fix makes resolution failure loud. The test now asserts that `src/domain`
exists at the resolved root and that at least one module was found. Both
messages begin `Repository root resolution failed: resolved ...`, so a reader
can distinguish repository-resolution failure from a genuine import
violation.

The guards were read and their conditions were confirmed against a
non-existent path, so the assertion demonstrably fires. A full end-to-end run
of the test with the repository actually located beneath a `mutants` component
was **not** performed.

### Finding 2 — the Mutation row in `PROJECT.md` was stale

The row said that the layer ran but did not pass. That was true when written
mid-task, but false after CI run `33485359092` killed all 129 mutants. The row
now records both the earlier abort and that passing run.

### Judgement on the previously raised Must NOT 1 reading

Codex observed that removing `from typing import cast` is a second textual line
under `src/`, while Must NOT 1 permits “exactly one edit.” Claude judged the
removal accepted, not a violation: it is the mechanical completion of the
permitted `card_value` edit, not a separate edit, because leaving the unused
import would fail the Cleanup layer on F401. The original literal-reading
observation remains recorded in Honest notes together with that judgement.

## Spec -> Test mapping

All pass/fail results in this mapping were supplied by Claude or CI. Codex read
the approved SPEC, the governed code and tests, and the checkpoint diff, but did
not run any command.

### Structural import-check scenarios

| Contract scenario | Evidence | Mapping |
|---|---|---|
| Normal run, clean `src/domain` -> passes | `tests/test_domain_dependencies.py::test_domain_imports_only_standard_library`; final workstation and CI suites are included in the supplied 60-pass result | Covered |
| Normal run with `import hypothesis` at `src/domain/cards.py:1` -> fails and names the file and import | Required workstation negative control: `uv run pytest tests/test_domain_dependencies.py -q` exited 1 and named `domain\cards.py:1` and `hypothesis` | Covered by negative control |
| Under mutmut, clean `src/domain` -> the check runs and passes against the original tree | CI run `33485359092` completed stats collection and tested all 129 mutants instead of aborting on `mutmut.mutation.trampoline` | Covered; the clean run alone is strengthened by the next row's inside-mutmut negative control |
| Under mutmut with the same real violation -> fails | CI negative-control run `33485510913` failed during Mutation stats collection with `assert not ['domain/cards.py:1: hypothesis']`, not on `mutmut.mutation.trampoline` | Covered by the load-bearing half of the negative control |

The workstation half shows that the check fails normally. The CI half is the
one that distinguishes revision 3's live-inside-mutmut design from revision 1's
rejected skip: a skipped check and a live check with nothing to find look the
same in a green run.

The control is intentionally narrow. It exercises one static `import X` form;
it does not show that every prohibited import form is recognized, and it does
not show that dynamic imports are caught. Task 001's EVIDENCE already records
that `importlib.import_module` evades this check.

### Interpreter-pin scenarios

| Contract scenario | Evidence | Mapping |
|---|---|---|
| `.python-version` -> `3.13` | The checkpoint contains `.python-version` with exactly `3.13` | Covered by source-state inspection |
| Workstation `uv run python -V` -> `Python 3.13.x` | Observed output: `Python 3.13.15` | Covered by runtime observation |
| CI `Using CPython` line -> `3.13.x` | The `uv sync --locked` step logged `Using CPython 3.13.15` in runs `33485359092` and `33488038604` | Covered by CI runtime observations |

`.python-version` is configuration; the workstation and CI runtime lines are
the evidence that it took effect. The pin guarantees the same minor series,
not the same patch, which is what the SPEC promises. `pyproject.toml` remains
at `requires-python = ">=3.13"` and is unchanged by this task.

### Mutation-gate scenarios

| Contract scenario | Evidence | Mapping |
|---|---|---|
| Mutation completes and reports a count instead of `failed to collect stats` | CI runs `33485359092` and `33488038604`: 129 mutants tested in each | Covered |
| Empty `mutmut results` output -> exit 0 and every mutant killed | CI runs `33485359092` and `33488038604`: 129 killed, 0 survived; the Mutation step and all eight checks were green | Covered |
| Non-empty `mutmut results`, any non-killed status -> exit non-zero and print the mutants | CI run `33458012540` failed with 10 survivors; diagnostic run `33458192623` printed all 10 diffs. The persisted gate rejects any non-empty results text. Only the `survived` status was exercised by this task; the other non-killed statuses were not separately controlled | Partially exercised, with the unexercised statuses stated |

The RED reproduction was CI run `33394233626`: Mutation aborted at stats
collection and tested 0 mutants. The first GREEN was run `33485359092`, where
the layer reached a verdict and killed all 129 mutants. Run `33488038604`
repeated that 129/129 result on the current verified state.

### Equivalent-mutant and unchanged-value scenarios

| Contract scenario | Evidence | Mapping |
|---|---|---|
| `min(cast(int, rank.value), 10)` returns the existing values but can mutate equivalently | CI run `33458012540` produced the surviving `cast(None, rank.value)` mutant; `typing.cast` returns its second argument without inspecting the first | Covered by the first completed Mutation run and semantic classification |
| `min(int(rank.value), 10)` returns the same values and removes that equivalence | Untouched `tests/test_cards.py` tests below passed in the 60-test suite; current-state run `33488038604` killed every generated mutant after the executable conversion replaced the inert cast | Covered within mutmut's configured mutation operators |
| `card_value(TWO)` through `card_value(TEN)` -> 2 through 10 | `tests/test_cards.py::test_card_values_two_through_ten` | Covered |
| `card_value(JACK)`, `card_value(QUEEN)`, `card_value(KING)` -> 10 each | `tests/test_cards.py::test_card_values_face_cards` | Covered |
| `card_value(ACE)` -> 11 | `tests/test_cards.py::test_card_value_ace` | Covered |

`tests/test_cards.py` is under **Do not modify** and is byte-for-byte unchanged
between `main` and `0309bb6`. It is untouched because those seven
`card_value` scenarios are the only evidence that the rewrite changed no value.

The first completed Mutation run found ten survivors. Nine exposed one test
weakness, and the tenth was equivalent rather than a weak test:

| Survivor group | Tests that now observe the message | Disposition |
|---|---|---|
| `TypeError: stake must be an integer` mutated to `None`, padded `XX` text, or upper case | `test_settle_rejects_fractional_float_stake`, `test_settle_rejects_exact_valued_float_stake`, `test_settle_rejects_string_stake` | Killed by `match=r"^stake must be an integer$"` |
| `ValueError: stake must be positive` mutated in the same three ways | `test_settle_rejects_zero_stake`, `test_settle_rejects_negative_stake` | Killed by `match=r"^stake must be positive$"` |
| `ValueError: decks must be at least 1` mutated in the same three ways | `test_shoe_rejects_zero_decks`, `test_shoe_rejects_negative_decks` | Killed by `match=r"^decks must be at least 1$"` |
| `cast(int, rank.value)` -> `cast(None, rank.value)` | Unkillable because the first argument to `typing.cast` is runtime-inert | Removed at its source after revision 3 approval by using `int(rank.value)`, which executes |

The `^...$` anchors are load-bearing. `pytest.raises(match=...)` uses
`re.search`, not a full match; without the anchors the padded `XX...XX` form
would still match and that mutant would survive.

### Must NOT clauses

| Clause | Evidence | Mapping |
|---|---|---|
| 1. No behavior change under `src/`; only the approved `card_value` rewrite; `tests/test_cards.py` stays unmodified | The only executable `src/` change is `min(cast(int, rank.value), 10)` -> `min(int(rank.value), 10)`; its now-unused `typing.cast` import is removed. `tests/test_cards.py` is unchanged and its seven `card_value` scenarios passed. Changed-line coverage reports the one executable line at 100%. Codex raised the second-textual-line reading; Claude accepted the import removal as the mechanical completion required to avoid Cleanup F401, not a separate violation | Covered for observable values and executable scope; the observation and judgement are both disclosed |
| 2. SPEC 001 Must NOT 1 remains enforced normally and under mutmut; no skip, xfail, mutmut allowlist, or environment-variable switch | `test_domain_imports_only_standard_library` has no skip, xfail, allowlist, or `MUTANT_UNDER_TEST` branch. Both halves of negative control failed on the real `hypothesis` violation, including CI run `33485510913` inside mutmut | Covered for the controlled static import form; prohibited-form breadth remains limited as stated above |
| 3. No test is modified to make a failing thing pass | The dependency test changes only how it locates the repository tree; both negative controls show its assertion remains live. The seven exception tests add exact-message assertions rather than relaxing behavior, and final Mutation killed all 129 mutants | Covered by diff inspection, negative controls, and Mutation |
| 4. No new dependency and no lockfile change; mutmut stays | `pyproject.toml` and `uv.lock` are byte-for-byte unchanged between `main` and `0309bb6`; the checkpoint still configures mutmut | Covered by source-state comparison |
| 5. The Mutation row is not left describing the obsolete no-remote/never-run state | `PROJECT.md` now classifies Mutation as `CI only`, states the Windows limitation, and records both the earlier abort and the passing run `33485359092` | Covered by source-state inspection; the stale mid-task wording was found and fixed during step 9 review |

The required negative-control sequence was completed in both contexts: the
temporary first-line import was added, the normal check failed, the inside-
mutmut check failed in CI, the import was removed, and the final workstation
and CI runs returned to green. The temporary import is absent from `0309bb6`.

## Gauntlet

These are the final supplied results for the verified tree. They were produced
by Claude on the workstation or by CI, not by Codex.

| Layer | Command | Where | Supplied output |
|---|---|---|---|
| Tests | `uv run pytest -q` | CI run `33488038604`, PR #1 | `60 passed` |
| Types | `uv run mypy src` | CI run `33488038604`, PR #1 | `Success: no issues found in 6 source files` |
| Lint + format | `uv run ruff check . && uv run ruff format --check .` | CI run `33488038604`, PR #1 | Pass |
| Changed-line coverage | `uv run pytest --cov=src --cov-branch --cov-report=xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=100` (CI PR form compares with `origin/main`) | CI run `33488038604`, PR #1 | `src/domain/cards.py`: 1 changed executable line, 100% |
| Mutation | `uv run mutmut run && results="$(uv run mutmut results)" && if [ -n "$results" ]; then printf '%s\n' "$results"; exit 1; fi` | **CI only**, run `33488038604`, PR #1 | 129 mutants, 129 killed, 0 survived |
| Property-based | `uv run pytest -m property -q` | CI run `33488038604`, PR #1 | `6 passed` |
| Cleanup | `uv run ruff check --select F401,F811,F841 . && uv run vulture src tests` | Workstation on `0309bb6` + CI run `33488038604`, PR #1 | No findings |
| Architecture | `uv run lint-imports` | CI run `33488038604`, PR #1 | 2 contracts kept |

### CI chronology

| Run | Branch | What it established |
|---|---|---|
| `33394233626` | `main` | RED reproduction: Mutation aborted at stats collection; 0 mutants tested |
| `33458012540` | PR #1 | First completed verdict: 132 tested, 122 killed, 10 survived |
| `33458192623` | Scratch branch, deleted | Diagnostic run printed the diffs of all 10 survivors |
| `33485359092` | PR #1 | First green: 129 tested, 129 killed, 0 survived; all eight checks green |
| `33485510913` | Scratch branch, deleted | Inside-mutmut negative control failed on the real `domain/cards.py:1: hypothesis` violation |
| `33488038604` | PR #1 | Verified `0309bb6` after the review fixes: 129 tested, 129 killed, 0 survived; all eight checks green |

The mutant count fell from 132 to 129 because replacing the cast removed the
cast's own mutants, including the equivalent one; it was not suppressed or
configured away.

## Independent verification

Not performed. Independent verification is a Tier 3 requirement; this task is
Tier 2 and requires no independent verification.

## Layers not run as specified

- **Not applicable:** None. All seven Tier 2 gauntlet layers and the project
  architecture check applied.
- **Not available:** None project-wide.
- **CI only, not reproduced here:** Mutation. It cannot run on this Windows
  workstation; CI run `33488038604` supplied the current-state 129/129 result,
  CI run `33485359092` supplied the earlier 129/129 result, and CI run
  `33485510913` supplied the inside-mutmut negative control.
- **Skipped:** None.

## Dismissed review findings

- Pin CPython to exact patch `3.13.15`: dismissed because the contract requires
  minor-series parity and an exact patch would create a scheduled failure when
  that patch becomes unavailable. `.python-version` therefore contains `3.13`.

No Mutation survivor was dismissed. The equivalent `cast` mutant returned for
revision 3 approval and was removed at its source.

## Structural blind spot

There is no project-wide unavailable layer: Mutation is now genuinely
`CI only`, supported by six actual CI executions. It remains a workstation
blind spot because mutmut cannot run there at all. In practice, every mutation
iteration requires a push and a CI round trip, so developers get no local
warning that a test is weak before publishing a branch. Diagnostics and
negative controls likewise require temporary remote scratch branches instead
of a local feedback loop.

## Honest notes

- Claude had already run `ruff format` again on `src/domain/cards.py`,
  `tests/test_settlement.py`, and `tests/test_shoe.py`, then ran it a fifth time
  on `tests/test_domain_dependencies.py` during the review fixes. The same
  line-ending cause applied. Baseline finding E2 is now five for five across
  two tasks.
- Cleanup was run once before the pre-Cleanup checkpoint during the first
  gauntlet pass, inverting AGENTS.md section 12's order. That run reported
  nothing and deleted nothing. Cleanup was run again after checkpoint
  `0309bb6`, so the required order holds for the final run recorded here.
- mutmut warns that `[tool.mutmut] paths_to_mutate` is deprecated in favor of
  `source_paths`. `pyproject.toml` is under **Do not modify**, so this task did
  not change it. The migration needs its own approved change.
- The workflow annotates Node 20 deprecation for `actions/checkout@v4` and
  `astral-sh/setup-uv@v5`; both are being forced onto Node 24. This task did not
  act on those warnings.
- Two scratch branches were pushed and deleted: one for survivor diagnostics
  and one for the inside-mutmut negative control. Mutation can run only in CI
  and the workflow triggers on pull requests. Neither branch is part of the
  delivered diff, but both remain visible in repository/PR history.
- This task's diff is thin, and the repaired Mutation layer did not gate most
  of it. Mutation scopes to `src/domain`; the only executable `src/` change is
  the one line it covered and mutated. The nine test fixes are not themselves
  mutation targets, so the layer repaired here does not directly test most of
  this task's changed lines.
- The source diff also removes the now-unused `from typing import cast` import.
  That deletion is the mechanical consequence of the approved one-line
  executable rewrite and was required for Cleanup, but it is a second textual
  line under `src/`; this report does not hide that literal reading of Must NOT
  1. Claude judged it accepted, not a violation, because removing the unused
  import mechanically completes the permitted edit and leaving it would fail
  Cleanup on F401.
- The workstation observation was `uv run python -V` -> `Python 3.13.15`. In CI,
  the `uv sync --locked` step logged `Using CPython 3.13.15` in runs
  `33485359092` and `33488038604`. These runtime observations, rather than the
  `.python-version` configuration alone, show that the minor-series pin took
  effect; the SPEC does not promise identical patch versions.
- Resolving out of a directory named `mutants` remains a path heuristic tied to
  mutmut's current working-copy layout. The added existence and non-empty
  module guards make a bad resolution fail loudly. Their conditions were
  confirmed against a non-existent path, but the full test was not run with
  the repository actually beneath a `mutants` component.
- Codex's workspace-write sandbox could not execute `uv`, and mutmut cannot run
  on this workstation at all. Claude and CI supplied every execution result in
  this report; Codex performed source-state inspection only.
