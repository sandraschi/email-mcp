# Local Testing Services

## MailHog

MailHog provides a local SMTP server with a web UI for viewing captured emails.

### Setup
```bash
# Start MailHog (Docker)
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or download from https://github.com/mailhog/MailHog/releases
```

### Configuration
```bash
export MAILHOG_ENABLED="true"
export MAILHOG_SMTP_HOST="localhost"
export MAILHOG_SMTP_PORT="1025"
export MAILHOG_HTTP_URL="http://localhost:8025"
```

### MCP Tool
```
configure_service(name="mailhog", type="local", config={
  "smtp_server": "localhost",
  "smtp_port": 1025,
  "http_url": "http://localhost:8025",
  "service_type": "mailhog"
})
```

## Mailpit

Modern mail testing tool with a clean web interface.

### Setup
```bash
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit
```

### Configuration
```
configure_service(name="mailpit", type="local", config={
  "smtp_server": "localhost",
  "smtp_port": 1025,
  "http_url": "http://localhost:8025",
  "service_type": "mailpit"
})
```

## MailCatcher

Ruby-based mail testing. SMTP on 1025, web UI on 1080.

```
configure_service(name="mailcatcher", type="local", config={
  "smtp_server": "localhost",
  "smtp_port": 1025,
  "http_url": "http://localhost:1080",
  "service_type": "mailcatcher"
})
```

## Inbucket

Lightweight testing with REST API.

```
configure_service(name="inbucket", type="local", config={
  "smtp_server": "localhost",
  "smtp_port": 2500,
  "http_url": "http://localhost:9000",
  "service_type": "inbucket"
})
```

## Notes
- Local services never send real emails
- All captured emails visible in the web UI
- Great for development and testing
