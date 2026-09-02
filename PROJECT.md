# PROJECT.md — this project's values

<!-- ============================================================ -->
<!-- This file holds answers, not instructions. How to fill each   -->
<!-- field is in AGENTS.md §14, which is overwritten on update.    -->
<!-- ============================================================ -->

## Project

A browser-based blackjack game with a Python server and server-rendered HTML. A
single human player sits at a table with 0–4 bot-driven seats, betting
session-only virtual chips against the dealer.

It deliberately does not persist anything across restarts, has no accounts, no
real money, and no client-side JavaScript. It exists to exercise this baseline
end to end, so the gauntlet matters more than the game.

Rules: hit / stand / double / split. Dealer soft-17 behaviour is chosen by the
player at the start (S17 or H17). Blackjack pays 3:2; double on any two cards;
dealer peeks; ties push; re-split to at most 4 hands; split aces get one card
each; 21 after a split pays 1:1, not 3:2. No insurance, surrender, or side bets.

Interface: one page, form submissions only, POST-Redirect-GET so a refresh
cannot deal an extra card. State lives in the server-side session. The page
shows the dealer's upcard, each seat's hand and total, the bankroll, the
available actions, and one line for the previous hand's result. Bets are typed
as integers with a minimum and maximum. When the bankroll reaches zero the game
ends with a summary. Bot seats hit below 17 and stand otherwise.

## Tech stack

Python 3.13, managed by uv. Flask with Jinja2 templates. No client-side
JavaScript, no frontend build step. Dependencies are pinned in `pyproject.toml`
and `uv.lock`.

## Commands

```bash
uv sync                               # install
uv run flask --app src.web.app run    # run
uv run pytest -q                      # test
uv run ruff check .                   # lint
uv run mypy src tools                 # typecheck
```

## Gauntlet commands

| Layer | Command |
|---|---|
| Tests | `uv run pytest -q` |
| Types | `uv run mypy src tools` |
| Lint + format | `uv run ruff check . && uv run ruff format --check .` |
| Changed-line coverage | `uv run pytest --cov=src --cov=tools --cov-branch --cov-report=xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=100` |
| Mutation | `uv run python tools/mutation_gate.py` — scoped to `src/domain` and `tools` via `[tool.mutmut] source_paths`; the gate fails on every non-killed status, retries only timeouts with a doubled `timeout_multiplier`, and fails if no mutants were generated. **`CI only`.** mutmut has no native Windows support and refuses to run on this workstation. CI run `33394233626` generated mutants and began stats collection before aborting; later, CI run `33485359092` on PR #1 tested 129 mutants, killed all 129 with 0 survivors, and passed all eight layers. |
| Property-based | `uv run pytest -m property -q` — pytest exits 5 when nothing is collected, so the layer fails if no property tests exist |
| Cleanup | `uv run ruff check --select F401,F811,F841 . && uv run vulture src tests tools` |

Architecture check: `uv run lint-imports` (import-linter; the contract lives in
`ARCHITECTURE.md` and is configured in `pyproject.toml`)

## Branches

- Main branch: `main`
- Task branch naming: `task/<NNN-kebab-slug>`

## Agent models

| Role | Model | Reasoning effort |
|---|---|---|
| Builder, Tier 1 | `gpt-5.6-sol` | `medium` |
| Builder, Tier 2 | `gpt-5.6-sol` | `high` |
| Builder, Tier 3 | `gpt-5.6-sol` | `xhigh` |
| Verifier, Tier 3 | `gpt-5.5` | `xhigh` |

Configured default effort: `xhigh` — the highest any Tier uses, so a forgotten
per-call override wastes reasoning instead of quietly under-thinking a Tier 3
change. Tier 1 and Tier 2 override downward with
`-c model_reasoning_effort=medium` and `=high`.

Capability gap between builder and verifier: the builder uses `gpt-5.6-sol`,
described by the vendor as the *latest frontier* agentic coding model. `gpt-5.5`
is the strongest remaining candidate — also described as frontier, but not the
latest — so the verifier is probably somewhat weaker than the builder, on
positioning alone with no benchmark to confirm it. `gpt-5.6-terra` and
`gpt-5.6-luna` are positioned lower still ("balanced everyday", "fast and
affordable") and are not eligible. Tier 3 EVIDENCE claims proportionally less
from a verification run under this gap.

Fallback when the builder model is unavailable: `gpt-reserve`.

Codex sandbox and approval policy in force: `-s` is passed explicitly on every
call — `read-only` for the feasibility review and the verifier, `workspace-write`
for the build. The configured approval policy is `OnRequest`, observed to
*reject* a write under a read-only sandbox rather than auto-approve it. Re-check
with `codex doctor` after any Codex update: the policy is inherited from account
configuration, not fixed by the CLI.

## Project-specific safety

The bankroll is virtual chips that never leave the process, so the Tier 3 "real
funds" trigger in AGENTS.md §3 does not fire here. §3 now names this case
directly — a simulated currency that never leaves the process is not real funds
— so this is the reading the rule asks to be recorded, not an interpretation
stretched around it. The earlier wording said "money" and did fire here; that
was filed as a baseline defect and fixed in v2.5.1.

If real payments are ever added the reading is void, and every task touching
them is Tier 3 without further argument.

Otherwise: none. No regulated data, no accounts, no external services.
