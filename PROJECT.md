# PROJECT.md — this project's values

<!-- ============================================================ -->
<!-- PROJECT LAYER. This file is yours; the baseline never edits   -->
<!-- it and an update never overwrites it.                         -->
<!--                                                               -->
<!-- The required fields are defined in AGENTS.md §14. After a      -->
<!-- baseline update, reconcile this file against that list:        -->
<!-- append any missing field as a placeholder in the same form as  -->
<!-- the ones below, then fill it in.                               -->
<!--                                                               -->
<!-- Any placeholder left unfilled is a setup defect. This comment  -->
<!-- block deliberately avoids writing the placeholder token, so    -->
<!-- that counting it in this file counts only real blanks.         -->
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
uv run mypy src                       # typecheck
```

## Gauntlet commands

One command per layer. Delete no row: if a layer cannot run in this project,
write `not available` and the reason — that row becomes the Structural blind
spot in every EVIDENCE report, and CI wires only the rows that have commands.

| Layer | Command |
|---|---|
| Tests | `uv run pytest -q` |
| Types | `uv run mypy src` |
| Lint + format | `uv run ruff check . && uv run ruff format --check .` |
| Changed-line coverage | `uv run pytest --cov=src --cov-branch --cov-report=xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=100` |
| Mutation | `uv run mutmut run` — scoped to `src/domain` via `[tool.mutmut] paths_to_mutate`; the layer fails if any mutant survives |
| Property-based | `uv run pytest -m property -q` — pytest exits 5 when nothing is collected, so the layer fails if no property tests exist |
| Cleanup | `uv run ruff check --select F401,F811,F841 . && uv run vulture src` |

Architecture check: `uv run lint-imports` (import-linter; the contract lives in
`ARCHITECTURE.md` and is configured in `pyproject.toml`)

See `SETUP.md` §4 for per-language tool suggestions and install commands.

## Branches

- Main branch: `main`
- Task branch naming: `task/<NNN-kebab-slug>`

Checkpoints are commits on the task branch (AGENTS.md §12). Nothing reaches the
main branch without human authorisation.

## Agent models

Model names and effort levels change often and differ per account, so they live
here. The rules they must satisfy are in AGENTS.md §11.

| Role | Model | Reasoning effort |
|---|---|---|
| Builder, Tier 2–3 | `gpt-5.6-sol` | `xhigh` |
| Builder, Tier 1 | same as above | `low`, passed per call with `-c model_reasoning_effort=low` |
| Verifier, Tier 3 | `gpt-5.6-terra` — judged by the human to be at least `gpt-5.6-sol`'s equal | `xhigh` |

Fallback when the builder model is unavailable: `gpt-reserve`.

Codex sandbox and approval policy in force: `-s` is passed explicitly on every
call; the configured approval policy is `OnRequest`, which was observed to
*reject* a write under a read-only sandbox rather than auto-approve it. Re-check
with `codex doctor` after any Codex update — the policy is inherited from
account configuration, not fixed by the CLI.

## Project-specific safety

The bankroll is virtual chips that never leave the process, so the Tier 3
"money" trigger in AGENTS.md §3 does not apply here. This is recorded as a
deliberate reading of that rule, not a waiver: the rule says "money" where it
means funds that can actually leave the system, and that wording is filed as a
baseline defect. If real payments are ever added, every task touching them is
Tier 3 without further argument.

Otherwise: none. No regulated data, no accounts, no external services.
