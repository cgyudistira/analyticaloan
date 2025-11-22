# Underwriting Service

AI-powered credit underwriting orchestration service.

## Features

- **AI Agent Orchestration**: 8-step automated underwriting workflow
- **Gemini Integration**: 
  - Flash Thinking for credit analysis (temperature=0.0)
  - Pro for credit memo generation (temperature=0.7)
- **RAG Policy Engine**: Semantic search for POJK compliance
- **Decision Fusion**: ML + LLM + Rules weighted voting
- **Human-in-the-Loop**: Manual review for borderline cases

## Workflow Steps

1. **Document Validation** - Check required documents uploaded
2. **Data Extraction** - Parse OCR results from documents
3. **Credit Bureau** - Fetch SLIK OJK data
4. **ML Scoring** - Calculate probability of default
5. **LLM Reasoning** - Gemini Flash analysis
6. **Policy Compliance** - RAG engine POJK check
7. **Decision Fusion** - Combine all signals
8. **Credit Memo** - Generate formal memorandum

## Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Setup Gemini API key
export GEMINI_API_KEY=your-api-key-here

# Run the service
uvicorn app.main:app --reload --port 8004
```

## API Endpoints

### Start Underwriting
```bash
curl -X POST http://localhost:8004/underwrite \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "<uuid>",
    "auto_approve_threshold": 0.7,
    "auto_reject_threshold": 0.4
  }'
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
```bash
curl http://localhost:8004/underwrite/<workflow_id>/status
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
```bash
curl http://localhost:8004/applications/<application_id>/decision
```

### Manual Override
```bash
curl -X POST http://localhost:8004/applications/<application_id>/override \
  -d "new_decision=APPROVE&override_reason=Collateral verified"
```

## Decision Logic

```
IF policy_violations:
    REJECT
ELSE IF ml_score >= 0.7:
    APPROVE
ELSE IF ml_score < 0.4:
    REJECT
ELSE:
    MANUAL_REVIEW
```

## RAG Engine Usage

```python
from app.rag_engine import RAGPolicyEngine

rag = RAGPolicyEngine()

# Index policy document
await rag.index_policy(
    title="POJK 33/2018 - Credit Risk Management",
    content="Full regulation text...",
    policy_type="POJK",
    regulation_number="POJK 33/2018"
)

# Query policies
results = await rag.query_policies(
    query="What are age limits for borrowers?",
    limit=3
)

# Check compliance
compliance = await rag.check_compliance({
    "loan_amount": 100000000,
    "age": 45,
    "loan_term_months": 24,
    "dti_ratio": 0.35
})
```

## Gemini Prompts

The service uses carefully crafted prompts for:

1. **Credit Analysis** (Flash Thinking):
   - DSCR calculation
   - Repayment capacity assessment
   - Financial health analysis
   - Risk factor identification
   - Recommendation with confidence level

2. **Credit Memo** (Pro):
   - Executive summary
   - Borrower profile
   - Loan request details
   - Financial analysis
   - Risk assessment
   - Approval requirements

## Configuration

Environment variables:

```
GEMINI_API_KEY=your-gemini-api-key
GEMINI_FLASH_MODEL=gemini-2.0-flash-thinking-exp
GEMINI_PRO_MODEL=gemini-2.0-flash-exp
WEAVIATE_URL=http://localhost:8080
```

## Monitoring

- Workflow progress tracked in `workflow_state` table
- Decisions logged in `decision_logs` with full reasoning
- All API calls audited in `audit_trail`
