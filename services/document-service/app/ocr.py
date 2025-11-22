"""
OCR Service - Google Cloud Vision API integration
Extracts text from documents (PDF, images)
"""
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import io

load_dotenv()

class OCRResult(BaseModel):
    """OCR processing result"""
    text: str
    confidence: float
    pages: int
    language: str = "id"  # Indonesian


class OCRService:
    """
    OCR Service using Google Cloud Vision API
    Falls back to Tesseract for local development
    """
    
    def __init__(self):
        self.use_google_vision = os.getenv("GCP_VISION_ENABLED", "true").lower() == "true"
        
        if self.use_google_vision:
            try:
                from google.cloud import vision
                self.vision_client = vision.ImageAnnotatorClient()
                self.provider = "google_vision"
            except Exception as e:
                print(f"Warning: Google Vision not available, falling back to Tesseract: {e}")
                self.use_google_vision = False
                self.provider = "tesseract"
        else:
            self.provider = "tesseract"
            # Tesseract will be imported when needed
    
    async def extract_text(
        self, 
        file_content: bytes, 
        mime_type: str = "application/pdf"
    ) -> OCRResult:
        """
        Extract text from document using OCR
        
        Args:
            file_content: Document bytes
            mime_type: MIME type (application/pdf or image/*)
        
        Returns:
            OCRResult with extracted text and metadata
        """
        if self.use_google_vision:
            return await self._extract_with_google_vision(file_content, mime_type)
        else:
            return await self._extract_with_tesseract(file_content, mime_type)
    
    async def _extract_with_google_vision(
        self, 
        file_content: bytes, 
        mime_type: str
    ) -> OCRResult:
        """Extract text using Google Cloud Vision API"""
        from google.cloud import vision
        
        # For PDF files
        if mime_type == "application/pdf":
            # Use async batch annotation for PDFs
            input_config = vision.InputConfig(
                content=file_content,
                mime_type='application/pdf'
            )
            
            features = [vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
            
            request = vision.AnnotateFileRequest(
                input_config=input_config,
                features=features,
            )
            
            response = self.vision_client.batch_annotate_files(requests=[request])
            
            # Extract text from all pages
            full_text = ""
            total_confidence = 0.0
            pages = 0
            
            for page_response in response.responses[0].responses:
                if page_response.full_text_annotation:
                    full_text += page_response.full_text_annotation.text + "\n\n"
                    # Calculate confidence (average of page confidences)
                    if page_response.full_text_annotation.pages:
                        for page in page_response.full_text_annotation.pages:
                            total_confidence += page.confidence if hasattr(page, 'confidence') else 0.9
                            pages += 1
            
            avg_confidence = (total_confidence / pages) if pages > 0 else 0.9
            
            return OCRResult(
                text=full_text.strip(),
                confidence=round(avg_confidence * 100, 2),  # Convert to percentage
                pages=pages,
                language="id"
            )
        
        else:
            # For images
            image = vision.Image(content=file_content)
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            # Extract text
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            # Calculate confidence
            confidence = 0.9  # Default
            if response.full_text_annotation and response.full_text_annotation.pages:
                page_confidences = [
                    page.confidence if hasattr(page, 'confidence') else 0.9
                    for page in response.full_text_annotation.pages
                ]
                confidence = sum(page_confidences) / len(page_confidences) if page_confidences else 0.9
            
            return OCRResult(
                text=full_text.strip(),
                confidence=round(confidence * 100, 2),
                pages=1,
                language="id"
            )
    
    async def _extract_with_tesseract(
        self, 
        file_content: bytes, 
        mime_type: str
    ) -> OCRResult:
        """Extract text using Tesseract OCR (fallback for local dev)"""
        try:
            import pytesseract
            from PIL import Image
            from pdf2image import convert_from_bytes
        except ImportError:
            raise Exception(
                "Tesseract dependencies not installed. "
                "Install with: pip install pytesseract pdf2image pillow"
            )
        
        # For PDF files
        if mime_type == "application/pdf":
            # Convert PDF to images
            images = convert_from_bytes(file_content)
            
            full_text = ""
            total_confidence = 0.0
            
            for i, image in enumerate(images):
                # Extract text with confidence data
                ocr_data = pytesseract.image_to_data(
                    image, 
                    lang='ind+eng',  # Indonesian + English
                    output_type=pytesseract.Output.DICT
                )
                
                # Get text
                page_text = pytesseract.image_to_string(image, lang='ind+eng')
                full_text += page_text + "\n\n"
                
                # Calculate average confidence for this page
                confidences = [
                    int(conf) for conf in ocr_data['conf'] 
                    if conf != '-1'  # -1 means no confidence
                ]
                if confidences:
                    total_confidence += sum(confidences) / len(confidences)
            
            avg_confidence = total_confidence / len(images) if images else 0
            
            return OCRResult(
                text=full_text.strip(),
                confidence=round(avg_confidence, 2),
                pages=len(images),
                language="id"
            )
        
        else:
            # For images
            image = Image.open(io.BytesIO(file_content))
            
            # Extract text with confidence
            ocr_data = pytesseract.image_to_data(
                image,
                lang='ind+eng',
                output_type=pytesseract.Output.DICT
            )
            
            text = pytesseract.image_to_string(image, lang='ind+eng')
            
            # Calculate confidence
            confidences = [
                int(conf) for conf in ocr_data['conf']
                if conf != '-1'
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=text.strip(),
                confidence=round(avg_confidence, 2),
                pages=1,
                language="id"
            )
    
    async def extract_tables(
        self, 
        file_content: bytes
    ) -> list:
        """
        Extract tables from document
        (Placeholder for future implementation with LayoutLM)
        """
        # TODO: Implement table extraction using LayoutLM or similar
        return []
