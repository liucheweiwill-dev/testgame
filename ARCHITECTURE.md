# ARCHITECTURE.md

Two layers. The contract below is enforced by import-linter
(`uv run lint-imports`), configured in `pyproject.toml`.

```
web      Flask routes, Jinja2 templates, session, POST-Redirect-GET
  |
  v
domain   cards, hands, hand values, shoe, rules, settlement, bot strategy
```

## Allowed

```
web -> domain
web -> flask, jinja2
domain -> the Python standard library only
```

## Forbidden

```
domain -> web
domain -> flask          the domain must be runnable with no web server present
domain -> any third-party package
any cycle between web and domain
```

## Why two layers and not three

There is one consumer of the domain. An `application` layer between `web` and
`domain` would be an abstraction with a single implementation and a single
caller, which the design rules in `AGENTS.md` §9 rule out. Flow orchestration —
turn sequencing, session handling, redirect-after-post — lives in `web` until a
second consumer exists. A CLI front end would be that second consumer, and
extracting the layer then is a smaller change than maintaining it now.

## The shoe

The shoe takes an explicit seed and lives in `domain`. It is not a port with an
injected adapter: there is one implementation, and a seed parameter is enough to
make production runs random and tests deterministic. The same rule as above —
no interface for a single implementation.

## Status

This contract describes the intended structure. **No code exists yet**, so
nothing has been checked against it. The first task that creates `src/domain`
also wires `lint-imports` and makes this file enforceable rather than aspirational.
