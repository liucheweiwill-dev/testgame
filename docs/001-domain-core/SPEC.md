# SPEC — 001 domain core (Tier 3), revision 3

## Goal

The blackjack rules that do not need a table, a bet or a second seat: what a
card is worth, what a hand totals when aces can count two ways, a shoe that
deals reproducibly from a seed, and who wins a single settled hand.

Nothing in this task knows about HTTP, sessions, bots, chips held between hands,
splitting or doubling. Settlement computes what a stake returns; it does not
place, validate or store bets. Later tasks own the rest.

## API

Every symbol below is public and its signature is fixed by this SPEC. An
implementation that exposes a different shape has not met it.

```python
# src/domain/cards.py
class Rank(Enum):    TWO … TEN, JACK, QUEEN, KING, ACE
class Suit(Enum):    CLUBS, DIAMONDS, HEARTS, SPADES

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

def card_value(rank: Rank) -> int          # ACE -> 11; hand_total demotes it

# src/domain/hand.py
def hand_total(cards: Sequence[Card]) -> int
def is_soft(cards: Sequence[Card]) -> bool
def is_bust(cards: Sequence[Card]) -> bool
def is_blackjack(cards: Sequence[Card]) -> bool

# src/domain/shoe.py
class ShoeExhausted(Exception): ...

class Shoe:
    def __init__(self, decks: int, seed: int) -> None   # decks < 1 -> ValueError
    def deal(self) -> Card                              # empty -> ShoeExhausted
    def remaining(self) -> int

# src/domain/settlement.py
class DealerRule(Enum):  STAND_ON_SOFT_17, HIT_ON_SOFT_17
class Outcome(Enum):     PLAYER_BLACKJACK, PLAYER_WINS, DEALER_WINS, PUSH

@dataclass(frozen=True)
class Settlement:
    outcome: Outcome
    returned: int        # chips handed back, stake included; 0 when the player loses

def dealer_should_hit(cards: Sequence[Card], rule: DealerRule) -> bool
def settle(player: Sequence[Card], dealer: Sequence[Card], stake: int) -> Settlement
```

Hands are `Sequence[Card]` everywhere. Scenario tables below name ranks alone
for brevity; the tests construct real `Card` values with distinct suits unless a
scenario says otherwise.

## Settlement rules

Evaluated strictly in this order — the order is the specification:

1. Player bust → `DEALER_WINS`, `returned = 0`. **Even if the dealer also
   busts**: the player busts first and loses immediately.
2. Both blackjack → `PUSH`, `returned = stake`.
3. Player blackjack only → `PLAYER_BLACKJACK`, `returned = stake + stake * 3 // 2`.
4. Dealer blackjack only → `DEALER_WINS`, `returned = 0`.
5. Dealer bust → `PLAYER_WINS`, `returned = stake * 2`.
6. Otherwise compare totals: higher wins; `PLAYER_WINS` returns `stake * 2`,
   `DEALER_WINS` returns `0`, equal totals give `PUSH` returning `stake`.

**The 3:2 payout truncates.** `stake * 3 // 2` is integer division; an odd stake
pays the floor. Chips are whole and there is no half-chip unit.

`PUSH` therefore means exactly: both hold blackjack, or neither holds blackjack,
neither is bust, and their totals are equal. Nothing else pushes.

## Scenarios

**Card values**

| Input | Expected |
|---|---|
| `card_value(TWO)` … `card_value(TEN)` | `2` … `10` |
| `card_value(JACK)`, `card_value(QUEEN)`, `card_value(KING)` | `10` each |
| `card_value(ACE)` | `11` |

**Hand totals**

| Hand | `hand_total` | `is_soft` |
|---|---|---|
| `[ACE, KING]` | `21` | `True` |
| `[ACE, SIX]` | `17` | `True` |
| `[ACE, SIX, KING]` | `17` | `False` |
| `[ACE, ACE]` | `12` | `True` |
| `[ACE, ACE, ACE]` | `13` | `True` |
| `[ACE, ACE, NINE]` | `21` | `True` |
| `[KING, QUEEN, FIVE]` | `25` | `False` |
| `[]` | `0` | `False` |

**Blackjack**

- `is_blackjack([ACE, KING])` → `True`; `is_blackjack([KING, ACE])` → `True`
- `is_blackjack([ACE, NINE, ACE])` → `False` — 21 on three cards is not blackjack

**Shoe**

- `Shoe(decks=6, seed=42).remaining()` → `312`
- Dealing all 312 yields exactly 6 copies of every one of the 52 `(Rank, Suit)`
  pairs — compared as a `Counter` against the canonical multiset, not by
  counting ranks alone.
- Two `Shoe(decks=6, seed=42)` deal identical sequences.
- `seed=42` and `seed=43` deal different sequences.
- `remaining()` decreases by one per `deal()`; the 313th `deal()` raises
  `ShoeExhausted`.
- `Shoe(decks=0, seed=1)` and `Shoe(decks=-1, seed=1)` raise `ValueError`.
- **Constructing and fully dealing a `Shoe` leaves `random.getstate()`
  unchanged.**

**Dealer play**

| Dealer hand | Rule | `dealer_should_hit` |
|---|---|---|
| `[KING, SEVEN]` hard 17 | S17 | `False` |
| `[KING, SEVEN]` hard 17 | H17 | `False` — H17 concerns *soft* 17 only |
| `[ACE, SIX]` soft 17 | S17 | `False` |
| `[ACE, SIX]` soft 17 | H17 | `True` |
| `[KING, SIX]` 16 | either | `True` |
| `[KING, EIGHT]` 18 | either | `False` |

**Settlement** — stake `10` unless stated.

| Player | Dealer | `outcome` | `returned` |
|---|---|---|---|
| blackjack | blackjack | `PUSH` | `10` |
| blackjack | 21 on three cards | `PLAYER_BLACKJACK` | `25` |
| blackjack | 20 | `PLAYER_BLACKJACK` | `25` |
| **blackjack, stake 5** | 20 | `PLAYER_BLACKJACK` | **`12`** — `5 + 5*3//2` |
| **blackjack, stake 1** | 20 | `PLAYER_BLACKJACK` | **`2`** — `1 + 1*3//2`, and `1*3//2` is `1`, not `0` |
| 20 | blackjack | `DEALER_WINS` | `0` |
| 20 | 19 | `PLAYER_WINS` | `20` |
| 19 | 20 | `DEALER_WINS` | `0` |
| 20 | 20 | `PUSH` | `10` |
| 22 bust | 23 bust | `DEALER_WINS` | `0` |
| 18 | 24 bust | `PLAYER_WINS` | `20` |

## Must NOT

1. `src/domain` imports nothing outside the Python standard library — not
   `hypothesis`, not `pytest`, nothing installed. Enforced by an executable
   test over `sys.stdlib_module_names`, because the import-linter contract names
   only `web`, `flask` and `jinja2` and would pass a third-party import.
2. No global randomness. Every shuffle derives from the seed passed in.
   `random.seed(...)` followed by module-level `random.shuffle` is the specific
   defect this forbids, and the `getstate()` scenario is what detects it.
3. No `Config` object, no strategy interface, no card factory, no abstraction
   with a single implementation. `DealerRule` is a two-valued enum, not a
   pluggable policy.
4. No split, double, insurance, surrender, bet validation or bot logic — not
   even stubbed.
5. Payout arithmetic is integer throughout. No float touches a stake.
6. The bootstrap scaffolding does not survive: `src/domain/scaffold.py`,
   `tests/test_scaffold.py` and `tests/test_scaffold_properties.py` are deleted,
   and the Cleanup layer stays green afterwards.

## Failure model (Tier 3)

This module has no I/O, so every way it can hurt is a wrong number reaching a
caller that trusts it. Each mode names the check that catches it.

| Failure mode | Check |
|---|---|
| Ace demoted always, or never | `[ACE, ACE, NINE]` and `[ACE, SIX, KING]` scenarios; the total-bounds property |
| Blackjack confused with a three-card 21 | dedicated scenarios plus the exact `PUSH` definition |
| Bust ordering inverted — both bust scored by total | the `22 vs 23 bust` scenario |
| 3:2 payout rounded up, or floated | stake 5 and stake 1 boundary scenarios |
| Shoe reproducible but globally seeded | `random.getstate()` unchanged scenario |
| Shoe short, or wrong suit composition | canonical `(Rank, Suit)` multiset comparison |
| Dead code left behind by the scaffold removal | Cleanup layer, after its threshold is lowered (below) |
| Weak tests that no assertion catches | Mutation layer — **CI only on this workstation** |

## Files to edit

```
src/domain/cards.py         new
src/domain/hand.py          new
src/domain/shoe.py          new
src/domain/settlement.py    new
tests/                      new tests, including tests marked `property`
pyproject.toml              vulture min_confidence and paths; mutmut scope if needed
PROJECT.md                  Mutation row only — add the results gate
.github/workflows/gauntlet.yml   Mutation step only — add the results gate
```

Deleted: `src/domain/scaffold.py`, `tests/test_scaffold.py`,
`tests/test_scaffold_properties.py`.

**The Mutation layer currently cannot fail.** `mutmut run` prints survivor
statistics and exits 0 — verified in the locked mutmut 3.7.0 source — so the
layer is decoration under AGENTS.md §5. This change adds a gate that exits
non-zero when any mutant survives. That is why `PROJECT.md` and the workflow are
editable here, for that row and that step only.

**The Cleanup layer under-reports.** `min_confidence = 80` filters out vulture's
unused-function and unused-class findings, which carry 60. Lower the threshold,
scan tests alongside `src`, and prove the gate works with a deliberately dead
function that is removed once the layer has been seen to fail on it.

## Do not modify

```
AGENTS.md  CLAUDE.md  SETUP.md      general layer
ARCHITECTURE.md                      the dependency contract
.gitignore  .mcp.json                
uv.lock                              no new dependency is approved
docs/development-status.md           Claude writes this at step 10
PROJECT.md                           except the Mutation row
.github/workflows/gauntlet.yml       except the Mutation step
```

## Setup plan

- **No new dependencies.** Everything needed is installed and locked. Adding one
  requires a further revision and re-approval.
- **Files the gauntlet adds:** `coverage.xml` and the caches already in
  `.gitignore`. Nothing new needs ignoring.
- **Checkpoints:** the two AGENTS.md §12 requires, no more. **Claude makes
  them**, not Codex — see the execution split below.
- Branch `task/001-domain-core`, from `main`.

## Acceptance tests

Every row of every table under **Scenarios** is a named test. Beyond those:

- **Property**: for any hand of 1–10 cards, `hand_total` never exceeds the sum
  of the cards' soft values and never falls below the sum of their hard values.
- **Property**: a hand with no ace has `is_soft() == False` and a total equal to
  the plain sum of its card values.
- **Property**: for any seed and any `decks ≥ 1`, dealing the shoe dry yields a
  `Counter` exactly equal to `decks` copies of all 52 `(Rank, Suit)` pairs.
- **Property**: `settle` returns `PUSH` if and only if both hands are blackjack,
  or neither is blackjack, neither is bust, and the totals are equal.
- **Test**: no module under `src/domain` imports a name outside
  `sys.stdlib_module_names`.
- **Test**: constructing and exhausting a `Shoe` leaves `random.getstate()`
  unchanged.
- **Negative control**: a deliberately unused function makes the Cleanup layer
  exit non-zero. Removed once observed; its purpose is to prove the layer fails.

## Commands to run

The full gauntlet from `PROJECT.md`, in order — not only the new test files:

```bash
uv run pytest -q
uv run mypy src
uv run ruff check . && uv run ruff format --check .
uv run pytest --cov=src --cov-branch --cov-report=xml \
  && uv run diff-cover coverage.xml --compare-branch=main --fail-under=100
uv run pytest -m property -q
uv run ruff check --select F401,F811,F841 . && uv run vulture src tests
uv run lint-imports
```

**Claude runs these, not Codex.** Codex's `workspace-write` sandbox cannot
execute `uv`, which lives outside the workspace, and cannot write `.git` — so it
can neither run the gauntlet as specified nor make a checkpoint commit. Codex
writes the code; Claude executes the gauntlet and records the results. Neither
side can assert an outcome the other did not produce, which suits the double
track better than the original split did.

Mutation is `CI only` here — mutmut has no native Windows support. Record it
under "Layers not run as specified — CI only, not reproduced here", never as
skipped, and state that the new results gate is therefore unverified locally.

## Risk notes

- Ace demotion, blackjack-versus-21, and bust ordering are the three classic
  defects in this domain. All three are in the failure model with named checks.
- Mutation cannot run locally, so weak tests go uncaught until CI. The property
  tests are the local substitute and are required, not optional.
- Two gauntlet layers are being repaired inside a task that also writes domain
  code. That is unusual and deliberate: both were discovered by this SPEC's own
  feasibility review, and shipping domain code behind checks known not to fail
  would be worse. Keep the two concerns in separate commits.
- **Tier 3 by structural trigger, not by domain risk.** AGENTS.md §3 fires on
  "a new module" and "more than 2 new services/classes", both unavoidable in a
  greenfield package. The rule reads as though it assumes an existing codebase;
  that is filed against the baseline and is **not** grounds for lowering this
  task. The Tier stands.

## Human approval

Revision 1: superseded, never approved.
Revision 2: approved by Will, 2026-08-28; superseded by revision 3.
Revision 3: **approved by Will, 2026-08-28**.

## Revisions

**Revision 3** — three findings from the implementation attempt:

- **The stake-1 scenario was arithmetically wrong.** `1 * 3 // 2` is `1`, not
  `0`, so the payout is `2`. Codex left the test RED and reported the
  contradiction instead of bending the implementation to a false SPEC — which is
  what a boundary scenario is for, even when the boundary catches its author.
- **Codex cannot make checkpoint commits.** Its sandbox refuses writes to
  `.git`, which is a deliberate protection and not something to relax for
  convenience. Checkpoints move to Claude.
- **Codex cannot run the gauntlet as specified.** `uv` lives outside the
  workspace and the sandbox will not execute it. Codex declined to substitute
  the `.venv` binaries and call them the specified commands, which is the
  correct reading of the rule. Execution moves to Claude.

**Revision 2** — rewritten after the Codex feasibility review raised ten
findings, nine accepted:

- Tier 2 → **Tier 3** on the §3 structural triggers, with a failure model added.
  Codex raised it; the ratchet permits that and forbids arguing it down.
- Added the **API** section. Revision 1 named `settle` without a return shape,
  and mixed bare ranks with a `Card` type.
- Defined the **settlement precedence** as an ordered list, and `PUSH` exactly.
  Revision 1's PUSH property contradicted its own blackjack-versus-21 row.
- **3:2 truncates**; stake 5 and stake 1 boundary scenarios added. Revision 1
  demanded integer payouts and 3:2 without saying what an odd stake does.
- Must NOT 1 is now enforced by a `sys.stdlib_module_names` test. The
  import-linter contract names three modules and never enforced the invariant it
  was mapped to.
- Added the `random.getstate()` scenario. Revision 1's seed tests passed for the
  globally-seeded implementation it forbade.
- Shoe composition compares the full `(Rank, Suit)` multiset, not rank counts.
- `PROJECT.md` and the CI workflow become editable for the Mutation row, which
  could not fail as configured; the Cleanup threshold is lowered with a negative
  control proving the gate works.

**Revision 1** — initial. Scope settled in a `/grill-me` session covering 22
decisions on rules, interface, stack and gauntlet.
