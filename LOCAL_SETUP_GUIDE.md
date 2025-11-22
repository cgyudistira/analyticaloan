# AnalyticaLoan - Local Development Setup

Quick start guide untuk menjalankan AnalyticaLoan di lokal.

---

## Prerequisites

### Required Software
- ✅ **Python 3.11+** - `python --version`
- ✅ **Poetry 1.7+** - `poetry --version`
- ✅ **Docker Desktop** - `docker --version`
- ✅ **Git** - `git --version`

### Optional (Recommended)
- Postman / Insomnia (untuk testing API)
- VS Code dengan extensions: Python, Docker, YAML

---

## Step 1: Clone & Setup Environment

```bash
# Navigate to project
cd d:\Projects\vibe\analyticaloan

# Copy environment template
copy .env.example .env

# Edit .env file dengan text editor
notepad .env
```

**Minimal .env configuration:**
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/analyticaloan

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Encryption
ENCRYPTION_KEY=your-fernet-encryption-key-32-bytes

# Gemini AI (OPTIONAL untuk lokal testing)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_FLASH_MODEL=gemini-2.0-flash-thinking-exp
GEMINI_PRO_MODEL=gemini-2.0-flash-exp

# Services
AUTH_SERVICE_URL=http://localhost:8001
DOCUMENT_SERVICE_URL=http://localhost:8003
UNDERWRITING_SERVICE_URL=http://localhost:8004
SCORING_SERVICE_URL=http://localhost:8005

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## Step 2: Install Dependencies

```bash
# Install Poetry (if not installed)
pip install poetry

# Install project dependencies
poetry install

# Verify installation
poetry run python --version
```

---

## Step 3: Start Infrastructure Services

```bash
# Start all infrastructure dengan Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected services:
# - postgres (port 5432)
# - redis (port 6379)
# - rabbitmq (port 5672, 15672)
# - weaviate (port 8080)
# - minio (port 9000, 9001)
# - prometheus (port 9090)
# - grafana (port 3000)
```

**Troubleshooting:**
```bash
#  Jika ada error port already in use
docker-compose down
netstat -ano | findstr :5432  # Check what's using port

# If PostgreSQL conflicts
net stop postgresql  # Stop local PostgreSQL if running
```

---

## Step 4: Setup Database

```bash
# Wait for PostgreSQL to be ready (15 seconds)
timeout /t 15

# Run migrations (create tables)
poetry run alembic upgrade head

# Seed initial data (users)
poetry run python scripts/seed_data.py
```

**Expected output:**
```
✓ Tables created
✓ Seeded 3 users

Default Credentials:
  Admin:
    Email: admin@analyticaloan.com
    Password: admin123
  Underwriter:
    Email: underwriter@analyticaloan.com
    Password: underwriter123
```

---

## Step 5: Start All Services

### Option A: Using Make (Recommended)
```bash
# Start all services di background
make dev

# Or start individual services in separate terminals:
make dev-auth       # Terminal 1
make dev-documents  # Terminal 2
make dev-underwriting  # Terminal 3
make dev-scoring    # Terminal 4
make dev-gateway    # Terminal 5
```

### Option B: Manual Start
```bash
# Terminal 1 - API Gateway (Port 8000)
cd services/api-gateway
poetry run uvicorn app.main:app --reload --port 8000

# Terminal 2 - Auth Service (Port 8001)
cd services/auth-service
poetry run uvicorn app.main:app --reload --port 8001

# Terminal 3 - Document Service (Port 8003)
cd services/document-service
poetry run uvicorn app.main:app --reload --port 8003

# Terminal 4 - Underwriting Service (Port 8004)
cd services/underwriting-service
poetry run uvicorn app.main:app --reload --port 8004

# Terminal 5 - Scoring Service (Port 8005)
cd services/scoring-service
poetry run uvicorn app.main:app --reload --port 8005

# Terminal 6 - WebSocket Service (Port 8006)
cd services/websocket-service
poetry run uvicorn app.main:app --reload --port 8006
```

---

## Step 6: Verify Services

### Health Checks
```bash
# API Gateway
curl http://localhost:8000/health

# Auth Service
curl http://localhost:8001/health

# Document Service
curl http://localhost:8003/health

# Underwriting Service
curl http://localhost:8004/health

# Scoring Service
curl http://localhost:8005/health
```

**Expected:** All return `{"status": "healthy"}`

---

## Step 7: Test Authentication

```bash
# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@analyticaloan.com&password=admin123"

# Response akan ada access_token
# Copy token untuk request selanjutnya
```

---

## Step 8: Open Frontend

```bash
# Buka browser
start http://localhost:8000

# Or langsung buka file
start frontend/index.html
```

**Note:** Frontend belum fully integrated dengan backend. Untuk testing API, gunakan Postman/curl.

---

## Common Commands

```bash
# Infrastructure
docker-compose up -d         # Start infrastructure
docker-compose down          # Stop infrastructure
docker-compose logs -f       # View logs

# Database
poetry run alembic upgrade head     # Run migrations
poetry run alembic downgrade -1     # Rollback 1 migration
poetry run python scripts/seed_data.py  # Seed data

# Development
poetry run pytest                   # Run tests
poetry run ruff check .             # Lint code
poetry run mypy services/           # Type check

# Services
make dev                            # Start all services
make stop                           # Stop all services
make logs                           # View logs
```

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| API Gateway | http://localhost:8000 | - |
| Auth Service | http://localhost:8001 | - |
| Document Service | http://localhost:8003 | - |
| Underwriting Service | http://localhost:8004 | - |
| Scoring Service | http://localhost:8005 | - |
| WebSocket | ws://localhost:8006 | - |
| PostgreSQL | localhost:5432 | postgres/postgres |
| Redis | localhost:6379 | - |
| RabbitMQ UI | http://localhost:15672 | guest/guest |
| MinIO UI | http://localhost:9001 | minioadmin/minioadmin |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Jaeger UI | http://localhost:16686 | - |

---

## Test Workflow (End-to-End)

### 1. Login
```bash
curl -X POST http://localhost:8001/auth/login \
  -d "username=admin@analyticaloan.com&password=admin123"
```

### 2. Create Application (TODO - implement endpoint)
```bash
# Will be available at POST /applications
```

### 3. Upload Document
```bash
curl -X POST http://localhost:8003/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "application_id=<uuid>" \
  -F "document_type=INCOME_STATEMENT" \
  -F "file=@path/to/document.pdf"
```

### 4. Trigger OCR
```bash
curl -X POST http://localhost:8003/documents/<doc_id>/ocr \
  -H "Authorization: Bearer <token>"
```

### 5. Start Underwriting
```bash
curl -X POST http://localhost:8004/underwrite \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"application_id": "<uuid>"}'
```

### 6. Check Workflow Status
```bash
curl http://localhost:8004/underwrite/<workflow_id>/status \
  -H "Authorization: Bearer <token>"
```

### 7. Get Decision
```bash
curl http://localhost:8004/applications/<app_id>/decision \
  -H "Authorization: Bearer <token>"
```

---

## Troubleshooting

### Issue: Port already in use
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Issue: Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Issue: Import errors
```bash
# Reinstall dependencies
poetry install --no-cache

# Or update
poetry update
```

### Issue: Gemini API errors
```bash
# Set env var untuk skip Gemini
export GEMINI_API_KEY=""

# Service akan gunakan fallback/mocked responses
```

---

## Development Tips

### Hot Reload
Semua services menggunakan `--reload` flag, jadi setiap perubahan code akan auto-restart service.

### Debugging
```bash
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use VS Code debugger
# F5 to start debugging
```

### Database GUI
```bash
# Install pgAdmin atau DBeaver
# Connect to localhost:5432
# Database: analyticaloan
# User: postgres
# Password: postgres
```

### API Testing
Import Postman collection dari `docs/API_Documentation.md` atau buat manual requests.

---

## Next Steps

1. ✅ Verify all services are running
2. ✅ Test authentication flow
3. ✅ Upload sample documents
4. ✅ Run full underwriting workflow
5. ✅ Check monitoring dashboards (Grafana, Prometheus)
6. ✅ Implement unit tests
7. ✅ Train ML model with real data
8. ✅ Deploy to staging

---

## Support

- **Documentation:** `docs/` directory
- **API Reference:** `docs/API_Documentation.md`
- **Architecture:** `docs/System_Architecture.md`
- **Issues:** Create GitHub issue

---

**Happy Coding! 🚀**
