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

### Graph & Memory Endpoints

- `POST /graph/entries` - ingest a raw memory/note (text first, media soon). Extraction runs in the background.
- `GET /graph/entities/{id}` - fetch a single entity (ENTRY, PERSON, LOCATION, etc.).
- `GET /graph/entities` - basic listing with pagination.
- `POST /graph/search/text` - lightweight substring search across entity names/summaries.
- `POST /graph/search/semantic` - semantic search placeholder (currently proxies to text search until embeddings are plugged in).

### MCP Connectors

- `GET /mcp/connectors` - list registered external model connections.
- `POST /mcp/connectors` - register a new connection for future MCP integrations (stored in-memory for now).

## Graph Module Layout

```
src/graph/
├── models.py              # Pydantic Entity/Relation + supporting value objects
├── schemas.py             # Request/response objects for FastAPI
├── repositories/          # Neo4j persistence helpers
├── services/              # Entry ingestion, entity CRUD, search orchestration
├── use_cases/             # Command/query use cases for routers + MCP
├── providers/             # Extraction providers (local heuristic, Ollama, OpenAI, Anthropic)
├── pipeline/              # Extraction runner + observers
├── tasks/                 # Background task dispatchers
└── routers.py             # FastAPI endpoints calling the use cases
```

A parallel `src/integrations/mcp/` package houses connector schemas/services/routes so model connections can enter through the same service layer in the future.

## Configuration & Models

See `.env.example` for exhaustive environment variables. Highlights:

- `EXTRACTION_PROVIDER` controls which provider (local, ollama, openai, anthropic) powers entity extraction.
- `EXTRACTION_ALLOW_FALLBACK` toggles whether we fall back to heuristics or fail fast when the provider response is invalid (defaults to `False` now, so failures surface immediately).
- `EXTRACTION_CONTEXT_WINDOW_TOKENS` defines how much text is passed to the provider so you can align with each model's context window.
- `OLLAMA_TIMEOUT_SECONDS`, `OLLAMA_MAX_RETRIES`, and `OLLAMA_KEEP_ALIVE` control long-running local model calls so you can keep a model warm and tolerate slower generations.
- `OLLAMA_*`, `OPENAI_*`, `ANTHROPIC_*` variables hold connection info/keys for each provider.
- `API_RATE_LIMIT_PER_MINUTE` and `ENABLE_AUDIT_LOGGING` prepare for future security hardening.

The graph pipeline writes everything through the Pydantic models in `src/graph/models.py`, ensuring the FastAPI docs show rich examples (content blocks, attachments, embeddings, observations, etc.).
