# System Architecture Design
## AnalyticaLoan – AI Agent for Credit Underwriting

**Version:** 1.0  
**Date:** 2025-11-22  
**Author:** AI/ML Engineering Team

---

## 1. HIGH-LEVEL ARCHITECTURE (HLA)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Mobile App   │  │  Web Portal  │  │  Dashboard   │  │ Admin Panel  │   │
│  │  (React)     │  │  (Next.js)   │  │  (Grafana)   │  │  (React)     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼──────────────────┼──────────────────┼──────────────────┼──────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                      │
                   ┌──────────────────┴──────────────────┐
                   │         API GATEWAY (Kong)          │
                   │  • Rate Limiting                    │
                   │  • SSL/TLS Termination              │
                   │  • Request Routing                  │
                   │  • Load Balancing                   │
                   └──────────────────┬──────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
┌─────────▼─────────┐      ┌──────────▼──────────┐    ┌──────────▼─────────┐
│  AUTH SERVICE     │      │  LOAN APPLICATION   │    │  DOCUMENT SERVICE  │
│  • OAuth 2.0      │◄─────┤  SERVICE            │───►│  • Upload/Download │
│  • JWT Tokens     │      │  • Create           │    │  • Storage (S3)    │
│  • RBAC           │      │  • Retrieve         │    │  • Versioning      │
│  • Session Mgmt   │      │  • Update Status    │    └──────────┬─────────┘
└─────────┬─────────┘      └──────────┬──────────┘               │
          │                           │                           │
          │         ┌─────────────────┴───────────────────────────┘
          │         │
          │  ┌──────▼────────────────────────────────────────────────────┐
          │  │     AI UNDERWRITING AGENT ORCHESTRATOR (Core Engine)     │
          │  │  • State Machine (Temporal.io / Apache Airflow)          │
          │  │  • Workflow DAG Execution                                │
          │  │  • Agent Coordination                                    │
          │  │  • Error Recovery & Retry Logic                          │
          │  └──────┬────────────┬──────────────┬───────────────────────┘
          │         │            │              │
          │         │            │              │
    ┌─────▼─────────▼┐  ┌───────▼──────────┐  ┌▼────────────────────────┐
    │ DOCUMENT       │  │  RAG POLICY      │  │  RULE ENGINE            │
    │ INTELLIGENCE   │  │  ENGINE          │  │  (Open Policy Agent)    │
    │ ┌────────────┐ │  │ ┌──────────────┐ │  │  • Deterministic Rules  │
    │ │ OCR        │ │  │ │ Vector DB    │ │  │  • POJK Compliance      │
    │ │ (Google    │ │  │ │ (Weaviate)   │ │  │  • Business Policies    │
    │ │  Vision)   │ │  │ │              │ │  │  • Rego DSL             │
    │ └────────────┘ │  │ └──────────────┘ │  └─────────────────────────┘
    │ ┌────────────┐ │  │ ┌──────────────┐ │
    │ │ LayoutLM   │ │  │ │ Embeddings   │ │
    │ │ (Table     │ │  │ │ (Gemini)     │ │
    │ │  Extract)  │ │  │ │              │ │
    │ └────────────┘ │  │ └──────────────┘ │
    │ ┌────────────┐ │  │ ┌──────────────┐ │
    │ │ Bank Stmt  │ │  │ │ Semantic     │ │
    │ │ Parser     │ │  │ │ Search       │ │
    │ └────────────┘ │  │ └──────────────┘ │
    └────────┬───────┘  └─────────┬────────┘
             │                    │
             │      ┌─────────────┴────────────────┐
             │      │                              │
      ┌──────▼──────▼──────────┐        ┌─────────▼─────────────┐
      │  CREDIT SCORING        │        │  LLM SERVICE          │
      │  ENGINE                │        │  (Gemini API)         │
      │  ┌──────────────────┐  │        │  ┌─────────────────┐  │
      │  │ ML Models        │  │        │  │ Flash Thinking  │  │
      │  │ • Logistic Reg   │  │        │  │ (Reasoning)     │  │
      │  │ • XGBoost        │  │        │  └─────────────────┘  │
      │  │ • LightGBM       │  │        │  ┌─────────────────┐  │
      │  └──────────────────┘  │        │  │ Pro (Content    │  │
      │  ┌──────────────────┐  │        │  │  Generation)    │  │
      │  │ Feature Eng      │  │        │  └─────────────────┘  │
      │  │ • Credit Bureau  │  │        │  • Temperature: 0.0  │
      │  │ • Demographics   │  │        │  • Function Calling  │
      │  │ • Financials     │  │        └──────────────────────┘
      │  └──────────────────┘  │
      │  ┌──────────────────┐  │
      │  │ MLflow Registry  │  │
      │  └──────────────────┘  │
      └──────────┬─────────────┘
                 │
          ┌──────▼───────────────────────────────────┐
          │      DECISION ENGINE                     │
          │  • Weighted Fusion Algorithm             │
          │    - ML Score (40%)                      │
          │    - LLM Reasoning (30%)                 │
          │    - Rule Compliance (30%)               │
          │  • Risk Rating (AAA to D)                │
          │  • XAI Explanation Generator (SHAP)     │
          │  • Credit Memo Generator                 │
          └──────────┬───────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼──────┐  ┌───▼────────┐  ┌──▼──────────────┐
│ AUDIT LOG  │  │ POSTGRES   │  │ EXTERNAL APIs   │
│ (Immutable)│  │ (Primary   │  │ • SLIK OJK      │
│ • ELK      │  │  DB)       │  │ • Core Banking  │
│ • S3       │  │            │  │ • Email/SMS     │
└────────────┘  └────────────┘  └─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              OBSERVABILITY & MONITORING LAYER                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Prometheus   │  │ Grafana      │  │ Jaeger       │      │
│  │ (Metrics)    │  │ (Dashboards) │  │ (Tracing)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. SUBSYSTEM DESIGN

### 2.1 AI Agent Orchestrator

**Purpose:** Central brain coordinating all underwriting activities

**Technology Stack:**
- **Workflow Engine:** Temporal.io (preferred) or Apache Airflow
- **State Store:** Redis (for fast state access)
- **Message Queue:** RabbitMQ or Apache Kafka

**Workflow Steps:**

```
START
  │
  ├─► [1] Document Validation
  │     ├─ Check file format
  │     ├─ Virus scan
  │     └─ Metadata extraction
  │
  ├─► [2] Parallel Processing Branch
  │     ├─► [2a] OCR & Document Parsing
  │     │     ├─ Extract financial statements
  │     │     ├─ Parse bank statements
  │     │     └─ Extract applicant info
  │     │
  │     ├─► [2b] Credit Bureau Check
  │     │     └─ Fetch SLIK OJK data
  │     │
  │     └─► [2c] Blacklist Verification
  │           └─ Check NIK/NPWP
  │
  ├─► [3] Data Aggregation & Feature Engineering
  │     ├─ Normalize extracted data
  │     ├─ Calculate financial ratios
  │     └─ Prepare ML features
  │
  ├─► [4] Scoring & Reasoning (Parallel)
  │     ├─► [4a] ML Scoring
  │     │     ├─ Probability of Default (PD)
  │     │     └─ Credit Score (0-1000)
  │     │
  │     ├─► [4b] LLM Reasoning
  │     │     ├─ Gemini Flash Thinking
  │     │     └─ Contextual analysis
  │     │
  │     └─► [4c] Rule Evaluation
  │           ├─ OPA policy check
  │           └─ POJK compliance
  │
  ├─► [5] Decision Fusion
  │     ├─ Weighted voting
  │     ├─ Risk rating assignment
  │     └─ XAI explanation
  │
  ├─► [6] Human-in-the-Loop Check
  │     ├─ IF borderline THEN manual_queue
  │     ├─ IF fraud_flag THEN escalate
  │     └─ IF high_value THEN committee_review
  │
  ├─► [7] Credit Memo Generation
  │     ├─ Gemini Pro (content generation)
  │     └─ PDF rendering
  │
  └─► [8] Finalize Decision
        ├─ Update database
        ├─ Send notifications
        └─ Archive to audit log
  │
END
```

**Pseudocode:**

```python
async def underwriting_workflow(application_id: str):
    """
    Main underwriting workflow orchestrated by Temporal
    """
    # Initialize workflow state
    state = await initialize_workflow_state(application_id)
    
    try:
        # Step 1: Document Validation
        docs = await activity_validate_documents(application_id)
        state.update(step=1, status="completed", data=docs)
        
        # Step 2: Parallel processing
        results = await asyncio.gather(
            activity_ocr_parsing(docs),
            activity_credit_bureau_check(application_id),
            activity_blacklist_verification(application_id)
        )
        ocr_data, bureau_data, blacklist_result = results
        state.update(step=2, ocr=ocr_data, bureau=bureau_data, blacklist=blacklist_result)
        
        # Step 3: Feature engineering
        features = await activity_feature_engineering(state.data)
        state.update(step=3, features=features)
        
        # Step 4: Scoring & Reasoning (parallel)
        scores = await asyncio.gather(
            activity_ml_scoring(features),
            activity_llm_reasoning(state.data, features),
            activity_rule_evaluation(state.data, features)
        )
        ml_score, llm_reasoning, rule_result = scores
        state.update(step=4, ml=ml_score, llm=llm_reasoning, rules=rule_result)
        
        # Step 5: Decision fusion
        decision = await activity_decision_fusion(ml_score, llm_reasoning, rule_result)
        state.update(step=5, decision=decision)
        
        # Step 6: HITL check
        if decision.requires_manual_review:
            await send_to_manual_queue(application_id, decision)
            return state  # Wait for human decision
        
        # Step 7: Generate credit memo
        memo = await activity_generate_credit_memo(state.data, decision)
        state.update(step=7, memo=memo)
        
        # Step 8: Finalize
        await activity_finalize_decision(application_id, decision, memo)
        state.update(step=8, status="completed")
        
        return state
        
    except Exception as e:
        await handle_workflow_error(application_id, state, e)
        raise
```

---

### 2.2 Document Intelligence Layer

**Components:**

#### 2.2.1 OCR Service

**Technology:**
- **Primary:** Google Cloud Vision API (high accuracy)
- **Fallback:** Tesseract OCR (cost-effective for clear scans)

**Capabilities:**
- Text extraction from PDF/JPG/PNG
- Handwriting recognition
- Table detection
- Form field extraction

**API Interface:**

```python
class OCRService:
    async def extract_text(
        self, 
        document: bytes, 
        mime_type: str
    ) -> OCRResult:
        """
        Extract text from document
        
        Returns:
            OCRResult with text, confidence, bounding boxes
        """
        pass
    
    async def extract_tables(
        self, 
        document: bytes
    ) -> List[Table]:
        """
        Extract tables using LayoutLM
        """
        pass
```

#### 2.2.2 Financial Statement Parser

**Handles:**
- **Laporan Laba Rugi (Income Statement)**
  - Pendapatan (Revenue)
  - Beban Operasional (Operating Expenses)
  - Laba Bersih (Net Income)
  - EBITDA

- **Neraca (Balance Sheet)**
  - Aset Lancar (Current Assets)
  - Aset Tetap (Fixed Assets)
  - Liabilitas (Liabilities)
  - Ekuitas (Equity)

- **Laporan Arus Kas (Cash Flow Statement)**
  - Arus Kas Operasi (Operating CF)
  - Arus Kas Investasi (Investing CF)
  - Arus Kas Pendanaan (Financing CF)

**Output Format:**

```json
{
  "income_statement": {
    "revenue": 1500000000,
    "operating_expenses": 800000000,
    "net_income": 450000000,
    "ebitda": 600000000,
    "currency": "IDR",
    "period": "2024-Q3"
  },
  "balance_sheet": {
    "current_assets": 2000000000,
    "fixed_assets": 5000000000,
    "total_assets": 7000000000,
    "current_liabilities": 1500000000,
    "long_term_liabilities": 2500000000,
    "equity": 3000000000
  },
  "ratios": {
    "current_ratio": 1.33,
    "debt_to_equity": 1.33,
    "roe": 0.15,
    "roa": 0.064
  }
}
```

#### 2.2.3 Bank Statement Parser

**Supported Banks:**
- BCA, Mandiri, BNI, BRI, CIMB Niaga, Permata, Danamon, etc.

**Extracted Metrics:**
- Monthly average balance (6 months)
- Salary/income patterns
- Recurring expenses
- Large irregular transactions
- Gambling/risky transactions
- Cash flow volatility (std dev)

---

### 2.3 Risk Modelling Layer

#### 2.3.1 ML Models

**Model 1: Logistic Regression (Baseline)**
- Simple, interpretable
- Fast inference
- Used for A/B testing baseline

**Model 2: XGBoost (Primary)**
- High accuracy
- Feature importance
- Handles missing values

**Model 3: LightGBM (Alternative)**
- Faster training
- Lower memory footprint

**Features (50+ variables):**

| Category | Features |
|----------|----------|
| Demographics | Age, Gender, Marital Status, Education, Occupation |
| Credit Bureau | Payment history, Number of accounts, Credit utilization |
| Financials | Revenue, Profit margin, Debt ratio, Cash flow |
| Behavioral | Application channel, Time of day, Device type |
| Bank Statement | Avg balance, Income stability, Expense patterns |

**Training Pipeline:**

```python
# Pseudocode
def train_credit_scoring_model():
    # 1. Load data
    df = load_training_data()  # Historical loans
    
    # 2. Feature engineering
    features = engineer_features(df)
    
    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, df['default_flag'], 
        test_size=0.2, stratify=df['default_flag']
    )
    
    # 4. Train XGBoost
    model = xgb.XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=200,
        objective='binary:logistic',
        scale_pos_weight=sum(y_train==0)/sum(y_train==1)  # Handle imbalance
    )
    model.fit(X_train, y_train)
    
    # 5. Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"AUC: {auc_score}")
    
    # 6. Register to MLflow
    mlflow.sklearn.log_model(model, "xgb_credit_model")
    
    return model
```

#### 2.3.2 Decision Thresholds

| Score Range | Risk Rating | Decision | PD Range |
|-------------|-------------|----------|----------|
| 800-1000 | AAA | Auto-Approve | 0-2% |
| 700-799 | AA | Auto-Approve | 2-5% |
| 600-699 | A | Approve with Conditions | 5-10% |
| 500-599 | BBB | Manual Review | 10-15% |
| 400-499 | BB | Manual Review | 15-25% |
| 300-399 | B | High Risk - Reject | 25-40% |
| 0-299 | C/D | Auto-Reject | >40% |

---

### 2.4 Underwriting Policy RAG Engine

**Architecture:**

```
┌──────────────────────────────────────────┐
│         Policy Documents (Sources)        │
│  • POJK Regulations (PDF)                │
│  • Internal SOP (Docx)                   │
│  • Lending Guidelines (Markdown)         │
│  • Historical Memos (PDF)                │
└────────────────┬─────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Document Chunker│
        │ • Chunk size: 512│
        │ • Overlap: 50   │
        └────────┬────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Embedding Generator │
        │ (Gemini Embeddings) │
        │ • Model: text-      │
        │   embedding-004     │
        │ • Dimensions: 768   │
        └────────┬────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │   Vector Database    │
        │   (Weaviate)         │
        │ • HNSW Index         │
        │ • Cosine Similarity  │
        └────────┬─────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Retrieval at Query Time   │
    │  • Top-K = 5               │
    │  • Re-ranking (optional)   │
    └────────────┬───────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  LLM Augmented  │
        │  Generation     │
        │  (Gemini Pro)   │
        └────────────────┘
```

**Sample Query:**

```python
async def query_policy_rag(question: str) -> str:
    """
    Query RAG engine for policy compliance
    
    Example:
        question = "Berapa maksimum LTV untuk KPR sesuai POJK?"
        
    Returns:
        Contextualized answer with citations
    """
    # 1. Generate embedding for question
    query_embedding = await gemini_embed(question)
    
    # 2. Search vector DB
    results = await weaviate_client.query(
        class_name="PolicyDocument",
        vector=query_embedding,
        limit=5
    )
    
    # 3. Format context
    context = "\n\n".join([r.text for r in results])
    
    # 4. Generate answer with LLM
    prompt = f"""
    Jawab pertanyaan berikut berdasarkan konteks kebijakan.
    
    Konteks:
    {context}
    
    Pertanyaan: {question}
    
    Jawaban harus menyertakan:
    - Jawaban langsung
    - Dasar regulasi (POJK X/Tahun/Pasal Y)
    - Penjelasan singkat
    """
    
    response = await gemini_pro.generate(prompt, temperature=0.0)
    
    return response
```

---

### 2.5 Decision Layer

**Decision Fusion Algorithm:**

```python
def decision_fusion(
    ml_score: float,        # 0.0 - 1.0
    llm_reasoning: dict,    # Contains score, explanation
    rule_result: dict       # Contains pass/fail, violations
) -> Decision:
    """
    Weighted fusion of ML, LLM, and Rules
    
    Weights:
    - ML Score: 40%
    - LLM Reasoning: 30%
    - Rule Compliance: 30%
    """
    
    # Normalize scores to 0-1
    ml_normalized = ml_score
    llm_normalized = llm_reasoning['score'] / 100  # Assuming 0-100 scale
    rule_normalized = 1.0 if rule_result['pass'] else 0.0
    
    # Weighted average
    final_score = (
        0.4 * ml_normalized +
        0.3 * llm_normalized +
        0.3 * rule_normalized
    )
    
    # Convert to 0-1000 scale
    credit_score = int(final_score * 1000)
    
    # Determine risk rating
    risk_rating = get_risk_rating(credit_score)
    
    # Determine decision
    if rule_result['hard_violations']:
        decision_status = "REJECT"
        reason = f"Hard rule violation: {rule_result['violations']}"
    elif credit_score >= 700:
        decision_status = "APPROVE"
        reason = "Strong creditworthiness"
    elif credit_score >= 500:
        decision_status = "MANUAL_REVIEW"
        reason = "Borderline case - requires underwriter review"
    else:
        decision_status = "REJECT"
        reason = "Insufficient creditworthiness"
    
    # Generate XAI explanation
    explanation = generate_shap_explanation(ml_score, features)
    
    return Decision(
        credit_score=credit_score,
        risk_rating=risk_rating,
        status=decision_status,
        reason=reason,
        ml_contribution=ml_normalized,
        llm_contribution=llm_normalized,
        rule_contribution=rule_normalized,
        explanation=explanation
    )
```

---

## 3. DATABASE SCHEMA (PostgreSQL)

### 3.1 Complete DDL

```sql
-- ============================================================================
-- AnalyticaLoan Database Schema
-- PostgreSQL 15+
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USER MANAGEMENT
-- ============================================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'UNDERWRITER', 'RISK_ANALYST', 'OPS', 'VIEWER')),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    created_by UUID REFERENCES users(user_id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- 2. APPLICANTS
-- ============================================================================

CREATE TABLE applicants (
    applicant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nik VARCHAR(16) UNIQUE NOT NULL,  -- NIK Indonesia
    npwp VARCHAR(20),  -- Tax ID
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('MALE', 'FEMALE', 'OTHER')),
    marital_status VARCHAR(20) CHECK (marital_status IN ('SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED')),
    education VARCHAR(50),
    occupation VARCHAR(100),
    monthly_income DECIMAL(15, 2),
    phone_number VARCHAR(20),
    email VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'Indonesia',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_applicants_nik ON applicants(nik);
CREATE INDEX idx_applicants_npwp ON applicants(npwp);
CREATE INDEX idx_applicants_name ON applicants(full_name);

-- ============================================================================
-- 3. LOAN APPLICATIONS
-- ============================================================================

CREATE TABLE loan_applications (
    application_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_number VARCHAR(50) UNIQUE NOT NULL,  -- Display ID: LA-2024-00001
    applicant_id UUID NOT NULL REFERENCES applicants(applicant_id),
    loan_product VARCHAR(100) NOT NULL,  -- KPR, KTA, Modal Usaha, etc.
    loan_amount DECIMAL(15, 2) NOT NULL,
    loan_term_months INTEGER NOT NULL,
    interest_rate DECIMAL(5, 2),
    purpose TEXT,
    application_channel VARCHAR(50) CHECK (application_channel IN ('WEB', 'MOBILE', 'BRANCH', 'AGENT')),
    status VARCHAR(50) DEFAULT 'SUBMITTED' CHECK (
        status IN (
            'SUBMITTED', 
            'DOCUMENT_VERIFICATION', 
            'UNDERWRITING', 
            'MANUAL_REVIEW', 
            'APPROVED', 
            'REJECTED', 
            'CANCELLED'
        )
    ),
    assigned_to UUID REFERENCES users(user_id),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_loan_applications_applicant ON loan_applications(applicant_id);
CREATE INDEX idx_loan_applications_status ON loan_applications(status);
CREATE INDEX idx_loan_applications_number ON loan_applications(application_number);
CREATE INDEX idx_loan_applications_submitted ON loan_applications(submitted_at DESC);

-- ============================================================================
-- 4. FINANCIAL DOCUMENTS
-- ============================================================================

CREATE TABLE financial_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES loan_applications(application_id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL CHECK (
        document_type IN (
            'INCOME_STATEMENT', 
            'BALANCE_SHEET', 
            'CASH_FLOW', 
            'BANK_STATEMENT', 
            'TAX_RETURN',
            'SALARY_SLIP',
            'BUSINESS_LICENSE',
            'ID_CARD',
            'OTHER'
        )
    ),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- S3 path
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    upload_channel VARCHAR(50),
    ocr_status VARCHAR(50) DEFAULT 'PENDING' CHECK (
        ocr_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')
    ),
    ocr_confidence DECIMAL(5, 2),  -- 0-100
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_documents_application ON financial_documents(application_id);
CREATE INDEX idx_documents_type ON financial_documents(document_type);
CREATE INDEX idx_documents_ocr_status ON financial_documents(ocr_status);

-- ============================================================================
-- 5. EXTRACTED METRICS (From Documents)
-- ============================================================================

CREATE TABLE extracted_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES financial_documents(document_id) ON DELETE CASCADE,
    application_id UUID NOT NULL REFERENCES loan_applications(application_id),
    metric_type VARCHAR(100) NOT NULL,  -- income_statement, balance_sheet, etc.
    metric_data JSONB NOT NULL,  -- Flexible storage for different metric types
    extraction_method VARCHAR(50) CHECK (
        extraction_method IN ('OCR', 'MANUAL', 'API', 'PARSER')
    ),
    confidence_score DECIMAL(5, 2),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by UUID REFERENCES users(user_id),
    verified_at TIMESTAMP
);

CREATE INDEX idx_metrics_document ON extracted_metrics(document_id);
CREATE INDEX idx_metrics_application ON extracted_metrics(application_id);
CREATE INDEX idx_metrics_type ON extracted_metrics(metric_type);
CREATE INDEX idx_metrics_data ON extracted_metrics USING gin(metric_data);

-- Example metric_data structure:
-- {
--   "revenue": 1500000000,
--   "net_income": 450000000,
--   "total_assets": 7000000000,
--   "current_ratio": 1.33,
--   "debt_to_equity": 1.33,
--   "period": "2024-Q3"
-- }

-- ============================================================================
-- 6. SCORING RESULTS
-- ============================================================================

CREATE TABLE scoring_results (
    scoring_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES loan_applications(application_id),
    model_version VARCHAR(50) NOT NULL,  -- e.g., "xgboost_v1.2.3"
    credit_score INTEGER NOT NULL CHECK (credit_score BETWEEN 0 AND 1000),
    probability_of_default DECIMAL(5, 4),  -- 0.0000 to 1.0000
    risk_rating VARCHAR(5) CHECK (risk_rating IN ('AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'C', 'D')),
    ml_score DECIMAL(5, 4),  -- Raw ML output
    llm_score DECIMAL(5, 4),  -- LLM reasoning score
    rule_score DECIMAL(5, 4),  -- Rule compliance score
    final_score DECIMAL(5, 4),  -- Fused score
    explanation JSONB,  -- XAI explanation (SHAP values)
    feature_importances JSONB,  -- Top features
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scoring_application ON scoring_results(application_id);
CREATE INDEX idx_scoring_version ON scoring_results(model_version);
CREATE INDEX idx_scoring_rating ON scoring_results(risk_rating);

-- ============================================================================
-- 7. DECISION LOGS
-- ============================================================================

CREATE TABLE decision_logs (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES loan_applications(application_id),
    scoring_id UUID REFERENCES scoring_results(scoring_id),
    decision_status VARCHAR(50) NOT NULL CHECK (
        decision_status IN ('APPROVE', 'REJECT', 'MANUAL_REVIEW', 'PENDING')
    ),
    decision_reason TEXT,
    decision_maker VARCHAR(50) CHECK (decision_maker IN ('AUTO', 'UNDERWRITER', 'COMMITTEE')),
    decided_by UUID REFERENCES users(user_id),
    ml_contribution DECIMAL(5, 4),
    llm_contribution DECIMAL(5, 4),
    rule_contribution DECIMAL(5, 4),
    policy_violations JSONB,  -- List of policy violations, if any
    override_reason TEXT,  -- If manual override
    credit_memo_path VARCHAR(500),  -- S3 path to generated PDF
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decision_application ON decision_logs(application_id);
CREATE INDEX idx_decision_status ON decision_logs(decision_status);
CREATE INDEX idx_decision_maker ON decision_logs(decision_maker);
CREATE INDEX idx_decision_date ON decision_logs(decided_at DESC);

-- ============================================================================
-- 8. AUDIT TRAIL (Immutable Log)
-- ============================================================================

CREATE TABLE audit_trail (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES loan_applications(application_id),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,  -- e.g., 'CREATE_APPLICATION', 'UPLOAD_DOCUMENT', 'APPROVE_LOAN'
    entity_type VARCHAR(50),  -- e.g., 'APPLICATION', 'DOCUMENT', 'DECISION'
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Prevent updates and deletes (immutable)
CREATE RULE audit_no_update AS ON UPDATE TO audit_trail DO INSTEAD NOTHING;
CREATE RULE audit_no_delete AS ON DELETE TO audit_trail DO INSTEAD NOTHING;

CREATE INDEX idx_audit_application ON audit_trail(application_id);
CREATE INDEX idx_audit_user ON audit_trail(user_id);
CREATE INDEX idx_audit_action ON audit_trail(action);
CREATE INDEX idx_audit_timestamp ON audit_trail(timestamp DESC);

-- ============================================================================
-- 9. MODEL METADATA (ML Model Registry)
-- ============================================================================

CREATE TABLE model_metadata (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) CHECK (
        model_type IN ('LOGISTIC_REGRESSION', 'XGBOOST', 'LIGHTGBM', 'NEURAL_NETWORK', 'ENSEMBLE')
    ),
    model_path VARCHAR(500),  -- MLflow artifact path
    training_data_version VARCHAR(50),
    performance_metrics JSONB,  -- {"auc": 0.85, "precision": 0.78, ...}
    feature_list JSONB,  -- List of features used
    is_active BOOLEAN DEFAULT FALSE,
    trained_at TIMESTAMP,
    deployed_at TIMESTAMP,
    retired_at TIMESTAMP,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_version ON model_metadata(model_version);
CREATE INDEX idx_model_active ON model_metadata(is_active);

-- ============================================================================
-- 10. BLACKLIST (Fraud Prevention)
-- ============================================================================

CREATE TABLE blacklist (
    blacklist_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identifier_type VARCHAR(50) CHECK (identifier_type IN ('NIK', 'NPWP', 'PHONE', 'EMAIL', 'DEVICE_ID')),
    identifier_value VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    added_by UUID REFERENCES users(user_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_blacklist_identifier ON blacklist(identifier_type, identifier_value);
CREATE INDEX idx_blacklist_active ON blacklist(is_active);

-- ============================================================================
-- 11. CREDIT BUREAU DATA (SLIK OJK Cache)
-- ============================================================================

CREATE TABLE credit_bureau_data (
    bureau_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    applicant_id UUID NOT NULL REFERENCES applicants(applicant_id),
    bureau_source VARCHAR(50) DEFAULT 'SLIK_OJK',
    nik VARCHAR(16) NOT NULL,
    credit_score INTEGER,
    total_accounts INTEGER,
    active_accounts INTEGER,
    delinquent_accounts INTEGER,
    total_debt DECIMAL(15, 2),
    payment_history JSONB,  -- Detailed payment history
    inquiries_last_6m INTEGER,
    raw_response JSONB,  -- Full API response
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- Cache expiry
);

CREATE INDEX idx_bureau_applicant ON credit_bureau_data(applicant_id);
CREATE INDEX idx_bureau_nik ON credit_bureau_data(nik);
CREATE INDEX idx_bureau_fetched ON credit_bureau_data(fetched_at DESC);

-- ============================================================================
-- 12. WORKFLOW STATE (For Temporal/Airflow)
-- ============================================================================

CREATE TABLE workflow_state (
    workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES loan_applications(application_id),
    workflow_name VARCHAR(100) NOT NULL,
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER,
    step_status VARCHAR(50) CHECK (step_status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'RETRY')),
    state_data JSONB,  -- Workflow context
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_application ON workflow_state(application_id);
CREATE INDEX idx_workflow_status ON workflow_state(step_status);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Application Dashboard Summary
CREATE VIEW vw_application_dashboard AS
SELECT 
    la.application_id,
    la.application_number,
    a.full_name AS applicant_name,
    a.nik,
    la.loan_product,
    la.loan_amount,
    la.status,
    sr.credit_score,
    sr.risk_rating,
    dl.decision_status,
    la.submitted_at,
    dl.decided_at,
    u.full_name AS assigned_underwriter
FROM loan_applications la
LEFT JOIN applicants a ON la.applicant_id = a.applicant_id
LEFT JOIN scoring_results sr ON la.application_id = sr.application_id
LEFT JOIN decision_logs dl ON la.application_id = dl.application_id
LEFT JOIN users u ON la.assigned_to = u.user_id
ORDER BY la.submitted_at DESC;

-- View: Risk Portfolio Summary
CREATE VIEW vw_risk_portfolio AS
SELECT 
    sr.risk_rating,
    COUNT(*) AS application_count,
    SUM(la.loan_amount) AS total_exposure,
    AVG(sr.probability_of_default) AS avg_pd,
    SUM(la.loan_amount * sr.probability_of_default) AS expected_loss
FROM loan_applications la
JOIN scoring_results sr ON la.application_id = sr.application_id
WHERE la.status = 'APPROVED'
GROUP BY sr.risk_rating
ORDER BY sr.risk_rating;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_applicants_updated
BEFORE UPDATE ON applicants
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_applications_updated
BEFORE UPDATE ON loan_applications
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- PARTITIONING (For Large Scale)
-- ============================================================================

-- Partition audit_trail by month
-- CREATE TABLE audit_trail_2024_11 PARTITION OF audit_trail
-- FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

-- ============================================================================
-- SAMPLE DATA (For Testing)
-- ============================================================================

-- Insert admin user
INSERT INTO users (email, password_hash, full_name, role) VALUES
('admin@analyticaloan.com', '$2b$12$...hashed...', 'System Admin', 'ADMIN');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
```

---

## 4. API DESIGN (OpenAPI 3.0 Specification)

```yaml
openapi: 3.0.3
info:
  title: AnalyticaLoan API
  description: AI-Powered Credit Underwriting API
  version: 1.0.0
  contact:
    name: API Support
    email: api@analyticaloan.com

servers:
  - url: https://api.analyticaloan.com/v1
    description: Production
  - url: https://staging-api.analyticaloan.com/v1
    description: Staging
  - url: http://localhost:8000/v1
    description: Development

security:
  - BearerAuth: []

paths:
  # ==========================================================================
  # AUTHENTICATION
  # ==========================================================================
  /auth/login:
    post:
      tags:
        - Authentication
      summary: User login
      operationId: login
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    example: Bearer
                  expires_in:
                    type: integer
                    example: 3600
        '401':
          description: Invalid credentials

  # ==========================================================================
  # LOAN APPLICATIONS
  # ==========================================================================
  /applications:
    post:
      tags:
        - Applications
      summary: Create new loan application
      operationId: createApplication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoanApplicationCreate'
      responses:
        '201':
          description: Application created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoanApplication'
        '400':
          description: Invalid input
        '429':
          description: Rate limit exceeded

    get:
      tags:
        - Applications
      summary: List loan applications
      operationId: listApplications
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [SUBMITTED, UNDERWRITING, APPROVED, REJECTED]
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: List of applications
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/LoanApplication'
                  pagination:
                    $ref: '#/components/schemas/Pagination'

  /applications/{application_id}:
    get:
      tags:
        - Applications
      summary: Get application by ID
      operationId: getApplication
      parameters:
        - name: application_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Application details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoanApplication'
        '404':
          description: Application not found

  # ==========================================================================
  # UNDERWRITING (Core Endpoint)
  # ==========================================================================
  /underwrite:
    post:
      tags:
        - Underwriting
      summary: Submit application for AI underwriting
      operationId: underwriteApplication
      description: |
        Triggers the AI underwriting workflow for a loan application.
        This is an async operation that returns immediately with a workflow ID.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - application_id
              properties:
                application_id:
                  type: string
                  format: uuid
                force_manual_review:
                  type: boolean
                  default: false
                priority:
                  type: string
                  enum: [LOW, NORMAL, HIGH, URGENT]
                  default: NORMAL
      responses:
        '202':
          description: Underwriting started
          content:
            application/json:
              schema:
                type: object
                properties:
                  workflow_id:
                    type: string
                    format: uuid
                  application_id:
                    type: string
                    format: uuid
                  status:
                    type: string
                    example: PROCESSING
                  estimated_completion:
                    type: string
                    format: date-time
        '404':
          description: Application not found
        '409':
          description: Application already being processed

  /underwrite/{workflow_id}/status:
    get:
      tags:
        - Underwriting
      summary: Get underwriting workflow status
      operationId: getUnderwritingStatus
      parameters:
        - name: workflow_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Workflow status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WorkflowStatus'

  # ==========================================================================
  # DOCUMENTS
  # ==========================================================================
  /documents/upload:
    post:
      tags:
        - Documents
      summary: Upload financial document
      operationId: uploadDocument
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - application_id
                - document_type
                - file
              properties:
                application_id:
                  type: string
                  format: uuid
                document_type:
                  type: string
                  enum:
                    - INCOME_STATEMENT
                    - BALANCE_SHEET
                    - CASH_FLOW
                    - BANK_STATEMENT
                    - TAX_RETURN
                    - SALARY_SLIP
                    - BUSINESS_LICENSE
                    - ID_CARD
                file:
                  type: string
                  format: binary
      responses:
        '201':
          description: Document uploaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Document'
        '400':
          description: Invalid file type or size

  /documents/{document_id}/ocr:
    post:
      tags:
        - Documents
      summary: Trigger OCR processing
      operationId: processOCR
      parameters:
        - name: document_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '202':
          description: OCR processing started
          content:
            application/json:
              schema:
                type: object
                properties:
                  document_id:
                    type: string
                    format: uuid
                  ocr_status:
                    type: string
                    example: PROCESSING

  # ==========================================================================
  # SCORING
  # ==========================================================================
  /applications/{application_id}/score:
    get:
      tags:
        - Scoring
      summary: Get credit score for application
      operationId: getCreditScore
      parameters:
        - name: application_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Credit score details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScoringResult'
        '404':
          description: Score not available yet

  # ==========================================================================
  # POLICIES (RAG)
  # ==========================================================================
  /policies:
    get:
      tags:
        - Policies
      summary: List all policies
      operationId: listPolicies
      responses:
        '200':
          description: Policy list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Policy'

  /policies/query:
    post:
      tags:
        - Policies
      summary: Query policies using RAG
      operationId: queryPolicies
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - question
              properties:
                question:
                  type: string
                  example: "Berapa maksimum LTV untuk KPR sesuai POJK?"
                top_k:
                  type: integer
                  default: 5
      responses:
        '200':
          description: Policy answer
          content:
            application/json:
              schema:
                type: object
                properties:
                  answer:
                    type: string
                  sources:
                    type: array
                    items:
                      type: object
                      properties:
                        document:
                          type: string
                        page:
                          type: integer
                        relevance_score:
                          type: number

  /rag/update:
    post:
      tags:
        - Policies
      summary: Update RAG knowledge base
      operationId: updateRAG
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                document_type:
                  type: string
                  enum: [POJK, SOP, GUIDELINE, MEMO]
      responses:
        '202':
          description: RAG update started
          content:
            application/json:
              schema:
                type: object
                properties:
                  task_id:
                    type: string
                  status:
                    type: string
                    example: PROCESSING

  # ==========================================================================
  # AUDIT
  # ==========================================================================
  /audit/{application_id}:
    get:
      tags:
        - Audit
      summary: Get audit trail for application
      operationId: getAuditTrail
      parameters:
        - name: application_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Audit trail
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AuditLog'

# ==============================================================================
# COMPONENTS (Schemas)
# ==============================================================================
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    LoanApplicationCreate:
      type: object
      required:
        - applicant
        - loan_product
        - loan_amount
        - loan_term_months
      properties:
        applicant:
          $ref: '#/components/schemas/ApplicantCreate'
        loan_product:
          type: string
          example: "KPR"
        loan_amount:
          type: number
          example: 500000000
        loan_term_months:
          type: integer
          example: 120
        purpose:
          type: string
          example: "Pembelian rumah"

    ApplicantCreate:
      type: object
      required:
        - nik
        - full_name
        - date_of_birth
      properties:
        nik:
          type: string
          pattern: '^\d{16}$'
        npwp:
          type: string
        full_name:
          type: string
        date_of_birth:
          type: string
          format: date
        gender:
          type: string
          enum: [MALE, FEMALE, OTHER]
        monthly_income:
          type: number
        phone_number:
          type: string
        email:
          type: string
          format: email

    LoanApplication:
      type: object
      properties:
        application_id:
          type: string
          format: uuid
        application_number:
          type: string
          example: "LA-2024-00001"
        applicant:
          $ref: '#/components/schemas/Applicant'
        loan_product:
          type: string
        loan_amount:
          type: number
        status:
          type: string
          enum: [SUBMITTED, DOCUMENT_VERIFICATION, UNDERWRITING, MANUAL_REVIEW, APPROVED, REJECTED]
        submitted_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    Applicant:
      type: object
      properties:
        applicant_id:
          type: string
          format: uuid
        nik:
          type: string
        full_name:
          type: string
        date_of_birth:
          type: string
          format: date

    Document:
      type: object
      properties:
        document_id:
          type: string
          format: uuid
        application_id:
          type: string
          format: uuid
        document_type:
          type: string
        file_name:
          type: string
        file_size_bytes:
          type: integer
        ocr_status:
          type: string
          enum: [PENDING, PROCESSING, COMPLETED, FAILED]
        uploaded_at:
          type: string
          format: date-time

    ScoringResult:
      type: object
      properties:
        scoring_id:
          type: string
          format: uuid
        application_id:
          type: string
          format: uuid
        credit_score:
          type: integer
          minimum: 0
          maximum: 1000
        probability_of_default:
          type: number
          minimum: 0
          maximum: 1
        risk_rating:
          type: string
          enum: [AAA, AA, A, BBB, BB, B, C, D]
        ml_score:
          type: number
        llm_score:
          type: number
        rule_score:
          type: number
        explanation:
          type: object
        scored_at:
          type: string
          format: date-time

    WorkflowStatus:
      type: object
      properties:
        workflow_id:
          type: string
          format: uuid
        application_id:
          type: string
          format: uuid
        current_step:
          type: integer
        total_steps:
          type: integer
        step_status:
          type: string
          enum: [PENDING, RUNNING, COMPLETED, FAILED, RETRY]
        progress_percentage:
          type: number
        updated_at:
          type: string
          format: date-time

    Policy:
      type: object
      properties:
        policy_id:
          type: string
        title:
          type: string
        document_type:
          type: string
        version:
          type: string
        last_updated:
          type: string
          format: date-time

    AuditLog:
      type: object
      properties:
        audit_id:
          type: string
          format: uuid
        action:
          type: string
        entity_type:
          type: string
        timestamp:
          type: string
          format: date-time
        user:
          type: object
          properties:
            user_id:
              type: string
              format: uuid
            full_name:
              type: string

    Pagination:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        total_pages:
          type: integer

    Error:
      type: object
      properties:
        error_code:
          type: string
        message:
          type: string
        details:
          type: object
```

---

## 5. DEPLOYMENT ARCHITECTURE

### 5.1 Cloud Architecture (GCP Example)

```
┌──────────────────────────────────────────────────────────────┐
│                    CLOUD LOAD BALANCER                       │
│                  (Global HTTPS Load Balancer)                │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌─────────▼────────┐
│  GKE CLUSTER 1  │            │  GKE CLUSTER 2   │
│  (Primary)      │            │  (DR/Failover)   │
│  Region: asia-  │            │  Region: asia-   │
│  southeast2     │            │  southeast1      │
└────────┬────────┘            └──────────────────┘
         │
    ┌────┴─────┐
    │  Pods:   │
    │  • API   │
    │  • Agent │
    │  • ML    │
    └──────────┘

DATABASES:
- Cloud SQL (PostgreSQL 15) - Multi-region HA
- Cloud Memorystore (Redis) - For caching
- Cloud Storage - Document storage

AI/ML:
- Vertex AI - Model training & serving
- Gemini API - LLM calls

MONITORING:
- Cloud Monitoring
- Cloud Logging
- Cloud Trace
```

---

**Document End**

*For implementation details, refer to Engineering Roadmap.*
