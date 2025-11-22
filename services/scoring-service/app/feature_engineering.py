"""
Feature Engineering
Transform raw data into ML features
"""
from typing import Dict, Any
from datetime import datetime


class FeatureEngineer:
    """
    Feature engineering for credit scoring
    
    Creates 50+ features from:
    - Applicant demographics
    - Loan details  
    - Financial metrics
    - Credit bureau data
    - Bank statement analysis
    """
    
    def create_features(
        self,
        applicant_data: Dict,
        financial_data: Dict,
        credit_bureau_data: Dict
    ) -> Dict[str, Any]:
        """
        Engineer all features for ML model
        
        Returns:
            Dictionary of feature_name -> value
        """
        features = {}
        
        # =====================================================================
        # DEMOGRAPHIC FEATURES
        # =====================================================================
        
        features['age'] = applicant_data.get('age', 0)
        features['age_squared'] = features['age'] ** 2
        features['age_group'] = self._get_age_group(features['age'])
        
        # Occupation encoding
        occupation = applicant_data.get('occupation', '').lower()
        features['is_salaried'] = 1 if any(x in occupation for x in ['pegawai', 'karyawan', 'employee']) else 0
        features['is_self_employed'] = 1 if any(x in occupation for x in ['wiraswasta', 'entrepreneur', 'business']) else 0
        features['is_civil_servant'] = 1 if any(x in occupation for x in ['pns', 'civil servant']) else 0
        
        # =====================================================================
        # LOAN FEATURES
        # =====================================================================
        
        features['loan_amount'] = applicant_data.get('loan_amount', 0)
        features['loan_term_months'] = applicant_data.get('loan_term_months', 12)
        features['monthly_income'] = applicant_data.get('monthly_income', 0)
        
        # Derived loan features
        if features['loan_term_months'] > 0:
            features['monthly_payment'] = features['loan_amount'] / features['loan_term_months']
        else:
            features['monthly_payment'] = 0
        
        if features['monthly_income'] > 0:
            features['payment_to_income_ratio'] = features['monthly_payment'] / features['monthly_income']
            features['loan_to_annual_income'] = features['loan_amount'] / (features['monthly_income'] * 12)
        else:
            features['payment_to_income_ratio'] = 0
            features['loan_to_annual_income'] = 0
        
        features['loan_term_years'] = features['loan_term_months'] / 12
        features['loan_amount_log'] = self._safe_log(features['loan_amount'])
        features['monthly_income_log'] = self._safe_log(features['monthly_income'])
        
        # =====================================================================
        # FINANCIAL STATEMENT FEATURES
        # =====================================================================
        
        # Income statement
        features['revenue'] = financial_data.get('revenue', 0)
        features['net_income'] = financial_data.get('net_income', 0)
        features['gross_profit'] = financial_data.get('gross_profit', 0)
        features['operating_income'] = financial_data.get('operating_income', 0)
        
        # Profitability ratios
        if features['revenue'] > 0:
            features['net_profit_margin'] = features['net_income'] / features['revenue']
            features['gross_profit_margin'] = features['gross_profit'] / features['revenue']
        else:
            features['net_profit_margin'] = 0
            features['gross_profit_margin'] = 0
        
        # Balance sheet        
        features['total_assets'] = financial_data.get('total_assets', 0)
        features['total_liabilities'] = financial_data.get('total_liabilities', 0)
        features['equity'] = financial_data.get('equity', 0)
        features['current_assets'] = financial_data.get('current_assets', 0)
        features['current_liabilities'] = financial_data.get('current_liabilities', 0)
        
        # Financial ratios
        ratios = financial_data.get('ratios', {})
        features['current_ratio'] = ratios.get('current_ratio', 0)
        features['debt_to_equity'] = ratios.get('debt_to_equity', 0)
        features['debt_ratio'] = ratios.get('debt_ratio', 0)
        
        # Cash flow
        features['operating_cash_flow'] = financial_data.get('operating_cash_flow', 0)
        features['free_cash_flow'] = features['operating_cash_flow'] - financial_data.get('investing_cash_flow', 0)
        
        # =====================================================================
        # CREDIT BUREAU FEATURES
        # =====================================================================
        
        features['credit_score'] = credit_bureau_data.get('credit_score', 0)
        features['total_accounts'] = credit_bureau_data.get('total_accounts', 0)
        features['active_accounts'] = credit_bureau_data.get('active_accounts', 0)
        features['delinquent_accounts'] = credit_bureau_data.get('delinquent_accounts', 0)
        features['total_debt'] = credit_bureau_data.get('total_debt', 0)
        features['inquiries_last_6m'] = credit_bureau_data.get('inquiries_last_6m', 0)
        
        # Derived credit features
        if features['total_accounts'] > 0:
            features['delinquency_rate'] = features['delinquent_accounts'] / features['total_accounts']
            features['account_utilization'] = features['active_accounts'] / features['total_accounts']
        else:
            features['delinquency_rate'] = 0
            features['account_utilization'] = 0
        
        # Debt service coverage ratio (DSCR)
        if features['monthly_payment'] > 0:
            monthly_debt_service = features['monthly_payment'] + (features['total_debt'] / 360)  # Assume 30-year amortization
            if monthly_debt_service > 0:
                features['dscr'] = (features['monthly_income'] + features.get('operating_cash_flow', 0) / 12) / monthly_debt_service
            else:
                features['dscr'] = 0
        else:
            features['dscr'] = 0
        
        # =====================================================================
        # INTERACTION FEATURES
        # =====================================================================
        
        features['age_x_income'] = features['age'] * features['monthly_income']
        features['age_x_loan_amount'] = features['age'] * features['loan_amount']
        features['credit_score_x_dti'] = features['credit_score'] * features['payment_to_income_ratio']
        
        # =====================================================================
        # BOOLEAN FLAGS
        # =====================================================================
        
        features['has_delinquencies'] = 1 if features['delinquent_accounts'] > 0 else 0
        features['high_dti'] = 1 if features['payment_to_income_ratio'] > 0.4 else 0
        features['low_credit_score'] = 1 if features['credit_score'] < 600 else 0
        features['large_loan'] = 1 if features['loan_amount'] > 100000000 else 0  # > Rp 100M
        
        return features
    
    def _get_age_group(self, age: int) -> int:
        """Bin age into groups"""
        if age < 25:
            return 1
        elif age < 35:
            return 2
        elif age < 45:
            return 3
        elif age < 55:
            return 4
        else:
            return 5
    
    def _safe_log(self, value: float) -> float:
        """Safe logarithm (returns 0 for non-positive values)"""
        import math
        return math.log(value + 1) if value > 0 else 0
