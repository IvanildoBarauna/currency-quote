# Claude Code repository instructions

Read [AGENTS.md](AGENTS.md) first. It is the canonical guide for architecture,
the public v6 API, dependency boundaries, tests and release safety. Keep any
future changes to this file consistent with it and with [README.md](README.md).

There is no automatic Claude Code Review on newly opened/updated PRs. The
remaining `.github/workflows/claude.yml` runs only on an explicit `@claude`
mention in a supported comment/review/issue; do not assume a failing or absent
Claude check indicates a product regression.
