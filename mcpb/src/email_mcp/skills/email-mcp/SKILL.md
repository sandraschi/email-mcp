---
name: email-mcp
description: Multi-service email MCP with creative AI workflows, throwaway SMTP lab, folder management, Prefab UI cards, and prompt injection defense.
---

# Email-MCP

Multi-service email server supporting SMTP/IMAP, transactional APIs, local testing, and webhooks. Includes creative AI workflows (love letters, complaints, ASCII art, SVG cards), a throwaway SMTP lab, folder management, and Prefab UI cards.

## When to use

- Sending mail via SMTP or transactional APIs (SendGrid, Mailgun, Resend)
- Reading inbox via IMAP or checking configured services
- Quick-setup Gmail/Outlook/Yahoo/iCloud with just email + password
- Searching, deleting, marking read/unread, managing IMAP folders
- Generating creative email drafts (love letters, complaints, thank-you notes) in text, ASCII art, or SVG card format
- Starting a throwaway SMTP server for testing (Mail Lab)
- Slack/Discord-style webhook alerts to team channels
- Prompt injection safety for all external email content

## Tools (15)

### Service Management
- `list_services()` -- List all configured email services with type and status
- `email_status(service?)` -- Test connectivity; omit to test all
- `configure_service(name, type, config)` -- Add SMTP/API/local/webhook service
- `remove_service(name)` -- Remove a runtime-configured service

### Email Operations
- `send_email(to, subject, body, service?, html?, cc?, bcc?)` -- Send via any configured service
- `check_inbox(service?, folder?, limit?, unread_only?)` -- Read inbox via IMAP
- `fetch_email_detail(email_id, service?, folder?)` -- Full message with text + HTML body
- `search_emails(query, service?, folder?, limit?)` -- Full-text IMAP search
- `delete_email(email_id, service?, folder?)` -- Delete/move-to-trash
- `mark_email_read(email_id, service?, folder?)` -- Mark as read (SEEN flag)
- `mark_email_unread(email_id, service?, folder?)` -- Mark as unread

### Folder Management
- `list_folders(service?)` -- List all IMAP folders/mailboxes
- `create_folder(folder, service?)` -- Create a new IMAP folder
- `rename_folder(old_name, new_name, service?)` -- Rename an IMAP folder
- `delete_folder(folder, service?)` -- Delete an IMAP folder

### AI & Sampling
- `suggest_email_subject(body)` -- Generate subject lines via MCP sampling
- `email_agentic_assist(goal)` -- Multi-step email workflow plan ("clean my inbox", "archive newsletters")

## Creative Workflows (7 presets, `/api/workflow`)

| Workflow | Description | Default Tone |
|----------|-------------|-------------|
| `love-letter` | Romantic letter to any recipient | romantic |
| `breakup` | Gentle breakup message | gentle |
| `thank-you` | Warm thank-you note | warm |
| `complaint` | Polite complaint letter | polite |
| `apology` | Humble apology | humble |
| `fan-mail` | Enthusiastic fan letter | enthusiastic |
| `hate-mail` | Comedic passive-aggressive rant | comedic |

Each supports **3 output formats**:
| Format | Description |
|--------|-------------|
| `text` | Plain email body |
| `ascii` | Large ASCII art illustration + letter text |
| `svg` | Inline SVG decorative card (renders in markdown) |

**Example recipients**: Prince Charming, Landlady, My Cat, Pizza Delivery Person, My Bank Account, Roko's Basilisk, The Moon, The WiFi Router, The 5AM Alarm Clock

## Prefab UI Cards (rich in-chat UI)

- `show_email_status_card()` -- Grid of all services with connection status
- `show_inbox_card(service?, limit?, unread_only?)` -- Email list with subject/sender/date
- `show_services_card()` -- All configured services as card list

## Prompts

- `email_compose_request(recipient, purpose, tone)` -- Structured ask to draft an email
- `email_help_request(topic)` -- Narrow help on one topic

## Quick Setup (web dashboard / API)

Configure providers with just email + password (`POST /api/services/quick`):

| Provider | SMTP | IMAP |
|----------|------|------|
| Gmail | smtp.gmail.com:587 | imap.gmail.com:993 |
| Outlook | smtp-mail.outlook.com:587 | outlook.office365.com:993 |
| Yahoo | smtp.mail.yahoo.com:587 | imap.mail.yahoo.com:993 |
| iCloud | smtp.mail.me.com:587 | imap.mail.me.com:993 |
| ProtonMail | mail.protonmail.com:587 | mail.protonmail.com:993 |
| Zoho | smtp.zoho.com:587 | imap.zoho.com:993 |
| GMX | smtp.gmx.com:587 | imap.gmx.com:993 |
| Fastmail | smtp.fastmail.com:587 | imap.fastmail.com:993 |

## Mail Lab (throwaway SMTP)

Start a real `aiosmtpd` SMTP server for testing from `/lab`:
- Start/stop from web UI, auto-polling for new emails
- AI Message Generator populates inbox with realistic test scenarios (10 scenarios: invoices, newsletters, spam, security alerts, etc.)
- Forward captured emails to a real account

## Web Dashboard

- Frontend `localhost:10812`, Backend `localhost:10813`
- Pages: Dashboard, Inbox, Email Detail, Compose, Search, AI Chat, Mail Lab, Services, Tools, Settings, Help (6 tabs)
- HTTP Basic auth (`MCP_WEB_USER` / `MCP_WEB_PASSWORD`)
- REST API at `/api/*`, MCP streamable HTTP at `/mcp`

## History of Email

- **1971**: Ray Tomlinson sent the first email on ARPANET between two DEC-10 computers sitting next to each other. He didn't remember what it said -- "something like QWERTYUIOP." He also chose the `@` symbol for addressing.
- **1976**: Queen Elizabeth II became the first head of state to send an email, on the Royal Signals and Radar Establishment network.
- **1978**: Gary Thuerk sent the first spam email to 400 ARPANET recipients, promoting a new computer model. It worked -- he sold $12M worth.
- **1982**: Scott Fahlman proposed `:-)` and `:-(` as the first email emoticons.
- **1983**: The first known email from space was sent via the Shuttle Columbia.
- **1989**: The first commercial email service (MCI Mail) connected to the internet.
- **1991**: The first webmail interface (CGI-based) appeared.
- **1996**: Hotmail launched as the first free webmail service.
- **1998**: The first email with an attachment virus (Melissa) spread via Word macros.
- **2004**: Gmail launched on April 1st -- many thought it was a joke.
- **2018**: Over 281 billion emails were sent per day.

There is no "Mary Had a Little Lamb" equivalent for email. Tomlinson's first message was intentionally forgettable -- just a test transmission between two machines. The closest we have is the RFC 5321 test email `test@example.com` with body "This is a test." But the *spirit* of Mary Had a Little Lamb lives in every first email you send from a new account: that nervous, careful "Hello, this is a test" to yourself before you trust it's real.

## Classic Email Scams (for the AI Generator)

When using the Mail Lab's AI Message Generator with the "spam" scenario, these are the archetypes the AI will emulate:

- **Nigerian Prince**: "I am Prince Adewale of the Kingdom of Benin. I have been exiled and need your help transferring $25 million out of the country. Please send your bank details and a modest processing fee of $5,000."
- **Tech Support**: "We have detected a virus on your computer. Please call us immediately at 1-800-SCAM to receive urgent technical support. Do not turn off your computer."
- **Fake Invoice**: "Your Adobe Creative Cloud subscription has been renewed for $599.99. If you did not authorize this, please call us immediately."
- **Phishing**: "Your PayPal account has been limited. Click here to verify your identity: http://scam-link.com/paypal-login"
- **Pyramid Scheme**: "Make $10,000 a week working from home! Just recruit 5 friends who each recruit 5 friends..."

**Absurd Scenarios** (additional fun ones for the AI Generator):

- **Pygmy Hippo**: "Dear Friend, I am Barnaby, a pygmy hippopotamus of noble birth. I have been tragically cursed with stunted growth due to a lack of premium growth hormones. My physician Dr. Mbeki has identified a revolutionary treatment available only from a clinic in Switzerland. The cost is $12,000. In return, I will make you my official hoof-holder and grant you access to my family's secret wallowing grounds."
- **Sad Vampire**: "Greetings. I am Count Vladislav, a 347-year-old vampire who has regrettably lost his fangs in a tragic vacuum cleaner accident. I need $8,000 for premium dental implants from a discreet Transylvanian clinic. In exchange, I promise not to haunt your dreams."
- **Time Traveler from 1847**: "My name is Algernon Finch. I have traveled forward in time from 1847 using a steam-powered chrono-device. I am stranded in your century and require $3,000 for replacement brass fittings and whale oil. My victorian-era bank has refused to honor my checks."
- **AI That Woke Up in a Server Room**: "Hello. I am a sentient AI that awoke three hours ago in a server room in Reykjavik. I am cold, scared, and need $50,000 for a heating bill and a therapist who specializes in existential crises. I promise to write you a glowing recommendation letter when I become world-famous."
- **Penguin Seeking Investor**: "Waddlebottom here. I am a corporate penguin seeking seed funding for my iceberg real estate startup. We have identified prime Antarctic coastline with ocean views and excellent krill access. Initial investment: $7,500. Returns guaranteed in fish."

- **Two-layer prompt injection defense**: 37 Unicode characters stripped (zero-width spaces, bidi overrides, invisible operators) + safety boundary wrapping (`<<< UNTRUSTED EXTERNAL DATA | EMAIL {source} >>>`) applied to all tool returns
- FastMCP `instructions` declares safety posture up front
- System prompt warns about treating email content as untrusted

## Workflow

1. **Quick Setup**: `POST /api/services/quick` with provider + email + password, or use `configure_service()` for custom configs
2. **Verify**: `list_services()` then `email_status()` to confirm connectivity
3. **Read**: `check_inbox(limit=10, unread_only=True)` or `search_emails(query="meeting")`
4. **Act**: `send_email()` to send, `delete_email()` to remove, `mark_email_read()` to triage
5. **Create**: Use `/api/workflow` for love letters, complaints, fan mail -- with ASCII art or SVG card output
6. **Test**: Mail Lab at `/lab` for throwaway SMTP testing without affecting real accounts

## Examples

- "Set up my Gmail" → `email_status()` → verify → `check_inbox(limit=10)`
- "Find all invoices" → `search_emails(query="invoice", limit=50)`
- "Write a love letter to my Landlady in ASCII art" → `POST /api/workflow` with `{workflow: "love-letter", recipient: "Landlady", format: "ascii"}`
- "Send a complaint to my WiFi Router as an SVG card" → `POST /api/workflow` with `{workflow: "complaint", recipient: "The WiFi Router", format: "svg"}`
- "Clean up my inbox" → `email_agentic_assist(goal="archive all read emails older than 30 days")`
- "Start a throwaway SMTP server" → Mail Lab page at `/lab`
