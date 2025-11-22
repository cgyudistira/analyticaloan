"""
Document Service - Main FastAPI Application
Handles document upload, storage, OCR processing, and parsing
"""
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

from libs.database.session import get_db
from libs.database.models import FinancialDocument, LoanApplication, DocumentType, OCRStatus
from app.storage import StorageService
from app.ocr import OCRService

load_dotenv()

# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="AnalyticaLoan Document Service",
    description="Document Upload, OCR, and Parsing Service",
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
storage_service = StorageService()
ocr_service = OCRService()

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class DocumentUploadResponse(BaseModel):
    document_id: str
    application_id: str
    document_type: str
    file_name: str
    file_size_bytes: int
    storage_path: str
    ocr_status: str
    uploaded_at: str
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    document_id: str
    application_id: str
    document_type: str
    file_name: str
    file_size_bytes: int
    ocr_status: str
    ocr_confidence: Optional[float]
    uploaded_at: str
    processed_at: Optional[str]
    
    class Config:
        from_attributes = True

class OCRResultResponse(BaseModel):
    document_id: str
    text: str
    confidence: float
    pages: int
    processed_at: str

# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {
        "service": "AnalyticaLoan Document Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check storage connectivity
    storage_healthy = await storage_service.health_check()
    
    return {
        "status": "healthy" if storage_healthy else "degraded",
        "storage": "connected" if storage_healthy else "disconnected"
    }

@app.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload financial document
    
    Supported document types:
    - INCOME_STATEMENT
    - BALANCE_SHEET
    - CASH_FLOW
    - BANK_STATEMENT
    - TAX_RETURN
    - SALARY_SLIP
    - BUSINESS_LICENSE
    - ID_CARD
    """
    # Validate application exists
    application = db.query(LoanApplication).filter(
        LoanApplication.application_id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    # Validate document type
    try:
        doc_type = DocumentType[document_type]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type: {document_type}"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file size (max 10MB)
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Allowed file types
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed: {allowed_extensions}"
        )
    
    # Upload to storage
    storage_path = f"applications/{application_id}/documents/{uuid.uuid4()}{file_ext}"
    
    try:
        await storage_service.upload(
            file_content=file_content,
            storage_path=storage_path,
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Create database record
    document = FinancialDocument(
        document_id=uuid.uuid4(),
        application_id=application_id,
        document_type=doc_type,
        file_name=file.filename,
        file_path=storage_path,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        upload_channel="API",
        ocr_status=OCRStatus.PENDING,
        uploaded_at=datetime.utcnow()
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Trigger async OCR processing (background task)
    # In production, this would be sent to a message queue
    # For now, we'll just return the document
    
    return DocumentUploadResponse(
        document_id=str(document.document_id),
        application_id=str(document.application_id),
        document_type=document.document_type.value,
        file_name=document.file_name,
        file_size_bytes=document.file_size_bytes,
        storage_path=document.file_path,
        ocr_status=document.ocr_status.value,
        uploaded_at=document.uploaded_at.isoformat()
    )

@app.post("/documents/{document_id}/ocr", response_model=OCRResultResponse)
async def process_ocr(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Trigger OCR processing for uploaded document
    """
    # Get document
    document = db.query(FinancialDocument).filter(
        FinancialDocument.document_id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    # Check if already processed
    if document.ocr_status == OCRStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already processed"
        )
    
    # Update status to processing
    document.ocr_status = OCRStatus.PROCESSING
    db.commit()
    
    try:
        # Download file from storage
        file_content = await storage_service.download(document.file_path)
        
        # Process OCR
        ocr_result = await ocr_service.extract_text(
            file_content=file_content,
            mime_type=document.mime_type or "application/pdf"
        )
        
        # Update document
        document.ocr_status = OCRStatus.COMPLETED
        document.ocr_confidence = ocr_result.confidence
        document.processed_at = datetime.utcnow()
        db.commit()
        
        return OCRResultResponse(
            document_id=str(document.document_id),
            text=ocr_result.text,
            confidence=ocr_result.confidence,
            pages=ocr_result.pages,
            processed_at=document.processed_at.isoformat()
        )
    
    except Exception as e:
        # Mark as failed
        document.ocr_status = OCRStatus.FAILED
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get document details"""
    document = db.query(FinancialDocument).filter(
        FinancialDocument.document_id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    return DocumentResponse(
        document_id=str(document.document_id),
        application_id=str(document.application_id),
        document_type=document.document_type.value,
        file_name=document.file_name,
        file_size_bytes=document.file_size_bytes,
        ocr_status=document.ocr_status.value,
        ocr_confidence=float(document.ocr_confidence) if document.ocr_confidence else None,
        uploaded_at=document.uploaded_at.isoformat(),
        processed_at=document.processed_at.isoformat() if document.processed_at else None
    )

@app.get("/applications/{application_id}/documents", response_model=List[DocumentResponse])
async def list_application_documents(
    application_id: str,
    db: Session = Depends(get_db)
):
    """List all documents for an application"""
    documents = db.query(FinancialDocument).filter(
        FinancialDocument.application_id == application_id
    ).all()
    
    return [
        DocumentResponse(
            document_id=str(doc.document_id),
            application_id=str(doc.application_id),
            document_type=doc.document_type.value,
            file_name=doc.file_name,
            file_size_bytes=doc.file_size_bytes,
            ocr_status=doc.ocr_status.value,
            ocr_confidence=float(doc.ocr_confidence) if doc.ocr_confidence else None,
            uploaded_at=doc.uploaded_at.isoformat(),
            processed_at=doc.processed_at.isoformat() if doc.processed_at else None
        )
        for doc in documents
    ]

@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete document (soft delete)"""
    document = db.query(FinancialDocument).filter(
        FinancialDocument.document_id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    # Delete from storage
    try:
        await storage_service.delete(document.file_path)
    except Exception as e:
        print(f"Warning: Failed to delete from storage: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return None

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("Document Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("Document Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=True)
