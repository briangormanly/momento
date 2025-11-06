# momento


|## Setup Instructions

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

# Application Configuration
APP_NAME=Momento
APP_VERSION=0.1.0
```

**Important**: Generate a secure JWT secret key:
```bash
openssl rand -hex 32
```


### 3. Run the Application

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