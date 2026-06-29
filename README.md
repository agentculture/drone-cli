# drone-cli

Agent and CLI to control a single flying drone (UAV) — connect, arm, fly missions, stream telemetry, and land.

## What you get

- **An agent-first CLI** cited from [teken](https://github.com/agentculture/teken)
  (`afi-cli`) — the runtime package has no third-party dependencies.
- **A mesh identity** — `culture.yaml` (`suffix` + `backend`) and the matching
  resident prompt file (`AGENTS.colleague.md`, since this template runs
  `backend: colleague`).
- **The canonical guildmaster skill kit plus the eidetic memory skills**
  (14 skills) under `.claude/skills/`, vendored cite-don't-import. See
  [`docs/skill-sources.md`](docs/skill-sources.md).
- **A build + deploy baseline** — pytest, lint, the agent-first rubric gate, and
  PyPI Trusted Publishing wired into GitHub Actions.

## Quickstart

Install the published CLI — the distribution name is `drone-cli`, the command it
installs is `drone`:

```bash
uv tool install drone-cli   # or: pipx install drone-cli
drone whoami                 # identity from culture.yaml
drone learn                  # self-teaching prompt (add --json)
```

From a source checkout, prefix the command with `uv run`:

```bash
uv sync
uv run pytest -n auto                 # run the test suite
uv run drone whoami
uv run teken cli doctor . --strict    # the agent-first rubric gate CI runs
```

## CLI

| Verb | What it does |
|------|--------------|
| `whoami` | Report this agent's nick, version, backend, and model from `culture.yaml`. |
| `learn` | Print a structured self-teaching prompt. |
| `explain <path>` | Markdown docs for any noun/verb path. |
| `overview` | Read-only descriptive snapshot of the agent. |
| `doctor` | Check the agent-identity invariants (prompt-file-present, backend-consistency). |
| `cli overview` | Describe the CLI surface itself. |

Every command supports `--json`. Results go to stdout, errors/diagnostics to
stderr (never mixed). Exit codes: `0` success, `1` user error, `2` environment
error, `3+` reserved.

## Make it your own

1. Rename the import package `drone/`, the `drone` command (`[project.scripts]`),
   and the `drone-cli` distribution name throughout `pyproject.toml`, the package,
   `tests/`, `sonar-project.properties`, and this `README.md`. The names are
   hard-coded in ~100+ places, so list every occurrence first — see the `git grep`
   discovery commands in [`CLAUDE.md`](CLAUDE.md), the authoritative rename procedure.
2. Edit `culture.yaml` with your `suffix` and `backend`.
3. Rewrite `CLAUDE.md` for your agent and run `/init`.
4. Re-vendor only the skills you need from guildmaster (see
   [`docs/skill-sources.md`](docs/skill-sources.md)).

See [`CLAUDE.md`](CLAUDE.md) for the full conventions (version-bump-every-PR,
the `cicd` PR lane, deploy setup).

## License

Apache 2.0 — see [`LICENSE`](LICENSE).
