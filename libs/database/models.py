"""
Database models for AnalyticaLoan
SQLAlchemy ORM models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, 
    Numeric, String, Text, DECIMAL, BigInteger, Date, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()

# =============================================================================
# ENUMS
# =============================================================================

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    UNDERWRITER = "UNDERWRITER"
    RISK_ANALYST = "RISK_ANALYST"
    OPS = "OPS"
    VIEWER = "VIEWER"

class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class MaritalStatus(str, enum.Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"

class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    UNDERWRITING = "UNDERWRITING"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class DocumentType(str, enum.Enum):
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    BANK_STATEMENT = "BANK_STATEMENT"
    TAX_RETURN = "TAX_RETURN"
    SALARY_SLIP = "SALARY_SLIP"
    BUSINESS_LICENSE = "BUSINESS_LICENSE"
    ID_CARD = "ID_CARD"
    OTHER = "OTHER"

class OCRStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RiskRating(str, enum.Enum):
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    C = "C"
    D = "D"

class DecisionStatus(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    PENDING = "PENDING"

# =============================================================================
# MODELS
# =============================================================================

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))

    # Relationships
    loan_applications = relationship("LoanApplication", back_populates="assigned_user")
    audit_logs = relationship("AuditTrail", back_populates="user")


class Applicant(Base):
    __tablename__ = "applicants"

    applicant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nik = Column(String(16), unique=True, nullable=False, index=True)  # Encrypted
    npwp = Column(String(20))  # Encrypted
    full_name = Column(String(255), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender))
    marital_status = Column(Enum(MaritalStatus))
    education = Column(String(50))
    occupation = Column(String(100))
    monthly_income = Column(DECIMAL(15, 2))
    phone_number = Column(String(20))
    email = Column(String(255))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(10))
    country = Column(String(50), default="Indonesia")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    loan_applications = relationship("LoanApplication", back_populates="applicant")
    credit_bureau_data = relationship("CreditBureauData", back_populates="applicant")


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.applicant_id"), nullable=False)
    loan_product = Column(String(100), nullable=False)
    loan_amount = Column(DECIMAL(15, 2), nullable=False)
    loan_term_months = Column(Integer, nullable=False)
    interest_rate = Column(DECIMAL(5, 2))
    purpose = Column(Text)
    application_channel = Column(String(50))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applicant = relationship("Applicant", back_populates="loan_applications")
    assigned_user = relationship("User", back_populates="loan_applications")
    documents = relationship("FinancialDocument", back_populates="application")
    metrics = relationship("ExtractedMetric", back_populates="application")
    scoring_results = relationship("ScoringResult", back_populates="application")
    decision_logs = relationship("DecisionLog", back_populates="application")
    workflow_states = relationship("WorkflowState", back_populates="application")


class FinancialDocument(Base):
    __tablename__ = "financial_documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.application_id", ondelete="CASCADE"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # S3/GCS path
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))
    upload_channel = Column(String(50))
    ocr_status = Column(Enum(OCRStatus), default=OCRStatus.PENDING)
    ocr_confidence = Column(DECIMAL(5, 2))  # 0-100
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    application = relationship("LoanApplication", back_populates="documents")
    extracted_metrics = relationship("ExtractedMetric", back_populates="document")


class ExtractedMetric(Base):
    __tablename__ = "extracted_metrics"

    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("financial_documents.document_id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.application_id"), nullable=False)
    metric_type = Column(String(100), nullable=False)
    metric_data = Column(JSONB, nullable=False)  # Flexible JSON storage
    extraction_method = Column(String(50))  # OCR, MANUAL, API, PARSER
    confidence_score = Column(DECIMAL(5, 2))
    extracted_at = Column(DateTime, default=datetime.utcnow)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    verified_at = Column(DateTime)

    # Relationships
    document = relationship("FinancialDocument", back_populates="extracted_metrics")
    application = relationship("LoanApplication", back_populates="metrics")


class ScoringResult(Base):
    __tablename__ = "scoring_results"

    scoring_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.application_id"), nullable=False)
    model_version = Column(String(50), nullable=False)
    credit_score = Column(Integer, nullable=False)  # 0-1000
    probability_of_default = Column(DECIMAL(5, 4))  # 0.0000-1.0000
    risk_rating = Column(Enum(RiskRating))
    ml_score = Column(DECIMAL(5, 4))
    llm_score = Column(DECIMAL(5, 4))
    rule_score = Column(DECIMAL(5, 4))
    final_score = Column(DECIMAL(5, 4))
    explanation = Column(JSONB)  # XAI explanation
    feature_importances = Column(JSONB)
    scored_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("LoanApplication", back_populates="scoring_results")
    decision_logs = relationship("DecisionLog", back_populates="scoring_result")


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.application_id"), nullable=False)
    scoring_id = Column(UUID(as_uuid=True), ForeignKey("scoring_results.scoring_id"))
    decision_status = Column(Enum(DecisionStatus), nullable=False)
    decision_reason = Column(Text)
    decision_maker = Column(String(50))  # AUTO, UNDERWRITER, COMMITTEE
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    ml_contribution = Column(DECIMAL(5, 4))
    llm_contribution = Column(DECIMAL(5, 4))
    rule_contribution = Column(DECIMAL(5, 4))
    policy_violations = Column(JSONB)
    override_reason = Column(Text)
    credit_memo_path = Column(String(500))  # S3 path
    decided_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("LoanApplication", back_populates="decision_logs")
    scoring_result = relationship("ScoringResult", back_populates="decision_logs")


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.application_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False, index=True)
    model_type = Column(String(50))
    model_path = Column(String(500))  # MLflow path
    training_data_version = Column(String(50))
    performance_metrics = Column(JSONB)
    feature_list = Column(JSONB)
    is_active = Column(Boolean, default=False, index=True)
    trained_at = Column(DateTime)
    deployed_at = Column(DateTime)
    retired_at = Column(DateTime)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Blacklist(Base):
    __tablename__ = "blacklist"

    blacklist_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier_type = Column(String(50), nullable=False)  # NIK, NPWP, PHONE, EMAIL
    identifier_value = Column(String(255), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    added_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)


class CreditBureauData(Base):
    __tablename__ = "credit_bureau_data"

    bureau_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.applicant_id"), nullable=False)
    bureau_source = Column(String(50), default="SLIK_OJK")
    nik = Column(String(16), nullable=False, index=True)
    credit_score = Column(Integer)
    total_accounts = Column(Integer)
    active_accounts = Column(Integer)
    delinquent_accounts = Column(Integer)
    total_debt = Column(DECIMAL(15, 2))
    payment_history = Column(JSONB)
    inquiries_last_6m = Column(Integer)
    raw_response = Column(JSONB)
    fetched_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)

    # Relationships
    applicant = relationship("Applicant", back_populates="credit_bureau_data")


class WorkflowState(Base):
    __tablename__ = "workflow_state"

    workflow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.application_id"), nullable=False)
    workflow_name = Column(String(100), nullable=False)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer)
    step_status = Column(String(50))  # PENDING, RUNNING, COMPLETED, FAILED, RETRY
    state_data = Column(JSONB)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = relationship("LoanApplication", back_populates="workflow_states")
