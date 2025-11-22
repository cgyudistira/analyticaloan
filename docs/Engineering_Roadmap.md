# Engineering Roadmap
## AnalyticaLoan – AI Agent for Credit Underwriting

**Version:** 1.0  
**Date:** 2025-11-22  
**Duration:** 16-20 weeks  

---

## OVERVIEW

This roadmap breaks down the AnalyticaLoan implementation into **7 phases**, each with clear deliverables, dependencies, and success criteria.

**Team Structure (Recommended):**
- 1x Tech Lead / Architect
- 2x Backend Engineers
- 1x ML Engineer
- 1x Frontend Engineer
- 1x DevOps Engineer
- 1x QA Engineer

---

## PHASE 1: FOUNDATION (Weeks 1-2)

### Week 1: Project Bootstrap

#### 1.1 Repository Setup
- [ ] Initialize Git monorepo structure
- [ ] Setup branch protection rules
- [ ] Configure pre-commit hooks (black, flake8, mypy)
- [ ] Create `.gitignore` and `.dockerignore`
- [ ] Setup environment management (Poetry/pipenv)

**Directory Structure:**
```
analyticaloan/
├── services/
│   ├── api-gateway/
│   ├── auth-service/
│   ├── application-service/
│   ├── document-service/
│   ├── underwriting-service/
│   ├── scoring-service/
│   └── decision-service/
├── libs/
│   ├── common/           # Shared utilities
│   ├── database/         # Database models & migrations
│   └── messaging/        # Event bus abstractions
├── ml/
│   ├── models/
│   ├── training/
│   └── inference/
├── infrastructure/
│   ├── terraform/
│   ├── kubernetes/
│   └── docker/
├── docs/
├── tests/
└── scripts/
```

#### 1.2 Technology Stack Installation
- [ ] Python 3.11+
- [ ] PostgreSQL 15
- [ ] Redis 7
- [ ] RabbitMQ / Apache Kafka
- [ ] Docker & Docker Compose
- [ ] Temporal.io (workflow engine)

#### 1.3 Development Environment
- [ ] Docker Compose for local development
- [ ] `.env.example` file with all required variables
- [ ] Makefile for common tasks
- [ ] README.md with setup instructions

**Deliverables:**
- ✅ Working local development environment
- ✅ All developers can run `make dev` and start coding

---

### Week 2: API Gateway & Authentication

#### 2.1 API Gateway (Kong/FastAPI)
- [ ] Install and configure Kong Gateway
- [ ] Setup rate limiting (1000 req/hour per API key)
- [ ] SSL/TLS termination
- [ ] Request/response logging
- [ ] CORS configuration

#### 2.2 Authentication Service
**Tech Stack:** FastAPI + JWT

**Features:**
- [ ] User registration endpoint
- [ ] Login endpoint (email + password)
- [ ] JWT token generation (access + refresh)
- [ ] Token validation middleware
- [ ] Password hashing (bcrypt)
- [ ] Role-Based Access Control (RBAC)

**Code Structure:**
```python
# services/auth-service/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

app = FastAPI()

# RBAC roles
ROLES = {
    "ADMIN": ["*"],
    "UNDERWRITER": ["read:applications", "write:decisions"],
    "RISK_ANALYST": ["read:applications", "read:scores"],
    "OPS": ["read:applications"],
    "VIEWER": ["read:applications"]
}

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    # Verify credentials
    # Generate JWT
    # Return tokens
    pass

@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    # Validate refresh token
    # Issue new access token
    pass

@app.get("/auth/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    # Validate JWT
    # Return user info
    pass
```

#### 2.3 Database Setup
- [ ] Create PostgreSQL database
- [ ] Install Alembic (migration tool)
- [ ] Create initial migration (users table)
- [ ] Seed admin user

**Migration:**
```bash
# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

**Deliverables:**
- ✅ Working authentication API
- ✅ Postman collection for testing
- ✅ Unit tests (≥80% coverage)

---

## PHASE 2: DOCUMENT INTELLIGENCE LAYER (Weeks 3-5)

### Week 3: Document Upload & Storage

#### 3.1 Document Service
**Tech Stack:** FastAPI + AWS S3 / Google Cloud Storage

**Features:**
- [ ] Multipart file upload endpoint
- [ ] File validation (size, type, virus scan)
- [ ] S3 integration with signed URLs
- [ ] Document metadata storage (PostgreSQL)
- [ ] Thumbnail generation for images

**API Endpoints:**
```python
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    application_id: UUID,
    document_type: DocumentType,
    db: Session = Depends(get_db)
):
    # Validate file
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(400, "File too large")
    
    # Upload to S3
    s3_key = f"applications/{application_id}/{file.filename}"
    await s3_client.upload_fileobj(file.file, BUCKET_NAME, s3_key)
    
    # Save metadata
    doc = FinancialDocument(
        application_id=application_id,
        document_type=document_type,
        file_path=s3_key,
        file_size_bytes=file.size,
        mime_type=file.content_type
    )
    db.add(doc)
    db.commit()
    
    return {"document_id": doc.document_id}
```

---

### Week 4: OCR Pipeline

#### 4.1 OCR Service Integration
**Tech Stack:** Google Cloud Vision API + Tesseract (fallback)

**Features:**
- [ ] Text extraction from PDF/images
- [ ] Table detection with LayoutLM
- [ ] Confidence scoring
- [ ] Async processing (RabbitMQ queue)
- [ ] Retry logic for failures

**Worker Architecture:**
```python
# services/document-service/workers/ocr_worker.py
import pika
from google.cloud import vision

def process_ocr_task(document_id: UUID):
    # 1. Fetch document from DB
    doc = db.query(FinancialDocument).get(document_id)
    
    # 2. Download from S3
    file_bytes = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=doc.file_path
    )['Body'].read()
    
    # 3. Call Google Vision API
    vision_client = vision.ImageAnnotatorClient()
    image = vision.Image(content=file_bytes)
    response = vision_client.document_text_detection(image=image)
    
    # 4. Extract text
    extracted_text = response.full_text_annotation.text
    confidence = response.full_text_annotation.pages[0].confidence
    
    # 5. Update database
    doc.ocr_status = "COMPLETED"
    doc.ocr_confidence = confidence * 100
    db.commit()
    
    # 6. Trigger parsing
    publish_message("ocr.completed", {"document_id": str(document_id)})

# Start worker
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='ocr_queue', durable=True)
channel.basic_consume(queue='ocr_queue', on_message_callback=process_ocr_task)
channel.start_consuming()
```

---

### Week 5: Financial Statement Parser

#### 5.1 Parser Implementation
**Tech Stack:** Python + Regex + NLP

**Parsers:**
- [ ] Income Statement Parser (Laporan Laba Rugi)
- [ ] Balance Sheet Parser (Neraca)
- [ ] Cash Flow Parser (Arus Kas)
- [ ] Bank Statement Parser (Multi-bank support)

**Example Parser:**
```python
# libs/common/parsers/income_statement_parser.py
import re
from decimal import Decimal

class IncomeStatementParser:
    def parse(self, text: str) -> dict:
        """
        Extract financial metrics from income statement text
        """
        metrics = {}
        
        # Revenue patterns (Indonesian & English)
        revenue_patterns = [
            r'pendapatan\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
            r'revenue\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
            r'penjualan\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
        ]
        
        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['revenue'] = self._parse_currency(match.group(1))
                break
        
        # Operating expenses
        expense_patterns = [
            r'beban\s+operasional\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
            r'operating\s+expenses?\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
        ]
        
        for pattern in expense_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['operating_expenses'] = self._parse_currency(match.group(1))
                break
        
        # Net income
        profit_patterns = [
            r'laba\s+bersih\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
            r'net\s+income\s*[:\-]?\s*Rp?\s*([\d,\.]+)',
        ]
        
        for pattern in profit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['net_income'] = self._parse_currency(match.group(1))
                break
        
        # Calculate derived metrics
        if 'revenue' in metrics and 'operating_expenses' in metrics:
            metrics['ebitda'] = metrics['revenue'] - metrics['operating_expenses']
        
        return metrics
    
    def _parse_currency(self, value: str) -> Decimal:
        """Convert string currency to Decimal"""
        # Remove commas and convert to Decimal
        cleaned = value.replace(',', '').replace('.', '')
        return Decimal(cleaned)
```

**Deliverables:**
- ✅ OCR pipeline processing documents
- ✅ Parsers extracting key financial metrics
- ✅ 95%+ accuracy on standard formats
- ✅ Integration tests with sample documents

---

## PHASE 3: AI AGENT & RAG ENGINE (Weeks 6-9)

### Week 6: Workflow Orchestration

#### 6.1 Temporal.io Setup
- [ ] Install Temporal server
- [ ] Create underwriting workflow
- [ ] Setup activity definitions
- [ ] Implement state persistence
- [ ] Add error handling & retries

**Workflow Definition:**
```python
# services/underwriting-service/workflows/underwriting_workflow.py
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

@workflow.defn
class UnderwritingWorkflow:
    @workflow.run
    async def run(self, application_id: str) -> dict:
        # Step 1: Validate documents
        await workflow.execute_activity(
            validate_documents,
            application_id,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 2: Parallel processing
        ocr_task = workflow.execute_activity(ocr_processing, application_id)
        bureau_task = workflow.execute_activity(credit_bureau_check, application_id)
        blacklist_task = workflow.execute_activity(blacklist_check, application_id)
        
        ocr_result, bureau_result, blacklist_result = await asyncio.gather(
            ocr_task, bureau_task, blacklist_task
        )
        
        # Step 3: Feature engineering
        features = await workflow.execute_activity(
            feature_engineering,
            {
                'ocr': ocr_result,
                'bureau': bureau_result,
                'blacklist': blacklist_result
            }
        )
        
        # Step 4: Scoring
        ml_score = await workflow.execute_activity(ml_scoring, features)
        llm_score = await workflow.execute_activity(llm_reasoning, features)
        rule_score = await workflow.execute_activity(rule_evaluation, features)
        
        # Step 5: Decision
        decision = await workflow.execute_activity(
            decision_fusion,
            {
                'ml': ml_score,
                'llm': llm_score,
                'rules': rule_score
            }
        )
        
        # Step 6: Generate memo
        if decision['status'] != 'REJECT':
            memo = await workflow.execute_activity(generate_credit_memo, decision)
        
        return decision
```

---

### Week 7-8: RAG Engine Implementation

#### 7.1 Vector Database Setup
**Tech Stack:** Weaviate or Pinecone

**Features:**
- [ ] Weaviate cluster setup
- [ ] Schema definition for policy documents
- [ ] Document chunking strategy (512 tokens, 50 overlap)
- [ ] Embedding generation (Gemini text-embedding-004)
- [ ] Semantic search implementation

**Code:**
```python
# services/rag-service/app/indexer.py
import weaviate
from google.generativeai import embed_content

class PolicyIndexer:
    def __init__(self):
        self.client = weaviate.Client("http://localhost:8080")
        
        # Create schema
        schema = {
            "class": "PolicyDocument",
            "vectorizer": "none",  # Manual embedding
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "source", "dataType": ["string"]},
                {"name": "document_type", "dataType": ["string"]},
                {"name": "page_number", "dataType": ["int"]},
                {"name": "version", "dataType": ["string"]},
            ]
        }
        self.client.schema.create_class(schema)
    
    async def index_document(self, file_path: str, document_type: str):
        # 1. Load document
        text = self._load_pdf(file_path)
        
        # 2. Chunk document
        chunks = self._chunk_text(text, chunk_size=512, overlap=50)
        
        # 3. Generate embeddings
        for i, chunk in enumerate(chunks):
            embedding = await self._generate_embedding(chunk)
            
            # 4. Store in Weaviate
            self.client.data_object.create(
                data_object={
                    "content": chunk,
                    "source": file_path,
                    "document_type": document_type,
                    "page_number": i // 2,  # Approximate page
                },
                class_name="PolicyDocument",
                vector=embedding
            )
    
    async def _generate_embedding(self, text: str) -> list:
        result = embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
```

#### 7.2 RAG Query Service
```python
# services/rag-service/app/query.py
class RAGQueryService:
    async def query(self, question: str, top_k: int = 5) -> dict:
        # 1. Generate query embedding
        query_embedding = await self._generate_embedding(question)
        
        # 2. Search Weaviate
        results = self.client.query.get(
            "PolicyDocument",
            ["content", "source", "page_number"]
        ).with_near_vector({
            "vector": query_embedding
        }).with_limit(top_k).do()
        
        # 3. Format context
        context_parts = []
        sources = []
        for r in results['data']['Get']['PolicyDocument']:
            context_parts.append(r['content'])
            sources.append({
                'source': r['source'],
                'page': r['page_number']
            })
        
        context = "\n\n".join(context_parts)
        
        # 4. Generate answer with Gemini
        prompt = f"""
        Jawab pertanyaan berikut berdasarkan konteks kebijakan lending.
        
        Konteks:
        {context}
        
        Pertanyaan: {question}
        
        Jawaban harus:
        - Langsung menjawab pertanyaan
        - Menyebutkan sumber regulasi (POJK/Pasal)
        - Dalam bahasa Indonesia
        - Akurat dan compliance-oriented
        """
        
        response = await gemini_pro.generate_content(
            prompt,
            generation_config={'temperature': 0.0}
        )
        
        return {
            'answer': response.text,
            'sources': sources
        }
```

---

### Week 9: Rule Engine

#### 9.1 Open Policy Agent (OPA) Setup
**Tech Stack:** OPA with Rego DSL

**Features:**
- [ ] OPA server deployment
- [ ] Policy definitions in Rego
- [ ] REST API integration
- [ ] Policy testing framework

**Example Policy:**
```rego
# policies/credit_policies.rego
package credit.underwriting

import future.keywords.if

# Maximum Loan-to-Value (LTV) ratio for mortgages
default max_ltv_ratio = 80

# Minimum credit score for auto-approval
default min_auto_approve_score = 700

# Deny if applicant is blacklisted
deny[msg] if {
    input.applicant.nik in data.blacklist
    msg := "Applicant is blacklisted"
}

# Deny if age < 21 or > 65
deny[msg] if {
    input.applicant.age < 21
    msg := "Applicant too young (minimum age: 21)"
}

deny[msg] if {
    input.applicant.age > 65
    msg := "Applicant exceeds maximum age (65)"
}

# Deny if debt-to-income ratio > 40%
deny[msg] if {
    dti := (input.existing_debt + input.requested_loan_payment) / input.monthly_income
    dti > 0.4
    msg := sprintf("Debt-to-income ratio too high: %.2f%% (max: 40%%)", [dti * 100])
}

# POJK 33/2018 compliance: Maximum concentration per sector
deny[msg] if {
    input.business_sector == "REAL_ESTATE"
    input.loan_amount > 5000000000  # IDR 5 billion
    msg := "Loan amount exceeds sector concentration limit for real estate"
}

# Auto-approve if all conditions met
auto_approve if {
    count(deny) == 0
    input.credit_score >= min_auto_approve_score
    input.ltv_ratio <= max_ltv_ratio
}

# Manual review if borderline
manual_review if {
    count(deny) == 0
    input.credit_score >= 500
    input.credit_score < min_auto_approve_score
}

# Reject otherwise
reject if {
    count(deny) > 0
}
```

**Integration:**
```python
# services/decision-service/app/rule_engine.py
import httpx

class RuleEngine:
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
    
    async def evaluate(self, application_data: dict) -> dict:
        # Call OPA API
        response = await httpx.post(
            f"{self.opa_url}/v1/data/credit/underwriting",
            json={"input": application_data}
        )
        
        result = response.json()['result']
        
        return {
            'pass': result.get('auto_approve', False),
            'manual_review': result.get('manual_review', False),
            'reject': result.get('reject', False),
            'violations': result.get('deny', [])
        }
```

**Deliverables:**
- ✅ Temporal workflow executing end-to-end
- ✅ RAG engine answering policy questions
- ✅ OPA rule engine enforcing policies
- ✅ Integration tests

---

## PHASE 4: SCORING & DECISION ENGINE (Weeks 10-12)

### Week 10: ML Model Development

#### 10.1 Data Preparation
- [ ] Extract historical loan data
- [ ] Feature engineering pipeline
- [ ] Train/validation/test split (70/15/15)
- [ ] Handle class imbalance (SMOTE)

#### 10.2 Baseline Model
**Model:** Logistic Regression

```python
# ml/training/train_baseline.py
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report

def train_baseline_model():
    # Load data
    X_train, y_train = load_training_data()
    X_test, y_test = load_test_data()
    
    # Train logistic regression
    model = LogisticRegression(
        penalty='l2',
        C=1.0,
        class_weight='balanced',
        max_iter=1000
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"Baseline AUC: {auc:.4f}")
    
    return model
```

---

### Week 11: Advanced ML Models

#### 11.1 XGBoost Training
```python
# ml/training/train_xgboost.py
import xgboost as xgb
import mlflow

def train_xgboost_model():
    # Start MLflow run
    with mlflow.start_run():
        # Load data
        X_train, y_train = load_training_data()
        X_test, y_test = load_test_data()
        
        # Define model
        params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 200,
            'objective': 'binary:logistic',
            'scale_pos_weight': sum(y_train==0)/sum(y_train==1),
            'colsample_bytree': 0.8,
            'subsample': 0.8,
            'eval_metric': 'auc'
        }
        
        model = xgb.XGBClassifier(**params)
        
        # Train with early stopping
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=20,
            verbose=10
        )
        
        # Evaluate
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred_proba)
        
        # Log to MLflow
        mlflow.log_params(params)
        mlflow.log_metric("auc", auc)
        mlflow.xgboost.log_model(model, "xgboost_model")
        
        print(f"XGBoost AUC: {auc:.4f}")
        
        return model
```

#### 11.2 Feature Importance
```python
import shap
import matplotlib.pyplot as plt

def explain_model(model, X_test):
    # SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # Plot summary
    shap.summary_plot(shap_values, X_test, show=False)
    plt.savefig('feature_importance.png')
    
    return shap_values
```

---

### Week 12: Decision Fusion & XAI

#### 12.1 Decision Fusion Implementation
See Section 2.5 in System Architecture document.

#### 12.2 XAI Explanation Generator
```python
# services/decision-service/app/xai.py
class XAIExplainer:
    def generate_explanation(
        self,
        features: dict,
        ml_score: float,
        shap_values: np.ndarray
    ) -> str:
        """
        Generate human-readable explanation
        """
        # Get top 5 contributing features
        feature_names = list(features.keys())
        top_indices = np.argsort(np.abs(shap_values))[-5:][::-1]
        
        explanation_parts = [
            f"Credit Score: {int(ml_score * 1000)}",
            "",
            "Top Contributing Factors:"
        ]
        
        for idx in top_indices:
            feature = feature_names[idx]
            value = features[feature]
            impact = "positive" if shap_values[idx] > 0 else "negative"
            
            explanation_parts.append(
                f"• {feature}: {value} ({impact} impact)"
            )
        
        return "\n".join(explanation_parts)
```

**Deliverables:**
- ✅ Trained ML models (AUC ≥ 0.80)
- ✅ MLflow model registry setup
- ✅ Decision fusion algorithm
- ✅ XAI explanation generator
- ✅ Model monitoring dashboard

---

## PHASE 5: FRONTEND & DASHBOARD (Weeks 13-14)

### Week 13: Underwriter Dashboard

#### 13.1 Tech Stack
- **Frontend:** Next.js 14 + TypeScript
- **UI Library:** shadcn/ui + Tailwind CSS
- **State Management:** Zustand
- **API Client:** TanStack Query (React Query)

#### 13.2 Key Screens
**1. Application Queue**
```tsx
// app/applications/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { ApplicationTable } from '@/components/ApplicationTable';

export default function ApplicationsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['applications', { status: 'MANUAL_REVIEW' }],
    queryFn: () => fetch('/api/applications?status=MANUAL_REVIEW').then(r => r.json())
  });
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Underwriting Queue</h1>
      <ApplicationTable applications={data.data} />
    </div>
  );
}
```

**2. Application Detail View**
- Applicant information
- Uploaded documents (with viewer)
- Credit score & risk rating
- XAI explanation
- Approve/Reject buttons

**3. Credit Memo Viewer**
- PDF rendering with annotations
- Download functionality

---

### Week 14: Admin Console & Monitoring

#### 14.1 Admin Console Features
- [ ] User management (CRUD)
- [ ] Policy document upload
- [ ] Model deployment controls
- [ ] System configuration

#### 14.2 Grafana Dashboards
**Dashboard 1: Underwriting Metrics**
- Applications per day
- Approval rate
- Average processing time
- Manual review queue size

**Dashboard 2: Model Performance**
- Model accuracy over time
- Prediction distribution
- Feature drift detection
- Error rates

**Dashboard 3: System Health**
- API latency (P50, P95, P99)
- Request rate
- Error rate
- Database connection pool

**Deliverables:**
- ✅ Fully functional web dashboard
- ✅ Mobile-responsive design
- ✅ Real-time updates via WebSocket
- ✅ Grafana monitoring dashboards

---

## PHASE 6: SECURITY & COMPLIANCE (Week 15)

### 6.1 Security Hardening
- [ ] Implement AES-256 encryption for PII
- [ ] TLS 1.3 for all communications
- [ ] API rate limiting (Kong)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (Content Security Policy)
- [ ] CSRF tokens for state-changing operations

### 6.2 Audit Logging
- [ ] Centralized logging (ELK Stack)
- [ ] Log encryption
- [ ] Tamper-proof audit trail
- [ ] Log retention policy (7 years)

### 6.3 POJK Compliance Mapping
**Checklist:**
- [ ] POJK 33/2018 - Credit risk governance ✓
- [ ] POJK 1/2024 - Digital service security ✓
- [ ] POJK 29/2024 - IT risk management ✓
- [ ] Data retention policy implemented
- [ ] Explainable AI documentation

### 6.4 Penetration Testing
**Scope:**
- [ ] OWASP Top 10 vulnerabilities
- [ ] Authentication bypass attempts
- [ ] Authorization flaws
- [ ] Data leakage
- [ ] API security

**Deliverables:**
- ✅ Security audit report
- ✅ Penetration test results
- ✅ Compliance certification
- ✅ Incident response playbook

---

## PHASE 7: DEPLOYMENT & OBSERVABILITY (Week 16)

### 7.1 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=app tests/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t analyticaloan-api:${{ github.sha }} .
      
      - name: Push to GCR
        run: |
          docker tag analyticaloan-api:${{ github.sha }} gcr.io/PROJECT_ID/analyticaloan-api:${{ github.sha }}
          docker push gcr.io/PROJECT_ID/analyticaloan-api:${{ github.sha }}
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GKE
        run: |
          kubectl set image deployment/analyticaloan-api \
            analyticaloan-api=gcr.io/PROJECT_ID/analyticaloan-api:${{ github.sha }}
          kubectl rollout status deployment/analyticaloan-api
```

### 7.2 Kubernetes Deployment

```yaml
# infrastructure/kubernetes/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analyticaloan-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analyticaloan-api
  template:
    metadata:
      labels:
        app: analyticaloan-api
    spec:
      containers:
      - name: api
        image: gcr.io/PROJECT_ID/analyticaloan-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: analyticaloan-api-service
spec:
  type: LoadBalancer
  selector:
    app: analyticaloan-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: analyticaloan-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: analyticaloan-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 7.3 Observability Stack

**Prometheus + Grafana + Jaeger + ELK**

```yaml
# infrastructure/kubernetes/monitoring-stack.yaml
# (Prometheus, Grafana, Jaeger configurations)
```

### 7.4 Canary Deployment
- [ ] Deploy to 10% of traffic
- [ ] Monitor error rates & latency
- [ ] Rollback if metrics degrade
- [ ] Gradually increase to 100%

**Deliverables:**
- ✅ Production deployment on GKE/EKS
- ✅ CI/CD pipeline fully automated
- ✅ Monitoring & alerting configured
- ✅ Disaster recovery tested
- ✅ Documentation complete

---

## SUCCESS CRITERIA

### Phase 1-2
- [ ] All developers can run system locally
- [ ] Authentication working with JWT
- [ ] Documents uploading to S3
- [ ] OCR extracting text with ≥95% accuracy

### Phase 3-4
- [ ] Temporal workflow executing end-to-end
- [ ] RAG answering questions correctly
- [ ] ML model achieving AUC ≥ 0.80
- [ ] Decision fusion producing consistent results

### Phase 5-6
- [ ] Dashboard accessible to underwriters
- [ ] All POJK compliance checks passing
- [ ] Security audit completed
- [ ] Zero critical vulnerabilities

### Phase 7
- [ ] Production deployment successful
- [ ] SLA of 99.9% achieved
- [ ] API latency P95 < 2 seconds
- [ ] Zero data breaches

---

## RISK MITIGATION

| Risk | Mitigation |
|------|------------|
| LLM API downtime | Implement circuit breaker + fallback to rules-only mode |
| Database bottleneck | Setup read replicas + caching layer (Redis) |
| Team dependency | Cross-train developers on multiple services |
| Scope creep | Strict change control process + weekly reviews |
| Regulatory changes | Monthly compliance review + flexible policy engine |

---

**END OF ROADMAP**

*For detailed technical specs, see System Architecture document.*
