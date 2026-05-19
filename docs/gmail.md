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

### Configuration via Environment

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

### Configuration via Webapp
Go to **Settings → Email Services** in the Email Hub dashboard and add an SMTP service with the credentials above.

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
