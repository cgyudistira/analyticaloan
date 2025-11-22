"""
External API Integrations
- SLIK OJK (Credit Bureau)
- Core Banking System
- Third-party data providers
"""
from typing import Dict, Optional
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class SLIKOJKClient:
    """
    SLIK OJK Credit Bureau Integration
    
    Fetches credit history from Indonesia's financial services authority
    """
    
    def __init__(self):
        self.base_url = os.getenv("SLIK_OJK_URL", "https://api.ojk.go.id/slik")
        self.api_key = os.getenv("SLIK_OJK_API_KEY", "")
        self.timeout = 30.0
    
    async def get_credit_report(
        self,
        nik: str,  # National ID number
        npwp: Optional[str] = None  # Tax ID
    ) -> Dict:
        """
        Fetch credit report from SLIK OJK
        
        Args:
            nik: Nomor Induk Kependudukan
            npwp: Nomor Pokok Wajib Pajak (optional)
        
        Returns:
            Credit report dict with score, accounts, delinquencies
        """
        # In production, this would call actual SLIK OJK API
        # For now, return simulated data
        
        if not self.api_key:
            print("Warning: SLIK OJK API key not configured. Using simulated data.")
            return self._get_simulated_credit_report(nik)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/credit-report",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "nik": nik,
                        "npwp": npwp,
                        "request_date": datetime.utcnow().isoformat()
                    }
                )
                
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            print(f"SLIK OJK API error: {e}")
            # Fallback to simulated data
            return self._get_simulated_credit_report(nik)
    
    def _get_simulated_credit_report(self, nik: str) -> Dict:
        """Generate simulated credit report for testing"""
        # Hash NIK to get consistent but varied scores
        hash_val = sum(ord(c) for c in nik) % 300
        
        credit_score = 500 + hash_val
        
        return {
            "nik": nik,
            "report_date": datetime.utcnow().isoformat(),
            "credit_score": min(850, credit_score),
            "score_range": "300-850",
            "risk_category": self._get_risk_category(credit_score),
            "accounts": {
                "total": 2 + (hash_val % 5),
                "active": 1 + (hash_val % 3),
                "closed": hash_val % 3,
                "delinquent": 0 if credit_score > 650 else (hash_val % 2)
            },
            "debt_summary": {
                "total_debt": float((hash_val * 1000000) % 100000000),
                "monthly_payment": float((hash_val * 50000) % 5000000),
                "currency": "IDR"
            },
            "payment_history": {
                "on_time_percentage": 95 if credit_score > 700 else 80,
                "late_payments_12m": 0 if credit_score > 650 else (hash_val % 3),
                "defaults": 0 if credit_score > 600 else (hash_val % 2)
            },
            "inquiries": {
                "last_6_months": hash_val % 4,
                "last_12_months": hash_val % 7
            },
            "public_records": {
                "bankruptcies": 0,
                "liens": 0,
                "judgments": 0
            },
            "data_source": "SLIK OJK (Simulated)",
            "disclaimer": "This is simulated data for development purposes"
        }
    
    def _get_risk_category(self, credit_score: int) -> str:
        """Map credit score to risk category"""
        if credit_score >= 750:
            return "VERY_LOW"
        elif credit_score >= 650:
            return "LOW"
        elif credit_score >= 550:
            return "MEDIUM"
        else:
            return "HIGH"


class CoreBankingClient:
    """
    Core Banking System Integration
    
    Fetches account information, transaction history, balances
    """
    
    def __init__(self):
        self.base_url = os.getenv("CORE_BANKING_URL", "https://api.bank.internal")
        self.api_key = os.getenv("CORE_BANKING_API_KEY", "")
        self.timeout = 30.0
    
    async def get_account_balance(
        self,
        account_number: str
    ) -> Dict:
        """
        Fetch account balance
        
        Args:
            account_number: Bank account number
        
        Returns:
            Account balance and details
        """
        if not self.api_key:
            print("Warning: Core Banking API key not configured. Using simulated data.")
            return self._get_simulated_balance(account_number)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/accounts/{account_number}/balance",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            print(f"Core Banking API error: {e}")
            return self._get_simulated_balance(account_number)
    
    async def get_transaction_history(
        self,
        account_number: str,
        days: int = 90
    ) -> Dict:
        """
        Fetch transaction history
        
        Args:
            account_number: Bank account number
            days: Number of days to retrieve (default 90)
        
        Returns:
            List of transactions
        """
        if not self.api_key:
            return self._get_simulated_transactions(account_number, days)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/accounts/{account_number}/transactions",
                    params={"days": days},
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            print(f"Core Banking API error: {e}")
            return self._get_simulated_transactions(account_number, days)
    
    def _get_simulated_balance(self, account_number: str) -> Dict:
        """Generate simulated account balance"""
        hash_val = sum(ord(c) for c in account_number) % 10000
        
        return {
            "account_number": account_number,
            "account_type": "CHECKING",
            "currency": "IDR",
            "available_balance": float(hash_val * 10000),
            "current_balance": float(hash_val * 10000),
            "as_of_date": datetime.utcnow().isoformat(),
            "data_source": "Core Banking (Simulated)"
        }
    
    def _get_simulated_transactions(self, account_number: str, days: int) -> Dict:
        """Generate simulated transaction history"""
        return {
            "account_number": account_number,
            "period_days": days,
            "transaction_count": 15,
            "transactions": [
                {
                    "date": "2024-01-15",
                    "description": "Salary Deposit",
                    "amount": 15000000,
                    "type": "CREDIT"
                },
                {
                    "date": "2024-01-16",
                    "description": "Rent Payment",
                    "amount": -5000000,
                    "type": "DEBIT"
                }
            ],
            "data_source": "Core Banking (Simulated)"
        }


class ExternalAPIIntegration:
    """
    Unified interface for all external API integrations
    """
    
    def __init__(self):
        self.slik_client = SLIKOJKClient()
        self.core_banking_client = CoreBankingClient()
    
    async def fetch_all_data(
        self,
        nik: str,
        account_number: Optional[str] = None
    ) -> Dict:
        """
        Fetch all external data for applicant
        
        Returns combined data from all sources
        """
        results = {}
        
        # Fetch SLIK credit report
        try:
            credit_report = await self.slik_client.get_credit_report(nik)
            results['credit_bureau'] = credit_report
        except Exception as e:
            results['credit_bureau'] = {"error": str(e)}
        
        # Fetch banking data if account number provided
        if account_number:
            try:
                balance = await self.core_banking_client.get_account_balance(account_number)
                transactions = await self.core_banking_client.get_transaction_history(account_number)
                
                results['banking'] = {
                    "balance": balance,
                    "transactions": transactions
                }
            except Exception as e:
                results['banking'] = {"error": str(e)}
        
        return results
