# Email MCP Server - Troubleshooting Guide

## Common Issues & Solutions

### 1. Authentication Failures

#### Gmail SMTP Authentication Issues

**Problem:** `Authentication failed` when using Gmail SMTP

**Symptoms:**
- Error: "535-5.7.8 Username and Password not accepted"
- Email sending fails immediately
- Works in web interface but not via SMTP

**Solutions:**

1. **Use App Passwords (Required for Gmail)**
   ```bash
   # 1. Enable 2FA on your Google account
   # 2. Go to https://myaccount.google.com/apppasswords
   # 3. Generate app password for "Mail"
   # 4. Use the 16-character password (without spaces)
   ```

   ```python
   configure_service(
       name="gmail-fixed",
       type="smtp",
       config={
           "smtp_server": "smtp.gmail.com",
           "smtp_port": 587,
           "smtp_user": "your.email@gmail.com",
           "smtp_password": "abcd-efgh-ijkl-mnop"  # 16-char app password
       }
   )
   ```

2. **Check Account Security Settings**
   - Ensure 2FA is enabled
   - Allow less secure apps (if 2FA not available)
   - Check for account locks or suspicious activity alerts

3. **Verify SMTP Settings**
   ```python
   # Correct Gmail SMTP settings
   config = {
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587,  # TLS
       "smtp_user": "your.email@gmail.com",
       "smtp_password": "your-app-password"
   }
   ```

#### Outlook/Hotmail Authentication

**Problem:** Authentication fails with Outlook accounts

**Solutions:**
1. Use app passwords for Microsoft accounts with 2FA
2. Check account status at https://account.microsoft.com
3. Verify SMTP settings:
   ```python
   config = {
       "smtp_server": "smtp-mail.outlook.com",
       "smtp_port": 587,
       "smtp_user": "your.email@outlook.com",
       "smtp_password": "your-app-password"
   }
   ```

### 2. Connection Problems

#### SMTP Connection Timeouts

**Problem:** `Connection timeout` or `Connection refused`

**Symptoms:**
- Emails queue but never send
- Service status shows "disconnected"
- Works intermittently

**Solutions:**

1. **Check Network/Firewall Settings**
   ```bash
   # Test basic connectivity
   telnet smtp.gmail.com 587
   telnet smtp-mail.outlook.com 587
   ```

2. **Verify SMTP Server Details**
   ```python
   # Common SMTP servers and ports
   smtp_servers = {
       "gmail": {"server": "smtp.gmail.com", "port": 587},
       "outlook": {"server": "smtp-mail.outlook.com", "port": 587},
       "yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
       "icloud": {"server": "smtp.mail.me.com", "port": 587}
   }
   ```

3. **Try Alternative Ports**
   ```python
   # Some providers support multiple ports
   ports_to_try = [587, 465, 25]  # TLS, SSL, plaintext
   ```

4. **Check ISP Blocking**
   - Some ISPs block port 25
   - Use port 587 (TLS) or 465 (SSL) instead

#### IMAP Connection Issues

**Problem:** Cannot check inbox or read emails

**Solutions:**
1. **Verify IMAP Settings**
   ```python
   imap_settings = {
       "gmail": {"server": "imap.gmail.com", "port": 993},
       "outlook": {"server": "outlook.office365.com", "port": 993},
       "yahoo": {"server": "imap.mail.yahoo.com", "port": 993}
   }
   ```

2. **Enable IMAP in Account Settings**
   - Gmail: Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
   - Outlook: Account settings → Sync email → IMAP

### 3. Service Configuration Issues

#### API Service Authentication

**Problem:** SendGrid/Mailgun API calls fail

**Symptoms:**
- `401 Unauthorized` errors
- `Invalid API key` messages
- Service shows as "configured" but fails

**Solutions:**

1. **Verify API Keys**
   ```python
   # Test API key validity
   import requests

   def test_sendgrid_key(api_key):
       response = requests.get(
           "https://api.sendgrid.com/v3/user/account",
           headers={"Authorization": f"Bearer {api_key}"}
       )
       return response.status_code == 200

   def test_mailgun_key(api_key, domain):
       response = requests.get(
           f"https://api.mailgun.net/v3/domains/{domain}",
           auth=("api", api_key)
       )
       return response.status_code == 200
   ```

2. **Check API Key Permissions**
   - SendGrid: Ensure key has "Mail Send" permission
   - Mailgun: Verify domain ownership and API key scope

3. **Update Expired Keys**
   ```python
   # Rotate API keys
   configure_service(
       name="sendgrid-updated",
       type="api",
       config={
           "api_key": "SG.new-api-key-here",
           "from_email": "noreply@yourdomain.com",
           "service_type": "sendgrid"
       }
   )
   ```

#### Webhook Configuration Problems

**Problem:** Slack/Discord webhooks not working

**Solutions:**
1. **Verify Webhook URLs**
   ```python
   import requests

   def test_webhook(url, service_type):
       test_payload = {"text": "Test message"}
       if service_type == "slack":
           response = requests.post(url, json=test_payload)
       elif service_type == "discord":
           response = requests.post(url, json={"content": "Test message"})
       return response.status_code == 200
   ```

2. **Check Webhook Permissions**
   - Slack: Ensure bot has chat:write permission
   - Discord: Verify webhook has Send Messages permission

### 4. Rate Limiting & Quotas

#### Email Service Limits

**Problem:** `Rate limit exceeded` or `Too many requests`

**Solutions:**

1. **Implement Rate Limiting**
   ```python
   import time
   from collections import defaultdict

   class EmailRateLimiter:
       def __init__(self):
           self.requests = defaultdict(list)
           self.limits = {
               "sendgrid": 100,  # per minute
               "mailgun": 300,   # per hour
               "smtp": 50        # per minute
           }

       def can_send(self, service):
           now = time.time()
           self.requests[service] = [
               t for t in self.requests[service] if now - t < 60
           ]
           return len(self.requests[service]) < self.limits.get(service, 10)

       def record_send(self, service):
           self.requests[service].append(time.time())
   ```

2. **Batch Email Sending**
   ```python
   import asyncio

   async def send_batch_with_delay(emails, delay_seconds=1):
       for email in emails:
           await send_email(**email)
           await asyncio.sleep(delay_seconds)
   ```

3. **Queue Management**
   ```python
   from queue import Queue
   import threading
   import time

   class EmailQueue:
       def __init__(self, rate_limiter):
           self.queue = Queue()
           self.rate_limiter = rate_limiter
           self.worker_thread = threading.Thread(target=self._process_queue)
           self.worker_thread.daemon = True
           self.worker_thread.start()

       def add_email(self, email_data):
           self.queue.put(email_data)

       def _process_queue(self):
           while True:
               if not self.queue.empty() and self.rate_limiter.can_send(email_data.get('service', 'smtp')):
                   email_data = self.queue.get()
                   try:
                       result = send_email(**email_data)
                       if result['success']:
                           self.rate_limiter.record_send(email_data.get('service', 'smtp'))
                       else:
                           # Re-queue failed emails
                           self.queue.put(email_data)
                   except Exception as e:
                       print(f"Failed to send email: {e}")
                       self.queue.put(email_data)
               time.sleep(1)
   ```

### 5. Content & Formatting Issues

#### HTML Email Problems

**Problem:** HTML emails display as plain text or format incorrectly

**Solutions:**

1. **Proper HTML Structure**
   ```python
   def create_html_email(content, title):
       html_template = f"""
       <!DOCTYPE html>
       <html>
       <head>
           <meta charset="utf-8">
           <title>{title}</title>
           <style>
               body {{ font-family: Arial, sans-serif; margin: 20px; }}
               .header {{ background: #f0f0f0; padding: 20px; }}
               .content {{ margin: 20px 0; }}
           </style>
       </head>
       <body>
           <div class="header">
               <h1>{title}</h1>
           </div>
           <div class="content">
               {content}
           </div>
       </body>
       </html>
       """
       return html_template
   ```

2. **Inline CSS for Compatibility**
   ```python
   def inline_css_styles(html_content):
       # Use a library like premailer or inline CSS manually
       # For simple cases, ensure all styles are inline
       return html_content.replace(
           '<p>',
           '<p style="margin: 10px 0; line-height: 1.5;">'
       )
   ```

#### Email Encoding Issues

**Problem:** Special characters display incorrectly

**Solutions:**
1. **UTF-8 Encoding**
   ```python
   send_email(
       to="user@example.com",
       subject="Test with special chars: café, naïve, résumé",
       body="Content with special characters: é, ñ, ü",
       service="sendgrid"  # APIs handle encoding better than SMTP
   )
   ```

2. **Header Encoding**
   ```python
   import email.utils

   def encode_subject(subject):
       # Let the email library handle encoding
       msg = email.message.EmailMessage()
       msg['Subject'] = subject
       return msg['Subject']
   ```

### 6. Delivery & Bounce Issues

#### Emails Not Being Delivered

**Problem:** Emails sent successfully but not received

**Solutions:**

1. **Check Spam/Junk Folders**
   - Advise recipients to check spam folders
   - Use services with good deliverability (SendGrid, Mailgun)

2. **SPF/DKIM/DMARC Setup**
   ```python
   # For custom domains, ensure proper DNS records
   spf_record = "v=spf1 include:_spf.google.com ~all"  # Gmail
   dkim_record = "v=DKIM1; k=rsa; p=..."  # Provided by email service
   dmarc_record = "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"
   ```

3. **Monitor Delivery Status**
   ```python
   def check_delivery_status(message_id, service):
       if service == "sendgrid":
           # SendGrid delivery tracking
           response = requests.get(
               f"https://api.sendgrid.com/v3/mailbox_providers/stats",
               headers={"Authorization": f"Bearer {api_key}"}
           )
       elif service == "mailgun":
           # Mailgun delivery tracking
           response = requests.get(
               f"https://api.mailgun.net/v3/{domain}/events",
               auth=("api", api_key),
               params={"message-id": message_id}
           )
   ```

#### Bounce Handling

**Problem:** High bounce rates affecting sender reputation

**Solutions:**

1. **Clean Email Lists**
   ```python
   def clean_email_list(emails):
       # Remove invalid email formats
       import re
       email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
       return [email for email in emails if re.match(email_pattern, email)]
   ```

2. **Handle Bounces**
   ```python
   def process_bounce_notification(bounce_data):
       # Remove bounced emails from lists
       bounced_email = bounce_data['email']
       bounce_type = bounce_data['type']  # hard, soft

       if bounce_type == 'hard':
           remove_from_all_lists(bounced_email)
       elif bounce_type == 'soft':
           mark_as_temporary_issue(bounced_email)
   ```

### 7. Performance Issues

#### Slow Email Sending

**Problem:** Emails take too long to send or process

**Solutions:**

1. **Async Processing**
   ```python
   import asyncio

   async def send_emails_async(email_list):
       tasks = [send_email(**email_data) for email_data in email_list]
       results = await asyncio.gather(*tasks, return_exceptions=True)
       return results
   ```

2. **Connection Reuse**
   ```python
   import smtplib

   class PersistentSMTP:
       def __init__(self, server, port, user, password):
           self.server = server
           self.port = port
           self.user = user
           self.password = password
           self.connection = None

       def connect(self):
           if not self.connection:
               self.connection = smtplib.SMTP(self.server, self.port)
               self.connection.starttls()
               self.connection.login(self.user, self.password)

       def send(self, msg):
           self.connect()
           self.connection.send_message(msg)

       def close(self):
           if self.connection:
               self.connection.quit()
               self.connection = None
   ```

3. **Batch Processing**
   ```python
   def process_emails_in_batches(email_list, batch_size=10):
       for i in range(0, len(email_list), batch_size):
           batch = email_list[i:i + batch_size]
           results = send_emails_async(batch)  # or sync processing
           process_batch_results(results)
           time.sleep(1)  # Rate limiting between batches
   ```

### 8. Debugging & Monitoring

#### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# For SMTP debugging
smtplib.SMTP.debuglevel = 1  # Shows SMTP protocol messages

# For requests debugging
import http.client
http.client.HTTPConnection.debuglevel = 1
```

#### Monitor Email Operations

```python
class EmailMonitor:
    def __init__(self):
        self.stats = {
            'sent': 0,
            'failed': 0,
            'avg_response_time': 0,
            'service_usage': defaultdict(int)
        }
        self.response_times = []

    def record_send(self, service, success, response_time):
        if success:
            self.stats['sent'] += 1
        else:
            self.stats['failed'] += 1

        self.stats['service_usage'][service] += 1
        self.response_times.append(response_time)

        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

        self.stats['avg_response_time'] = sum(self.response_times) / len(self.response_times)

    def get_stats(self):
        return dict(self.stats)

# Usage
monitor = EmailMonitor()

async def monitored_send_email(**kwargs):
    start_time = time.time()
    result = await send_email(**kwargs)
    response_time = time.time() - start_time

    monitor.record_send(
        kwargs.get('service', 'smtp'),
        result.get('success', False),
        response_time
    )

    return result
```

### 9. Testing & Development

#### Local Testing Setup

1. **MailHog for SMTP Testing**
   ```bash
   # Install and run MailHog
   docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog

   # Configure service
   configure_service(
       name="mailhog-test",
       type="local",
       config={
           "smtp_server": "localhost",
           "smtp_port": 1025,
           "http_url": "http://localhost:8025"
       }
   )
   ```

2. **Mailpit Alternative**
   ```bash
   docker run -p 1025:1025 -p 8025:8025 axllent/mailpit
   ```

#### Integration Testing

```python
def test_email_integration():
    """Comprehensive email integration test"""

    # Test SMTP service
    result = send_email(
        to="test@example.com",
        subject="Integration Test",
        body="Testing email integration",
        service="mailhog"
    )
    assert result['success'], f"SMTP test failed: {result.get('error')}"

    # Test inbox checking
    inbox_result = check_inbox(limit=1)
    assert 'emails' in inbox_result, "Inbox check failed"

    # Test service status
    status_result = email_status()
    assert status_result['connected_services'] > 0, "No services connected"

    print("✅ All email integrations working correctly")

# Run integration tests
test_email_integration()
```

### 10. Security Considerations

#### Secure Credential Management

1. **Environment Variables**
   ```bash
   # Use environment variables for credentials
   export SMTP_PASSWORD="your-secure-password"
   export SENDGRID_API_KEY="SG.your-secure-api-key"
   ```

2. **Secret Management Services**
   ```python
   # AWS Secrets Manager
   import boto3

   def get_secret(secret_name):
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId=secret_name)
       return response['SecretString']

   # Azure Key Vault
   from azure.keyvault.secrets import SecretClient
   from azure.identity import DefaultAzureCredential

   def get_azure_secret(vault_url, secret_name):
       credential = DefaultAzureCredential()
       client = SecretClient(vault_url=vault_url, credential=credential)
       secret = client.get_secret(secret_name)
       return secret.value
   ```

3. **Credential Rotation**
   ```python
   def rotate_api_keys():
       """Rotate API keys periodically"""
       new_sendgrid_key = generate_new_sendgrid_key()
       new_mailgun_key = generate_new_mailgun_key()

       # Update services
       configure_service(
           name="sendgrid-rotated",
           type="api",
           config={
               "api_key": new_sendgrid_key,
               "service_type": "sendgrid"
           }
       )

       # Archive old keys
       archive_old_keys()
   ```

This troubleshooting guide covers the most common issues and provides practical solutions for maintaining reliable email functionality with the Email MCP Server.