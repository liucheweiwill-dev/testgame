# Evidence Report — 003 mutation gate (Tier 3)

## Verified source state

`1192bd0c0b9cb3e4e269c749fa07d784b2b78413` on `task/003-mutation-gate`.

This is the tree CI run `34958012692` passed on, all eight layers, and the tree
every claim below is about.

## Roles

**Mixed, and the split matters.**

| Phase | Roles |
|---|---|
| SPEC revision 2, feasibility review, gate implementation | dual-agent |
| Repair of the `mutants/` path defect and the 34 surviving mutants | **single-agent (correlation not broken)** |

The SPEC was authored by Claude and reviewed by Codex, which raised nine
findings and ratcheted the Tier from 2 to 3. The gate and its first tests were
built dual-agent. Everything after CI run `34933173997` — the path fix and both
rounds of test strengthening — was done by Claude alone, because the human's
Codex budget was exhausted mid-task. `AGENTS.md` §0 permits that degradation;
this report records it rather than reporting the task as uniformly dual-agent.

## Double-track

**N/A (single-agent) for the repair.** §7 is `[dual-agent]`. The three commits
`fffdd27`, `b71f7a6` and `1192bd0` had no second agent available to review the
diff line by line. The earlier dual-agent phases had it.

## Spec -> Test mapping

81 collected tests in `tests/test_mutation_gate.py`. Every scenario row and every
Must NOT below resolves to a test, a layer, or a stated gap.

### Status vocabulary

| Status | Test |
|---|---|
| `survived` | `test_survived_fails` |
| `no tests` | `test_no_tests_fails_with_exact_two_word_status` |
| `not checked` | `test_not_checked_fails_with_exact_two_word_status` |
| `skipped` | `test_skipped_fails` |
| `suspicious` | `test_suspicious_fails` |
| `caught by type check` | `test_caught_by_type_check_fails` |
| `segfault` | `test_segfault_fails` |
| `check was interrupted by user` | `test_check_was_interrupted_by_user_fails` |
| `timeout` -> retry, classified by the retry | `test_timeout_retries_with_a_larger_budget_and_classifies_retry_status`, `test_retry_note_for_a_killed_retry_is_exact`, `test_retry_note_for_a_second_timeout_is_exact`, `test_retry_resolving_to_survived_fails_and_lists_the_mutant_twice` |
| anything else fails, naming it | `test_unrecognised_status_fails_and_names_it` |

### Parsing

| Row | Test |
|---|---|
| four-space line parsed | `test_four_space_result_line_is_parsed` |
| non-blank line with no `: ` fails | `test_nonblank_line_without_separator_fails_and_names_line` |
| unexpected header fails as malformed | `test_unexpected_header_fails_as_malformed` |
| blank line ignored | `test_blank_line_is_ignored`, `test_blank_line_between_results_does_not_stop_parsing` |
| no dependence on result ordering | `test_results_keep_input_order_and_every_character_after_the_indent` |

Added by the mutation rounds, not required by the SPEC but pinning the same
behaviour: three- and five-space indents, an empty mutant name, an empty status,
a status with a trailing space, a duplicate mutant, and a mutant name containing
the separator itself.

### Exit behaviour

| Row | Test |
|---|---|
| no non-killed results, mutants run -> `0` and a count | `test_no_non_killed_results_with_generated_mutants_passes_and_prints_count`, `test_passing_gate_prints_only_the_exact_summary_line` |
| only timeouts, resolved as killed -> `0` | `test_only_timeouts_resolved_as_killed_pass_and_print_retry_outcome`, `test_timeout_again_on_larger_budget_counts_as_killed` |
| one `survived` -> `1` | `test_one_survivor_exits_one_and_prints_line` |
| `timeout` beside `survived` -> `1`, **both** reported | `test_timeout_beside_survivor_exits_one_and_reports_both`, `test_retry_notes_are_printed_before_failures` |
| producer exits non-zero -> `1` | `test_nonzero_producer_exit_propagates_as_gate_failure`, `test_results_producer_failure_names_the_results_stage` |
| empty output **and** zero mutants -> `1` | `test_empty_results_and_zero_generated_mutants_fails`, `test_zero_generated_mutants_prints_only_the_exact_failure_line` |

### The gate is covered by the gauntlet it serves

| Layer | Test | Layer result |
|---|---|---|
| Types includes `tools` | `test_types_command_includes_tools_in_project_and_workflow` | `Success: no issues found in 7 source files` |
| Cleanup includes `tools` | `test_cleanup_command_includes_tools_in_project_and_workflow` | `All checks passed!` |
| Coverage includes `tools` | `test_changed_line_coverage_includes_tools_in_project_and_workflow` | `Coverage: 100%`, 163 lines |
| Mutation includes `tools` | `test_mutation_source_paths_include_domain_and_tools` | 446 mutants, 0 non-killed |
| Tests run the gate suite | `test_gate_test_runs_in_normal_test_suite` | 141 passed |

### The deprecation is gone

| Check | Result |
|---|---|
| `[tool.mutmut]` uses `source_paths` | `test_mutmut_configuration_uses_source_paths_not_paths_to_mutate` |
| No `paths_to_mutate is deprecated` in the CI Mutation step | grep over run `34958012692`: 0 occurrences |

### Must NOT

| # | How it is held |
|---|---|
| 1 | No change under `src/domain`. `git diff main...1192bd0 -- src/` is empty. |
| 2 | Only `timeout` is special-cased, and it is retried rather than forgiven: `test_retry_resolving_to_survived_fails_and_lists_the_mutant_twice` proves a retry that resolves to another status is classified normally and still fails. Unrecognised statuses fail. |
| 3 | The gate was not loosened. The one change to production code in this session was path resolution in the test module; the gate's classification is untouched. |
| 4 | No new dependency. `uv.lock` unchanged; the gate imports only the standard library. |
| 5 | All five layers were pointed at `tools/`; none had to be excluded. |
| 6 | `test_retry_command_runs_the_retry_program_with_the_factor_and_mutant` and `test_retry_budget_returns_the_exact_rendered_transition` pin the factor at 2.0 and require the reported budget to have risen; `test_retry_fails_when_reported_budget_was_not_raised` fails the gate if it did not. The budget used for each pass is `timeout_multiplier=15 -> 30`. |

### Failure model (Tier 3)

| Mode | Check | Held |
|---|---|---|
| Unknown status silently ignored | unrecognised-status scenario | yes |
| Producer crash read as "all killed" | zero-mutants scenario + exit-code propagation | yes |
| Malformed line skipped | malformed-line scenarios | yes |
| A timeout hides a survivor | mixed-status scenario | yes |
| Retry masks an undetected mutant | retry applies only to `timeout` | yes |
| Retry at an unchanged budget | Must NOT 6; budget stated above | yes |
| The gate itself untested or unchecked | five-layer table; the gate is mutated by its own layer | yes — 317 of the 446 mutants are the gate's |
| Mutation scope drifts off `src/domain` | mutant count reported and compared | 129 (task 002, domain only) -> 446 (domain + tools) |

## Gauntlet

Final fresh run: CI `34958012692` on `1192bd0`, all steps `success`.

| Layer | Command | Where | Output |
|---|---|---|---|
| Tests | `uv run pytest -q` | CI and workstation | `141 passed` |
| Types | `uv run mypy src tools` | CI and workstation | `Success: no issues found in 7 source files` |
| Lint + format | `uv run ruff check . && uv run ruff format --check .` | CI and workstation | `All checks passed!` |
| Changed-line coverage | `uv run pytest --cov=src --cov=tools --cov-branch --cov-report=xml && uv run diff-cover coverage.xml --compare-branch=... --fail-under=100` | CI (PR) and workstation | `Coverage: 100%`, `Total: 163 lines`, `Missing: 0` |
| Mutation | `uv run python tools/mutation_gate.py` | **CI only** | `mutation gate passed: 446 mutants generated` |
| Property-based | `uv run pytest -m property -q` | CI and workstation | `6 passed, 135 deselected` |
| Cleanup | `uv run ruff check --select F401,F811,F841 . && uv run vulture src tests tools` | CI and workstation | `All checks passed!` |
| Architecture | `uv run lint-imports` | CI and workstation | `Contracts: 2 kept, 0 broken.` |

## Independent verification

**Not performed.**

This is a Tier 3 task and §11.3 requires a fresh Codex session on a different
model, read-only, given four blind inputs. The human's Codex budget was
exhausted before this phase, so no verification round was run against
`1192bd0`.

What this costs, stated rather than implied: the SPEC's own record shows that
across task 001 every accepted verification finding was a contract gap the
gauntlet could not have found. Nothing in this report substitutes for that. The
gauntlet shows the code satisfies the constraints the SPEC expresses; it cannot
show the SPEC expresses what matters, and here nothing else looked.

`1192bd0` should not be treated as having met the Tier 3 bar. It met every other
requirement of it.

## Layers not run as specified

| Layer | State |
|---|---|
| Mutation | **`CI only`, not reproduced on the workstation.** mutmut 3.7.0 refuses to run on Windows — `platform.system()` guard, and `import resource`, which does not exist there. It ran in CI, run `34958012692`. |

Every other layer ran in both places. No layer was skipped, and none is
`not available`.

## Dismissed review findings

Carried forward from task 002, unchanged, per the standing instruction to repeat
them until the underlying layer changes.

- **Vulture whitelist entries match by bare name.** The four permitted names
  would also silence a future unused item sharing them. This is how vulture
  whitelists work. No fifth entry was added by this task: the gate's `main()`
  under an `if __name__ == "__main__"` guard is seen as used.
- **Stale scaffold `.pyc` files under `__pycache__`.** Gitignored, untracked,
  and not importable without their source.
- **CI skips changed-line coverage on a push to `main`.** The workflow states
  the reason above the condition. This task is merging through PR #4, so the
  layer does run against this diff. The residual gap — CI not enforcing that
  layer on the merge commit itself — is unchanged.

## Structural blind spot

**Mutation cannot run on this project's only workstation.** Every verdict that
layer produces comes from one environment, and a CI outage or a runner change
removes the layer entirely rather than degrading it.

A partial mitigation was found during this task and is worth recording: mutmut's
*mutant generation* is pure AST work and does run on Windows once
`platform.system`, the `resource` module and multiprocessing's `fork` context
are stubbed. That makes the 446 mutants readable locally. It does not make the
layer runnable — nothing executes them here — so the classification stands.

## Honest notes

- **The task's motivating premise was never confirmed.** The SPEC attributes CI
  run `33490174020`'s timeout to runner speed, 4.71 against ~10 mutations per
  second. mutmut's budget is `(estimated time + timeout_constant) x
  timeout_multiplier`, defaults `+1s` and `x15`; at roughly 0.1s per mutant that
  is a budget near 16s, which a twofold slowdown does not obviously exhaust. The
  design does not depend on the premise — a retry decides rather than assumes —
  but the original diagnosis remains unverified and should not be cited as
  established.

- **The same agent diagnosed the repair and judged it.** `AGENTS.md` §11.1
  requires this to be said. For this session Claude wrote the fix, chose which
  mutants to attack, wrote the tests, and read the CI result. There was no
  second agent and no human review of the intermediate steps.

- **`_repository_root` is duplicated.** `tests/test_domain_dependencies.py`
  already carries the same resolution, written for the same defect in task 002,
  but it is under `Do not modify` in this SPEC. A shared helper is the better
  design and was not taken because it would have needed a file the contract puts
  out of scope. Deliberate, not overlooked.

- **Two of the three repair commits were written blind.** mutmut does not run
  here, so the first round of 25 tests was written by predicting mutations and
  took 34 survivors to 13. Only after the generation trick above was the second
  round targeted, and it took 13 to 0 with 6 tests. The first round's hit rate
  is a fair measure of how much of this kind of work is guesswork without the
  layer in front of you.

- **`4ebd3e3` carries the message `20260915` and no body.** It adds 260 lines of
  tests. It is the one commit on this branch whose message does not say what it
  did or why.

- **What the gate's tests cannot show**, as the SPEC requires stating: they
  prove classification against mutmut 3.7.0's current vocabulary and output
  shape, neither of which mutmut publishes as a contract. A format change should
  surface through the malformed-line and unrecognised-status rules rather than
  passing silently — both fail closed — but that is a design intention, not a
  demonstrated property of a future mutmut.

- **446 mutants is a count, not a guarantee.** 317 of them are the gate's own,
  and they were killed by tests written specifically to kill them, in two rounds,
  after seeing which survived. That is the correct loop, and it also means the
  gate's test suite is shaped by its mutants rather than by an independent
  reading of what the gate should do.
