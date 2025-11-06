## API Endpoints

### Public Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check (includes database status)

### Authentication Endpoints

- `POST /auth/login` - Login with email and password
- `POST /auth/refresh` - Refresh access token using refresh token
- `GET /auth/me` - Get current user information (requires auth)
- `POST /auth/logout` - Logout (client-side token cleanup)

### Protected Endpoint Example

- `GET /protected` - Example protected route (requires auth)

## Usage Examples

### 1. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your_password_here"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer <your_access_token>"
```

### 3. Refresh Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<your_refresh_token>"
  }'
```

### 4. Get Current User

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <your_access_token>"
```

## Protecting Your Routes

To protect a route, add the `get_current_user` dependency:

```python
from fastapi import Depends
from src.auth.dependencies import get_current_user
from src.auth.models import User

@app.get("/my-protected-route")
async def my_route(user: User = Depends(get_current_user)):
    return {"message": f"Hello {user.email}"}
```

### Role-Based Protection

For future role-based access control:

```python
from src.auth.dependencies import require_roles

@app.get("/admin-only")
async def admin_route(user: User = Depends(require_roles(["admin"]))):
    return {"message": "Admin access granted"}
```

## Error Handling

The API returns standardized error responses:

- **401 Unauthorized**: Invalid credentials, missing token, or expired token
- **403 Forbidden**: Insufficient privileges (for role-based endpoints)

Example error response:
```json
{
  "error": "authentication_error",
  "detail": "Invalid email or password"
}
```