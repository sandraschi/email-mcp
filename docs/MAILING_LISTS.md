# Mailing Lists page

**Route:** `/mailing-lists` (nav: Mailing Lists)
**Backend:** `src/email_mcp/mailing_lists_store.py` + `web.py` `/api/mailing-lists*`
**Purpose:** sender presets (e.g. AlphaSignal), 3-day crawl, distilled digest in-page + optional push to AIWatcher.

## Presets

- Merged view: env presets from `EMAIL_MCP_MAILING_LISTS` / `FILE` (readonly, `source=env`) + user presets from `src/mailing_lists_user.json` (gitignored, `source=user`).
- CRUD: `GET /api/mailing-lists`, `POST /api/mailing-lists`, `PUT /api/mailing-lists/{id}`, `DELETE /api/mailing-lists/{id}`.
- Env ids cannot be overwritten or deleted from the UI (422/404 with reason).
- Seed: "Seed AlphaSignal preset" button fills `alphasignal / default / AI / news@alphasignal.ai`. Save once, crawl right away.

## Crawl (3-day default)

- `GET /api/mailing-lists/{id}/crawl?days=3&limit=20`
- Server calls `check_inbox(service, folder, from/subject)` then filters by `date >= now-days` (unparseable dates kept, not dropped).
- Returns newest-first `{id, subject, from, date}` rows. Checkbox = include in digest. Default: all checked.

## Distill (in-page + report)

- `POST /api/mailing-lists/{id}/distill` with `{email_ids?, days?, limit?, push_aiwatcher?, urgency_hint?}`.
- No ids = distill current crawl window (up to 10).
- Per email: `fetch_email_detail` -> prefer `text_body` (>=200 chars) else stripped `html_body` (6000-char cap, no bs4), extract up to 15 links (safelinks skipped).
- Response: `{items: [{id, subject, from, date, summary(1500), links}], report_md (30k cap), pushed}`.
- In-page: digest cards (600-char summary + top 5 links) + full `report_md` in `<pre>` for copy.
- Report: same markdown doubles as the shareable artifact. `push_aiwatcher=true` calls `connectors.push_aiwatcher(title, joined summaries, urgency_hint=7.0)` -> lands in AIWatcher `inbox_add` flow -> `distill_pending` -> bundles/digest. Failures surface inline, digest still returned.

## Proven flow (2026-10-24)

AlphaSignal 10-22 + 10-23 manually ran as: `search_emails -> fetch_detail -> Task-extract (180KB HTML dodge) -> inbox_add(tags=alphasignal, urgency 7.5)` -> visible in `search_items`, pending Claude `distill_pending` (local LLM timeout, daemon picks up). This page automates that chain.

## Limits

- 20 emails max per distill (context guard).
- No LLM in email-mcp itself: summaries are extracts. Full Sandra-voice scoring happens in AIWatcher after push.
- User presets file is local-only (gitignored). Env presets remain the shareable/team path.
