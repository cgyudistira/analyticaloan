# AnalyticaLoan - Complete API Documentation

## Base URL
```
Production: https://api.analyticaloan.com
Development: http://localhost:8000
```

## Authentication
All API requests (except `/auth/login`) require JWT Bearer token:
```
Authorization: Bearer <access_token>
```

---

## 🔐 Authentication Service (Port 8001)

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@analyticaloan.com&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

---

## 📄 Document Service (Port 8003)

### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

application_id=<uuid>
document_type=INCOME_STATEMENT
file=@financial_statement.pdf
```

**Response:**
```json
{
  "document_id": "doc-uuid",
  "application_id": "app-uuid",
  "document_type": "INCOME_STATEMENT",
  "file_name": "financial_statement.pdf",
  "file_size_bytes": 245678,
  "storage_path": "applications/.../documents/...",
  "ocr_status": "PENDING",
  "uploaded_at": "2024-01-15T10:00:00Z"
}
```

### Trigger OCR Processing
```http
POST /documents/{document_id}/ocr
Authorization: Bearer <token>
```

**Response:**
```json
{
  "document_id": "doc-uuid",
  "text": "Extracted OCR text...",
  "confidence": 92.5,
  "pages": 3,
  "processed_at": "2024-01-15T10:05:00Z"
}
```

### List Application Documents
```http
GET /applications/{application_id}/documents
Authorization: Bearer <token>
```

---

## 🤖 Underwriting Service (Port 8004)

### Start Underwriting
```http
POST /underwrite
Content-Type: application/json
Authorization: Bearer <token>

{
  "application_id": "app-uuid",
  "auto_approve_threshold": 0.7,
  "auto_reject_threshold": 0.4
}
```

**Response:**
```json
{
  "workflow_id": "workflow-uuid",
  "application_id": "app-uuid",
  "status": "STARTED",
  "message": "Underwriting process initiated"
}
```

### Check Workflow Status
```http
GET /underwrite/{workflow_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "workflow_id": "workflow-uuid",
  "application_id": "app-uuid",
  "status": "RUNNING",
  "current_step": 5,
  "total_steps": 8,
  "progress_percentage": 62.5,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": null,
  "error_message": null
}
```

### Get Decision
```http
GET /applications/{application_id}/decision
Authorization: Bearer <token>
```

**Response:**
```json
{
  "decision_id": "decision-uuid",
  "application_id": "app-uuid",
  "decision_status": "APPROVE",
  "decision_reason": "Auto-approved: ML score 0.82 >= 0.7",
  "credit_score": 720,
  "probability_of_default": 0.12,
  "risk_rating": "A",
  "decided_at": "2024-01-15T10:15:00Z"
}
```

### Manual Override
```http
POST /applications/{application_id}/override
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer <token>

new_decision=APPROVE&override_reason=Collateral verified by underwriter
```

---

## 📊 Scoring Service (Port 8005)

### Calculate Credit Score
```http
POST /score
Content-Type: application/json
Authorization: Bearer <token>

{
  "application_id": "app-uuid",
  "applicant_data": {
    "monthly_income": 15000000,
    "age": 35,
    "occupation": "Software Engineer",
    "loan_amount": 100000000,
    "loan_term_months": 24
  },
  "financial_data": {
    "revenue": 500000000,
    "net_income": 50000000
  },
  "credit_bureau_data": {
    "credit_score": 680,
    "delinquent_accounts": 0
  }
}
```

**Response:**
```json
{
  "scoring_id": "score-uuid",
  "application_id": "app-uuid",
  "credit_score": 720,
  "probability_of_default": 0.15,
  "risk_rating": "A",
  "model_version": "1.0.0",
  "confidence": 0.85,
  "scored_at": "2024-01-15T10:10:00Z"
}
```

### Get XAI Explanation
```http
GET /score/{scoring_id}/explain
Authorization: Bearer <token>
```

**Response:**
```json
{
  "scoring_id": "score-uuid",
  "feature_importances": {
    "payment_to_income_ratio": 0.25,
    "credit_score": 0.20,
    "monthly_income": 0.15
  },
  "shap_values": {
    "payment_to_income_ratio": -0.15,
    "credit_score": -0.10
  },
  "top_positive_factors": [
    {
      "feature": "Payment-to-Income Ratio",
      "shap_value": -0.15,
      "feature_value": 0.28,
      "impact": "Reduces default risk"
    }
  ],
  "top_negative_factors": [
    {
      "feature": "Delinquent Accounts",
      "shap_value": 0.05,
      "feature_value": 0,
      "impact": "Increases default risk"
    }
  ],
  "explanation_text": "## Credit Score Explanation\n\n### Overall Assessment..."
}
```

---

## 🔄 WebSocket Service (Port 8006)

### Workflow Updates
```javascript
const ws = new WebSocket('ws://localhost:8006/ws/workflow/<workflow_id>');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Workflow update:', data);
};

// Example message received:
{
  "type": "step_completed",
  "step": 3,
  "step_name": "Credit Bureau Fetch",
  "status": "COMPLETED",
  "progress": 37.5,
  "timestamp": "2024-01-15T10:05:00Z"
}
```

### Application Updates
```javascript
const ws = new WebSocket('ws://localhost:8006/ws/application/<application_id>');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Application update:', data);
};

// Example message:
{
  "type": "document_uploaded",
  "document_id": "doc-123",
  "document_type": "INCOME_STATEMENT",
  "status": "UPLOADED",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

---

## 🚪 API Gateway (Port 8000)

All services can be accessed through the API Gateway:

```
/api/v1/auth/*         → Auth Service (8001)
/api/v1/applications/* → Application Service (8002)
/api/v1/documents/*    → Document Service (8003)
/api/v1/underwriting/* → Underwriting Service (8004)
/api/v1/scoring/*      → Scoring Service (8005)
```

**Rate Limits:**
- 60 requests/minute per IP
- 1000 requests/hour per IP

**Headers:**
```
X-Request-ID: Unique request identifier
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
```

---

## 📋 Error Responses

All errors follow standard format:

```json
{
  "error": "Error description",
  "status_code": 400,
  "request_id": "req_1700000000123"
}
```

**Common Status Codes:**
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `413 Payload Too Large` - File too large (>10MB)
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service down

---

## 🔒 RBAC Roles

- **ADMIN**: Full system access
- **UNDERWRITER**: Review and override decisions
- **RISK_ANALYST**: View analytics and reports
- **OPS**: Operational tasks
- **VIEWER**: Read-only access

---

## 📊 Complete Workflow Example

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@analyticaloan.com&password=admin123"

# 2. Upload documents
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "application_id=<uuid>" \
  -F "document_type=INCOME_STATEMENT" \
  -F "file=@statement.pdf"

# 3. Trigger OCR
curl -X POST http://localhost:8000/api/v1/documents/<doc_id>/ocr \
  -H "Authorization: Bearer <token>"

# 4. Start underwriting
curl -X POST http://localhost:8000/api/v1/underwriting/underwrite \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"application_id": "<uuid>"}'

# 5. Monitor via WebSocket
# Connect to ws://localhost:8006/ws/workflow/<workflow_id>

# 6. Get final decision
curl http://localhost:8000/api/v1/underwriting/applications/<app_id>/decision \
  -H "Authorization: Bearer <token>"

# 7. Get XAI explanation
curl http://localhost:8000/api/v1/scoring/score/<score_id>/explain \
  -H "Authorization: Bearer <token>"
```

---

## 📚 Additional Resources

- **OpenAPI Spec**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`
- **Health Checks**: `/health` on each service
- **Metrics**: Prometheus at `:9090`
- **Tracing**: Jaeger UI at `:16686`
