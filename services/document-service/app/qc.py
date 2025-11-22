"""
Quality Control (QC) Module for OCR Results
Validates and scores OCR output quality
"""
from typing import Dict, List, Tuple
import re
from decimal import Decimal


class OCRQualityControl:
    """
    Quality control checks for OCR results
    
    Performs:
    - Confidence threshold checking
    - Text coherence validation
    - Expected field detection
    - Anomaly detection
    """
    
    def __init__(self):
        self.min_confidence = 60.0  # Minimum acceptable OCR confidence
        self.min_text_length = 50   # Minimum text length for valid document
    
    def validate_ocr_result(
        self,
        ocr_text: str,
        ocr_confidence: float,
        document_type: str
    ) -> Tuple[bool, List[str], float]:
        """
        Validate OCR result quality
        
        Args:
            ocr_text: Extracted text
            ocr_confidence: OCR confidence score (0-100)
            document_type: Type of document (INCOME_STATEMENT, BANK_STATEMENT, etc.)
        
        Returns:
            Tuple of (is_valid, error_messages, quality_score)
        """
        errors = []
        quality_score = 100.0
        
        # Check 1: Confidence threshold
        if ocr_confidence < self.min_confidence:
            errors.append(f"OCR confidence {ocr_confidence:.1f}% below threshold {self.min_confidence}%")
            quality_score -= 30
        
        # Check 2: Text length
        if len(ocr_text) < self.min_text_length:
            errors.append(f"Text too short ({len(ocr_text)} chars), may be incomplete")
            quality_score -= 25
        
        # Check 3: Document type specific checks
        type_errors = self._validate_document_type(ocr_text, document_type)
        errors.extend(type_errors)
        quality_score -= len(type_errors) * 10
        
        # Check 4: Text coherence
        coherence_score = self._check_text_coherence(ocr_text)
        if coherence_score < 0.5:
            errors.append(f"Low text coherence score ({coherence_score:.2f})")
            quality_score -= 15
        
        # Check 5: Garbage character detection
        garbage_ratio = self._detect_garbage_characters(ocr_text)
        if garbage_ratio > 0.15:
            errors.append(f"High garbage character ratio ({garbage_ratio:.1%})")
            quality_score -= 20
        
        # Clamp quality score
        quality_score = max(0, min(100, quality_score))
        
        is_valid = len(errors) == 0 and quality_score >= 50
        
        return is_valid, errors, quality_score
    
    def _validate_document_type(
        self,
        text: str,
        document_type: str
    ) -> List[str]:
        """Check if text contains expected keywords for document type"""
        errors = []
        text_lower = text.lower()
        
        # Define expected keywords per document type
        expected_keywords = {
            'INCOME_STATEMENT': ['pendapatan', 'revenue', 'laba', 'profit', 'beban', 'expense'],
            'BALANCE_SHEET': ['aset', 'asset', 'liabilitas', 'liability', 'ekuitas', 'equity'],
            'CASH_FLOW': ['arus kas', 'cash flow', 'operasi', 'investasi', 'pendanaan'],
            'BANK_STATEMENT': ['rekening', 'account', 'saldo', 'balance', 'transaksi', 'transaction'],
            'TAX_RETURN': ['pajak', 'tax', 'npwp', 'spt'],
            'SALARY_SLIP': ['gaji', 'salary', 'tunjangan', 'allowance', 'potongan', 'deduction'],
        }
        
        if document_type in expected_keywords:
            keywords = expected_keywords[document_type]
            found_keywords = [kw for kw in keywords if kw in text_lower]
            
            if len(found_keywords) == 0:
                errors.append(f"No expected keywords found for {document_type}")
            elif len(found_keywords) < 2:
                errors.append(f"Only {len(found_keywords)} expected keyword(s) found for {document_type}")
        
        return errors
    
    def _check_text_coherence(self, text: str) -> float:
        """
        Check if text appears coherent (not random gibberish)
        
        Returns score 0.0-1.0
        """
        if not text:
            return 0.0
        
        # Check 1: Word-like patterns (spaces between words)
        words = text.split()
        if len(words) < 5:
            return 0.3
        
        # Check 2: Average word length (Indonesian/English: 4-8 chars)
        avg_word_length = sum(len(w) for w in words) / len(words)
        if 3 <= avg_word_length <= 10:
            coherence = 0.7
        else:
            coherence = 0.4
        
        # Check 3: Sentence-like structures (periods, commas)
        sentence_markers = text.count('.') + text.count(',') + text.count(':')
        if sentence_markers >= len(words) / 20:  # At least one marker per 20 words
            coherence += 0.2
        
        # Check 4: Common Indonesian/English words
        common_words = ['dan', 'yang', 'di', 'ke', 'dari', 'untuk', 'the', 'is', 'of', 'and', 'to', 'in']
        common_word_count = sum(1 for word in words if word.lower() in common_words)
        if common_word_count >= len(words) * 0.05:  # At least 5% common words
            coherence += 0.1
        
        return min(1.0, coherence)
    
    def _detect_garbage_characters(self, text: str) -> float:
        """
        Detect ratio of garbage/nonsense characters
        
        Returns ratio 0.0-1.0
        """
        if not text:
            return 1.0
        
        # Count problematic characters
        garbage_chars = 0
        total_chars = len(text)
        
        for char in text:
            # Non-printable (except whitespace)
            if not char.isprintable() and not char.isspace():
                garbage_chars += 1
            # Random Unicode artifacts
            elif ord(char) > 1000 and not (0x0600 <= ord(char) <= 0x06FF):  # Allow Arabic if needed
                garbage_chars += 1
        
        return garbage_chars / total_chars if total_chars > 0 else 0.0
    
    def auto_correct_common_errors(self, text: str) -> str:
        """
        Auto-correct common OCR errors
        
        Common mistakes:
        - O/0 confusion
        - I/l/1 confusion
        - Rp/Bp confusion
        """
        corrections = text
        
        # Fix common currency errors
        corrections = re.sub(r'\bBp\s*(\d)', r'Rp \1', corrections)
        corrections = re.sub(r'\bRD\s*(\d)', r'Rp \1', corrections)
        
        # Fix common number formatting
        corrections = re.sub(r'(\d)\s+(\d{3})', r'\1.\2', corrections)  # Add thousand separators
        
        # Fix common word errors (Indonesian)
        word_corrections = {
            'Pendaoatan': 'Pendapatan',
            'Behan': 'Beban',
            'Laoa': 'Laba',
            'Ekuites': 'Ekuitas',
            'Liabllitas': 'Liabilitas',
        }
        
        for wrong, right in word_corrections.items():
            corrections = corrections.replace(wrong, right)
        
        return corrections
    
    def suggest_manual_review(
        self,
        quality_score: float,
        errors: List[str]
    ) -> bool:
        """
        Determine if document should be flagged for manual review
        
        Returns True if manual review recommended
        """
        # Low quality score
        if quality_score < 60:
            return True
        
        # Critical errors present
        critical_keywords = ['confidence', 'too short', 'no expected keywords']
        for error in errors:
            if any(kw in error.lower() for kw in critical_keywords):
                return True
        
        return False


class ErrorHandler:
    """Error handling and retry logic for document processing"""
    
    def __init__(self):
        self.max_retries = 3
        self.qc = OCRQualityControl()
    
    def handle_ocr_failure(
        self,
        error: Exception,
        document_id: str,
        retry_count: int = 0
    ) -> Dict:
        """
        Handle OCR processing failures
        
        Returns dict with error info and retry recommendation
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Categorize error
        if 'timeout' in error_message.lower():
            category = 'TIMEOUT'
            should_retry = retry_count < self.max_retries
            retry_strategy = 'EXPONENTIAL_BACKOFF'
        
        elif 'api' in error_message.lower() or 'quota' in error_message.lower():
            category = 'API_ERROR'
            should_retry = retry_count < 2
            retry_strategy = 'FALLBACK_TO_TESSERACT'
        
        elif 'invalid' in error_message.lower() or 'corrupt' in error_message.lower():
            category = 'INVALID_FILE'
            should_retry = False
            retry_strategy = 'MANUAL_REVIEW'
        
        else:
            category = 'UNKNOWN'
            should_retry = retry_count < 1
            retry_strategy = 'SINGLE_RETRY'
        
        return {
            'document_id': document_id,
            'error_type': error_type,
            'error_message': error_message,
            'category': category,
            'should_retry': should_retry,
            'retry_count': retry_count,
            'retry_strategy': retry_strategy,
            'recommended_action': self._get_recommended_action(category)
        }
    
    def _get_recommended_action(self, category: str) -> str:
        """Get recommended action based on error category"""
        actions = {
            'TIMEOUT': 'Retry with longer timeout',
            'API_ERROR': 'Switch to Tesseract OCR fallback',
            'INVALID_FILE': 'Request user to re-upload document',
            'UNKNOWN': 'Log error and notify administrator'
        }
        return actions.get(category, 'Contact support')
