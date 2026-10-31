# Contributing to email-mcp

Small fleet repo, one maintainer plus collaborators, zero patience for process theatre. These rules exist so your contribution gets merged instead of stalled.

## Issues first

- **Search before you file.** Duplicates get closed.
- **One issue, one request.** Two features = two issues.
- **Bug reports need the reproducer**: service, folder/operation, exact error — from a throwaway or MailHog account, NEVER a real mailbox.
- **Feature requests need a use case**: which mail, what workflow, what is missing?

## Pull requests

- **File the issue first** (unless it's a trivial fix: typo, broken link, lint). The issue is where scope gets agreed before code exists.
- **Keep diffs small.** One concern per PR.
- **Tests required.** New behavior without a test is a draft, not a PR. Run `uv run pytest tests -q` before pushing (use throwaway SMTP/IMAP servers — see Mail Lab — never real accounts).
- **Lint green:** `uv run ruff check src tests`; webapp touched? `biome` + `tsc` clean, Playwright e2e passes.
- **The maintainer merges.** Don't merge your own PR. Note: default branch here is `master`.

## Email rules: the hard parts

- **All email content is untrusted.** Subjects, bodies, sender names: strip zero-width chars and wrap with the safety boundary (`sanitize.py`) before anything LLM-facing.
- **Never touch a real mailbox in dev or tests.** MailHog/Mailpit, throwaway accounts, Mail Lab only.
- **Auto-respond rules never auto-send without approval** unless the rule explicitly says so and the owner configured it.

## What this repo never does

- **No live credentials in code, tests, or examples.** Ever. Graph tokens, app passwords, all env-only.
- **No real-mailbox fixtures.** Redacted samples only.
- **No auto-merge to `master`.**
