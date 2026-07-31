# Outlook / Hotmail Integration

> **⚠️ Personal accounts (outlook.com / hotmail / live.com): Microsoft disabled
> SMTP/IMAP basic authentication for personal accounts (Sept 2024+). App passwords
> ARE basic auth, so they no longer work — expect `5.7.139 Authentication
> unsuccessful, basic authentication is disabled` on SMTP and `AUTHENTICATE failed`
> on IMAP. Email MCP only supports password auth (no OAuth2 yet), so personal
> Outlook/Hotmail mailboxes **cannot be used** with this server. Options:
> - Send with an API service instead: SendGrid / Mailgun / Resend (free tiers,
>   configure via `EMAIL_SERVICES`).
> - Use a **Microsoft 365 business** mailbox where the admin enables SMTP AUTH
>   (steps below) — app passwords work there.
> - OAuth2 client support is a roadmap item; until then no personal-account path
>   exists.

Microsoft requires additional authorization steps on their site before SMTP/IMAP
clients can connect. Plain account passwords do **not** work for SMTP AUTH on
personal accounts since the "less secure apps" retirement.

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
