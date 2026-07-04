# Cursor Setup for Email MCP

## Project-level MCP Config

**Config location**: `.cursor/mcp.json` in your project root

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/email-mcp", "run", "email-mcp"],
      "env": {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-app-password",
        "IMAP_SERVER": "imap.gmail.com",
        "IMAP_USER": "your-email@gmail.com",
        "IMAP_PASSWORD": "your-app-password"
      }
    }
  }
}
```

## Available Commands

- `list_services()` -- show configured services
- `email_status()` -- test connectivity
- `send_email(to, subject, body)` -- send via default service
- `check_inbox(limit=10)` -- read inbox
- `configure_service(name, type, config)` -- add services at runtime

See [README.md](README.md) for all 32+ available tools.
