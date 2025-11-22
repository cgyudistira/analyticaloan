"""
Scoring Service - Main FastAPI Application
ML-based credit scoring with XAI explanations
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
from datetime import datetime

from libs.database.session import get_db
from libs.database.models import (
    LoanApplication, Applicant, ScoringResult, RiskRating
)
from app.credit_model import CreditScoringModel
from app.feature_engineering import FeatureEngineer
from app.xai_explainer import XAIExplainer

load_dotenv()

# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="AnalyticaLoan Scoring Service",
    description="ML-based Credit Scoring with XAI",
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
credit_model = CreditScoringModel()
feature_engineer = FeatureEngineer()
xai_explainer = XAIExplainer(credit_model)

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ScoreRequest(BaseModel):
    application_id: str
    applicant_data: Dict
    financial_data: Optional[Dict] = None
    credit_bureau_data: Optional[Dict] = None

class ScoreResponse(BaseModel):
    scoring_id: str
    application_id: str
    credit_score: int  # 0-1000
    probability_of_default: float  # 0.0-1.0
    risk_rating: str  # AAA, AA, A, BBB, BB, B, C, D
    model_version: str
    confidence: float
    scored_at: str

class ExplanationResponse(BaseModel):
    scoring_id: str
    feature_importances: Dict[str, float]
    shap_values: Dict[str, float]
    top_positive_factors: List[Dict]
    top_negative_factors: List[Dict]
    explanation_text: str

# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {
        "service": "AnalyticaLoan Scoring Service",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": credit_model.model is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_healthy = credit_model.model is not None
    
    return {
        "status": "healthy" if model_healthy else "degraded",
        "model_loaded": model_healthy,
        "model_version": credit_model.model_version if model_healthy else None
    }

@app.post("/score", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def score_application(
    request: ScoreRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate credit score for loan application
    
    Returns:
    - Credit score (0-1000)
    - Probability of default (0.0-1.0)
    - Risk rating (AAA to D)
    - Model confidence
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
    
    try:
        # Engineer features
        features = feature_engineer.create_features(
            applicant_data=request.applicant_data,
            financial_data=request.financial_data or {},
            credit_bureau_data=request.credit_bureau_data or {}
        )
        
        # Get prediction
        prediction = credit_model.predict(features)
        
        # Calculate credit score (0-1000 scale)
        # Lower PD = higher score
        credit_score = int((1 - prediction['probability_of_default']) * 1000)
        
        # Determine risk rating
        risk_rating = _calculate_risk_rating(credit_score)
        
        # Save scoring result
        scoring_result = ScoringResult(
            application_id=request.application_id,
            model_version=credit_model.model_version,
            credit_score=credit_score,
            probability_of_default=prediction['probability_of_default'],
            risk_rating=risk_rating,
            ml_score=prediction['probability_of_default'],
            llm_score=None,  # Set by underwriting service
            rule_score=None,  # Set by underwriting service
            final_score=prediction['probability_of_default'],
            explanation=prediction.get('feature_importances', {}),
            feature_importances=prediction.get('feature_importances', {}),
            scored_at=datetime.utcnow()
        )
        
        db.add(scoring_result)
        db.commit()
        db.refresh(scoring_result)
        
        return ScoreResponse(
            scoring_id=str(scoring_result.scoring_id),
            application_id=str(scoring_result.application_id),
            credit_score=credit_score,
            probability_of_default=prediction['probability_of_default'],
            risk_rating=risk_rating.value,
            model_version=credit_model.model_version,
            confidence=prediction.get('confidence', 0.85),
            scored_at=scoring_result.scored_at.isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring failed: {str(e)}"
        )

@app.get("/score/{scoring_id}/explain", response_model=ExplanationResponse)
async def explain_score(
    scoring_id: str,
    db: Session = Depends(get_db)
):
    """
    Get XAI explanation for credit score using SHAP
    
    Returns:
    - Feature importances
    - SHAP values
    - Top positive/negative factors
    - Natural language explanation
    """
    # Get scoring result
    scoring = db.query(ScoringResult).filter(
        ScoringResult.scoring_id == scoring_id
    ).first()
    
    if not scoring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scoring {scoring_id} not found"
        )
    
    # Get application data
    application = db.query(LoanApplication).join(Applicant).filter(
        LoanApplication.application_id == scoring.application_id
    ).first()
    
    # Recreate features
    applicant_data = {
        "monthly_income": float(application.applicant.monthly_income) if application.applicant.monthly_income else 0,
        "age": (datetime.now().year - application.applicant.date_of_birth.year) if application.applicant.date_of_birth else 0,
        "occupation": application.applicant.occupation or "",
        "loan_amount": float(application.loan_amount),
        "loan_term_months": application.loan_term_months,
    }
    
    features = feature_engineer.create_features(
        applicant_data=applicant_data,
        financial_data={},
        credit_bureau_data={}
    )
    
    # Generate SHAP explanation
    explanation = xai_explainer.explain(features)
    
    return ExplanationResponse(
        scoring_id=str(scoring_id),
        feature_importances=explanation['feature_importances'],
        shap_values=explanation['shap_values'],
        top_positive_factors=explanation['top_positive_factors'],
        top_negative_factors=explanation['top_negative_factors'],
        explanation_text=explanation['explanation_text']
    )

@app.get("/applications/{application_id}/score")
async def get_application_score(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Get latest scoring result for application"""
    scoring = db.query(ScoringResult).filter(
        ScoringResult.application_id == application_id
    ).order_by(ScoringResult.scored_at.desc()).first()
    
    if not scoring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scoring found for application {application_id}"
        )
    
    return {
        "scoring_id": str(scoring.scoring_id),
        "application_id": str(scoring.application_id),
        "credit_score": scoring.credit_score,
        "probability_of_default": float(scoring.probability_of_default),
        "risk_rating": scoring.risk_rating.value,
        "model_version": scoring.model_version,
        "scored_at": scoring.scored_at.isoformat()
    }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _calculate_risk_rating(credit_score: int) -> RiskRating:
    """Map credit score to risk rating"""
    if credit_score >= 850:
        return RiskRating.AAA
    elif credit_score >= 750:
        return RiskRating.AA
    elif credit_score >= 650:
        return RiskRating.A
    elif credit_score >= 550:
        return RiskRating.BBB
    elif credit_score >= 450:
        return RiskRating.BB
    elif credit_score >= 350:
        return RiskRating.B
    elif credit_score >= 250:
        return RiskRating.C
    else:
        return RiskRating.D

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("Scoring Service started successfully")
    print(f"Model loaded: {credit_model.model is not None}")
    print(f"Model version: {credit_model.model_version}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("Scoring Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=True)
