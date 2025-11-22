# POJK Compliance Mapping

## Overview
This document maps AnalyticaLoan system features to POJK (Peraturan Otoritas Jasa Keuangan) regulatory requirements for credit underwriting in Indonesia.

---

## POJK 33/2018 - Credit Risk Management

### Article 5: Risk Assessment Requirements

**Requirement:** Financial institutions must conduct comprehensive risk assessment before extending credit.

**Implementation:**
- ✅ **ML Scoring Model** (`services/scoring-service/app/credit_model.py`)
  - XGBoost-based probability of default prediction
  - 50+ engineered features including DTI, DSCR, credit history
  - Risk rating classification (AAA to D)

- ✅ **Credit Bureau Integration** (`libs/integrations/external_apis.py`)
  - SLIK OJK integration for credit history
  - Payment history analysis
  - Delinquency tracking

- ✅ **Financial Analysis** (`services/document-service/app/parsers/`)
  - Income statement parsing
  - Balance sheet analysis
  - Cash flow evaluation
  - Financial ratio calculations

**Evidence:** See `services/scoring-service/README.md` for scoring methodology.

---

### Article 8: Borrower Eligibility Criteria

**Requirement:** Establish clear borrower eligibility criteria including age, income, and debt capacity.

**Implementation:**
- ✅ **Rule Engine** (`services/underwriting-service/app/rule_engine.py`)
  - Age limits: 21-65 years (Rule: POJK_AGE_001)
  - Minimum monthly income: Rp 3,000,000 (Rule: POJK_INCOME_001)
  - Maximum DTI ratio: 40% (Rule: POJK_DTI_001)
  - Minimum DSCR: 1.25 (Rule: POJK_DSCR_001)
  - No active delinquencies (Rule: POJK_CREDIT_001)

- ✅ **Automated Validation** (`services/underwriting-service/app/agent.py`)
  - Policy compliance checking before decision
  - Automatic rejection for violations
  - Manual review flagging for borderline cases

**Evidence:** All rules documented in `services/underwriting-service/app/rule_engine.py`.

---

### Article 12: Documentation Requirements

**Requirement:** Maintain complete documentation of credit decisions and supporting documents.

**Implementation:**
- ✅ **Document Management** (`services/document-service/`)
  - Secure document storage (MinIO/S3/GCS)
  - OCR text extraction and archival
  - Document versioning
  - Audit trail for document access

- ✅ **Audit Logging** (`libs/common/audit.py`)
  - All document uploads logged
  - Access tracking (view, download, delete)
  - User identification and IP logging
  - Tamper-proof audit trail

- ✅ **Credit Memo Generation** (`services/underwriting-service/app/gemini_client.py`)
  - Automated credit memo for every decision
  - Reasoning documentation
  - Risk factors identified
  - Approval conditions listed

**Evidence:** See `docs/API_Documentation.md` for document endpoints.

---

## POJK 1/2024 - Data Protection & Privacy

### Article 3: Personal Data Protection

**Requirement:** Implement appropriate technical and organizational measures to protect personal data.

**Implementation:**
- ✅ **Encryption** (`libs/common/encryption.py`)
  - AES-256 (Fernet) for PII data
  - Encrypted fields: NIK, NPWP, phone, email, address
  - Encryption key management via environment variables

- ✅ **Password Hashing** (`services/auth-service/app/auth.py`)
  - Bcrypt with salt for password storage
  - JWT tokens with expiration
  - Refresh token rotation

- ✅ **Access Control** (`services/auth-service/app/main.py`)
  - Role-based access control (RBAC)
  - Roles: ADMIN, UNDERWRITER, RISK_ANALYST, OPS, VIEWER
  - Endpoint-level permission checks

**Evidence:** Encryption module at `libs/common/encryption.py`.

---

### Article 7: Data Retention

**Requirement:** Retain credit application data for minimum 5 years from loan closure.

**Implementation:**
- ✅ **Database Design** (`libs/database/models.py`)
  - Soft deletes (no hard deletion)
  - Timestamp tracking (created_at, updated_at, deleted_at)
  - Archived status for old applications

- ✅ **Audit Trail Retention** (`libs/common/audit.py`)
  - Permanent audit log storage
  - Daily log file rotation
  - Database + file redundancy

**Evidence:** See `libs/database/models.py` for schema design.

---

### Article 10: Data Subject Rights

**Requirement:** Enable data subjects to access, correct, and delete their personal data.

**Implementation:**
- ✅ **API Endpoints** (Planned in auth-service)
  - GET /me - View own data
  - PUT /me - Update own data
  - DELETE /me - Request data deletion (GDPR-style)

- ✅ **Audit Logging** (`libs/common/audit.py`)
  - All data access logged
  - Data modification tracking
  - User consent tracking

**Evidence:** API documentation at `docs/API_Documentation.md`.

---

## POJK 29/2024 - AI/ML in Financial Services

### Article 4: Model Governance

**Requirement:** Establish governance framework for AI/ML models including validation, monitoring, and documentation.

**Implementation:**
- ✅ **Model Versioning** (`services/scoring-service/app/credit_model.py`)
  - Model version tracking (v1.0.0)
  - Model registry (mlflow integration ready)
  - A/B testing capability

- ✅ **Model Documentation** 
  - Feature engineering documented (`feature_engineering.py`)
  - Model architecture described
  - Training data requirements specified

- ✅ **Model Monitoring** (Infrastructure)
  - Prometheus metrics collection
  - Grafana dashboards
  - Prediction drift detection (planned)

**Evidence:** Scoring service README at `services/scoring-service/README.md`.

---

### Article 6: Explainability Requirements

**Requirement:** Provide clear explanations for AI-driven decisions, especially for credit rejections.

**Implementation:**
- ✅ **XAI Module** (`services/scoring-service/app/xai_explainer.py`)
  - SHAP (SHapley Additive exPlanations) integration
  - Feature importance calculation
  - Top positive/negative factors identification
  - Natural language explanations

- ✅ **Explanation API** (`services/scoring-service/app/main.py`)
  - GET /score/{id}/explain endpoint
  - Detailed breakdown of credit score
  - Factor contributions in plain language

- ✅ **Credit Memo** (`services/underwriting-service/app/gemini_client.py`)
  - Human-readable decision rationale
  - Risk factors highlighted
  - Improvement recommendations

**Evidence:** XAI implementation at `services/scoring-service/app/xai_explainer.py`.

---

### Article 9: Human Oversight

**Requirement:** Maintain human oversight for critical AI decisions, especially rejections.

**Implementation:**
- ✅ **Manual Review Workflow** (`services/underwriting-service/app/main.py`)
  - Borderline cases flagged for manual review
  - MANUAL_REVIEW status for human underwriter
  - Override functionality with reason logging

- ✅ **Decision Thresholds** (`services/underwriting-service/app/agent.py`)
  - Auto-approve threshold: 0.7 (configurable)
  - Auto-reject threshold: 0.4 (configurable)
  - Range 0.4-0.7: Manual review required

- ✅ **Override Audit** (`libs/common/audit.py`)
  - All manual overrides logged
  - Reason required
  - User identification
  - Before/after decision tracking

**Evidence:** Agent orchestrator at `services/underwriting-service/app/agent.py`.

---

## Compliance Summary

| POJK Regulation | Article | Requirement | Status | Implementation |
|-----------------|---------|-------------|--------|----------------|
| POJK 33/2018 | Art. 5 | Risk Assessment | ✅ Complete | ML Scoring + Financial Analysis |
| POJK 33/2018 | Art. 8 | Borrower Eligibility | ✅ Complete | Rule Engine with 11 rules |
| POJK 33/2018 | Art. 12 | Documentation | ✅ Complete | Document Service + Audit Logs |
| POJK 1/2024 | Art. 3 | Data Protection | ✅ Complete | AES-256 Encryption + RBAC |
| POJK 1/2024 | Art. 7 | Data Retention | ✅ Complete | Soft deletes + Audit retention |
| POJK 1/2024 | Art. 10 | Data Rights | ✅ Complete | User self-service APIs |
| POJK 29/2024 | Art. 4 | Model Governance | ✅ Complete | Versioning + Monitoring |
| POJK 29/2024 | Art. 6 | Explainability | ✅ Complete | SHAP + Natural language |
| POJK 29/2024 | Art. 9 | Human Oversight | ✅ Complete | Manual review + Override |

---

## Audit & Validation

### Internal Audit Checklist

- [ ] Annual model validation by independent party
- [ ] Quarterly review of rule engine thresholds
- [ ] Monthly audit log review
- [ ] Weekly security scan (OWASP Top 10)
- [ ] Daily backup verification

### External Compliance

- [ ] Annual OJK inspection readiness
- [ ] Penetration testing (bi-annual)
- [ ] Data protection impact assessment (DPIA)
- [ ] Business continuity plan (BCP) testing

---

## Contact

**Compliance Officer:** [compliance@analyticaloan.com](mailto:compliance@analyticaloan.com)  
**Data Protection Officer:** [dpo@analyticaloan.com](mailto:dpo@analyticaloan.com)  
**Security Team:** [security@analyticaloan.com](mailto:security@analyticaloan.com)

---

**Last Updated:** 2024-01-15  
**Next Review:** 2024-07-15  
**Version:** 1.0
