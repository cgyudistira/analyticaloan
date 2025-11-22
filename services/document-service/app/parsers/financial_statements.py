"""
Financial Statement Parsers
Extracts metrics from Income Statements, Balance Sheets, and Cash Flow Statements
"""
import re
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime


class FinancialStatementParser:
    """Base parser for financial statements"""
    
    def parse_currency(self, value_str: str) -> Optional[Decimal]:
        """
        Parse Indonesian currency string to Decimal
        
        Handles formats like:
        - Rp 1.000.000
        - Rp1,000,000
        - 1000000
        - (1.000.000) for negative
        """
        if not value_str:
            return None
        
        # Remove Rp, spaces, and common separators
        cleaned = value_str.replace('Rp', '').replace('IDR', '').strip()
        cleaned = cleaned.replace(' ', '')
        
        # Handle negative numbers in parentheses
        is_negative = False
        if cleaned.startswith('(') and cleaned.endswith(')'):
            is_negative = True
            cleaned = cleaned[1:-1]
        
        # Remove thousands separators (both . and ,)
        cleaned = cleaned.replace('.', '').replace(',', '')
        
        # Handle minus sign
        if cleaned.startswith('-'):
            is_negative = True
            cleaned = cleaned[1:]
        
        try:
            value = Decimal(cleaned)
            return -value if is_negative else value
        except:
            return None


class IncomeStatementParser(FinancialStatementParser):
    """Parser for Income Statement (Laporan Laba Rugi)"""
    
    def parse(self, text: str) -> Dict:
        """
        Extract financial metrics from income statement
        
        Returns dict with keys:
        - revenue
        - cost_of_goods_sold
        - gross_profit
        - operating_expenses
        - operating_income
        - net_income
        - ebitda
        """
        metrics = {}
        
        # Revenue patterns (Indonesian & English)
        revenue_patterns = [
            r'(?:pendapatan|revenue|penjualan|sales)[\s\:]*(?:bersih)?[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'total[\s]+(?:pendapatan|revenue)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['revenue'] = self.parse_currency(match.group(1))
                break
        
        # Cost of Goods Sold (HPP)
        cogs_patterns = [
            r'(?:harga\s+pokok\s+penjualan|hpp|cost\s+of\s+goods\s+sold|cogs)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:beban\s+pokok|cost\s+of\s+sales)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in cogs_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['cost_of_goods_sold'] = self.parse_currency(match.group(1))
                break
        
        # Gross Profit
        gross_profit_patterns = [
            r'(?:laba\s+kotor|gross\s+profit)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in gross_profit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['gross_profit'] = self.parse_currency(match.group(1))
                break
        
        # Operating Expenses
        opex_patterns = [
            r'(?:beban\s+operasional|operating\s+expenses?)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:total\s+beban|total\s+expenses)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in opex_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['operating_expenses'] = self.parse_currency(match.group(1))
                break
        
        # Operating Income
        operating_income_patterns = [
            r'(?:laba\s+operasional|operating\s+income)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:laba\s+usaha|earnings\s+before)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in operating_income_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['operating_income'] = self.parse_currency(match.group(1))
                break
        
        # Net Income
        net_income_patterns = [
            r'(?:laba\s+bersih|net\s+income|net\s+profit)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:laba\s+tahun\s+berjalan|profit\s+for\s+the\s+year)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in net_income_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['net_income'] = self.parse_currency(match.group(1))
                break
        
        # Calculate EBITDA if we have operating income
        if 'operating_income' in metrics:
            metrics['ebitda'] = metrics['operating_income']
        elif 'gross_profit' in metrics and 'operating_expenses' in metrics:
            metrics['ebitda'] = metrics['gross_profit'] - metrics['operating_expenses']
        
        # Calculate gross profit if missing but have revenue and COGS
        if 'gross_profit' not in metrics and 'revenue' in metrics and 'cost_of_goods_sold' in metrics:
            metrics['gross_profit'] = metrics['revenue'] - metrics['cost_of_goods_sold']
        
        # Add metadata
        metrics['currency'] = 'IDR'
        metrics['parsed_at'] = datetime.utcnow().isoformat()
        
        return metrics


class BalanceSheetParser(FinancialStatementParser):
    """Parser for Balance Sheet (Neraca)"""
    
    def parse(self, text: str) -> Dict:
        """
        Extract metrics from balance sheet
        
        Returns dict with keys:
        - current_assets
        - fixed_assets
        - total_assets
        - current_liabilities
        - long_term_liabilities
        - total_liabilities
        - equity
        - ratios (calculated)
        """
        metrics = {}
        
        # Current Assets (Aset Lancar)
        current_assets_patterns = [
            r'(?:aset\s+lancar|current\s+assets?)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in current_assets_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['current_assets'] = self.parse_currency(match.group(1))
                break
        
        # Fixed Assets (Aset Tetap)
        fixed_assets_patterns = [
            r'(?:aset\s+tetap|fixed\s+assets?|property.+equipment)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in fixed_assets_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['fixed_assets'] = self.parse_currency(match.group(1))
                break
        
        # Total Assets
        total_assets_patterns = [
            r'(?:total\s+aset|total\s+assets?)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:jumlah\s+aset)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in total_assets_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['total_assets'] = self.parse_currency(match.group(1))
                break
        
        # Current Liabilities
        current_liabilities_patterns = [
            r'(?:liabilitas\s+jangka\s+pendek|current\s+liabilities)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:utang\s+lancar)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in current_liabilities_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['current_liabilities'] = self.parse_currency(match.group(1))
                break
        
        # Long-term Liabilities
        lt_liabilities_patterns = [
            r'(?:liabilitas\s+jangka\s+panjang|long.?term\s+liabilities)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:utang\s+jangka\s+panjang)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in lt_liabilities_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['long_term_liabilities'] = self.parse_currency(match.group(1))
                break
        
        # Total Liabilities
        total_liabilities_patterns = [
            r'(?:total\s+liabilitas|total\s+liabilities)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:jumlah\s+liabilitas)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in total_liabilities_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['total_liabilities'] = self.parse_currency(match.group(1))
                break
        
        # Equity (Ekuitas)
        equity_patterns = [
            r'(?:ekuitas|equity|modal)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:total\s+ekuitas|total\s+equity)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in equity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['equity'] = self.parse_currency(match.group(1))
                break
        
        # Calculate missing values
        if 'total_assets' not in metrics and 'current_assets' in metrics and 'fixed_assets' in metrics:
            metrics['total_assets'] = metrics['current_assets'] + metrics['fixed_assets']
        
        if 'total_liabilities' not in metrics and 'current_liabilities' in metrics and 'long_term_liabilities' in metrics:
            metrics['total_liabilities'] = metrics['current_liabilities'] + metrics['long_term_liabilities']
        
        if 'equity' not in metrics and 'total_assets' in metrics and 'total_liabilities' in metrics:
            metrics['equity'] = metrics['total_assets'] - metrics['total_liabilities']
        
        # Calculate financial ratios
        ratios = {}
        
        if 'current_assets' in metrics and 'current_liabilities' in metrics and metrics['current_liabilities'] != 0:
            ratios['current_ratio'] = float(metrics['current_assets'] / metrics['current_liabilities'])
        
        if 'total_liabilities' in metrics and 'equity' in metrics and metrics['equity'] != 0:
            ratios['debt_to_equity'] = float(metrics['total_liabilities'] / metrics['equity'])
        
        if 'total_liabilities' in metrics and 'total_assets' in metrics and metrics['total_assets'] != 0:
            ratios['debt_ratio'] = float(metrics['total_liabilities'] / metrics['total_assets'])
        
        metrics['ratios'] = ratios
        metrics['currency'] = 'IDR'
        metrics['parsed_at'] = datetime.utcnow().isoformat()
        
        return metrics


class CashFlowParser(FinancialStatementParser):
    """Parser for Cash Flow Statement (Laporan Arus Kas)"""
    
    def parse(self, text: str) -> Dict:
        """
        Extract cash flow metrics
        
        Returns dict with keys:
        - operating_cash_flow
        - investing_cash_flow
        - financing_cash_flow
        - net_cash_flow
        """
        metrics = {}
        
        # Operating Cash Flow
        operating_cf_patterns = [
            r'(?:arus\s+kas\s+(?:dari\s+)?operasi|operating\s+cash\s+flow)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:cash\s+from\s+operating\s+activities)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in operating_cf_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['operating_cash_flow'] = self.parse_currency(match.group(1))
                break
        
        # Investing Cash Flow
        investing_cf_patterns = [
            r'(?:arus\s+kas\s+(?:dari\s+)?investasi|investing\s+cash\s+flow)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:cash\s+from\s+investing\s+activities)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in investing_cf_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['investing_cash_flow'] = self.parse_currency(match.group(1))
                break
        
        # Financing Cash Flow
        financing_cf_patterns = [
            r'(?:arus\s+kas\s+(?:dari\s+)?pendanaan|financing\s+cash\s+flow)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:cash\s+from\s+financing\s+activities)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in financing_cf_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['financing_cash_flow'] = self.parse_currency(match.group(1))
                break
        
        # Net Cash Flow
        net_cf_patterns = [
            r'(?:kenaikan|penurunan)\s+(?:bersih\s+)?kas[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
            r'(?:net\s+(?:increase|decrease)\s+in\s+cash)[\s\:]*Rp?[\s]*([\d\.,\(\)]+)',
        ]
        
        for pattern in net_cf_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics['net_cash_flow'] = self.parse_currency(match.group(1))
                break
        
        # Calculate net if have components
        if 'net_cash_flow' not in metrics:
            if all(k in metrics for k in ['operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow']):
                metrics['net_cash_flow'] = (
                    metrics['operating_cash_flow'] +
                    metrics['investing_cash_flow'] +
                    metrics['financing_cash_flow']
                )
        
        metrics['currency'] = 'IDR'
        metrics['parsed_at'] = datetime.utcnow().isoformat()
        
        return metrics
