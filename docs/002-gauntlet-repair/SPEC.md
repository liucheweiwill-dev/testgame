# SPEC — 002 gauntlet repair (Tier 2), revision 3

## Goal

Make the Mutation layer a layer. It has never produced a verdict on any machine,
and CI run `33394233626` showed why: it aborts before testing a single mutant,
because two gauntlet layers contradict each other. Fix that, pin the interpreter
so CI and the workstation run the same Python, and carry the layer through to a
green result — including whatever weak tests it exposes, and removing the one
construct that made a mutant unkillable by anyone.

**No product behaviour changes.** One expression under `src/` is rewritten to an
equivalent that is actually executed rather than merely asserted; every observable
value stays identical, and the existing `card_value` scenarios pin that.

## Background — what CI proved

The first execution of `.github/workflows/gauntlet.yml`, on `main` at `efc85a0`:
Tests, Types, Lint + format, Cleanup and Architecture passed; changed-line
coverage was skipped by design on a push to `main`; **Mutation failed in 20
seconds**, before any mutant was tested.

mutmut copies the project into `mutants/`, rewrites every file under
`paths_to_mutate` to inject `from mutmut.mutation.trampoline import ...`, and
runs pytest with the working directory changed to that copy.
`tests/test_domain_dependencies.py` — the only executable check for Must NOT 1 of
SPEC 001, "`src/domain` imports nothing outside the standard library" — walks
those rewritten files and fires on mutmut's own import:

```
domain/cards.py:6: mutmut.mutation.trampoline
failed to collect stats. runner returned 1
```

Neither the test nor the layer is wrong. The test resolves its target from
`__file__`, so inside `mutants/` it inspects generated code, while the invariant
it enforces is about this repository's source.

The same run resolved **CPython 3.14.7** against a workstation running
**3.13.15**. `requires-python = ">=3.13"` sets a floor and no ceiling, the
workflow names no version, and `uv sync --locked` pins dependencies, not the
interpreter.

## Scenarios

**The structural import check inspects this repository's source, in every
context**

The test resolves the directory to inspect rather than assuming `__file__` sits
in the real tree. When the resolved path lies inside a `mutants/` working copy,
it walks out to the original.

| Condition | Expected |
|---|---|
| Normal run, clean `src/domain` | passes |
| Normal run, `import hypothesis` added to `src/domain/cards.py` | **fails**, naming `src/domain/cards.py` and `hypothesis` |
| Under mutmut, clean `src/domain` | **runs and passes** — it inspects the original tree, not the rewritten copy |
| Under mutmut, `import hypothesis` added to `src/domain/cards.py` | **fails** |

The check is never skipped and never disabled. It does not branch on
`MUTANT_UNDER_TEST`: an environment variable is spoofable and inheritable, and a
check that goes dark when one is set is a check with an off switch.

**The interpreter is pinned to one minor series**

| Where | Expected |
|---|---|
| `.python-version` | `3.13` |
| `uv run python -V`, workstation | `Python 3.13.x` |
| `Using CPython` line in the CI log | `3.13.x` |

The guarantee is **the same Python minor**, not the same patch. Pinning
`3.13.15` exactly would make CI fail the day that patch stops being fetchable,
which trades a real problem for a scheduled one.

`requires-python` in `pyproject.toml` is **not** changed. A ceiling there would
make `uv.lock`'s recorded metadata stale, and `uv sync --locked` exits when
project metadata would change the lockfile — so CI would fail at sync, before
reaching Mutation. `.python-version` is an explicit interpreter request that uv
honours on both sides without touching the lock.

**The Mutation layer reaches a verdict**

The configured gate is `mutmut run`, then `mutmut results`, then failure if that
output is non-empty. `mutmut results` prints **every mutant whose status is not
`killed`** — survived, no-tests, skipped, suspicious, timeout, interrupted,
not-checked, and caught-by-type-check.

| Condition | Expected |
|---|---|
| Mutation step in CI, after the fix | completes and reports a mutant count, instead of `failed to collect stats` |
| `mutmut results` output empty | step exits 0 — every mutant killed |
| `mutmut results` output non-empty, any status | step exits non-zero and prints those mutants |

"Passes" therefore means every mutant was killed, not merely that none survived.
A timeout or an untested mutant fails the layer, and that is the intended
reading: a mutant nobody tested is not a mutant the tests caught.

**The equivalent mutant in `card_value`**

The first completed run left one mutant no test could ever kill:

```python
-    return min(cast(int, rank.value), 10)
+    return min(cast(None, rank.value), 10)
```

`typing.cast` returns its second argument untouched and never inspects the
first, so both forms behave identically at runtime. This is not a weak test. It
is a line that claims a type without checking one.

`cast` is there only because `Enum.value` is typed `Any`. Replacing it with a
conversion that actually runs removes the equivalence at its source:

| Expression | `card_value` results | Mutable into an equivalent? |
|---|---|---|
| `min(cast(int, rank.value), 10)` | unchanged | yes — the cast's first argument is inert |
| `min(int(rank.value), 10)` | unchanged | no — `int()` executes |

| Input | Expected, unchanged |
|---|---|
| `card_value(TWO)` … `card_value(TEN)` | `2` … `10` |
| `card_value(JACK)`, `(QUEEN)`, `(KING)` | `10` each |
| `card_value(ACE)` | `11` |

Those rows are already tests in `tests/test_cards.py`. They are what proves the
rewrite changed no value, so they must pass untouched — editing them would
destroy the only evidence that this is equivalent.

**Suppressing the mutant was not an option.** SPEC 002 forbids configuring a
result away, and an exclusion list would have to grow an admission rule to avoid
becoming an amnesty — the shape SPEC 001 revision 4 already had to build once,
for vulture. Deleting the construct is cheaper than governing an exemption.

**Non-killed results block this task**

AGENTS.md §5 says survivors mean weak tests, and §3 requires a Tier 2 task to
pass all seven layers. If the first completed run reports non-killed mutants in
`src/domain`, this task fixes them — by adding tests under `tests/` — before it
can produce green EVIDENCE. They may not be deferred as task 001 findings.

If a mutant turns out to be genuinely equivalent, or the gate's treatment of a
status turns out to be wrong, that is a SPEC change: revise and re-approve. It
is not a thing to configure away mid-task.

## Must NOT

1. **No behavioural change under `src/`.** Exactly one edit is permitted:
   replacing `cast(int, rank.value)` with `int(rank.value)` in
   `src/domain/cards.py`, for the reason given above. Every other line under
   `src/` is out of scope, and `card_value`'s results must be identical before
   and after — `tests/test_cards.py` proves it and must pass unmodified. Any
   other diff under `src/` means the scope was wrong.
2. **Must NOT 1 of SPEC 001 stays enforced, in every context.** The import check
   must fail on a genuine non-stdlib import in `src/domain` both under a normal
   run and under mutmut. It must not be skipped, marked xfail, allowlisted for
   `mutmut`, or made conditional on an environment variable.
3. **No test is modified to make a failing thing pass.** The test is being
   pointed at the artifact its invariant is about. If that reading is wrong, the
   answer is to say so and stop — not to relax the test.
4. **No new dependency, and no lockfile change.** mutmut stays. Replacing it
   with another mutation tool is a different task at a different Tier, since a
   new dependency fires a §3 structural trigger.
5. **The Mutation row is not left describing a state that has passed.**
   `PROJECT.md` still says no remote exists and the command has never run
   anywhere. Both became false when run `33394233626` executed it. See below.

## Files to edit

```
src/domain/cards.py                 the cast only — see Must NOT 1
tests/test_domain_dependencies.py   resolve the target tree instead of assuming it
tests/                              further tests, if the Mutation layer exposes weak ones
.python-version                     new — pins CPython 3.13
PROJECT.md                          the Mutation row only
docs/development-status.md          Claude writes this at step 10
```

**Correct the Mutation row first, before any other work.** `PROJECT.md` records
that this project has no remote and that the command has never executed
anywhere. Run `33394233626` made both false, and `CI only` in AGENTS.md §5
describes where a layer runs, not whether it passes. The row becomes `CI only`
now, naming the failing run honestly. What this task changes afterwards is that
run's result, not its location.

## Do not modify

```
src/                                 except the one cast named in Must NOT 1
tests/test_cards.py                  it is the evidence the rewrite is equivalent
pyproject.toml                       a requires-python ceiling would stale the lock
uv.lock                              no dependency and no metadata change is approved
AGENTS.md  CLAUDE.md  SETUP.md       general layer
ARCHITECTURE.md                      the dependency contract
docs/001-domain-core/                task 001's record is closed
.github/workflows/gauntlet.yml       unless pinning demonstrably requires it; if so,
                                     say why in EVIDENCE
```

## Setup plan

- **No new dependencies, no lockfile change.**
- **Files the gauntlet adds:** `mutants/`, mutmut's working copy. Already covered
  by `.gitignore`; confirm rather than assume.
- **Checkpoints:** the two AGENTS.md §12 requires.
- Branch `task/002-gauntlet-repair`, created from `main` at step 1 per §12.

## Acceptance tests

Every row of every table under **Scenarios** is a named test or a named
observation of a CI run. The CI-dependent rows are the three under "The Mutation
layer reaches a verdict" and the `Using CPython` row; EVIDENCE records the run id
for each.

**Negative control — exact, and required in both contexts.** The scoping change
is otherwise indistinguishable from disabling the check.

1. Add exactly `import hypothesis` as the first line of `src/domain/cards.py`.
2. `uv run pytest tests/test_domain_dependencies.py -q` exits non-zero, and the
   assertion message names `src/domain/cards.py` and `hypothesis`.
3. In CI, the Mutation step's stats phase reaches the same failure — proving the
   check is live inside mutmut and not merely skipped there.
4. Remove the import. Both return to green.

Record the observed output of steps 2 and 3 in EVIDENCE. Step 3 is the one that
distinguishes this task's fix from the one revision 1 proposed.

**What the control does not prove**, and EVIDENCE must say so: it exercises one
static `import X` form. It does not show that every prohibited import form is
recognised, and it does not show that dynamic imports are caught — task 001's
EVIDENCE already records that `importlib.import_module` evades this check.

## Commands to run

The full gauntlet from `PROJECT.md`, in order. Mutation runs in CI only; every
other layer runs on the workstation.

**Merge through a pull request, not a direct push.** Changed-line coverage is
skipped on a push to `main` by design, so a direct merge would leave this task's
diff ungated by the one layer that measures it — and a PR is the first time that
layer will run anywhere.

## Risk notes

- **The RED state is a CI run, not a pytest failure.** §3 requires a Tier 2 bug
  fix to start from a RED test reproducing the bug. The bug is in the gauntlet,
  so the reproduction is CI run `33394233626`, already recorded and already
  failing; the GREEN is a later run where Mutation completes. Noted because the
  rule reads as though a bug always lives in the product. If that is a gap in the
  baseline it should be filed, not quietly reinterpreted.
- **This task's true size is unknown until Mutation completes once.** The layer
  has never reported anything. If it returns a long list of non-killed mutants in
  `src/domain`, closing them is inside this task's scope by the rule above, and
  the work is writing tests, not changing `src/`. That could be much larger than
  the repair itself.
- **Every iteration costs a CI round trip.** mutmut will not run on the Windows
  workstation, so the Mutation fix can only be exercised by pushing. Expect
  several runs.
- **Resolving out of `mutants/` is a path heuristic.** It depends on mutmut's
  working-copy layout, which is not a published contract and can change between
  versions. If it breaks, it breaks visibly — the layer aborts again rather than
  passing silently — but it is the weakest part of this design and EVIDENCE
  should say so.

## Human approval

Revision 1: superseded, never approved.
Revision 2: approved by Will, 2026-09-01; superseded by revision 3.
Revision 3: **approved by Will, 2026-09-01**.

## Revisions

**Revision 3** — the Mutation layer's first completed run, in CI on PR #1,
tested 132 mutants, killed 122 and left 10. Nine were one weakness: no
`pytest.raises` in the suite carried `match=`, so the tests asserted that an
exception was raised and never that it said anything. Mutating three error
messages into `None`, `XX…XX` and upper case changed nothing any test observed.
Those are fixed inside revision 2's existing scope, with anchored patterns —
`re.search` is not a full match, so an unanchored pattern still accepts the
`XX…XX` form and the mutant lives.

The tenth needs this revision. `cast(int, rank.value)` mutates to
`cast(None, rank.value)`, which is behaviourally identical, so no test can kill
it. Revision 2's Must NOT 1 forbade touching `src/` at all, which left three
options: leave the layer red, build an exclusion mechanism with an admission
rule, or delete the construct. The human chose deletion, and Must NOT 1 now
permits exactly that one edit and nothing else.

This is the rule in revision 2 working as intended: a genuinely equivalent
mutant was not configured away mid-task, it came back here for re-approval.

**Revision 2** — the Codex feasibility review raised eight findings; seven were
accepted and one was a confirmation that the Tier is right.

- **Skipping the import check was the wrong fix.** Revision 1 had it skip when
  `MUTANT_UNDER_TEST` was present. That disables SPEC 001's only executable
  enforcement during every mutation phase, keys a safety check to a spoofable
  environment variable, and is fairly read as changing a test to make a failing
  gauntlet pass — the §10 boundary. The test now resolves the tree it is about
  and runs in both contexts.
- **The `requires-python` ceiling would have broken CI before Mutation.** It
  stales `uv.lock`'s metadata and `uv sync --locked` exits on that.
  `.python-version` alone achieves the goal; `pyproject.toml` and `uv.lock` move
  to `Do not modify`.
- **The results gate is broader than "survivors".** `mutmut results` prints every
  non-killed status. Revision 1's "no mutant survives → exit 0" was wrong.
- **Non-killed mutants cannot be deferred.** Revision 1's risk note proposed
  recording them as task 001 findings; §5 and §3 do not allow a Tier 2 task to
  finish with a red layer. `tests/` joins Files to edit, and the size risk is
  stated rather than hidden.
- **The Mutation row is already stale.** `CI only` describes where a layer runs,
  not whether it passes, and the repository now has a remote. Revision 1's Must
  NOT 5 wrongly withheld that classification until the step succeeded.
- **The negative control was under-specified**, and is now exact, required in
  both contexts, and paired with a written statement of what it does not prove.
- **Acceptance criteria named "the three CI rows"** without identifying them.

One suggestion was declined: pinning `3.13.15` exactly. That trades a real
problem for a scheduled one — CI breaks when that patch stops being fetchable.
The guarantee is stated as the same minor, and the difference is written down
rather than left implied.

Revision 1's false claim that `uv.lock` "was built against 3.13" is removed; the
lock is universal and carries 3.14 and 3.15 resolution branches.

**Revision 1** — initial. Written after the first ever execution of
`.github/workflows/gauntlet.yml`, which failed the Mutation step in 20 seconds
and produced both defects this task fixes.
