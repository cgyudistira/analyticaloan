"""
Underwriting Service - Main FastAPI Application
AI-powered credit underwriting orchestration
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

from libs.database.session import get_db
from libs.database.models import (
    LoanApplication, ApplicationStatus, ScoringResult,
    DecisionLog, DecisionStatus, WorkflowState
)
from app.agent import UnderwritingAgent
from app.gemini_client import GeminiClient

load_dotenv()

# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="AnalyticaLoan Underwriting Service",
    description="AI Agent for Credit Underwriting",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances
gemini_client = GeminiClient()
underwriting_agent = UnderwritingAgent(gemini_client=gemini_client)

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class UnderwriteRequest(BaseModel):
    application_id: str
    auto_approve_threshold: Optional[float] = 0.7
    auto_reject_threshold: Optional[float] = 0.4

class UnderwriteResponse(BaseModel):
    workflow_id: str
    application_id: str
    status: str
    message: str

class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    application_id: str
    status: str
    current_step: int
    total_steps: int
    progress_percentage: float
    started_at: str
    completed_at: Optional[str]
    error_message: Optional[str]

class DecisionResponse(BaseModel):
    decision_id: str
    application_id: str
    decision_status: str
    decision_reason: str
    credit_score: Optional[int]
    probability_of_default: Optional[float]
    risk_rating: Optional[str]
    decided_at: str

# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {
        "service": "AnalyticaLoan Underwriting Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Gemini API connectivity
    gemini_healthy = await gemini_client.health_check()
    
    return {
        "status": "healthy" if gemini_healthy else "degraded",
        "gemini_api": "connected" if gemini_healthy else "disconnected"
    }

@app.post("/underwrite", response_model=UnderwriteResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_underwriting(
    request: UnderwriteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start AI underwriting process for a loan application
    
    This will:
    1. Validate application and documents
    2. Extract data via OCR
    3. Fetch credit bureau data
    4. Run ML scoring models
    5. Execute LLM reasoning
    6. Check policy compliance (RAG)
    7. Make final decision
    8. Generate credit memo
    """
    # Validate application exists
    application = db.query(LoanApplication).filter(
        LoanApplication.application_id == request.application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {request.application_id} not found"
        )
    
    # Check if already being processed
    existing_workflow = db.query(WorkflowState).filter(
        WorkflowState.application_id == request.application_id,
        WorkflowState.step_status.in_(["PENDING", "RUNNING"])
    ).first()
    
    if existing_workflow:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Application is already being processed (workflow: {existing_workflow.workflow_id})"
        )
    
    # Create workflow state
    workflow_id = uuid.uuid4()
    workflow = WorkflowState(
        workflow_id=workflow_id,
        application_id=request.application_id,
        workflow_name="ai_underwriting",
        current_step=0,
        total_steps=8,
        step_status="PENDING",
        state_data={
            "auto_approve_threshold": request.auto_approve_threshold,
            "auto_reject_threshold": request.auto_reject_threshold
        },
        started_at=datetime.utcnow()
    )
    
    db.add(workflow)
    
    # Update application status
    application.status = ApplicationStatus.UNDERWRITING
    
    db.commit()
    db.refresh(workflow)
    
    # Start async underwriting process
    background_tasks.add_task(
        underwriting_agent.process_application,
        application_id=str(request.application_id),
        workflow_id=str(workflow_id),
        auto_approve_threshold=request.auto_approve_threshold,
        auto_reject_threshold=request.auto_reject_threshold
    )
    
    return UnderwriteResponse(
        workflow_id=str(workflow_id),
        application_id=str(request.application_id),
        status="STARTED",
        message="Underwriting process initiated"
    )

@app.get("/underwrite/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get status of underwriting workflow"""
    workflow = db.query(WorkflowState).filter(
        WorkflowState.workflow_id == workflow_id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    progress = (workflow.current_step / workflow.total_steps * 100) if workflow.total_steps > 0 else 0
    
    return WorkflowStatusResponse(
        workflow_id=str(workflow.workflow_id),
        application_id=str(workflow.application_id),
        status=workflow.step_status,
        current_step=workflow.current_step,
        total_steps=workflow.total_steps,
        progress_percentage=round(progress, 2),
        started_at=workflow.started_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        error_message=workflow.error_message
    )

@app.get("/applications/{application_id}/decision", response_model=DecisionResponse)
async def get_decision(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get underwriting decision for application"""
    decision = db.query(DecisionLog).filter(
        DecisionLog.application_id == application_id
    ).order_by(DecisionLog.decided_at.desc()).first()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No decision found for application {application_id}"
        )
    
    # Get scoring result
    scoring = db.query(ScoringResult).filter(
        ScoringResult.scoring_id == decision.scoring_id
    ).first()
    
    return DecisionResponse(
        decision_id=str(decision.decision_id),
        application_id=str(decision.application_id),
        decision_status=decision.decision_status.value,
        decision_reason=decision.decision_reason or "",
        credit_score=scoring.credit_score if scoring else None,
        probability_of_default=float(scoring.probability_of_default) if scoring and scoring.probability_of_default else None,
        risk_rating=scoring.risk_rating.value if scoring and scoring.risk_rating else None,
        decided_at=decision.decided_at.isoformat()
    )

@app.post("/applications/{application_id}/override")
async def override_decision(
    application_id: str,
    new_decision: str,
    override_reason: str,
    db: Session = Depends(get_db)
):
    """
    Manual override of AI decision (human-in-the-loop)
    Only for MANUAL_REVIEW cases
    """
    # Validate application
    application = db.query(LoanApplication).filter(
        LoanApplication.application_id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    if application.status != ApplicationStatus.MANUAL_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application is not in manual review status"
        )
    
    # Validate new decision
    try:
        decision_status = DecisionStatus[new_decision]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision: {new_decision}"
        )
    
    # Create override decision log
    decision = DecisionLog(
        decision_id=uuid.uuid4(),
        application_id=application_id,
        decision_status=decision_status,
        decision_reason=f"Manual override: {override_reason}",
        decision_maker="UNDERWRITER",
        override_reason=override_reason,
        decided_at=datetime.utcnow()
    )
    
    db.add(decision)
    
    # Update application status
    if decision_status == DecisionStatus.APPROVE:
        application.status = ApplicationStatus.APPROVED
        application.approved_at = datetime.utcnow()
    elif decision_status == DecisionStatus.REJECT:
        application.status = ApplicationStatus.REJECTED
        application.rejected_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Decision overridden successfully",
        "decision_id": str(decision.decision_id)
    }

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("Underwriting Service started successfully")
    print(f"Gemini API configured: {gemini_client.api_key is not None}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("Underwriting Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004, reload=True)
