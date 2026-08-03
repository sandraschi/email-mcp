# Outlook / Hotmail Integration

> **⚠️ Personal accounts (outlook.com / hotmail / live.com): Microsoft disabled
> SMTP/IMAP basic authentication for personal accounts (Sept 2024+). App passwords
> ARE basic auth, so they no longer work for **password** login — expect `5.7.139
> Authentication unsuccessful, basic authentication is disabled` on SMTP and
> `AUTHENTICATE failed` on IMAP. The supported path is the **Microsoft Graph API**
> below (or XOAUTH2 for SMTP/IMAP).

## Graph API (recommended — simplest)

email-mcp can send, receive, search, and manage folders for personal
Outlook/Hotmail accounts through the Microsoft Graph REST API. No Azure app
registration is needed — the server uses Microsoft's public Graph command-line
client ID by default.

1. **Connect once** (device-code flow): open the webapp
   **Settings → Outlook OAuth**, pick **Graph (Mail API)**, click *Connect
   Outlook*, enter the displayed code at https://microsoft.com/devicelogin and
   approve. Tokens are stored in `data/oauth_tokens.json` (gitignored) and
   refresh automatically.
2. **Send**: `send_email(...)` with `service="graph"` — or nothing at all:
   when an OAuth token exists for an Outlook-family account, `service="default"`
   is backed by Graph automatically.
3. **Receive**: `check_inbox`, `fetch_email_detail`, `search_emails`,
   `list_folders`, `move_email`, `copy_email`, `forward_email`, `delete_email`
   all work through the same service.

Environment (already set in `.env`):

```bash
SMTP_USER="your-email@hotmail.com"
EMAIL_MCP_OAUTH_CLIENT_ID=14d82eec-204b-4c2f-b7e8-296a70dab67e
```

`EMAIL_MCP_OAUTH_CLIENT_ID` can be replaced with your own Azure app registration
if you prefer (Personal Microsoft accounts only, public client flows enabled,
`Mail.Read` + `Mail.Send` delegated permissions).

Custom folders (e.g. `Github`, `Family/Dog`) are matched by display name and
resolved to their Graph folder id automatically; the webapp Inbox shows a
folder tree with unread counts.

## OAuth2 / XOAUTH2 over SMTP-IMAP (alternative)

The device-code flow also supports the Exchange scopes (`IMAP.AccessAsUser.All`
+ `SMTP.Send`) — use the **Exchange (IMAP/SMTP)** scope in Settings instead.
When a token exists, `SMTPEmailService` authenticates with XOAUTH2 and
`SMTP_PASSWORD`/`IMAP_PASSWORD` can stay empty.

## Step 1: Enable two-step verification (required for app passwords)

1. Sign in at https://account.microsoft.com/security with the mailbox account.
2. Under **Two-step verification**, select **Turn on** and follow the prompts.
3. This is mandatory — app passwords can only be created when 2FA is enabled.

## Step 2: Create an app password

1. Go to **Advanced security options** (same page,
   https://account.microsoft.com/security).
2. Scroll to **App passwords** and select **Create a new app password**.
3. Copy the generated password (shown once) and use it as `SMTP_PASSWORD` and
   `IMAP_PASSWORD`. Never use the account's login password.

## Step 3: Configure Email MCP

```bash
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@outlook.com"
export SMTP_PASSWORD="<app password>"
export IMAP_SERVER="outlook.office365.com"
export IMAP_PORT="993"
export IMAP_USER="your-email@outlook.com"
export IMAP_PASSWORD="<app password>"
```

Or in the webapp: **Settings → Email Services → Add Service → SMTP** with the same
values. Or via MCP tool:

```
configure_service(name="outlook", type="smtp", config={
  "smtp_server": "smtp-mail.outlook.com",
  "smtp_port": 587,
  "smtp_user": "your-email@outlook.com",
  "smtp_password": "<app password>",
  "smtp_from": "your-email@outlook.com",
  "imap_server": "outlook.office365.com",
  "imap_port": 993,
  "imap_user": "your-email@outlook.com",
  "imap_password": "<app password>"
})
```

## Microsoft 365 / Exchange Online (business accounts)

1. **Enable SMTP AUTH for the mailbox** — Microsoft 365 blocks SMTP AUTH by
   default. Ask the admin to enable it, either in the Exchange admin center
   (Mail flow → Connectors / mailbox settings) or with PowerShell:

   ```powershell
   Set-CASMailbox -Identity "user@domain.com" -SmtpClientAuthenticationDisabled $false
   ```

2. **Security defaults / Conditional Access** — if the tenant enforces security
   defaults, legacy authentication (SMTP AUTH with a password) is blocked. Options:
   - Create an **app password** under the user's security info (works when MFA is
     on), or
   - Ask the admin for a Conditional Access exception for the SMTP/IMAP clients.
3. OAuth2 is not yet supported by Email MCP — app passwords are the supported path.

## Supported Features

- SMTP sending with STARTTLS (port 587)
- IMAP inbox checking (outlook.office365.com:993, SSL)
- Folder access (INBOX, Sent, Drafts, Trash, Junk)
- HTML and plain text formats

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `535 5.7.139 ... basic authentication is disabled` | **Personal account**: SMTP AUTH is permanently disabled for outlook.com/hotmail — no app password helps. Use an API service (SendGrid etc.) or an M365 business mailbox. For **M365 business**: admin must run `Set-CASMailbox -SmtpClientAuthenticationDisabled $false` (below) |
| `AUTHENTICATE failed` (IMAP) | Same root cause on personal accounts. For M365: verify IMAP is enabled on the mailbox |
| `SMTP AUTH` rejected / 535 5.7.3 | App password not used, or 2FA not enabled — redo Step 1 + 2 |
| `Client was not authenticated` | Same — plain passwords no longer work for personal accounts |
| Send fails right after enabling | Microsoft can take up to 24h to propagate SMTP AUTH changes — retry later |
| 365 account rejected | SMTP AUTH disabled on the mailbox — admin must run `Set-CASMailbox -SmtpClientAuthenticationDisabled $false` |
| IMAP works, SMTP fails | SMTP AUTH is controlled separately from IMAP enablement — check both |
| Security defaults block sign-in | Legacy auth blocked by tenant policy — app password or admin exception required |
