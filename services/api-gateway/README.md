# API Gateway Service

FastAPI-based API Gateway for routing requests to microservices.

## Features

- **Request Routing**: Routes requests to appropriate microservices
- **Rate Limiting**: 60 requests/minute, 1000 requests/hour per IP
- **Request ID Tracking**: Unique ID for each request
- **CORS**: Configurable cross-origin resource sharing
- **Health Checks**: Monitor all backend services
- **Request Logging**: Track all incoming requests
- **Error Handling**: Centralized error responses

## Running the Gateway

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the gateway
uvicorn app.main:app --reload --port 8000
```

## API Routes

Gateway routes all requests with `/api/v1/` prefix:

- `/api/v1/auth/*` → Auth Service (port 8001)
- `/api/v1/applications/*` → Application Service (port 8002)
- `/api/v1/documents/*` → Document Service (port 8003)
- `/api/v1/underwriting/*` → Underwriting Service (port 8004)
- `/api/v1/scoring/*` → Scoring Service (port 8005)

## Example Usage

```bash
# Login via gateway
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@analyticaloan.com&password=admin123"

# Check gateway health
curl http://localhost:8000/health
```

## Rate Limiting

Responses include rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

## Request Tracking

Every response includes `X-Request-ID` header for debugging and tracing.
