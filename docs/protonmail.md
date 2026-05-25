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

## Connecting ProtonMail to Email-MCP

| | Free Account | Paid Account (Mail Plus, €3.99/mo) |
|---|---|---|
| **SMTP/IMAP** | ❌ Not available | ✅ Direct access |
| **Bridge** | ❌ Not included (Bridge requires paid plan) | ✅ Included |
| **How to connect** | Upgrade to paid — no other option | Direct to mail.protonmail.com:587/993 |
| **Webmail** | ✅ Yes | ✅ Yes |
| **Mobile apps** | ✅ Yes | ✅ Yes |

**Important**: Since late 2023, ProtonMail restricts SMTP/IMAP and Bridge access to **paid subscribers only** (Mail Plus €3.99/mo or higher). Free accounts can only use the web interface and mobile apps.

### Option: Upgrade to Paid

1. Upgrade at https://proton.me/mail/settings/upgrade
2. Enable IMAP/SMTP in ProtonMail Settings → IMAP/SMTP
3. In email-mcp → Services → Quick Setup → **ProtonMail** — connects automatically

Once upgraded, email-mcp shows your inbox, folders, handles send/receive, search — everything works.

## Notes
- **Since late 2023**: Bridge and SMTP/IMAP access require a **paid ProtonMail subscription** (Mail Plus €3.99/mo or higher)
- Free accounts are limited to webmail and mobile apps — no third-party client access
- ProtonMail uses end-to-end encryption end-to-end
- Body search is limited (content is encrypted) — subject/sender search only
- ProtonMail also offers ProtonVPN, Proton Drive, and Proton Calendar
