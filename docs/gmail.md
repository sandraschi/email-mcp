# Gmail Integration

## Prerequisites
- Gmail account with 2-Factor Authentication enabled
- App Password generated at https://myaccount.google.com/apppasswords

## Setup

### Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" as the app and your device as the device
3. Copy the 16-character app password
4. Use this password (NOT your regular Gmail password)

### Configuration via Environment (persistent, survives restarts)

```bash
GMAIL_USER="your-email@gmail.com"
GMAIL_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
```

Set these in `.env` (see `.env.example`). The backend auto-configures a
service named `gmail` on startup. Use it from any tool with `service="gmail"`,
e.g. `check_inbox(service="gmail")`, `send_email(..., service="gmail")`.

Legacy alternative: point the generic SMTP/IMAP vars at Gmail:

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-gmail-app-password"
export IMAP_SERVER="imap.gmail.com"
export IMAP_PORT="993"
export IMAP_USER="your-email@gmail.com"
export IMAP_PASSWORD="your-gmail-app-password"
```

### Configuration via Webapp (persistent)
Go to **Settings → Gmail** in the dashboard, enter your Gmail address and app
password, then **Connect Gmail**. This saves the `gmail` service on this PC
and restores it on every backend restart. **Test Connection** verifies IMAP
reachability. Deleting the service in **Services** removes the saved credentials.

The generic **Settings → Email Service Credentials** form and
`POST /api/services/quick` with `{"provider": "gmail", ...}` persist the same way.

Precedence: explicit environment config (below) wins over Settings-saved
credentials when both define the same service name.

### Configuration via MCP Tool
```
configure_service(name="gmail", type="smtp", config={
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your-email@gmail.com",
  "smtp_password": "your-gmail-app-password",
  "smtp_from": "your-email@gmail.com",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "imap_user": "your-email@gmail.com",
  "imap_password": "your-gmail-app-password"
})
```

## Supported Features
- SMTP sending with STARTTLS
- IMAP inbox checking
- HTML and plain text email formats
- CC/BCC recipient support
- Folder access (INBOX, Sent, Drafts, Trash, Spam, custom labels)
- Gmail label support via IMAP folder paths

## Notes
- App passwords only work with 2FA enabled
- Regular Gmail passwords are blocked by Google for SMTP/IMAP
- Workspace/Google Apps accounts may need admin approval
