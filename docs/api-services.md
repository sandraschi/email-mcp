# Transactional Email APIs

## SendGrid

### Prerequisites
- SendGrid account (https://sendgrid.com)
- API Key with "Mail Send" permission

### Configuration
```bash
export SENDGRID_API_KEY="your-sendgrid-api-key"
export SENDGRID_FROM_EMAIL="noreply@yourdomain.com"
```

### MCP Tool
```
configure_service(name="sendgrid", type="api", config={
  "api_key": "your-sendgrid-api-key",
  "api_url": "https://api.sendgrid.com/v3/mail/send",
  "from_email": "noreply@yourdomain.com",
  "service_type": "sendgrid"
})
```

## Mailgun

### Prerequisites
- Mailgun account (https://mailgun.com)
- Verified domain

### Configuration
```bash
export MAILGUN_API_KEY="your-mailgun-api-key"
export MAILGUN_DOMAIN="yourdomain.com"
export MAILGUN_FROM_EMAIL="noreply@yourdomain.com"
```

### MCP Tool
```
configure_service(name="mailgun", type="api", config={
  "api_key": "your-mailgun-api-key",
  "api_url": "https://api.mailgun.net/v3/yourdomain.com/messages",
  "from_email": "noreply@yourdomain.com",
  "service_type": "mailgun"
})
```

## Resend

### Prerequisites
- Resend account (https://resend.com)
- API Key

### Configuration
```bash
export RESEND_API_KEY="your-resend-api-key"
export RESEND_FROM_EMAIL="noreply@yourdomain.com"
```

### MCP Tool
```
configure_service(name="resend", type="api", config={
  "api_key": "your-resend-api-key",
  "api_url": "https://api.resend.com/emails",
  "from_email": "noreply@yourdomain.com",
  "service_type": "resend"
})
```

## Amazon SES

### Configuration via MCP Tool
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
- Rate limits vary by provider and plan
- Store API keys securely — never commit to version control
