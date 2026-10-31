# Throwaway (Burner) Email via mail.tm

Give out an email address you can burn. Mint a fresh address in one click,
use it for signups/trials/testing, read the replies in the Inbox like any
other service, delete the service when done.

## Quick start

- **Webapp:** Services → Quick Setup → **Throwaway** → Mint address.
  No email, no password, no account — the address appears in your inbox list.
- **REST:** `POST /api/services/quick` with `{"provider": "throwaway"}`
  (optional `"domain"` and `"name"` fields).
- **MCP:** `configure_service(name="throwaway", type="disposable",
  config={"address": ..., "password": ..., "token": ...})` — normally you
  never do this by hand; Quick Setup mints and persists the credentials.

## How it works

Under the hood this is [mail.tm](https://mail.tm): a free, no-API-key,
receive-only email API. Minting does three calls — `GET /domains`,
`POST /accounts`, `POST /token` — and stores the JWT with the service, so
restarts keep working. Expired tokens re-login automatically with the
stored address + password.

Standard tools work: `check_inbox`, `fetch_email_detail`, `mark_email_read`,
`delete_email`, folder list (`INBOX` only), `test_connection`.

## Limits (read before you rely on it)

- **Receive-only.** mail.tm cannot send. `send_email` on a throwaway
  service returns an honest error — use another service to send.
- **No SLA.** It's a free community API (8 queries/sec per IP). If a mint
  fails with 502, mail.tm is down or out of domains — retry later.
- **Attribution.** mail.tm asks for a visible link-back when you use the
  API. Ours lives here and in the Services page.
- **Some sites block disposable domains** for registration. That's their
  choice, not a bug in this repo.
- **Lifetime.** Addresses live as long as mail.tm keeps them. Treat every
  throwaway as temporary by design — move anything important elsewhere.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `throwaway mint failed` (502) | mail.tm unreachable or no domains — retry in a minute |
| Inbox empty, `test_connection` ok | Nobody mailed the address yet, or the sender blocked disposable domains |
| 401s in a row | Token refresh failed — delete the service and mint a fresh address |
