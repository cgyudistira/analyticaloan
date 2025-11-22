"""
Gemini AI Client
Integration with Google Gemini 2.0 Flash Thinking and Pro models
"""
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()


class GeminiClient:
    """
    Client for Google Gemini AI models
    
    Models used:
    - Gemini 2.0 Flash Thinking: Complex reasoning, deterministic outputs
    - Gemini 2.0 Pro: Content generation, credit memo writing
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not set in environment")
            return
        
        # Configure API
        genai.configure(api_key=self.api_key)
        
        # Model names from environment
        self.flash_model_name = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.0-flash-thinking-exp")
        self.pro_model_name = os.getenv("GEMINI_PRO_MODEL", "gemini-2.0-flash-exp")
        
        # Initialize models
        self.flash_model = genai.GenerativeModel(
            model_name=self.flash_model_name,
            generation_config={
                "temperature": 0.0,  # Deterministic for credit decisions
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        self.pro_model = genai.GenerativeModel(
            model_name=self.pro_model_name,
            generation_config={
                "temperature": 0.7,  # More creative for memo writing
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
    
    async def analyze_credit_worthiness(
        self,
        applicant_data: Dict,
        financial_metrics: Dict,
        credit_bureau_data: Optional[Dict] = None,
        bank_statement_metrics: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Use Gemini Flash Thinking for credit analysis
        
        Args:
            applicant_data: Applicant information
            financial_metrics: Extracted financial statement data
            credit_bureau_data: SLIK OJK data
            bank_statement_metrics: Bank statement analysis
        
        Returns:
            Analysis with reasoning and recommendations
        """
        prompt = self._build_analysis_prompt(
            applicant_data,
            financial_metrics,
            credit_bureau_data,
            bank_statement_metrics
        )
        
        try:
            response = self.flash_model.generate_content(prompt)
            
            # Parse response
            analysis_text = response.text
            
            return {
                "analysis": analysis_text,
                "model": self.flash_model_name,
                "success": True
            }
        
        except Exception as e:
            return {
                "analysis": None,
                "error": str(e),
                "success": False
            }
    
    def _build_analysis_prompt(
        self,
        applicant_data: Dict,
        financial_metrics: Dict,
        credit_bureau_data: Optional[Dict],
        bank_statement_metrics: Optional[Dict]
    ) -> str:
        """Build comprehensive analysis prompt"""
        
        prompt = f"""You are an expert credit analyst for a Bank Perkreditan Rakyat (BPR) in Indonesia. 
Analyze the following loan application and provide a comprehensive credit assessment.

## Applicant Information:
- Name: {applicant_data.get('full_name', 'N/A')}
- Age: {applicant_data.get('age', 'N/A')}
- Occupation: {applicant_data.get('occupation', 'N/A')}
- Monthly Income: Rp {applicant_data.get('monthly_income', 0):,.0f}
- Loan Amount Requested: Rp {applicant_data.get('loan_amount', 0):,.0f}
- Loan Term: {applicant_data.get('loan_term_months', 'N/A')} months
- Purpose: {applicant_data.get('purpose', 'N/A')}

## Financial Metrics:
"""
        
        # Add financial statement data
        if financial_metrics:
            if 'revenue' in financial_metrics:
                prompt += f"\n### Income Statement:"
                prompt += f"\n- Revenue: Rp {financial_metrics.get('revenue', 0):,.0f}"
                prompt += f"\n- Net Income: Rp {financial_metrics.get('net_income', 0):,.0f}"
                prompt += f"\n- EBITDA: Rp {financial_metrics.get('ebitda', 0):,.0f}"
            
            if 'total_assets' in financial_metrics:
                prompt += f"\n\n### Balance Sheet:"
                prompt += f"\n- Total Assets: Rp {financial_metrics.get('total_assets', 0):,.0f}"
                prompt += f"\n- Total Liabilities: Rp {financial_metrics.get('total_liabilities', 0):,.0f}"
                prompt += f"\n- Equity: Rp {financial_metrics.get('equity', 0):,.0f}"
                
                if 'ratios' in financial_metrics:
                    ratios = financial_metrics['ratios']
                    prompt += f"\n- Current Ratio: {ratios.get('current_ratio', 'N/A')}"
                    prompt += f"\n- Debt-to-Equity: {ratios.get('debt_to_equity', 'N/A')}"
        
        # Add credit bureau data
        if credit_bureau_data:
            prompt += f"\n\n## Credit Bureau Data (SLIK OJK):"
            prompt += f"\n- Credit Score: {credit_bureau_data.get('credit_score', 'N/A')}"
            prompt += f"\n- Total Accounts: {credit_bureau_data.get('total_accounts', 'N/A')}"
            prompt += f"\n- Delinquent Accounts: {credit_bureau_data.get('delinquent_accounts', 'N/A')}"
            prompt += f"\n- Total Debt: Rp {credit_bureau_data.get('total_debt', 0):,.0f}"
        
        # Add bank statement metrics
        if bank_statement_metrics:
            prompt += f"\n\n## Bank Statement Analysis:"
            prompt += f"\n- Average Monthly Income: Rp {bank_statement_metrics.get('avg_monthly_income', 0):,.0f}"
            prompt += f"\n- Average Monthly Expense: Rp {bank_statement_metrics.get('avg_monthly_expense', 0):,.0f}"
            prompt += f"\n- Average Balance: Rp {bank_statement_metrics.get('average_balance', 0):,.0f}"
            prompt += f"\n- Transaction Count: {bank_statement_metrics.get('transaction_count', 0)}"
        
        prompt += """

## Your Task:
Provide a comprehensive credit analysis with the following structure:

1. **Debt Service Coverage Ratio (DSCR) Analysis:**
   - Calculate DSCR based on available income and proposed loan payment
   - Assess if DSCR meets minimum threshold (typically 1.25 for BPR)

2. **Repayment Capacity:**
   - Monthly income vs. monthly loan payment
   - Debt-to-Income (DTI) ratio
   - Disposable income after loan payment

3. **Financial Health:**
   - Liquidity position
   - Leverage ratios
   - Profitability trend (if business loan)

4. **Credit History Assessment:**
   - Payment track record
   - Existing debt obligations
   - Any red flags

5. **Risk Factors:**
   - List all identified risks (market, operational, financial)
   - Severity assessment (HIGH/MEDIUM/LOW)

6. **Mitigating Factors:**
   - Positive aspects that reduce risk
   - Collateral value (if applicable)

7. **Recommendation:**
   - APPROVE / REJECT / MANUAL_REVIEW
   - Confidence level (0-100%)
   - Suggested loan amount (may be lower than requested)
   - Suggested interest rate adjustment
   - Conditions for approval (if applicable)

Be thorough, analytical, and conservative in your assessment. BPR lending requires careful risk management.
"""
        
        return prompt
    
    async def generate_credit_memo(
        self,
        applicant_data: Dict,
        analysis_result: Dict,
        decision: str,
        scoring_data: Dict
    ) -> str:
        """
        Generate credit memorandum using Gemini Pro
        
        Args:
            applicant_data: Applicant information
            analysis_result: AI analysis result
            decision: Final decision (APPROVE/REJECT)
            scoring_data: Scoring model results
        
        Returns:
            Formatted credit memo in Markdown
        """
        prompt = f"""Generate a professional Credit Memorandum for a BPR loan application.

## Application Details:
- Applicant: {applicant_data.get('full_name', 'N/A')}
- Loan Amount: Rp {applicant_data.get('loan_amount', 0):,.0f}
- Loan Term: {applicant_data.get('loan_term_months', 'N/A')} months
- Purpose: {applicant_data.get('purpose', 'N/A')}

## Decision: {decision}

## Credit Score: {scoring_data.get('credit_score', 'N/A')}
## Probability of Default: {scoring_data.get('probability_of_default', 'N/A')}%
## Risk Rating: {scoring_data.get('risk_rating', 'N/A')}

## AI Analysis Summary:
{analysis_result.get('analysis', 'N/A')}

Generate a formal Credit Memorandum including:
1. Executive Summary
2. Borrower Profile
3. Loan Request Details
4. Financial Analysis
5. Risk Assessment
6. Recommendation & Conditions
7. Approval Requirements

Format in professional business Markdown. Use tables where appropriate.
"""
        
        try:
            response = self.pro_model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            return f"# Credit Memorandum\n\nError generating memo: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check if Gemini API is accessible"""
        if not self.api_key:
            return False
        
        try:
            # Simple test prompt
            response = self.flash_model.generate_content("Test")
            return bool(response.text)
        except:
            return False
