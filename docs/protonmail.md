# ProtonMail (Proton Mail)

## About

ProtonMail (now Proton Mail) is an encrypted email service founded in 2013 by a team of CERN scientists and MIT researchers — including Andy Yen, Jason Stockman, and Wei Sun. The company (Proton AG) is headquartered in **Geneva, Switzerland**, putting it under Swiss privacy law, which is among the strongest in the world and outside both US and EU jurisdiction.

The founding team met at CERN (the same lab that gave us the World Wide Web). They launched ProtonMail after Edward Snowden's 2013 NSA revelations, with the explicit goal of making encryption accessible to everyone. The company has never taken venture capital that would compromise its privacy mission — it's funded entirely by its users through paid plans.

## Why Use ProtonMail Instead of Gmail?

### Pros

| | Gmail | ProtonMail |
|---|---|---|
| **Encryption** | TLS in transit only | End-to-end encrypted by default. Google cannot read your emails even if compelled by a court. |
| **Business model** | You are the product. Google scans your email for ad targeting. | You are the customer. Paid subscriptions fund the service. No ad scanning. |
| **Jurisdiction** | US (Patriot Act, National Security Letters) | Switzerland (Swiss Federal Data Protection Act, no US gag orders) |
| **Privacy** | Google has full access to read, analyze, and store your mail indefinitely. | Proton cannot decrypt your email. Zero-access architecture. |
| **Open source** | No | All client apps and the bridge are open source. Independently audited. |
| **Account lockout** | Google can suspend your account (and all its services) with no appeal. Proton cannot access your data even if your account is terminated. |
| **Tracking** | Google reads your email to build an advertising profile. | No tracking, no profiling, no ad targeting. |

### Cons

| | ProtonMail | Gmail |
|---|---|---|
| **Cost** | Free tier is limited (1GB, 150msgs/day). Useful features require €3.99+/month. | Free with 15GB. |
| **Ecosystem** | Just mail + calendar + drive + VPN. No docs, sheets, photos, etc. | Full Google ecosystem: Drive, Docs, Photos, Calendar, Meet, etc. |
| **Search** | Can only search subject lines and sender names by default (body is encrypted). Gmail can search everything. | Full body search, smart categorization, AI-powered inbox. |
| **Speed** | Encryption/decryption adds latency. Noticable on slow devices. | Instant. No encryption overhead. |
| **3rd-party integration** | Limited. No easy Zapier/IFTTT integration. Everything goes through Bridge. | Thousands of integrations, OAuth, APIs. |
| **IMAP access** | Free: requires Bridge app running locally. Paid: direct SMTP/IMAP. | Direct IMAP access always works. |
| **Spam filter** | Functional but noticeably worse than Gmail's. | Best in class. Google processes billions of emails to train it. |

### Bottom Line

- **Choose Gmail if**: you want the full Google ecosystem, need powerful search, or don't want to pay for email.
- **Choose ProtonMail if**: you care about privacy, don't want a corporation reading your mail, need to communicate sensitive information, or want to de-Google your life.

## Technical Setup with Email-MCP

ProtonMail setup depends on your account type.

### Free Accounts (ProtonMail Bridge Required)

Free accounts cannot access SMTP/IMAP directly. You **must** run the **ProtonMail Bridge** application locally. Bridge creates local SMTP and IMAP servers on your machine that decrypt ProtonMail's encryption and present it as standard email protocols.

#### Bridge Setup
1. Download ProtonMail Bridge: https://proton.me/mail/bridge
2. Install and configure Bridge with your ProtonMail account
3. Bridge creates local SMTP (port 1025) and IMAP (port 1143) servers

#### Configuration
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

#### Environment Variables
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

### Paid Accounts (Direct Access)

Paid ProtonMail accounts (€3.99+/month) support direct SMTP/IMAP without Bridge.

#### Configuration
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

#### Environment Variables
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
1. Enable SMTP/IMAP access in ProtonMail settings (Settings → IMAP/SMTP)
2. Use your regular ProtonMail password (no app passwords needed, unlike Gmail)
3. Configure via environment variables or the webapp Settings page

## Notes
- Bridge must be running for free accounts to work — it's a local desktop app
- Paid accounts can skip Bridge entirely and connect directly
- ProtonMail uses end-to-end encryption; Bridge handles decryption locally
- Body search is limited because content is encrypted — ProtonMail cannot index what it cannot read
- ProtonMail also offers a VPN service (ProtonVPN) and cloud storage (Proton Drive)
