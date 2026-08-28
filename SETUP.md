# SETUP.md — Installing a Claude + Codex workstation

<!-- ============================================================ -->
<!-- GENERAL LAYER v2.3.0 — DO NOT EDIT.                          -->
<!-- Single source: https://github.com/liucheweiwill-dev/ai-sw-baseline                           -->
<!-- MIT licensed. Copyright (c) 2026 Will. Full text: LICENSE in that repo. -->
<!-- ============================================================ -->

> **Agents: do not install anything automatically.**
> Every command below is for a human to run, or for an agent to run **only
> after the human confirms that specific command**. Installing software is an
> irreversible change to a machine you do not own. Show the command, say what
> it does, wait.

Primary commands are Windows. macOS and Linux equivalents follow each one.
Every step has a verification command — run it before moving on.

**Scope: this file covers the workstation, once per machine.** Creating or
updating a *project* from the baseline — copying these files, filling in
`PROJECT.md`, wiring CI — is a separate procedure: `BOOTSTRAP.md` in the
baseline repository.

---

## 1. Prerequisites

| Tool | Check | Windows | macOS / Linux |
|---|---|---|---|
| git | `git --version` | `winget install Git.Git` | `brew install git` / distro package |
| Node + npm | `node --version && npm --version` | `winget install OpenJS.NodeJS.LTS` | `brew install node` / distro package |
| Claude Code | see its own docs | — | — |
| Codex CLI | `codex --version` | see its own docs | — |

**Neither agent's CLI is guaranteed to be on PATH.**

- *Codex*: the desktop-app build installs the CLI under a content-hashed
  directory that **changes on every update**. Never hard-code that path in a
  script or config. Resolve it at run time, or install the standalone CLI.
- *Claude Code*: a desktop-app install may expose no `claude` command at all, so
  `claude mcp list` and similar checks are simply unavailable. Verify its MCP
  servers from inside an interactive session (`/mcp`) or by reading the project's
  `.mcp.json`, and do not treat the missing command as a broken installation.

A check that cannot run is a finding to report, not a line to work around.

Verify Codex can reach a model before continuing:

```bash
codex exec --skip-git-repo-check "reply with OK and nothing else"
```

### 1.1 Git identity — required, once per machine

Commit authorship is per-machine configuration. A workstation that skips this
produces commits attributed to nobody, or to whoever used the machine before.

```bash
git config --global user.name  "<your name>"
git config --global user.email "<the email verified on your git host account>"
```

Verify the **effective** values from inside the project, not the global ones —
a repository-local override wins, and that is exactly how commits end up
attributed to the wrong person on a shared machine:

```bash
git -C <project> config user.name
git -C <project> config user.email
```

The email must be **verified on the account of your git host**, or the commits
will not be attributed to you. If your host offers a private no-reply address
and you enable its "block pushes that expose my email" setting, use the
no-reply address here instead — otherwise pushes are rejected outright.

### 1.2 Git host access — only if the baseline repo is on GitHub

The baseline is distributed through *a git repository*. Nothing in these rules
requires that repository to be on GitHub. Skip this section entirely for a
self-hosted or non-GitHub remote; plain `git` plus that host's normal
credentials is enough.

For GitHub-hosted remotes, the GitHub CLI is worth the install because it
solves credential setup and multi-account switching in one place:

```bash
winget install --id GitHub.cli --exact --silent --accept-package-agreements --accept-source-agreements
```

macOS / Linux: `brew install gh`, or your distro package.

Then, in a **new** shell:

```bash
gh auth login
```

Answer: GitHub.com · HTTPS · **Yes** to "Authenticate Git with your GitHub
credentials" · log in with a web browser. Confirm the browser is signed into
the intended account before approving.

```bash
gh auth status
gh auth setup-git      # run explicitly if you answered "No" above
```

Multiple accounts on one machine: `gh auth login` again for the second account,
then `gh auth switch` to change the active one.

> **`gh auth switch` changes push authentication only.** It does not touch
> `user.name` or `user.email`, so after switching, commits still carry the
> previous account's identity while pushing as the new one — and the commits
> land unattributed. Switching accounts means changing both: `gh auth switch`
> *and* the identity in §1.1, set per-repository when the machine serves more
> than one account.

> **Trap — a machine that already pushed as a different account.**
> Cached credentials outlive any change to `user.email`. On Windows they sit in
> Credential Manager; `git push` keeps using them and authenticates as the old
> account, silently. Setting a new commit email does **not** fix this, because
> commit authorship and push authentication are different things.
>
> `gh auth setup-git` is the fix: it resets the inherited credential-helper
> chain for `github.com` and installs `gh` in its place, so the stale entries
> are never consulted. It leaves them in place, so other tools that rely on
> them (IDEs, for example) keep working.
>
> Verify with `git config --global --get-regexp credential` — you should see a
> blank `credential.https://github.com.helper` (the reset) followed by one
> pointing at `gh auth git-credential`. If only the blank line or neither is
> present, `setup-git` never ran.

---

## 2. Skills

Installed with the `skills` CLI over `npx` — nothing to install first.

Two constraints, both learned the hard way:

- `-a` takes **one agent per invocation**. A comma-separated list is rejected.
- Use `--copy` on Windows. The default symlink mode needs Developer Mode or an
  elevated shell.

### Both agents

```bash
npx skills@latest add AmazingAng/old-coder -s old-coder -a claude-code -g -y --copy
npx skills@latest add AmazingAng/old-coder -s old-coder -a codex -g -y --copy

npx skills@latest add DietrichGebert/ponytail -s ponytail-review -a claude-code -g -y --copy
npx skills@latest add DietrichGebert/ponytail -s ponytail-review -a codex -g -y --copy

npx skills@latest add DietrichGebert/ponytail -s ponytail-audit -a claude-code -g -y --copy
npx skills@latest add DietrichGebert/ponytail -s ponytail-audit -a codex -g -y --copy

npx skills@latest add JUNERDD/skills -s exhaustive-code-slimmer -a claude-code -g -y --copy
npx skills@latest add JUNERDD/skills -s exhaustive-code-slimmer -a codex -g -y --copy
```

### Claude only

`grill-me` is a design-convergence tool used before the SPEC exists, and only a
human can invoke it. `grilling` carries the actual procedure — **`grill-me`
does nothing without it.**

```bash
npx skills@latest add mattpocock/skills -s grill-me -a claude-code -g -y --copy
npx skills@latest add mattpocock/skills -s grilling -a claude-code -g -y --copy
```

### Verify

```bash
npx skills@latest list -g
```

Expected: `old-coder`, `ponytail-review`, `ponytail-audit`,
`exhaustive-code-slimmer` on both agents; `grill-me` and `grilling` on Claude
Code. Skills load at session start — **restart both agents**.

### Note on `exhaustive-code-slimmer`

Its security scan reports **Medium risk, 1 alert**, unlike the others. The
cause is what it openly does: it ships Python scripts that run a subprocess (the
behaviour-preservation oracle you give it) and delete files. An inspection of
those scripts found no network access, no `eval`/`exec`, and no `os.system`.
The practical safeguard is the checkpoint commit `AGENTS.md` §12 requires
before the Cleanup layer runs. Remove it with:

```bash
npx skills@latest remove -s exhaustive-code-slimmer -g -y
```

---

## 3. Serena MCP

Symbol-level navigation for both agents: find definitions, references and
implementations without reading whole files. It replaces the
grep -> read -> grep loop, which is the single largest avoidable token cost.

### 3.1 Install uv

```bash
winget install --id astral-sh.uv --exact --silent --accept-package-agreements --accept-source-agreements
```

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `uv --version`

### 3.2 Install Serena

```bash
uv tool install -p 3.13 serena-agent
uv tool update-shell
```

`uv tool update-shell` puts `~/.local/bin` on PATH. **Do not skip it** — the
MCP configuration below relies on the bare command `serena` so that no config
file contains a machine-specific absolute path.

Open a new shell, then verify:

```bash
serena --version
serena init
```

> **Known failure on Windows.** `uv tool install` may abort with
> `Missing expected target directory for Python minor version link`. uv creates
> the minor-version junction before extraction finishes, leaving a link that
> resolves but cannot be traversed. Retrying does not help. Delete the link
> only — never the target — and rerun:
>
> ```powershell
> [System.IO.Directory]::Delete("$env:APPDATA\uv\python\cpython-3.13-windows-x86_64-none", $false)
> ```

### 3.3 Connect Serena to Codex

```bash
codex mcp add serena -- serena start-mcp-server --project-from-cwd --context=codex
codex mcp list
```

`serena setup codex` also exists, but it fails when `codex` is not on PATH.

### 3.4 Connect Serena to Claude Code

User scope, all projects:

```bash
claude mcp add --scope user serena -- serena start-mcp-server --context claude-code --project-from-cwd
```

Per project instead — commit this as `.mcp.json` in the repository root:

```json
{
  "mcpServers": {
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--context", "claude-code", "--project-from-cwd"]
    }
  }
}
```

> Do not hand-edit `~/.claude.json` while a Claude Code session is running. The
> session holds that file and will overwrite external edits when it exits —
> leaving a configuration that looks installed but is not.

---

## 4. Language-layer tooling

`AGENTS.md` fixes the seven gauntlet **layers**; this section suggests the
tools. Fill the actual commands into `PROJECT.md`. If a
layer has no tool in your language, write `not available` and the reason —
that becomes the Structural blind spot in every EVIDENCE report.

**A tool can exist and still not run where you are.** Some of the tools below
are unavailable on some platforms — mutmut on Windows is the one this baseline
has actually hit — so a layer can be runnable in CI and not on the workstation.
That is the `CI only` state in `AGENTS.md` §5. Record it as such, rather than
pretending either that the layer works everywhere or that it does not exist.

One rule outranks tool choice: **a layer must be able to fail.** A coverage run
without a threshold flag prints a number and exits 0 — it is decoration, not a
layer.

**Changed-line coverage needs a comparison base.** Overall coverage can sit at
90% while every line the change added is untested, so an overall-coverage gate
does not implement this layer. Where a diff-aware tool exists it is given below.
Where none does, record the layer as `not available (only overall coverage)`
with the overall gate as a fallback command — the gap is then visible in every
EVIDENCE report instead of being papered over by a passing number.

**Installation.** Each language block starts with the install command for its
tools. A human runs it. When an agent finds a tool missing, it shows that line
and stops — it does not install. Claude Code and Codex themselves install from
their own vendors' documentation; this file does not restate those.

### Python

```bash
pip install pytest mypy ruff pytest-cov diff-cover mutmut hypothesis vulture import-linter
```

| Layer | Tool | Command |
|---|---|---|
| Tests | pytest | `pytest -q` |
| Types | mypy / pyright | `mypy <pkg>` |
| Lint + format | ruff | `ruff check . && ruff format --check .` |
| Changed-line coverage | coverage.py + diff-cover | `pytest --cov=<pkg> --cov-branch --cov-report=xml && diff-cover coverage.xml --compare-branch=<base> --fail-under=<n>` |
| Mutation | mutmut | `mutmut run` — then `mutmut results`; survivors fail the layer. **Does not run natively on Windows** — it exits telling you to use WSL. On a Windows workstation record this layer as `CI only` and run it in CI on Linux. |
| Property | hypothesis | runs inside `pytest`; the layer is "the suite contains `@given` properties for the invariants in the SPEC" |
| Cleanup | ruff + vulture | `ruff check --select F401,F811,F841 . && vulture <pkg>` |

Architecture: **import-linter** (`lint-imports`) enforces the layer contract in
`ARCHITECTURE.md` and rejects cycles. This is the deterministic check that a
prompt rule cannot provide.

### JavaScript / TypeScript

```bash
npm i -D vitest typescript eslint @vitest/coverage-v8 @stryker-mutator/core fast-check knip dependency-cruiser
```

| Layer | Tool | Command |
|---|---|---|
| Tests | vitest / jest | `npx vitest run` |
| Types | tsc | `npx tsc --noEmit` |
| Lint + format | eslint | `npx eslint .` |
| Changed-line coverage | vitest coverage | `not available` out of the box — v8 coverage has no diff mode. Gate overall coverage with `coverage.thresholds` in the config and record the gap. |
| Mutation | Stryker | `npx stryker run` with `mutate` scoped to the changed files |
| Property | fast-check | runs inside the test suite; the layer is "properties exist for the SPEC's invariants" |
| Cleanup | knip | `npx knip` |

Architecture: **dependency-cruiser** for forbidden edges and cycles.

### C++

| Layer | Tool | Command |
|---|---|---|
| Tests | GoogleTest / Catch2 via CTest | `ctest --output-on-failure` |
| Types | the compiler | configure `-Werror` once, then build normally: `cmake -S . -B build -DCMAKE_CXX_FLAGS="-Werror" && cmake --build build` |
| Lint + format | clang-tidy, clang-format | `clang-tidy` on changed files; `clang-format --dry-run --Werror` |
| Changed-line coverage | llvm-cov / OpenCppCoverage | `not available` as a diff gate — emit a report and set an overall threshold, and record the gap |
| Mutation | mull | scope to changed translation units |
| Property | RapidCheck | runs inside the test binary; the layer is "properties exist for the SPEC's invariants" |
| Cleanup | include-what-you-use | `iwyu_tool.py -p build` plus `-Wunused` in the build flags |

> `cmake --build . -- -Werror` does **not** work: arguments after `--` go to the
> build backend, so Ninja rejects the flag and Make reads it as a Make option.
> The compiler never sees it. Set it in the CMake flags as above.

Architecture: **clang-uml** renders include and dependency diagrams. Generate
before and after a change and compare — a diff in the dependency graph that the
SPEC did not call for is a finding.

### Go

Install: `go install honnef.co/go/tools/cmd/staticcheck@latest`

Tests `go test ./... -race` · Types `go build ./...` · Lint
`go vet ./... && staticcheck ./...` · Changed-line coverage `not available` —
gate overall with `go test -coverprofile` plus a threshold script, record the
gap · Mutation no mature default, record `not available` · Property `rapid` ·
Cleanup `staticcheck` unused checks.

### Rust

Install: `cargo install cargo-llvm-cov cargo-mutants cargo-udeps`

Tests `cargo test` · Types `cargo check` · Lint `cargo clippy -- -D warnings` ·
Changed-line coverage `not available` — gate overall with
`cargo llvm-cov --branch --fail-under-lines <n>`, record the gap · Mutation
`cargo mutants --file <changed>` · Property `proptest` · Cleanup `cargo-udeps`.

### Java

Install: declare Checkstyle, Spotless, JaCoCo, PIT and jqwik as build plugins;
there is no separate install step.

Tests `./mvnw test` · Types `./mvnw compile` · Lint
`./mvnw checkstyle:check spotless:check` · Changed-line coverage `not available`
— JaCoCo check rules gate overall, record the gap · Mutation PIT, scoped to
changed classes · Property jqwik · Cleanup Checkstyle `UnusedImports` +
SpotBugs.

### A language not listed here

Do not improvise a table. Ask the human which tool fills each layer, and record
`not available` with the reason for any layer their toolchain has no answer for.
A guessed command that has never run is worse than an honest blank: it passes
review as though the layer existed.

---

## 5. Environment notes worth checking

- **`codex exec` inherits its sandbox and approval policy from configuration**,
  so there is no CLI default to rely on — the same command writes files on one
  machine and refuses on another. Always pass `-s` explicitly. A rejected patch
  reported as "blocked by read-only sandbox" means the policy in force was
  read-only, not that the CLI has that default.
- `codex doctor` reports sandbox provisioning, the search backend, and update
  status. Run it after installing and after every Codex update.
- If the sandbox reports a provisioning failure, isolation is weaker than these
  rules assume. It must be recorded in the EVIDENCE Honest notes, and the git
  checkpoint becomes the real safety net.
- Codex writes UTF-8 correctly on a CP950 console; the file encoding and the
  console code page are independent.
- **A model at capacity reports it at the end of the run, not the start.** A
  long `codex exec` can look like it completed while `ERROR: Selected model is
  at capacity` sits in the last lines of its output, with the work partly done
  or not done at all. Read the tail of every long run before treating it as
  finished, and never let a run's own summary stand in for that check. Record
  the fallback model in the project layer so there is something to switch to.
