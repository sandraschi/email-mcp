# Transactional Email APIs

## What "Transactional" Means (and Why It's Not Spam)

A **transactional email** is one the recipient **expects and wants** because it's triggered by something they did:

- "Your password reset link" ← you clicked "forgot password"
- "Your order has shipped" ← you bought something
- "Here's your receipt" ← you paid
- "Confirm your email address" ← you signed up
- "Your 2FA code is 847291" ← you're logging in

These are **not** spam. The recipient is actively waiting for them. If they don't arrive, the user is stuck — they can't reset their password, can't log in, don't know if their order went through.

Transactional APIs (SendGrid, Mailgun, Resend, Amazon SES) are built specifically for this. They are **not "spam cannons"** — in fact, they actively prevent spam:

| | Gmail SMTP | Transactional API |
|---|---|---|
| **Daily limit** | ~500 emails/day | **100,000+ per hour** (on paid plans) |
| **What it's for** | You typing emails by hand | Automated machine-to-human mail |
| **Deliverability** | Lands in spam if you send >20 automated emails | Pre-warmed IPs, ISP feedback loops |
| **Tracking** | None | Opens, clicks, bounces, complaints |
| **Complaint handling** | Your Gmail gets banned | Automatic suppression of hard bounces |
| **Templates** | Manual HTML | Dynamic templates with variables |

## Why Gmail SMTP Won't Cut It

If you use your personal Gmail to send password reset emails to 100 users, Gmail will:

1. **Rate-limit you** after ~20 automated emails per hour
2. **Flag your account** for suspicious behavior
3. **Land your emails in spam** because the content looks machine-generated
4. Eventually **suspend your account**

Transactional APIs solve this by operating from **dedicated sending infrastructure** with pre-warmed IPs, SPF/DKIM/DMARC authentication, and direct relationships with ISPs (Gmail, Outlook, Yahoo) so your password reset emails actually arrive in the inbox.

## The "100K per Hour" Number

That's the **upper limit on paid plans** (SendGrid Pro, for example). Most users send far less — a few hundred to a few thousand transactional emails per day. The free tiers are generous:

- **SendGrid Free**: 100 emails/day forever
- **Mailgun Flex**: 5,000 emails/month for 3 months
- **Resend Free**: 3,000 emails/month
- **Amazon SES**: 62,000 emails/month from EC2 (free)

## Caveats

- **No inbox checking**: Send-only. You can't read incoming mail via an API service.
- **No IMAP**: These are REST APIs, not mail servers. They don't store messages.
- **Rate limits vary by plan**: Check your provider's docs.
- **Still need SPF/DKIM**: Configure domain authentication or emails go to spam.
- **Not for newsletters without consent**: Sending unsolicited bulk mail will get your account terminated.

## Providers

### SendGrid

- API Key with "Mail Send" permission
- Environment: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`

```
configure_service(name="sendgrid", type="api", config={
  "api_key": "your-sendgrid-api-key",
  "api_url": "https://api.sendgrid.com/v3/mail/send",
  "from_email": "noreply@yourdomain.com",
  "service_type": "sendgrid"
})
```

### Mailgun

- Requires a verified domain

```
configure_service(name="mailgun", type="api", config={
  "api_key": "your-mailgun-api-key",
  "api_url": "https://api.mailgun.net/v3/yourdomain.com/messages",
  "from_email": "noreply@yourdomain.com",
  "service_type": "mailgun"
})
```

### Resend

- Modern API, Node.js/Python SDKs

```
configure_service(name="resend", type="api", config={
  "api_key": "your-resend-api-key",
  "api_url": "https://api.resend.com/emails",
  "from_email": "noreply@yourdomain.com",
  "service_type": "resend"
})
```

### Amazon SES

- Requires AWS account, domain verification

```
configure_service(name="ses", type="api", config={
  "api_key": "your-aws-access-key",
  "api_url": "https://email.YOUR-REGION.amazonaws.com/v2/email/outbound-emails",
  "from_email": "noreply@yourdomain.com",
  "service_type": "ses"
})
```

## Notes

- API services support sending only (no inbox checking)
- Store API keys securely — never commit to version control
- Free tiers are generous but production use requires a paid plan
- Always configure SPF, DKIM, and DMARC for your sending domain
