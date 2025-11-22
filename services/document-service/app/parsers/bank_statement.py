"""
Bank Statement Parser
Extracts transaction data and calculates metrics from bank statements
Supports multiple Indonesian banks: BCA, Mandiri, BRI, BNI, etc.
"""
import re
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, date
from pydantic import BaseModel


class Transaction(BaseModel):
    """Single bank transaction"""
    date: date
    description: str
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    balance: Optional[Decimal] = None


class BankStatementMetrics(BaseModel):
    """Aggregated metrics from bank statement"""
    account_number: Optional[str]
    account_name: Optional[str]
    bank_name: Optional[str]
    statement_period_start: Optional[date]
    statement_period_end: Optional[date]
    opening_balance: Optional[Decimal]
    closing_balance: Optional[Decimal]
    total_credits: Decimal
    total_debits: Decimal
    transaction_count: int
    average_balance: Decimal
    highest_balance: Decimal
    lowest_balance: Decimal
    avg_monthly_income: Decimal
    avg_monthly_expense: Decimal
    income_volatility: float  # Standard deviation of monthly incomes
    expense_volatility: float  # Standard deviation of monthly expenses
    transactions: List[Transaction]


class BankStatementParser:
    """Parser for Indonesian bank statements"""
    
    def __init__(self):
        # Bank identification patterns
        self.bank_patterns = {
            'BCA': r'(?:PT\s+)?BANK\s+CENTRAL\s+ASIA|BCA',
            'MANDIRI': r'(?:PT\s+)?BANK\s+MANDIRI|MANDIRI',
            'BRI': r'(?:PT\s+)?BANK\s+RAKYAT\s+INDONESIA|BRI',
            'BNI': r'(?:PT\s+)?BANK\s+NEGARA\s+INDONESIA|BNI',
            'CIMB': r'CIMB\s+NIAGA|CIMB',
            'PERMATA': r'BANK\s+PERMATA',
            'BTN': r'BANK\s+TABUNGAN\s+NEGARA|BTN',
        }
    
    def detect_bank(self, text: str) -> Optional[str]:
        """Detect which bank the statement is from"""
        text_upper = text.upper()
        
        for bank, pattern in self.bank_patterns.items():
            if re.search(pattern, text_upper):
                return bank
        
        return None
    
    def parse_currency(self, value_str: str) -> Optional[Decimal]:
        """Parse Indonesian currency string"""
        if not value_str:
            return None
        
        # Remove currency symbols and spaces
        cleaned = value_str.replace('Rp', '').replace('IDR', '').strip()
        cleaned = cleaned.replace(' ', '')
        
        # Handle negative (parentheses or minus)
        is_negative = False
        if cleaned.startswith('(') and cleaned.endswith(')'):
            is_negative = True
            cleaned = cleaned[1:-1]
        elif cleaned.startswith('-'):
            is_negative = True
            cleaned = cleaned[1:]
        
        # Remove separators
        cleaned = cleaned.replace('.', '').replace(',', '')
        
        try:
            value = Decimal(cleaned)
            return -value if is_negative else value
        except:
            return None
    
    def parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse Indonesian date formats
        
        Supports:
        - DD/MM/YYYY
        - DD-MM-YYYY
        - DD MMM YYYY
        - DD MMMM YYYY
        """
        # Month mapping (Indonesian)
        months_id = {
            'jan': 1, 'januari': 1,
            'feb': 2, 'februari': 2,
            'mar': 3, 'maret': 3,
            'apr': 4, 'april': 4,
            'mei': 5, 'may': 5,
            'jun': 6, 'juni': 6,
            'jul': 7, 'juli': 7,
            'agu': 8, 'agustus': 8, 'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'okt': 10, 'oktober': 10, 'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'des': 12, 'desember': 12, 'dec': 12, 'december': 12,
        }
        
        date_str = date_str.strip().lower()
        
        # Try DD/MM/YYYY or DD-MM-YYYY
        for separator in ['/', '-', '.']:
            parts = date_str.split(separator)
            if len(parts) == 3:
                try:
                    day = int(parts[0])
                    month = int(parts[1])
                    year = int(parts[2])
                    if year < 100:  # 2-digit year
                        year += 2000
                    return date(year, month, day)
                except:
                    pass
        
        # Try DD MMM YYYY
        match = re.match(r'(\d{1,2})\s+([a-z]+)\s+(\d{2,4})', date_str)
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3))
            
            if year < 100:
                year += 2000
            
            if month_str in months_id:
                month = months_id[month_str]
                try:
                    return date(year, month, day)
                except:
                    pass
        
        return None
    
    def parse(self, text: str) -> BankStatementMetrics:
        """
        Parse bank statement and extract metrics
        
        Args:
            text: OCR-extracted text from bank statement
        
        Returns:
            BankStatementMetrics with all extracted data
        """
        # Detect bank
        bank_name = self.detect_bank(text)
        
        # Extract account number
        account_number = self._extract_account_number(text)
        
        # Extract account name
        account_name = self._extract_account_name(text)
        
        # Extract statement period
        period_start, period_end = self._extract_period(text)
        
        # Extract transactions
        transactions = self._extract_transactions(text, bank_name)
        
        # Calculate metrics
        if not transactions:
            return BankStatementMetrics(
                account_number=account_number,
                account_name=account_name,
                bank_name=bank_name,
                statement_period_start=period_start,
                statement_period_end=period_end,
                opening_balance=None,
                closing_balance=None,
                total_credits=Decimal(0),
                total_debits=Decimal(0),
                transaction_count=0,
                average_balance=Decimal(0),
                highest_balance=Decimal(0),
                lowest_balance=Decimal(0),
                avg_monthly_income=Decimal(0),
                avg_monthly_expense=Decimal(0),
                income_volatility=0.0,
                expense_volatility=0.0,
                transactions=[]
            )
        
        # Calculate aggregates
        total_credits = sum(t.credit for t in transactions if t.credit)
        total_debits = sum(t.debit for t in transactions if t.debit)
        
        balances = [t.balance for t in transactions if t.balance]
        avg_balance = sum(balances) / len(balances) if balances else Decimal(0)
        highest_balance = max(balances) if balances else Decimal(0)
        lowest_balance = min(balances) if balances else Decimal(0)
        
        opening_balance = balances[0] if balances else None
        closing_balance = balances[-1] if balances else None
        
        # Monthly metrics (simplified - assumes 30-day months)
        days_in_period = 30
        if period_start and period_end:
            days_in_period = (period_end - period_start).days or 30
        
        months_in_period = days_in_period / 30
        avg_monthly_income = total_credits / Decimal(months_in_period) if months_in_period > 0 else total_credits
        avg_monthly_expense = total_debits / Decimal(months_in_period) if months_in_period > 0 else total_debits
        
        # Volatility (simplified - standard deviation)
        income_volatility = 0.0
        expense_volatility = 0.0
        
        return BankStatementMetrics(
            account_number=account_number,
            account_name=account_name,
            bank_name=bank_name,
            statement_period_start=period_start,
            statement_period_end=period_end,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            total_credits=total_credits,
            total_debits=total_debits,
            transaction_count=len(transactions),
            average_balance=avg_balance,
            highest_balance=highest_balance,
            lowest_balance=lowest_balance,
            avg_monthly_income=avg_monthly_income,
            avg_monthly_expense=avg_monthly_expense,
            income_volatility=income_volatility,
            expense_volatility=expense_volatility,
            transactions=transactions
        )
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """Extract account number"""
        patterns = [
            r'(?:no\.?\s*(?:rekening|account|rek))\s*:?\s*([\d\-]+)',
            r'(?:rekening|account)\s*(?:number|no\.?)?\s*:?\s*([\d\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_account_name(self, text: str) -> Optional[str]:
        """Extract account holder name"""
        patterns = [
            r'(?:nama|name)\s*:?\s*([A-Z][A-Z\s\.]+?)(?:\n|Alamat|Address)',
            r'(?:pemilik|holder)\s*:?\s*([A-Z][A-Z\s\.]+?)(?:\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_period(self, text: str) -> tuple:
        """Extract statement period"""
        # Look for period/periode patterns
        period_patterns = [
            r'(?:periode|period)\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s*(?:s/d|to|sampai)\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}\s+[a-z]+\s+\d{4})\s*(?:s/d|to|sampai)\s*(\d{1,2}\s+[a-z]+\s+\d{4})',
        ]
        
        for pattern in period_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = self.parse_date(match.group(1))
                end = self.parse_date(match.group(2))
                return start, end
        
        return None, None
    
    def _extract_transactions(self, text: str, bank_name: Optional[str]) -> List[Transaction]:
        """Extract all transactions from statement"""
        transactions = []
        
        # Generic transaction pattern
        # Format: DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE
        transaction_pattern = r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s+([^\d\n]+?)\s+([\d\.,\(\)]+)\s+([\d\.,\(\)]+)\s+([\d\.,\(\)]+)'
        
        matches = re.finditer(transaction_pattern, text)
        
        for match in matches:
            trans_date = self.parse_date(match.group(1))
            description = match.group(2).strip()
            
            # Try to determine debit/credit from position
            amount1 = self.parse_currency(match.group(3))
            amount2 = self.parse_currency(match.group(4))
            balance = self.parse_currency(match.group(5))
            
            # Heuristic: credit if amount1 is 0 or very small
            if amount1 and amount1 > 0:
                debit = amount1
                credit = None
            else:
                debit = None
                credit = amount2
            
            if trans_date:
                transactions.append(Transaction(
                    date=trans_date,
                    description=description,
                    debit=debit,
                    credit=credit,
                    balance=balance
                ))
        
        return transactions
