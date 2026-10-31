# Proton Mail

## Provenance

Proton Mail was born at **CERN, Geneva, in 2013**. Physicists **Andy Yen,
Jason Stockman, and Wei Sun** — the same lab that gave the world the Web —
started it as a direct answer to the **2013 Snowden revelations** about NSA
mass surveillance: email that even its operators cannot read.

- **Crowdfunded, not VC-funded.** The launch was crowdfunded, and Proton AG
  has stayed user-funded ever since. No venture capital means no investor
  who could one day demand data monetization — the privacy mission is
  structurally protected, not just promised.
- **Swiss jurisdiction.** Proton AG sits in Geneva under the Swiss Federal
  Act on Data Protection — outside US (CLOUD Act, NSLs) and EU jurisdiction.
- **From inbox to ecosystem.** Mail grew into VPN, Drive, Calendar, Pass
  (password manager), Docs, and **SimpleLogin** (email aliasing, acquired
  2022). One account, one privacy model across all of it.
- **Scale.** Tens of millions of users; Proton claims 100M+ accounts
  created across its services.

## Why pay — the ~€5/month question

Gmail and Outlook are free because **you are the product**: ad profiling,
content scanning, behavioral data sold up the chain. Proton charges roughly
**€5/month for Mail Plus** (verify current pricing at
https://proton.me/mail/pricing — it moves) because subscriptions *are* the
revenue. There is nothing to sell: **zero-access encryption** means Proton
literally cannot read your mail, even under court order.

What the paid plan unlocks for email-mcp purposes:

- **Direct SMTP/IMAP** (`mail.protonmail.com:587/993`) — no Bridge needed
- **Bridge access** — the local IMAP/SMTP translator for desktop clients
- **Custom domain + catch-all** — your own `you@yourdomain.com`
- **More storage, labels, filters**, SimpleLogin premium aliases
- A vote (with money) for surveillance-free infrastructure

The **free tier** (1 GB, ~150 msgs/day) is fine for a private webmail
inbox — but since late 2023 it cannot touch SMTP, IMAP, or Bridge, so it
cannot plug into email-mcp at all. If five euros a month keeps your mail
unreadable-to-everyone-but-you, that's the cheapest privacy deal going.

## Pros and cons (vs Gmail)

### Why Proton wins

| | Gmail | Proton Mail |
|---|---|---|
| **Encryption** | TLS in transit only | End-to-end by default; zero-access — Proton can't decrypt even if compelled |
| **Business model** | You are the product; mail scanned for ad targeting | You are the customer; subscriptions fund it, no ad scanning |
| **Jurisdiction** | US (CLOUD Act, National Security Letters, gag orders) | Switzerland (FADP), no US gag orders |
| **Open source** | No | Clients and Bridge are open source, independently audited |
| **Lockout risk** | Google can suspend your account — and all its services — unappealable | Proton can't access your data even if your account is terminated |
| **Tracking** | Reads mail to build an advertising profile | No tracking, no profiling, no ad targeting |

### Where Gmail still wins

| | Proton Mail | Gmail |
|---|---|---|
| **Cost** | Free tier limited (1 GB, ~150 msgs/day); real use needs a paid plan | Free with 15 GB |
| **Ecosystem** | Mail + VPN + Drive + Pass + Calendar — solid, but no Docs/Sheets-scale suite | Full suite: Docs, Sheets, Photos, Meet, ... |
| **Search** | Subject/sender only (body is encrypted — this is the price of the math) | Full-body search, smart categorization, AI inbox |
| **3rd-party integration** | Everything goes through Bridge or SMTP/IMAP | Thousands of integrations, OAuth, APIs |
| **Spam filter** | Functional, noticeably weaker than Gmail's | Best in class — billions of mails train it |
| **Speed** | Encryption adds latency, noticeable on slow devices | Instant |

**Bottom line:** choose Gmail if you want the ecosystem, the search, and
free. Choose Proton if your mail should be readable by exactly one party —
you — and ~€5/mo is a fair price for that math.

## Usage with email-mcp

| | Free account | Paid account (Mail Plus) |
|---|---|---|
| **Direct SMTP/IMAP** | ❌ Not available | ✅ `mail.protonmail.com:587` / `:993` |
| **Bridge** | ❌ Requires paid plan | ✅ Included — desktop clients + email-mcp via localhost |
| **email-mcp Quick Setup** | Blocked (by design) | ✅ One click |
| **Webmail / mobile apps** | ✅ Yes | ✅ Yes |

### Option A — Direct (paid plan, simplest)

1. Ensure IMAP/SMTP is enabled in Proton Mail Settings.
2. Email-mcp → Services → Quick Setup → **ProtonMail** → email + Proton password.

### Option B — Bridge (paid plan + Bridge app running)

1. Install [Proton Mail Bridge](https://proton.me/mail/bridge), log in,
   copy the per-app **Bridge password** (it is *not* your Proton password).
2. Email-mcp → Services → Quick Setup → **ProtonMail** — with Bridge
   detected, email-mcp configures `127.0.0.1:1025` / `127.0.0.1:1143`
   automatically. Use the Bridge credentials, not the web password.

### Power-user pattern: custom domain + SimpleLogin

Paid plans allow a custom domain with catch-all plus SimpleLogin aliases —
effectively self-hosted throwaways (`shopname@yourdomain.com` per signup).
Combine with email-mcp's [throwaway service](throwaway.md) for the full
spectrum: permanent aliases for things that matter, burner addresses for
everything else.

## Community

- **Open source + audited.** Clients and Bridge on GitHub; regular
  independent security audits published.
- **r/ProtonMail and the Proton community** — unusually technical user
  base; staff actually answer.
- **Transparency reports.** Proton publishes law-enforcement request
  statistics — and because of zero-access encryption, the answer to
  "hand over mailbox contents" is mathematically *can't*, not *won't*.
- **Bug bounty.** Paid program for reported vulnerabilities.

## Notes

- Since late 2023, Bridge and SMTP/IMAP access require a **paid Proton
  subscription**. Free accounts = webmail + mobile apps only.
- Body search is limited (content is encrypted) — subject/sender search only.
- Pricing moves — confirm at https://proton.me/mail/pricing.
