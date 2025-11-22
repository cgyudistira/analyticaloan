"""
AI Agent Orchestrator
Coordinates the entire underwriting workflow
"""
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json

from libs.database.session import SessionLocal
from libs.database.models import (
    WorkflowState, LoanApplication, Applicant,
    FinancialDocument, ExtractedMetric, ScoringResult,
    DecisionLog, DecisionStatus, RiskRating,
    ApplicationStatus
)
from app.gemini_client import GeminiClient
from app.rag_engine import RAGPolicyEngine


class UnderwritingAgent:
    """
    Main AI agent for credit underwriting
    Orchestrates entire process from document extraction to final decision
    """
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.rag_engine = RAGPolicyEngine()
        
        # Workflow steps
        self.total_steps = 8
    
    async def process_application(
        self,
        application_id: str,
        workflow_id: str,
        auto_approve_threshold: float = 0.7,
        auto_reject_threshold: float = 0.4
    ) -> None:
        """
        Main workflow executor
        
        Steps:
        1. Document validation
        2. Data extraction (OCR)
        3. Credit bureau fetch
        4. ML scoring
        5. LLM reasoning
        6. Policy compliance (RAG)
        7. Decision fusion
        8. Credit memo generation
        """
        db = SessionLocal()
        
        try:
            # Get workflow state
            workflow = db.query(WorkflowState).filter(
                WorkflowState.workflow_id == workflow_id
            ).first()
            
            if not workflow:
                print(f"Workflow {workflow_id} not found")
                return
            
            # Step 1: Validate documents
            await self._update_workflow(db, workflow, 1, "RUNNING")
            documents_valid = await self._validate_documents(db, application_id)
            
            if not documents_valid:
                await self._fail_workflow(db, workflow, "Insufficient documents")
                return
            
            # Step 2: Extract data from documents
            await self._update_workflow(db, workflow, 2, "RUNNING")
            extracted_data = await self._extract_document_data(db, application_id)
            
            # Step 3: Fetch credit bureau data (simulated for now)
            await self._update_workflow(db, workflow, 3, "RUNNING")
            credit_bureau_data = await self._fetch_credit_bureau(db, application_id)
            
            # Step 4: ML Scoring (placeholder - actual ML in Phase 5)
            await self._update_workflow(db, workflow, 4, "RUNNING")
            ml_score = await self._calculate_ml_score(db, application_id, extracted_data)
            
            # Step 5: LLM Reasoning with Gemini
            await self._update_workflow(db, workflow, 5, "RUNNING")
            llm_analysis = await self._llm_reasoning(
                db, application_id, extracted_data, credit_bureau_data
            )
            
            # Step 6: Policy compliance check with RAG
            await self._update_workflow(db, workflow, 6, "RUNNING")
            policy_check = await self._check_policy_compliance(
                db, application_id, extracted_data
            )
            
            # Step 7: Decision fusion
            await self._update_workflow(db, workflow, 7, "RUNNING")
            final_decision = await self._make_final_decision(
                db, application_id, ml_score, llm_analysis, policy_check,
                auto_approve_threshold, auto_reject_threshold
            )
            
            # Step 8: Generate credit memo
            await self._update_workflow(db, workflow, 8, "RUNNING")
            await self._generate_credit_memo(
                db, application_id, llm_analysis, final_decision
            )
            
            # Complete workflow
            workflow.step_status = "COMPLETED"
            workflow.completed_at = datetime.utcnow()
            workflow.current_step = self.total_steps
            db.commit()
            
            print(f"✓ Workflow {workflow_id} completed successfully")
        
        except Exception as e:
            print(f"✗ Workflow {workflow_id} failed: {str(e)}")
            if workflow:
                await self._fail_workflow(db, workflow, str(e))
        
        finally:
            db.close()
    
    async def _update_workflow(
        self, 
        db: Session, 
        workflow: WorkflowState, 
        step: int,
        status: str
    ):
        """Update workflow progress"""
        workflow.current_step = step
        workflow.step_status = status
        workflow.updated_at = datetime.utcnow()
        db.commit()
    
    async def _fail_workflow(
        self, 
        db: Session, 
        workflow: WorkflowState,
        error_message: str
    ):
        """Mark workflow as failed"""
        workflow.step_status = "FAILED"
        workflow.error_message = error_message
        workflow.completed_at = datetime.utcnow()
        db.commit()
    
    async def _validate_documents(
        self, 
        db: Session, 
        application_id: str
    ) -> bool:
        """Check if required documents are uploaded"""
        documents = db.query(FinancialDocument).filter(
            FinancialDocument.application_id == application_id
        ).all()
        
        # Minimum: 1 financial statement OR bank statement
        has_financial = any(
            d.document_type.value in ['INCOME_STATEMENT', 'BALANCE_SHEET', 'BANK_STATEMENT']
            for d in documents
        )
        
        return has_financial
    
    async def _extract_document_data(
        self,
        db: Session,
        application_id: str
    ) -> Dict:
        """Get all extracted metrics from documents"""
        metrics = db.query(ExtractedMetric).filter(
            ExtractedMetric.application_id == application_id
        ).all()
        
        # Aggregate all metrics
        financial_data = {}
        
        for metric in metrics:
            if metric.metric_data:
                financial_data.update(metric.metric_data)
        
        return financial_data
    
    async def _fetch_credit_bureau(
        self,
        db: Session,
        application_id: str
    ) -> Optional[Dict]:
        """Fetch credit bureau data from SLIK OJK"""
        # TODO: Implement actual SLIK OJK API integration
        # For now, return simulated data
        
        application = db.query(LoanApplication).filter(
            LoanApplication.application_id == application_id
        ).first()
        
        if not application:
            return None
        
        # Simulated credit bureau data
        return {
            "credit_score": 650,
            "total_accounts": 3,
            "active_accounts": 2,
            "delinquent_accounts": 0,
            "total_debt": 50000000,  # Rp 50 million
            "inquiries_last_6m": 1
        }
    
    async def _calculate_ml_score(
        self,
        db: Session,
        application_id: str,
        extracted_data: Dict
    ) -> float:
        """Calculate ML-based credit score"""
        # TODO: Implement actual ML model in Phase 5
        # For now, return simulated score based on simple heuristics
        
        application = db.query(LoanApplication).join(Applicant).filter(
            LoanApplication.application_id == application_id
        ).first()
        
        if not application:
            return 0.5
        
        # Simple heuristic score (0-1)
        score = 0.5
        
        # Adjust based on income
        if application.applicant.monthly_income:
            if application.applicant.monthly_income > 10000000:  # > Rp 10M
                score += 0.2
            elif application.applicant.monthly_income > 5000000:  # > Rp 5M
                score += 0.1
        
        # Adjust based on loan amount
        if application.loan_amount and application.applicant.monthly_income:
            dti = float(application.loan_amount / (application.applicant.monthly_income * application.loan_term_months))
            if dti < 0.3:
                score += 0.2
            elif dti < 0.5:
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    async def _llm_reasoning(
        self,
        db: Session,
        application_id: str,
        extracted_data: Dict,
        credit_bureau_data: Optional[Dict]
    ) -> Dict:
        """Use Gemini for qualitative analysis"""
        application = db.query(LoanApplication).join(Applicant).filter(
            LoanApplication.application_id == application_id
        ).first()
        
        if not application:
            return {"success": False, "error": "Application not found"}
        
        # Prepare applicant data
        applicant_data = {
            "full_name": application.applicant.full_name,
            "age": (datetime.now().year - application.applicant.date_of_birth.year) if application.applicant.date_of_birth else None,
            "occupation": application.applicant.occupation,
            "monthly_income": float(application.applicant.monthly_income) if application.applicant.monthly_income else 0,
            "loan_amount": float(application.loan_amount),
            "loan_term_months": application.loan_term_months,
            "purpose": application.purpose
        }
        
        # Call Gemini for analysis
        analysis = await self.gemini_client.analyze_credit_worthiness(
            applicant_data=applicant_data,
            financial_metrics=extracted_data,
            credit_bureau_data=credit_bureau_data,
            bank_statement_metrics=None  # TODO: Add when available
        )
        
        return analysis
    
    async def _check_policy_compliance(
        self,
        db: Session,
        application_id: str,
        extracted_data: Dict
    ) -> Dict:
        """Check compliance with POJK policies using RAG"""
        application = db.query(LoanApplication).join(Applicant).filter(
            LoanApplication.application_id == application_id
        ).first()
        
        if not application:
            return {"compliant": False, "violations": ["Application not found"]}
        
        # Query policies via RAG
        query = f"""
        Check compliance for:
        - Loan amount: Rp {application.loan_amount:,.0f}
        - Loan term: {application.loan_term_months} months
        - Borrower monthly income: Rp {application.applicant.monthly_income:,.0f}
        - Purpose: {application.purpose}
        """
        
        policy_results = await self.rag_engine.query_policies(query)
        
        # Check for violations
        violations = []
        
        # Age limits (example)
        if application.applicant.date_of_birth:
            age = datetime.now().year - application.applicant.date_of_birth.year
            if age < 21 or age > 65:
                violations.append(f"Age {age} outside acceptable range (21-65)")
        
        # Debt-to-income ratio
        if application.applicant.monthly_income and application.loan_amount:
            monthly_payment = application.loan_amount / application.loan_term_months
            dti = monthly_payment / float(application.applicant.monthly_income)
            if dti > 0.4:  # 40% max DTI
                violations.append(f"DTI ratio {dti:.1%} exceeds 40% limit")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "policy_references": policy_results.get("documents", [])
        }
    
    async def _make_final_decision(
        self,
        db: Session,
        application_id: str,
        ml_score: float,
        llm_analysis: Dict,
        policy_check: Dict,
        auto_approve_threshold: float,
        auto_reject_threshold: float
    ) -> DecisionStatus:
        """
        Fuse all signals into final decision
        
        Decision logic:
        - If policy violations -> REJECT
        - If ML score >= auto_approve_threshold AND no violations -> APPROVE
        - If ML score < auto_reject_threshold -> REJECT
        - Otherwise -> MANUAL_REVIEW
        """
        # Policy violations always result in rejection
        if not policy_check.get("compliant", False):
            decision = DecisionStatus.REJECT
            reason = "Policy violations: " + ", ".join(policy_check.get("violations", []))
        
        # High score -> auto approve
        elif ml_score >= auto_approve_threshold:
            decision = DecisionStatus.APPROVE
            reason = f"Auto-approved: ML score {ml_score:.2f} >= {auto_approve_threshold}"
        
        # Low score -> auto reject
        elif ml_score < auto_reject_threshold:
            decision = DecisionStatus.REJECT
            reason = f"Auto-rejected: ML score {ml_score:.2f} < {auto_reject_threshold}"
        
        # Borderline -> manual review
        else:
            decision = DecisionStatus.MANUAL_REVIEW
            reason = f"Manual review required: ML score {ml_score:.2f} in borderline range"
        
        # Create decision log
        decision_log = DecisionLog(
            application_id=application_id,
            decision_status=decision,
            decision_reason=reason,
            decision_maker="AUTO",
            ml_contribution=ml_score,
            llm_contribution=0.0,  # Placeholder
            rule_contribution=1.0 if policy_check.get("compliant") else 0.0,
            policy_violations=policy_check.get("violations"),
            decided_at=datetime.utcnow()
        )
        
        db.add(decision_log)
        
        # Update application status
        application = db.query(LoanApplication).filter(
            LoanApplication.application_id == application_id
        ).first()
        
        if decision == DecisionStatus.APPROVE:
            application.status = ApplicationStatus.APPROVED
            application.approved_at = datetime.utcnow()
        elif decision == DecisionStatus.REJECT:
            application.status = ApplicationStatus.REJECTED
            application.rejected_at = datetime.utcnow()
        else:
            application.status = ApplicationStatus.MANUAL_REVIEW
        
        db.commit()
        
        return decision
    
    async def _generate_credit_memo(
        self,
        db: Session,
        application_id: str,
        llm_analysis: Dict,
        decision: DecisionStatus
    ) -> None:
        """Generate credit memorandum"""
        application = db.query(LoanApplication).join(Applicant).filter(
            LoanApplication.application_id == application_id
        ).first()
        
        if not application:
            return
        
        # Prepare applicant data
        applicant_data = {
            "full_name": application.applicant.full_name,
            "loan_amount": float(application.loan_amount),
            "loan_term_months": application.loan_term_months,
            "purpose": application.purpose
        }
        
        # Get scoring data (placeholder)
        scoring_data = {
            "credit_score": 650,
            "probability_of_default": 15.5,
            "risk_rating": "BBB"
        }
        
        # Generate memo with Gemini
        memo_content = await self.gemini_client.generate_credit_memo(
            applicant_data=applicant_data,
            analysis_result=llm_analysis,
            decision=decision.value,
            scoring_data=scoring_data
        )
        
        # Save memo (in production, save to S3/GCS)
        print(f"Credit Memo generated for application {application_id}")
        print(f"Length: {len(memo_content)} characters")
        
        # TODO: Save to storage and update DecisionLog with credit_memo_path
