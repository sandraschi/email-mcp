# Outlook / Hotmail Integration

## Prerequisites
- Outlook.com, Hotmail, or Microsoft 365 account
- App password (if 2FA enabled) or regular password

## Setup

### Configuration via Environment

```bash
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@outlook.com"
export SMTP_PASSWORD="your-password"
export IMAP_SERVER="outlook.office365.com"
export IMAP_PORT="993"
export IMAP_USER="your-email@outlook.com"
export IMAP_PASSWORD="your-password"
```

### Configuration via Webapp
Go to **Settings → Email Services** in the Email Hub dashboard and add an SMTP service.

### Configuration via MCP Tool
```
configure_service(name="outlook", type="smtp", config={
  "smtp_server": "smtp-mail.outlook.com",
  "smtp_port": 587,
  "smtp_user": "your-email@outlook.com",
  "smtp_password": "your-password",
  "smtp_from": "your-email@outlook.com",
  "imap_server": "outlook.office365.com",
  "imap_port": 993,
  "imap_user": "your-email@outlook.com",
  "imap_password": "your-password"
})
```

## Microsoft 365 / Exchange Online
For business/enterprise accounts, use the same endpoints. If your organization uses Conditional Access or Modern Auth, you may need an app password or OAuth2 token.

## Supported Features
- SMTP sending with STARTTLS
- IMAP inbox checking
- Folder access (INBOX, Sent, Drafts, Trash, Junk)
- HTML and plain text formats

## Notes
- Microsoft may block "less secure apps" -- enable SMTP/IMAP in account settings
- For 365 accounts, check with your admin for SMTP/IMAP access policies
- OAuth2 is recommended but not yet supported (use app passwords)
