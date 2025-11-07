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


### 4. Run the Application

```bash
# Using uvicorn directly
uvicorn src.main:app --reload

# or -- using uv
uv run uvicorn src.main:app --reload

# Or specify host and port
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# or -- using unv
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
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
