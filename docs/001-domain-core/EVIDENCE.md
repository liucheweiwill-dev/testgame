# Evidence Report — 001 domain core (Tier 3)

## Verified source state

Approved contract: `docs/001-domain-core/SPEC.md`, revision 6, approved by Will
on 2026-08-31.

Verified source state: commit `3fd7521449496391348fcd58dd91e1d39d2408f9`
on branch `task/001-domain-core`. The Cleanup layer ran on the identical tree at
`c6e3920`; `3fd7521` is an empty commit that names that tree and records the
gauntlet result in its commit message.

## Roles

`dual-agent`. Codex built the implementation and wrote this report. Claude ran
the gauntlet and made the checkpoints. A separate read-only `gpt-5.5` session
performed independent verification.

## Double-track

`both`. This EVIDENCE report is written first, at AGENTS.md §2 step 8. Claude's
line-by-line diff review is the second track at step 9 and has not happened at
the time of writing.

## Spec -> Test mapping

All named test results below derive from the supplied final full-suite result of
60 passing tests; Codex did not execute them.

### Scenario rows

| Contract scenario | Named test | Mapping |
|---|---|---|
| `card_value(TWO)` through `card_value(TEN)` → 2 through 10 | `tests/test_cards.py::test_card_values_two_through_ten` | Covered |
| `JACK`, `QUEEN`, `KING` → 10 each | `tests/test_cards.py::test_card_values_face_cards` | Covered |
| `ACE` → 11 | `tests/test_cards.py::test_card_value_ace` | Covered |
| `[ACE, KING]` → total 21, soft | `tests/test_hand.py::test_hand_total_ace_king_is_soft_twenty_one` | Covered |
| `[ACE, SIX]` → total 17, soft | `tests/test_hand.py::test_hand_total_ace_six_is_soft_seventeen` | Covered |
| `[ACE, SIX, KING]` → total 17, hard | `tests/test_hand.py::test_hand_total_ace_six_king_is_hard_seventeen` | Covered |
| `[ACE, ACE]` → total 12, soft | `tests/test_hand.py::test_hand_total_two_aces_is_soft_twelve` | Covered |
| `[ACE, ACE, ACE]` → total 13, soft | `tests/test_hand.py::test_hand_total_three_aces_is_soft_thirteen` | Covered |
| `[ACE, ACE, NINE]` → total 21, soft | `tests/test_hand.py::test_hand_total_two_aces_nine_is_soft_twenty_one` | Covered |
| `[KING, QUEEN, FIVE]` → total 25, hard | `tests/test_hand.py::test_hand_total_king_queen_five_is_hard_twenty_five` | Covered |
| `[]` → total 0, hard | `tests/test_hand.py::test_empty_hand_total_is_hard_zero` | Covered |
| `[ACE, KING]` and `[KING, ACE]` are blackjack | `tests/test_hand.py::test_blackjack_ace_then_king`; `tests/test_hand.py::test_blackjack_king_then_ace` | Covered |
| `[ACE, TEN]` is blackjack | `tests/test_hand.py::test_blackjack_ace_then_ten` | Covered |
| `[ACE, NINE, ACE]` is not blackjack | `tests/test_hand.py::test_three_card_twenty_one_is_not_blackjack` | Covered |
| Six-deck shoe starts with 312 cards | `tests/test_shoe.py::test_six_deck_shoe_starts_with_312_cards` | Covered |
| Fully dealt six-deck shoe contains six of every `(Rank, Suit)` pair | `tests/test_shoe.py::test_six_deck_shoe_has_six_of_every_rank_suit_pair` | Covered |
| Equal seeds produce equal sequences | `tests/test_shoe.py::test_same_seed_deals_identical_sequences` | Covered |
| Seeds 42 and 43 produce different sequences | `tests/test_shoe.py::test_different_seeds_deal_different_sequences` | Covered |
| `remaining()` decrements; deal 313 raises `ShoeExhausted` | `tests/test_shoe.py::test_remaining_decreases_and_313th_deal_raises` | Covered |
| `decks=0` and `decks=-1` raise `ValueError` | `tests/test_shoe.py::test_shoe_rejects_zero_decks`; `tests/test_shoe.py::test_shoe_rejects_negative_decks` | Covered |
| Constructing and exhausting a shoe leaves global random state unchanged | `tests/test_shoe.py::test_exhausting_shoe_leaves_global_random_state_unchanged` | Covered |
| Hard 17 stands under S17 | `tests/test_settlement.py::test_dealer_hard_seventeen_stands_under_s17` | Covered for the valid enum value |
| Hard 17 stands under H17 | `tests/test_settlement.py::test_dealer_hard_seventeen_stands_under_h17` | Covered for the valid enum value |
| Soft 17 stands under S17 | `tests/test_settlement.py::test_dealer_soft_seventeen_stands_under_s17` | Covered for the valid enum value |
| Soft 17 hits under H17 | `tests/test_settlement.py::test_dealer_soft_seventeen_hits_under_h17` | Covered for the valid enum value |
| 16 hits under either rule | `tests/test_settlement.py::test_dealer_sixteen_hits_under_either_rule` | Covered for both valid enum values |
| 18 stands under either rule | `tests/test_settlement.py::test_dealer_eighteen_stands_under_either_rule` | Covered for both valid enum values |
| Blackjack vs blackjack, stake 10 → `PUSH`, 10 | `tests/test_settlement.py::test_both_blackjack_pushes` | Covered |
| Blackjack vs three-card 21, stake 10 → `PLAYER_BLACKJACK`, 25 | `tests/test_settlement.py::test_blackjack_beats_three_card_twenty_one` | Covered |
| Blackjack vs 20, stake 10 → `PLAYER_BLACKJACK`, 25 | `tests/test_settlement.py::test_blackjack_beats_twenty` | Covered |
| `[ACE, TEN]` vs 20, stake 10 → `PLAYER_BLACKJACK`, 25 | `tests/test_settlement.py::test_ace_ten_blackjack_beats_twenty` | Covered |
| Blackjack vs 20, stake 5 → `PLAYER_BLACKJACK`, 12 | `tests/test_settlement.py::test_blackjack_odd_stake_five_truncates_payout` | Covered |
| Blackjack vs 20, stake 1 → `PLAYER_BLACKJACK`, 2 | `tests/test_settlement.py::test_blackjack_stake_one_returns_stake_plus_one_chip_win` | Covered |
| 20 vs dealer blackjack, stake 10 → `DEALER_WINS`, 0 | `tests/test_settlement.py::test_dealer_blackjack_beats_player_twenty` | Covered |
| 20 vs 19, stake 10 → `PLAYER_WINS`, 20 | `tests/test_settlement.py::test_player_twenty_beats_dealer_nineteen` | Covered |
| 19 vs 20, stake 10 → `DEALER_WINS`, 0 | `tests/test_settlement.py::test_player_nineteen_loses_to_dealer_twenty` | Covered |
| 20 vs 20, stake 10 → `PUSH`, 10 | `tests/test_settlement.py::test_equal_twenty_pushes` | Covered |
| Player 22 bust vs dealer 23 bust → `DEALER_WINS`, 0 | `tests/test_settlement.py::test_player_bust_loses_even_when_dealer_busts_higher` | Covered; pins settlement precedence rule 1 |
| Player 18 vs dealer 24 bust → `PLAYER_WINS`, 20 | `tests/test_settlement.py::test_player_eighteen_beats_busted_dealer` | Covered |
| 20 vs 19, stake 7 → `PLAYER_WINS`, 14 | `tests/test_settlement.py::test_player_twenty_beats_dealer_nineteen_at_stake_seven` | Covered |
| 20 vs 20, stake 7 → `PUSH`, 7 | `tests/test_settlement.py::test_equal_twenty_pushes_at_stake_seven` | Covered |
| Blackjack vs 20, stake 7 → `PLAYER_BLACKJACK`, 17 | `tests/test_settlement.py::test_blackjack_at_stake_seven_returns_seventeen` | Covered |
| Blackjack at `10**16 + 1` → `25000000000000002` | `tests/test_settlement.py::test_blackjack_large_stake_uses_exact_integer_arithmetic` | Covered |
| `stake=0` raises `ValueError` | `tests/test_settlement.py::test_settle_rejects_zero_stake` | Covered |
| `stake=-5` raises `ValueError` | `tests/test_settlement.py::test_settle_rejects_negative_stake` | Covered |
| `stake=1.5` raises `TypeError` | `tests/test_settlement.py::test_settle_rejects_fractional_float_stake` | Covered |
| `stake=10.0` raises `TypeError` | `tests/test_settlement.py::test_settle_rejects_exact_valued_float_stake` | Covered |
| `stake="10"` raises `TypeError` | `tests/test_settlement.py::test_settle_rejects_string_stake` | Covered |

### Acceptance properties and checks

| Contract item | Named test or layer | Mapping |
|---|---|---|
| For hands of 1–10 cards, total stays between hard and soft sums | `tests/test_hand_properties.py::test_hand_total_stays_between_hard_and_soft_sums` | Covered |
| A hand without an ace is hard and equals the plain card-value sum | `tests/test_hand_properties.py::test_hand_without_ace_is_hard_plain_sum` | Covered |
| For any seed and any `decks >= 1`, a dry shoe is the canonical multiset | `tests/test_shoe_properties.py::test_dealing_any_shoe_yields_canonical_multiset` plus the six-deck scenario test | **Partial:** Hypothesis generates decks 1–4 only; the example covers 6. Deck 5 and decks above 6 are not generated. |
| PUSH iff both blackjack or equal live non-blackjack totals, and returns the stake | `tests/test_settlement_properties.py::test_settlement_pushes_exactly_for_defined_ties` | Covered for generated hands and integer stakes |
| Return amount follows the formula selected by the outcome | `tests/test_settlement_properties.py::test_settlement_returned_matches_outcome_formula` | Covered for generated hands and positive integer stakes |
| `returned` is an `int` | `tests/test_settlement_properties.py::test_settlement_returned_is_always_an_int` | **Partial:** `bool` subclasses `int`, so this assertion accepts the PUSH result `returned=True` when `stake=True`. |
| Domain imports only the standard library | `tests/test_domain_dependencies.py::test_domain_imports_only_standard_library` | **Partial:** checks static `ast.Import` and `ast.ImportFrom` nodes only; a dynamic `importlib.import_module(...)` call evades it. |
| Exhausting a shoe preserves global random state | `tests/test_shoe.py::test_exhausting_shoe_leaves_global_random_state_unchanged` | Covered |
| Cleanup negative control makes the layer fail | No supplied execution result | **Unverified:** the supplied result covers only the final clean-tree pass; this report does not claim the negative control was observed failing. |

### Failure model

| Failure mode | Named test or layer | Mapping |
|---|---|---|
| Ace demoted always or never | `tests/test_hand.py::test_hand_total_two_aces_nine_is_soft_twenty_one`; `tests/test_hand.py::test_hand_total_ace_six_king_is_hard_seventeen`; `tests/test_hand_properties.py::test_hand_total_stays_between_hard_and_soft_sums` | Covered |
| Blackjack confused with three-card 21 | `tests/test_hand.py::test_three_card_twenty_one_is_not_blackjack`; `tests/test_settlement.py::test_blackjack_beats_three_card_twenty_one`; `tests/test_settlement_properties.py::test_settlement_pushes_exactly_for_defined_ties` | Covered |
| Both-bust ordering inverted | `tests/test_settlement.py::test_player_bust_loses_even_when_dealer_busts_higher` | Covered |
| 3:2 payout rounded up | `tests/test_settlement.py::test_blackjack_odd_stake_five_truncates_payout`; `tests/test_settlement.py::test_blackjack_stake_one_returns_stake_plus_one_chip_win` | Covered |
| Payout computed in floating point | `tests/test_settlement.py::test_blackjack_large_stake_uses_exact_integer_arithmetic` | Covered for the specified discriminating value |
| Payout formula hardcoded to stake 10 | `tests/test_settlement.py::test_player_twenty_beats_dealer_nineteen_at_stake_seven`; `tests/test_settlement.py::test_equal_twenty_pushes_at_stake_seven`; `tests/test_settlement.py::test_blackjack_at_stake_seven_returns_seventeen` | Covered |
| Negative or zero stake accepted | `tests/test_settlement.py::test_settle_rejects_zero_stake`; `tests/test_settlement.py::test_settle_rejects_negative_stake` | Covered |
| Non-integer stake accepted and returns fractional chips | Three invalid-type tests plus `tests/test_settlement_properties.py::test_settlement_returned_is_always_an_int` | Covered for float and string inputs; the generated property supplies integers only, and its `isinstance(..., int)` assertion does not distinguish `bool`. |
| A natural recognizes face cards only | `tests/test_hand.py::test_blackjack_ace_then_ten`; `tests/test_settlement.py::test_ace_ten_blackjack_beats_twenty` | Covered |
| Shoe is reproducible by mutating global random state | `tests/test_shoe.py::test_exhausting_shoe_leaves_global_random_state_unchanged` | Covered |
| Shoe is short or has the wrong suit composition | `tests/test_shoe.py::test_six_deck_shoe_has_six_of_every_rank_suit_pair`; `tests/test_shoe_properties.py::test_dealing_any_shoe_yields_canonical_multiset` | Covered at six decks and property-generated decks 1–4; not generated for 5 or above 6. |
| Dead scaffold code remains | Final Cleanup layer: `uv run ruff check --select F401,F811,F841 . && uv run vulture src tests` | Final tree reported clean. Checker failure-path negative control is unverified because no result was supplied. |
| Weak tests fail to catch a changed behavior | Mutation command in `PROJECT.md` | **Unverified anywhere:** the layer is `not available` — configured, unrunnable on this workstation, and with no CI or WSL environment to run it elsewhere. Six passing property tests are the local substitute, not mutation evidence. |

### Must NOT clauses

| Clause | Named test, layer, or explicit gap | Mapping |
|---|---|---|
| 1. `src/domain` imports nothing outside the standard library | `tests/test_domain_dependencies.py::test_domain_imports_only_standard_library`; architecture check `uv run lint-imports` | **Partial:** the test enforces static imports only. Dynamic imports evade it, and the import-linter contracts name only `web`, `flask`, and `jinja2`. Round 3 source inspection found the clause holds in the verified source, but that prose verification is not an executable layer. |
| 2. No global randomness; every shuffle derives from the supplied seed | `tests/test_shoe.py::test_exhausting_shoe_leaves_global_random_state_unchanged`; same-seed and different-seed scenario tests | Covered |
| 3. No speculative config, strategy, factory, or single-implementation abstraction | **Skipped as a dedicated executable check:** no test or gauntlet layer semantically recognizes these design shapes. Round 3 source inspection found the clause holds; Claude's line-by-line diff review is still pending. Cleanup only detects unused code, not every prohibited abstraction. | Unverified by executable check |
| 4. No split, double, insurance, surrender, bet validation, or bot logic, even as stubs | **Skipped as a dedicated semantic check:** Cleanup can detect unused stubs, but not prohibited logic that is referenced. Round 3 source inspection found the clause holds; Claude's line-by-line diff review is still pending. | Partially enforced by Cleanup; unverified by a dedicated semantic test |
| 5. Payout arithmetic stays integer; floats neither implement nor enter settlement | Large-integer payout test; three invalid-type tests; `tests/test_settlement_properties.py::test_settlement_returned_is_always_an_int` | Covered for floating-point implementation and float/string callers. The output property does not distinguish `bool` from `int`; Round 3 found the separate PUSH rendering leak described below. |
| 6. Bootstrap scaffold source/tests are deleted and Cleanup stays green | Final Cleanup layer and Round 3 source inspection | Covered for the tracked source tree. No dedicated test asserts the three paths are absent; ignored `__pycache__` bytecode is addressed under dismissed findings. |

## Gauntlet

These are Claude's final fresh-run results supplied from the workstation. Codex
did not execute or reproduce any command and claims no mutation result.

| Layer | Command | Where | Supplied result |
|---|---|---|---|
| Tests | `uv run pytest -q` | workstation | `60 passed` |
| Types | `uv run mypy src` | workstation | `Success: no issues found in 6 source files` |
| Lint + format | `uv run ruff check . && uv run ruff format --check .` | workstation | `All checks passed!` / `22 files already formatted` |
| Changed-line coverage | `uv run pytest --cov=src --cov-branch --cov-report=xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=100` | workstation | 105 lines, 0 missing, 100% |
| Mutation | `uv run mutmut run && results="$(uv run mutmut results)" && if [ -n "$results" ]; then printf '%s\n' "$results"; exit 1; fi` | not available | Configured but never run: mutmut is unrunnable on this Windows workstation, and no CI or usable WSL environment exists to run the command or its results gate elsewhere. No mutation outcome is claimed. |
| Property-based | `uv run pytest -m property -q` | workstation | 6 passed, 54 deselected |
| Cleanup | `uv run ruff check --select F401,F811,F841 . && uv run vulture src tests` | workstation | `All checks passed!`; no vulture findings |
| Architecture | `uv run lint-imports` | workstation | 2 contracts kept, 0 broken |

## Independent verification

Three rounds used separate `gpt-5.5` sessions, read-only. The intended four
blind inputs were the approved SPEC revision for that round, the checkpoint SHA
and branch, the complete `PROJECT.md` gauntlet-command table, and the task's
`docs/001-domain-core/` directory. The verifier's extra read of its own skill
definition is disclosed under Honest notes.

| Round | Source and contract | Result and disposition |
|---|---|---|
| 1 | `c9ab88f`, SPEC revision 4 | Four findings. Three contract/gauntlet gaps were accepted and fixed in revision 5: stake-domain lower bound, multi-stake payout checks, and a large-integer check against floating-point payout arithmetic. The bare-name vulture-whitelist finding was dismissed. No code divergence from an explicit scenario was found. |
| 2 | `569f154`, SPEC revision 5 | Four findings. Two contract gaps were accepted and fixed in revision 6: runtime rejection of non-integer stakes and explicit `[ACE, TEN]` blackjack behavior. The whitelist and stale-scaffold-bytecode findings were dismissed. No code divergence from an explicit scenario was found. |
| 3 | `3fd7521`, SPEC revision 6 | **No explicit divergence found.** The verifier found no mismatch against any stated card value, hand total, blackjack example, valid shoe scenario, dealer-play row for valid enum values, settlement precedence rule, listed payout row, large-integer payout, or invalid-stake row. It confirmed all six Must NOT clauses hold in source. Seven contract- and gauntlet-completeness findings were logged and none was acted on in task 001. |

Before round 3 ran, the human set the termination rule: verification is
satisfied when a round finds no divergence between code and the approved
contract; completeness findings from that round are logged and triaged, and a
revision that closes a contract gap without fixing a code defect does not
re-open verification. Round 3 met that pre-set condition; the rule was not
chosen after seeing its result.

Round 3's seven logged findings and dispositions are:

1. **Invalid `DealerRule` silently behaves as S17.**
   `dealer_should_hit([ACE, SIX], "HIT_ON_SOFT_17")` returns `False` because the
   implementation compares identity with `DealerRule.HIT_ON_SOFT_17`. The SPEC
   defines behavior only for valid enum values and does not require bad runtime
   input to raise. Logged as a contract-domain gap; no task-001 change.
2. **`Shoe` runtime inputs are under-specified.** `Shoe(decks=True, seed=42)`
   yields 52 cards, and `Shoe(decks=6, seed="42")` constructs with a string
   seed. The SPEC pins only `decks=0` and `decks=-1`. Logged as a contract-domain
   gap; no task-001 change.
3. **A `bool` stake leaks through PUSH.**
   `settle([KING, QUEEN], [JACK, QUEEN], stake=True)` returns
   `Settlement(PUSH, returned=True)`, confirmed on the workstation. Only PUSH
   leaks the boolean object; `PLAYER_WINS` and `PLAYER_BLACKJACK` arithmetic
   produces real `int` objects. Because `True == 1` and `bool` subclasses `int`,
   the arithmetic is numerically correct and the current `isinstance(returned,
   int)` property passes. A template renders `True`, not `1`, so this is the
   **highest-value follow-up for whichever task builds the web layer**. Revision
   6's wording that `stake=True` is accepted as 1 is looser than the observable
   result. Logged; no task-001 change.
4. **CI skips changed-line coverage on a push to `main`.** Dismissed because the
   workflow comment directly above the condition records why: a push to `main`
   has no changed-line comparison base, so the layer is skipped instead of
   silently replaced by overall coverage. Residual limitation: CI does not
   independently enforce this layer on the merge commit; the pre-merge
   workstation run establishes it.
5. **The stdlib-only import test is static-only.** It walks `ast.Import` and
   `ast.ImportFrom`; `importlib.import_module("hypothesis")` would evade it, and
   the import-linter contract names only `web`, `flask`, and `jinja2`. Must NOT
   1 is therefore executable only against static imports. Logged; no task-001
   change.
6. **The shoe property generates decks 1–4 only.** The explicit scenarios cover
   six decks, but a defect specific to deck count 5 or above 6 could pass even
   though the property contract says any `decks >= 1`. Logged; no task-001
   change.
7. **`Settlement` immutability is untested.** `Card` immutability has
   `tests/test_cards.py::test_card_is_frozen`; removing `frozen=True` from
   `Settlement` would pass tests, types, lint, coverage, and properties. Logged;
   no task-001 change.

Across all three rounds, no verifier found code diverging from what the
then-approved SPEC stated. Every accepted finding was instead something the
SPEC failed to say or the gauntlet failed to check.

## Layers not run as specified

- **Not applicable:** none.
- **Not available:** Mutation is configured, but `mutmut` has no native Windows
  support and is unrunnable on this workstation. The repository has no git
  remote, so no CI exists or has executed the workflow, and WSL has no installed
  distribution. Neither the mutation command nor its results gate has ever run
  elsewhere.
- **CI only, not reproduced here:** none.
- **Skipped:** none. Mutation is classified as not available, not skipped.

## Dismissed review findings

- **The vulture whitelist matches by bare name.** The four permitted names
  (`CLUBS`, `DIAMONDS`, `HEARTS`, `returned`) would also silence any future
  unused item with the same bare name. This is vulture's whitelist behavior and
  cannot be narrowed. The mitigation is revision 4's admission rule plus
  review. It was raised independently in rounds 1 and 2, increasing its standing
  as a known limitation without changing the reason for dismissal.
- **Stale scaffold `.pyc` files under `__pycache__`.** Dismissed because
  `__pycache__/` is gitignored, no scaffold source or test is tracked, and
  `import domain.scaffold` raises `ModuleNotFoundError`. Under PEP 3147, a
  `__pycache__` bytecode file is not importable without its source. Must NOT 6
  concerns what survives in the repository.
- **Round 3 finding 4: CI skips changed-line coverage on a push to `main`.**
  Dismissed because the workflow explains that a push to `main` has no
  changed-line base and deliberately avoids substituting overall coverage.
  Residual limitation remains: CI does not independently enforce changed-line
  coverage on the merge commit; the pre-merge workstation run is the evidence.

## Structural blind spot

Mutation is a project-wide structural blind spot in the current setup, not a
workstation-only limitation. `mutmut` is configured but cannot run natively on
the Windows workstation; the repository has no git remote or CI, and WSL has no
installed distribution. There is no second environment in which the mutation
command or its revision 2 results gate has run. Nothing in the current setup
catches weak tests through mutation anywhere. The six property tests are not
mutation evidence and do not establish that the suite kills changed behavior.

## Honest notes

- **The central observed limit:** not one of the three verification rounds found
  code diverging from the explicit contract. Every accepted finding across all
  rounds was something the SPEC failed to state or the gauntlet failed to
  check. This is the AGENTS.md §6 limit of evidence observed in this task: a
  green gauntlet can constrain what the contract expresses but cannot prove the
  contract complete or its checkers exhaustive.
- Claude ran `ruff format` on `tests/test_settlement.py` in both revision 5 and
  revision 6. Codex cannot execute `ruff format` from its sandbox, hand-formats,
  and landed just outside the formatter's required layout twice. This is a
  role-split pattern, not a one-off. Both Claude-side changes touched Codex-owned
  files, changed whitespace only, and are visible in the checkpoint commits.
- Codex's workspace-write sandbox could not execute `uv`, which lives outside
  the workspace, or write the checkpoint commits under `.git`. Claude therefore
  executed every supplied gauntlet command and made the checkpoints. Codex did
  not run or reproduce those results.
- Builder model: `gpt-5.6-sol`; verifier model: `gpt-5.5`. Vendor positioning
  calls the builder the latest frontier agentic coding model and the verifier a
  frontier model but not the latest. On positioning alone, with no benchmark,
  the verifier is probably somewhat weaker. This report claims proportionally
  less from its verification.
- Correlation is reduced, not eliminated. Builder and verifier share a vendor,
  and the same human approved the SPEC they commissioned.
- The verifier read a fifth item beyond the four blind inputs: its own
  `old-coder` skill definition from the agent configuration directory. That is
  configuration rather than repository content and did not expose the
  builder's account, but the protocol boundary said four inputs and nothing
  else, so the deviation is disclosed.
- Mutation and its revision 2 results gate have never been exercised anywhere.
  The layer's repair is therefore unproven, and the green gauntlet reported for
  this task never included a mutation result from any environment. Weak tests
  can go uncaught throughout the project's current setup; the six property
  tests are not equivalent evidence.
- The step 9 line-by-line diff review caught the report's false `CI only`
  classification. No gauntlet layer, EVIDENCE section, or independent
  verification round caught it. All three independent verification rounds read
  the `PROJECT.md` gauntlet table as one of their four blind inputs, yet none
  questioned whether the CI named there existed. This is an observed limit of
  the process and of treating configuration as evidence without establishing
  that its execution environment exists.
- No separate Cleanup negative-control execution result was supplied. This
  report claims the final clean-tree pass only, not proof from this record that
  the Cleanup checker was observed taking its failure path.
- The SPEC reached six revisions. Revisions 2–6 were each forced by a review or
  independent-verification finding and were never cosmetic.
