# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo actually is (read first)

`drone-cli`'s **stated domain** (README / `pyproject` description) is "control a single
flying drone (UAV) — connect, arm, fly missions, stream telemetry, and land." **No
drone-control code exists yet.** The codebase today is the unmodified
*culture-agent-template*: an agent-first introspection CLI (`whoami`, `learn`,
`explain`, `overview`, `doctor`, `cli`) plus a mesh identity and a vendored skill kit.
The seed `CLAUDE.md` (now replaced by this file) was never expanded for the drone
domain.

So there are two layers here, and it matters which you're touching:

- **The template chassis** — the CLI framework, error/output contracts, identity, CI,
  and rubric gate described below. Stable and working; treat its contracts as fixed.
- **The drone domain** — does not exist. Connecting to a flight controller (e.g.
  MAVLink), arming, missions, telemetry, landing all need to be built as new noun
  groups under `drone/cli/_commands/` following the registration pattern below. When you
  add a runtime dependency for this (e.g. `pymavlink`), you break the zero-dependency
  invariant — see "Hard constraints."

## Commands

The package manager is **uv**. The runtime package has **no third-party dependencies**;
everything below is dev tooling pulled by `uv sync`.

```bash
uv sync                                  # install deps + dev group into .venv
uv run drone whoami                      # run the CLI (installed: `uv tool install drone-cli`)
uv run pytest -n auto                    # full test suite (xdist parallel)
uv run pytest tests/test_cli.py::test_whoami_text   # a single test
uv run pytest --cov=drone --cov-report=term         # with coverage (gate: fail_under=60)
```

Lint / format (CI's `lint` job runs all of these; line length is **100**):

```bash
uv run black --check drone tests
uv run isort --check-only drone tests
uv run flake8 drone tests
uv run bandit -c pyproject.toml -r drone
markdownlint-cli2 "**/*.md"              # config skips .claude/skills (vendored verbatim)
uv run teken cli doctor . --strict       # the agent-first rubric gate — see below
```

> **Three namespaces, don't conflate them:** the **distribution** is `drone-cli`
> (`uv tool install drone-cli`, the PyPI name, the repo, the sonar `projectKey`); the
> **command** is `drone` (`[project.scripts] drone = …`, the argparse `prog`, every
> usage/`explain`/`learn`/`overview`/`doctor` string); the **import package** is `drone`
> (`from drone.cli import main`, `python -m drone`, wheel `packages = ["drone"]`). Separately,
> the **mesh nick** is `drone-cli` (`culture.yaml` `suffix`, what `whoami` reports as
> `nick:`) — that's identity, not the command. So `drone whoami` printing `nick: drone-cli`
> is correct, not a bug. See "Renaming this template" before changing any of these.

## Architecture

### Command registration

`drone/cli/__init__.py` `main(argv) -> int` is the single entry point (also reachable via
`python -m drone`). `_build_parser()` builds an argparse tree where **each command module
under `drone/cli/_commands/` exposes a `register(sub)` function** that adds its subparser,
its `--json` flag, and sets `func=<handler>` via `set_defaults`. To add a verb or noun
group: write the module, then call its `register(sub)` in `_build_parser()` (there's a
marked spot for "your own noun groups"). `_dispatch()` calls `args.func(args)`; a handler
returns `None`/`0` for success or an `int` exit code.

A **noun group** (like `cli`) is a parser with its own sub-subparsers. The rubric requires
that any noun exposing action-verbs also expose `overview` — that's the entire reason the
`cli` noun exists today (`cli overview` describes the CLI surface; the global `overview`
describes the *agent*). Follow this pattern when you add drone nouns.

### The three contracts (stable — do not break)

1. **Errors** (`drone/cli/_errors.py`): every failure raises `CliError(code, message,
   remediation)`. `_dispatch()` catches it, and also wraps *any* unexpected exception into
   a `CliError`, so **no Python traceback ever reaches stderr**. Argparse's own errors
   (unknown verb, bad flag) are rerouted the same way by `_CliArgumentParser.error()`.
   Because parse-time errors happen before `args.json` exists, `main()` pre-scans raw argv
   for `--json` and stashes it on the class-level `_CliArgumentParser._json_hint` so even
   argparse errors honor JSON mode. New subparsers must be built with
   `parser_class=_CliArgumentParser` (the top-level subparsers propagate it) or their
   errors escape the contract — see the comment in `cli.py`.

2. **Output** (`drone/cli/_output.py`): **results → stdout, errors/diagnostics → stderr,
   never mixed.** Use `emit_result` / `emit_error` / `emit_diagnostic`; never `print`.
   Text-mode errors render as `error: <msg>` + `hint: <remediation>` — the `hint:` prefix
   is required by the rubric. Every command takes `--json` and routes structured payloads
   to the same split streams.

3. **Exit codes** (`drone/cli/_errors.py`): `0` success, `1` user-input error, `2`
   environment/setup error, `3+` reserved. This policy is echoed in `learn` output and the
   rubric checks that `learn` documents it.

### `explain` catalog

`drone/explain/catalog.py` holds verbatim markdown keyed by command-path tuples
(`("whoami",)`, `("cli", "overview")`, …; `()` and `("drone",)` — the command name — both
map to root, which is why the rubric's `explain <command>` self-check resolves).
`drone/cli/_commands/explain.py` resolves a path or raises `CliError` with a hint.
**Every registered noun/verb should have a catalog entry** — `test_every_catalog_path_resolves`
walks `known_paths()` and the rubric checks that `explain <self-name>` resolves. When you
add a command, add its catalog entry in the same change.

### `doctor` and identity

`whoami`/`doctor` read identity from `culture.yaml` via `find_culture_yaml()` (walks up
from `__file__`, **not** CWD — identity is the agent's own). Parsing is **hand-rolled**
(`read_agent_fields`) precisely to avoid a PyYAML runtime dependency; it only understands
the documented `agents: [{suffix, backend, model}]` shape and falls back to literals
otherwise. `doctor` mirrors the `steward doctor` invariants: **backend-consistency** (the
`_PROMPT_FILE` map: `claude→CLAUDE.md`, `colleague→AGENTS.colleague.md`, `acp→AGENTS.md`,
`gemini→GEMINI.md`) and **prompt-file-present**, plus a skills-present warning. From a
wheel install (no `culture.yaml` beside the package) it reports one info check and exits 0.

This agent runs **`backend: colleague`** (Qwen, per `culture.yaml`), so its resident mesh
prompt is **`AGENTS.colleague.md`**, not this `CLAUDE.md`. `CLAUDE.md` is for Claude Code;
`AGENTS.colleague.md` is what the mesh runtime loads. `test_doctor_recognizes_declared_backend`
fails if you change the declared backend without teaching `doctor` the matching prompt file.

### The agent-first rubric gate (the real design driver)

`uv run teken cli doctor . --strict` (the `teken` dev dep) is a CI gate that asserts the
contracts above as black-box behavior: top-level help runs, `main(argv)->int` conforms,
`learn` is ≥200 chars and mentions purpose/commands/exit-codes/`--json`/`explain`, errors
carry `hint:` with no traceback, descriptive verbs (`overview`) never hard-fail on a bad
path, every noun-with-verbs has an `overview`, `explain <self>` resolves, `doctor` returns
the `{healthy, checks:[{id,passed,severity,message,remediation}]}` shape. When changing CLI
behavior, **run this gate** — much of the seemingly-odd code (the ignored `target` arg on
`overview`, the bare `cli` noun, the `_json_hint` dance) exists only to satisfy it.

## Hard constraints

- **Zero runtime dependencies.** `pyproject` `dependencies = []`, and the YAML parser is
  hand-rolled to keep it that way. Adding a runtime dep (likely unavoidable for actual
  drone control, e.g. MAVLink) is a real architectural decision — do it deliberately,
  update this section, and keep `whoami`/`doctor` working without it.
- **Version is single-sourced.** `drone/__init__.__version__` is read from installed
  package metadata via `importlib.metadata` — there is **no** hard-coded version string in
  the package. The version lives only in `pyproject.toml` (and `CHANGELOG.md`). This
  differs from the sibling culture/daria projects that also bump `__init__.py`.

## Conventions

- **Every PR bumps the version**, even docs/config/CI-only ones — the `version-check` CI
  job blocks merge when `pyproject.toml`'s version equals `main`'s, and an unbumped version
  fails the PyPI publish. Use the `/version-bump` skill (updates `pyproject.toml` +
  prepends a Keep-a-Changelog entry to `CHANGELOG.md`).
- **PRs go through the `cicd` skill** (layered on `devex pr`): it adds `status`
  (SonarCloud quality gate + unresolved-thread tally) and `await` (blocks until CI + Sonar
  settle, non-zero on a red gate). SonarCloud project key is `agentculture_drone-cli`;
  the Sonar scan is a no-op when `SONAR_TOKEN` is absent (fork PRs stay green).
- **Publishing** is PyPI Trusted Publishing (OIDC) via `.github/workflows/publish.yml`:
  push to `main` → PyPI; PR → TestPyPI dev build (`<ver>.devN`). Only triggers on
  `pyproject.toml`/`drone/**` changes.
- **Skills under `.claude/skills/` are vendored cite-don't-import** from guildmaster (and
  `think`/`spec-to-plan`/`assign-to-workforce` from devague, `ask-colleague` from
  colleague). They're excluded from sonar, markdownlint, and coverage. Do **not** reformat
  them; provenance and the re-sync procedure live in `docs/skill-sources.md`.

## Renaming this template to a new agent

This is the procedure the README's "Make it your own" step 1 points to. Renaming touches
all four namespaces from the "Names" note above — the distribution `drone-cli`, the command
`drone`, the import package `drone`, and the mesh nick `drone-cli` — and the **command name
and the `explain` catalog self-key must move together**: the rubric's `explain_self` check
runs `explain <command-name>`, so the catalog must key whatever you name the command.
Discover every occurrence first — the `drone-cli` token (dist + nick) appears ~100+ times
and the bare `drone` token (command + package) ~120+ times outside vendored skills:

```bash
git grep -n "drone-cli" -- ':!.claude/skills' ':!uv.lock'   # distribution name + mesh nick
git grep -nw "drone"     -- ':!.claude/skills' ':!uv.lock'   # command + import package
```

Touch `pyproject.toml` (`name`, `[project.scripts]`, wheel `packages`, URLs), the `drone/`
package dir, `tests/`, `sonar-project.properties` (`projectKey`), `culture.yaml` (`suffix`,
if renaming the nick), the `explain` catalog keys/bodies, the `prog`/output strings, and
`README.md` together, then re-run `pytest` and the rubric gate (`uv run teken cli doctor .
--strict`) to confirm green.
