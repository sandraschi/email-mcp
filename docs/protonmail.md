# ProtonMail Integration

ProtonMail setup depends on your account type.

## Free Accounts (ProtonMail Bridge Required)

Free accounts need the **ProtonMail Bridge** application, which creates local SMTP/IMAP servers on your machine.

### Bridge Setup
1. Download ProtonMail Bridge: https://proton.me/mail/bridge
2. Install and configure Bridge with your ProtonMail account
3. Bridge creates local SMTP (port 1025) and IMAP (port 1143) servers

### Configuration
```json
{
  "smtp_server": "127.0.0.1",
  "smtp_port": 1025,
  "smtp_user": "your-username",
  "smtp_password": "your-protonmail-password",
  "imap_server": "127.0.0.1",
  "imap_port": 1143,
  "imap_user": "your-username",
  "imap_password": "your-protonmail-password"
}
```

### Environment Variables
```bash
export SMTP_SERVER="127.0.0.1"
export SMTP_PORT="1025"
export SMTP_USER="your-username"
export SMTP_PASSWORD="your-protonmail-password"
export IMAP_SERVER="127.0.0.1"
export IMAP_PORT="1143"
export IMAP_USER="your-username"
export IMAP_PASSWORD="your-protonmail-password"
```

## Paid Accounts (Direct Access)

Paid ProtonMail accounts support direct SMTP/IMAP without Bridge.

### Configuration
```json
{
  "smtp_server": "mail.protonmail.com",
  "smtp_port": 587,
  "smtp_user": "your@protonmail.com",
  "smtp_password": "your-protonmail-password",
  "imap_server": "mail.protonmail.com",
  "imap_port": 993,
  "imap_user": "your@protonmail.com",
  "imap_password": "your-protonmail-password"
}
```

### Environment Variables
```bash
export SMTP_SERVER="mail.protonmail.com"
export SMTP_PORT="587"
export SMTP_USER="your@protonmail.com"
export SMTP_PASSWORD="your-protonmail-password"
export IMAP_SERVER="mail.protonmail.com"
export IMAP_PORT="993"
export IMAP_USER="your@protonmail.com"
export IMAP_PASSWORD="your-protonmail-password"
```

### Setup Steps for Paid Accounts
1. Enable SMTP/IMAP access in ProtonMail settings
2. Use your regular ProtonMail password (no app passwords needed)
3. Configure via environment variables or the webapp

## Notes
- Bridge must be running for free accounts to work
- Paid accounts can skip Bridge entirely
- ProtonMail uses end-to-end encryption; Bridge handles decryption locally
