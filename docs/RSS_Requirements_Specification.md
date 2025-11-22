# Requirements Specification Sheet (RSS)
## AnalyticaLoan – AI Agent for Credit Underwriting

**Version:** 1.0  
**Date:** 2025-11-22  
**Classification:** Internal - Confidential  
**Prepared By:** AI/ML Engineering Team

---

## 1. FUNCTIONAL REQUIREMENTS

### 1.1 Credit Underwriting Decision Engine

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | System must perform end-to-end credit underwriting analysis | P0 | Complete decision within 120 seconds |
| FR-002 | Support multi-stage approval workflow (Auto/Manual/Hybrid) | P0 | 3 distinct approval modes implemented |
| FR-003 | Generate credit decision with risk rating (AAA to D) | P0 | Standard rating scale compliance |
| FR-004 | Support decision override by authorized underwriters | P1 | Role-based override with audit trail |
| FR-005 | Batch processing capability for bulk applications | P2 | Process ≥100 applications concurrently |

### 1.2 Financial Statement Parsing

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-010 | Extract data from PDF financial statements | P0 | ≥95% accuracy on standard formats |
| FR-011 | Parse income statements (Laba Rugi) | P0 | Extract 15+ key financial metrics |
| FR-012 | Parse balance sheets (Neraca) | P0 | Extract assets, liabilities, equity |
| FR-013 | Parse cash flow statements | P1 | Operating, investing, financing activities |
| FR-014 | Support handwritten documents via OCR | P2 | ≥80% accuracy for clear handwriting |
| FR-015 | Multi-language support (Indonesian/English) | P1 | Both languages processed accurately |

### 1.3 Customer Profile Scoring

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-020 | Behavioral scoring based on historical data | P0 | Incorporate ≥10 behavioral signals |
| FR-021 | Demographic scoring (age, location, education) | P0 | Weight factors per policy rules |
| FR-022 | Credit bureau integration (SLIK OJK) | P0 | Real-time API integration |
| FR-023 | Social media risk profiling (optional) | P3 | Privacy-compliant scraping |
| FR-024 | Industry-specific risk adjustment | P1 | 20+ industry categories |

### 1.4 Fraud Detection Signals

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-030 | Detect document tampering/forgery | P0 | Flag suspicious documents |
| FR-031 | Identify duplicate applications | P0 | Cross-reference NIK/NPWP |
| FR-032 | Velocity checks (application frequency) | P1 | Alert on ≥3 apps in 30 days |
| FR-033 | Anomaly detection in financial ratios | P1 | Statistical outlier detection |
| FR-034 | Blacklist checking (internal + OJK) | P0 | Real-time verification |

### 1.5 Bank Statement Analysis

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-040 | Parse bank statements (PDF/Excel/CSV) | P0 | Support top 10 Indonesian banks |
| FR-041 | Calculate monthly average balance | P0 | 6-month rolling average |
| FR-042 | Identify salary/income deposits | P0 | Pattern recognition algorithm |
| FR-043 | Detect irregular expenses/gambling | P1 | Flag high-risk transactions |
| FR-044 | Cash flow volatility scoring | P1 | Standard deviation analysis |

### 1.6 Risk Rating & Creditworthiness Index

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-050 | Calculate composite credit score (0-1000) | P0 | Weighted multi-factor model |
| FR-051 | Probability of Default (PD) estimation | P0 | ML-based PD prediction |
| FR-052 | Loss Given Default (LGD) calculation | P1 | Historical recovery data |
| FR-053 | Exposure at Default (EAD) projection | P1 | Loan amount consideration |
| FR-054 | Expected Loss (EL) computation | P1 | EL = PD × LGD × EAD |

### 1.7 Auto-Generated Credit Memorandum

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-060 | Generate credit memo in PDF format | P0 | Professional template |
| FR-061 | Include applicant summary & financials | P0 | Standardized sections |
| FR-062 | Include AI reasoning & decision rationale | P0 | Explainable AI output |
| FR-063 | Include risk mitigants & recommendations | P1 | Actionable insights |
| FR-064 | Digital signature support | P2 | PKI-based signing |

### 1.8 AI Agent Workflow

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-070 | Multi-agent orchestration (state machine) | P0 | Directed acyclic graph execution |
| FR-071 | Step-by-step underwriting process | P0 | 8-12 defined stages |
| FR-072 | Human-in-the-loop approval gates | P0 | Manual intervention points |
| FR-073 | Parallel task execution where possible | P1 | Reduce latency by 40% |
| FR-074 | Fault tolerance & retry mechanisms | P1 | Auto-retry on transient failures |

### 1.9 Rule-Based Policy Engine + LLM Hybrid

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-080 | Execute deterministic policy rules | P0 | 100% rule reproducibility |
| FR-081 | LLM-based contextual reasoning | P0 | Gemini Pro/Flash integration |
| FR-082 | Decision fusion (rules + LLM) | P0 | Weighted voting mechanism |
| FR-083 | Policy version control | P1 | Git-based policy management |
| FR-084 | A/B testing for policy changes | P2 | Controlled rollout |

### 1.10 RAG for POJK & Lending Policies

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-090 | Vector database for policy documents | P0 | Weaviate/Pinecone setup |
| FR-091 | Embedding generation (text-embedding-004) | P0 | High-quality embeddings |
| FR-092 | Semantic search over policies | P0 | Top-K retrieval (K=5) |
| FR-093 | POJK regulatory compliance checking | P0 | 33/2018, 1/2024, 29/2024 |
| FR-094 | Auto-update policy knowledge base | P1 | Scheduled re-indexing |

### 1.11 API Endpoints

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-100 | POST /underwrite - Submit application | P0 | RESTful JSON API |
| FR-101 | POST /documents/upload - Upload docs | P0 | Multipart form-data |
| FR-102 | GET /applications/{id}/score - Get score | P0 | JSON response |
| FR-103 | GET /policies - List policies | P1 | Paginated results |
| FR-104 | POST /rag/update - Update knowledge base | P1 | Admin-only access |
| FR-105 | GET /audit/{id} - Audit trail | P0 | Complete decision log |

### 1.12 Dashboard (Ops + Risk + Underwriting)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-110 | Underwriter dashboard for application queue | P0 | Real-time queue updates |
| FR-111 | Risk dashboard for portfolio monitoring | P0 | KPI visualization |
| FR-112 | Ops dashboard for system health | P1 | Metrics & alerts |
| FR-113 | Approval workflow UI | P0 | Accept/Reject/Return actions |
| FR-114 | Document viewer with annotations | P1 | PDF viewer integration |

### 1.13 Logging, Audit Trail & Traceability

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-120 | Log all API requests/responses | P0 | Structured logging |
| FR-121 | Audit trail for all decisions | P0 | Immutable audit log |
| FR-122 | User action tracking | P0 | Who/What/When/Where |
| FR-123 | Model version tracking | P1 | ML model lineage |
| FR-124 | Data lineage for compliance | P1 | End-to-end traceability |

---

## 2. NON-FUNCTIONAL REQUIREMENTS

### 2.1 Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-001 | API latency (P95) for scoring endpoint | < 2 seconds | Load testing |
| NFR-002 | API latency (P99) for scoring endpoint | < 5 seconds | Load testing |
| NFR-003 | Throughput | ≥ 500 req/min | JMeter/Locust |
| NFR-004 | OCR processing time per document | < 10 seconds | Benchmark tests |
| NFR-005 | LLM response time | < 3 seconds | Gemini API monitoring |

### 2.2 Determinism & Reproducibility

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-010 | LLM temperature control | temperature=0 for production |
| NFR-011 | Seeded randomness | Fixed seeds for testing |
| NFR-012 | Version-locked dependencies | requirements.txt with exact versions |
| NFR-013 | Model versioning | MLflow model registry |

### 2.3 Availability & Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-020 | Service availability (SLA) | 99.9% uptime |
| NFR-021 | Mean Time To Recovery (MTTR) | < 30 minutes |
| NFR-022 | Error rate | < 0.1% |
| NFR-023 | Data durability | 99.999% (5 nines) |

### 2.4 Security

| ID | Requirement | Standard |
|----|-------------|----------|
| NFR-030 | Data encryption at rest | AES-256 |
| NFR-031 | Data encryption in transit | TLS 1.3 |
| NFR-032 | Credential management | Vault (HashiCorp) or Secret Manager |
| NFR-033 | Authentication | OAuth 2.0 + JWT |
| NFR-034 | Authorization | RBAC with least privilege |
| NFR-035 | API rate limiting | 1000 req/hour per API key |
| NFR-036 | DDoS protection | Cloudflare / AWS Shield |

### 2.5 Scalability

| ID | Requirement | Approach |
|----|-------------|----------|
| NFR-040 | Horizontal scaling | Microservices architecture |
| NFR-041 | Database sharding | Application-level sharding |
| NFR-042 | Caching strategy | Redis for hot data |
| NFR-043 | Load balancing | NGINX / GCP Load Balancer |
| NFR-044 | Auto-scaling | Kubernetes HPA |

### 2.6 Cloud Agnostic

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-050 | Multi-cloud support | GCP/AWS/Azure compatibility |
| NFR-051 | Infrastructure as Code | Terraform |
| NFR-052 | Container orchestration | Kubernetes |
| NFR-053 | Service mesh | Istio (optional) |

### 2.7 Observability

| ID | Requirement | Tool |
|----|-------------|------|
| NFR-060 | Metrics collection | Prometheus |
| NFR-061 | Metrics visualization | Grafana |
| NFR-062 | Distributed tracing | OpenTelemetry + Jaeger |
| NFR-063 | Log aggregation | ELK Stack / Cloud Logging |
| NFR-064 | Alerting | AlertManager / PagerDuty |

---

## 3. COMPLIANCE REQUIREMENTS

### 3.1 POJK 33/POJK.03/2018 - Credit Risk Management

| ID | POJK Clause | Requirement | Implementation |
|----|-------------|-------------|----------------|
| CR-001 | Article 7 | Credit risk governance | Board approval process |
| CR-002 | Article 10 | Credit policy documentation | RAG-indexed policies |
| CR-003 | Article 13 | Credit analysis standards | AI scoring + manual review |
| CR-004 | Article 16 | Credit approval authority | RBAC with approval limits |
| CR-005 | Article 25 | Credit monitoring | Portfolio dashboard |

### 3.2 POJK 1/POJK.03/2024 - Digital Financial Services

| ID | POJK Clause | Requirement | Implementation |
|----|-------------|-------------|----------------|
| CR-010 | Article 5 | Digital service security | End-to-end encryption |
| CR-011 | Article 12 | API security standards | OAuth 2.0 + rate limiting |
| CR-012 | Article 18 | Data protection | PII encryption & masking |
| CR-013 | Article 22 | Audit trail | Immutable logging |

### 3.3 POJK 29/POJK.03/2024 - IT Risk Governance

| ID | POJK Clause | Requirement | Implementation |
|----|-------------|-------------|----------------|
| CR-020 | Article 6 | IT risk management framework | ISO 27001 controls |
| CR-021 | Article 11 | Business continuity plan | DR/BCP procedures |
| CR-022 | Article 15 | Change management | GitOps workflow |
| CR-023 | Article 20 | Security incident response | SIEM integration |

### 3.4 ISO 27001 Controls

| ID | Control | Requirement |
|----|---------|-------------|
| CR-030 | A.8.2 | Information classification |
| CR-031 | A.9.4 | Access control |
| CR-032 | A.12.2 | Protection from malware |
| CR-033 | A.18.1 | Compliance with legal requirements |

### 3.5 Explainable AI (XAI)

| ID | Requirement | Implementation |
|----|-------------|----------------|
| CR-040 | Decision transparency | SHAP/LIME explanations |
| CR-041 | Feature importance | Model interpretability |
| CR-042 | Bias detection | Fairness metrics |
| CR-043 | Human oversight | Manual review for edge cases |

### 3.6 Data Retention Policy

| ID | Data Type | Retention Period | Compliance |
|----|-----------|------------------|------------|
| CR-050 | Loan applications | 10 years | Bank Indonesia |
| CR-051 | Decision logs | 7 years | POJK 33/2018 |
| CR-052 | Audit trails | 5 years | ISO 27001 |
| CR-053 | Financial documents | 10 years | Tax law |
| CR-054 | Personal data (GDPR-like) | User consent-based | Best practice |

---

## 4. AI REQUIREMENTS

### 4.1 Multi-Agent Orchestration

| ID | Requirement | Specification |
|----|-------------|---------------|
| AI-001 | Agent types | DocumentAgent, ScoringAgent, PolicyAgent, DecisionAgent |
| AI-002 | Orchestration pattern | Directed Acyclic Graph (DAG) |
| AI-003 | State management | Redis-backed state machine |
| AI-004 | Inter-agent communication | Message queue (RabbitMQ/Kafka) |

### 4.2 LLM Routing Strategy

| ID | Model | Use Case | Temperature |
|----|-------|----------|-------------|
| AI-010 | Gemini 2.0 Flash Thinking | Complex reasoning, multi-step analysis | 0.0 |
| AI-011 | Gemini 2.0 Pro | Content generation, credit memo | 0.0 |
| AI-012 | Gemini 1.5 Flash | Quick lookups, simple tasks | 0.0 |

### 4.3 Tool Use (Function Calling)

| ID | Tool | Purpose |
|----|------|---------|
| AI-020 | ocr_extract | Extract text from documents |
| AI-021 | vector_search | Query RAG knowledge base |
| AI-022 | calculate_score | Execute ML scoring model |
| AI-023 | check_blacklist | Verify against blacklist |
| AI-024 | get_credit_bureau | Fetch SLIK OJK data |
| AI-025 | execute_policy_rule | Run deterministic rules |

### 4.4 Deterministic Rules + Probabilistic LLM

| ID | Requirement | Implementation |
|----|-------------|----------------|
| AI-030 | Rule priority | Rules override LLM when conflict |
| AI-031 | Confidence threshold | LLM output > 0.8 confidence |
| AI-032 | Fallback mechanism | Escalate to human if uncertain |
| AI-033 | Voting system | Weighted decision fusion |

### 4.5 Human-in-the-Loop (HITL)

| ID | Requirement | Trigger Condition |
|----|-------------|-------------------|
| AI-040 | Manual review queue | Borderline scores (0.45-0.55) |
| AI-041 | Fraud flag escalation | Fraud score > 0.7 |
| AI-042 | High-value loans | Loan amount > IDR 1 billion |
| AI-043 | Policy conflict | Rule engine deadlock |

### 4.6 Model Governance

| ID | Requirement | Tool |
|----|-------------|------|
| AI-050 | Model versioning | MLflow |
| AI-051 | Experiment tracking | MLflow |
| AI-052 | A/B testing | Custom framework |
| AI-053 | Model monitoring | Evidently AI / WhyLabs |
| AI-054 | Drift detection | Statistical tests |

### 4.7 Prompt Engineering

| ID | Requirement | Standard |
|----|-------------|----------|
| AI-060 | Prompt templates | Versioned in Git |
| AI-061 | Few-shot examples | Minimum 3 examples per task |
| AI-062 | Output format | Structured JSON output |
| AI-063 | Safety filters | Content policy enforcement |

---

## 5. INTEGRATION REQUIREMENTS

### 5.1 External Systems

| ID | System | Integration Type | SLA |
|----|--------|------------------|-----|
| INT-001 | SLIK OJK (Credit Bureau) | REST API | < 5s response |
| INT-002 | Core Banking System | SOAP/REST | Real-time |
| INT-003 | Document Management (DMS) | REST API | < 2s upload |
| INT-004 | Email/SMS Gateway | SMTP/HTTP | Best effort |
| INT-005 | Payment Gateway | Webhook | < 3s |

### 5.2 Data Formats

| ID | Format | Use Case |
|----|--------|----------|
| INT-010 | JSON | API request/response |
| INT-011 | PDF | Document upload/download |
| INT-012 | CSV | Batch import/export |
| INT-013 | Parquet | Data lake storage |
| INT-014 | Protobuf | Inter-service communication |

---

## 6. TESTING REQUIREMENTS

### 6.1 Test Coverage

| ID | Test Type | Target Coverage |
|----|-----------|-----------------|
| TST-001 | Unit tests | ≥ 80% |
| TST-002 | Integration tests | ≥ 70% |
| TST-003 | API tests | 100% endpoints |
| TST-004 | Load tests | 2x expected load |
| TST-005 | Security tests | OWASP Top 10 |

### 6.2 Test Environments

| ID | Environment | Purpose |
|----|-------------|---------|
| TST-010 | Development | Developer testing |
| TST-011 | Staging | Pre-production validation |
| TST-012 | UAT | User acceptance testing |
| TST-013 | Production | Live system |

---

## APPENDIX A: Glossary

| Term | Definition |
|------|------------|
| **BPR** | Bank Perkreditan Rakyat (Rural Bank) |
| **POJK** | Peraturan Otoritas Jasa Keuangan (OJK Regulation) |
| **SLIK** | Sistem Layanan Informasi Keuangan (Financial Information Service System) |
| **NIK** | Nomor Induk Kependudukan (National ID Number) |
| **NPWP** | Nomor Pokok Wajib Pajak (Tax ID Number) |
| **PD** | Probability of Default |
| **LGD** | Loss Given Default |
| **EAD** | Exposure at Default |
| **XAI** | Explainable AI |
| **RAG** | Retrieval-Augmented Generation |

---

## APPENDIX B: Risk Matrix

| Risk ID | Risk Description | Likelihood | Impact | Mitigation |
|---------|------------------|------------|--------|------------|
| RISK-001 | LLM hallucination in credit decision | Medium | High | Hybrid rules + LLM with validation |
| RISK-002 | Data breach of applicant PII | Low | Critical | Encryption + access controls |
| RISK-003 | Model bias against demographics | Medium | High | Fairness testing + monitoring |
| RISK-004 | API downtime during peak hours | Low | High | Auto-scaling + circuit breakers |
| RISK-005 | Regulatory non-compliance | Low | Critical | Compliance checklist + audits |

---

**Document Control:**
- **Author:** AI/ML Engineering Team
- **Reviewers:** CTO, Risk Head, Compliance Officer
- **Approval:** Board of Directors
- **Next Review Date:** 2026-05-22

---

*END OF DOCUMENT*
