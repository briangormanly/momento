# momento

## Setup Instructions

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Create .env File

Create a `.env` file in the project root with the following content:

```env
# Neo4j Database Configuration
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j_password
NEO4J_DATABASE=momento

# JWT Configuration
# Generate a secure secret key: openssl rand -hex 32
JWT_SECRET_KEY=your-secret-key-here-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Verification Configuration
EMAIL_VERIFICATION_EXPIRE_HOURS=24

# Email/SMTP Configuration
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_FROM=noreply@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
MAIL_FROM_NAME=Momento

# Application Configuration
APP_NAME=Momento
APP_VERSION=0.1.0
```

**Important**: Generate a secure JWT secret key:
```bash
openssl rand -hex 32
```

### 3. Configure SMTP for Email Verification

The application sends email verification links during user registration. You need to configure an SMTP server for this functionality.

#### Option A: Using an Email Service Provider (Recommended)

For production, use a reliable email service provider:

- **Gmail**: Use Gmail SMTP with an app-specific password
  - `MAIL_SERVER=smtp.gmail.com`
  - `MAIL_PORT=587`
  - `MAIL_STARTTLS=True`

- **SendGrid**: Professional email delivery service
  - `MAIL_SERVER=smtp.sendgrid.net`
  - `MAIL_PORT=587`
  - `MAIL_USERNAME=apikey`
  - `MAIL_PASSWORD=your_sendgrid_api_key`

- **AWS SES**: Amazon's email service
  - `MAIL_SERVER=email-smtp.us-east-1.amazonaws.com`
  - `MAIL_PORT=587`
  - Configure with SMTP credentials from AWS

- **Mailgun, Postmark, etc.**: Follow their SMTP configuration docs

#### Option B: Local Testing (macOS/Development)

For local development and testing on macOS (Apple Silicon or Intel):

**Using MailHog (Recommended for Testing)**

MailHog is a local SMTP server with a web UI that captures all emails - perfect for development.

**Install MailHog:**

```bash
# Using Homebrew (recommended)
brew install mailhog

# Or download binary from GitHub
# https://github.com/mailhog/MailHog/releases
```

**Start MailHog:**

```bash
# Start MailHog (runs on ports 1025 for SMTP, 8025 for web UI)
mailhog
```

MailHog will start and be available at:
- **SMTP Server**: `localhost:1025` (no authentication needed)
- **Web UI**: http://localhost:8025 (view all captured emails)

**Configure Application:**

Add to your `.env` file:
```env
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_STARTTLS=False
MAIL_SSL_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@localhost
```

**Alternative: Using Docker**

If you prefer Docker:
```bash
# Run MailHog in Docker
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or use docker-compose
```

**Alternative: macOS Built-in Postfix**

macOS includes Postfix, but it's disabled by default. To enable:

```bash
# Enable Postfix
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.postfix.master.plist

# Check status
sudo postfix status

# Configure for local delivery only
sudo nano /etc/postfix/main.cf
```

Add/modify:
```conf
inet_interfaces = loopback-only
mydestination = $myhostname, localhost.$mydomain, localhost
```

Restart:
```bash
sudo postfix reload
```

Then configure your app:
```env
MAIL_SERVER=localhost
MAIL_PORT=25
MAIL_STARTTLS=False
MAIL_SSL_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
```

**View Emails:**

- **MailHog**: Open http://localhost:8025 in your browser
- **Postfix**: Check `/var/mail/yourusername` or use `mail` command

#### Option C: Self-Hosted SMTP Server (Linux)

For development or self-hosted deployments on Linux servers:

**Install Postfix (SMTP Server)**

```bash
# Update package list
sudo apt update

# Install Postfix (select "Internet Site" when prompted)
sudo apt install postfix -y

# Install mail utilities (optional, for testing)
sudo apt install mailutils -y
```

**Configure Postfix for Relay**

Edit the main configuration:
```bash
sudo nano /etc/postfix/main.cf
```

Key configuration options:
```conf
# Set your server's hostname
myhostname = yourdomain.com

# Network interfaces to listen on
inet_interfaces = loopback-only

# For relay through another SMTP server (optional)
relayhost = [smtp.example.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt
```

If using relay with authentication, create credential file:
```bash
sudo nano /etc/postfix/sasl_passwd
```

Add relay credentials:
```
[smtp.example.com]:587 username:password
```

Secure and reload:
```bash
sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
sudo systemctl restart postfix
```

**Test Email Sending**

```bash
echo "Test email body" | mail -s "Test Subject" recipient@example.com
```

**Configure Application**

For local Postfix:
```env
MAIL_SERVER=localhost
MAIL_PORT=25
MAIL_STARTTLS=False
MAIL_SSL_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
```

**Security Notes:**
- Ensure your firewall allows outbound SMTP traffic (port 587 or 25)
- Configure SPF, DKIM, and DMARC records for production email
- Monitor `/var/log/mail.log` for email delivery issues
- Consider using a dedicated email service for better deliverability

### 4. Run the Application

```bash
# Using uvicorn directly
uvicorn src.main:app --reload

# Or specify host and port
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user account (sends verification email)
- `GET /auth/verify-email?token={token}` - Verify email and activate account
- `POST /auth/login` - Login with email and password
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user information (authenticated)
- `POST /auth/logout` - Logout (client-side token cleanup)

### Registration Flow

1. User submits email and password to `/auth/register`
2. System sends verification email with a time-limited JWT token
3. User clicks the link in the email (valid for 24 hours by default)
4. System verifies the token, creates the account, and returns JWT tokens
5. User is immediately logged in and can make authenticated requests

**Security Features:**
- Email enumeration prevention (same response for existing/new emails)
- Password never appears in URLs (stored hashed in JWT payload)
- Verification links expire after configured time (24 hours default)
- Expired verification records are automatically cleaned up
