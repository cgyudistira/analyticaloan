"""
Rule Engine for Credit Underwriting
Policy-based decision rules using custom engine
(Alternative to OPA - Open Policy Agent)
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import json


class Rule:
    """Single business rule"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: callable,
        severity: str = "HIGH",  # HIGH, MEDIUM, LOW
        action: str = "REJECT"   # REJECT, FLAG, WARN
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.condition = condition
        self.severity = severity
        self.action = action
    
    def evaluate(self, data: Dict) -> bool:
        """Evaluate rule condition"""
        try:
            return self.condition(data)
        except Exception as e:
            print(f"Error evaluating rule {self.rule_id}: {e}")
            return False


class RuleEngine:
    """
    Custom rule engine for credit policy compliance
    
    Implements POJK and internal lending policies as executable rules
    """
    
    def __init__(self):
        self.rules: List[Rule] = []
        self._initialize_pojk_rules()
        self._initialize_internal_rules()
    
    def _initialize_pojk_rules(self):
        """Initialize POJK regulatory rules"""
        
        # POJK Rule 1: Borrower age limits
        self.add_rule(Rule(
            rule_id="POJK_AGE_001",
            name="Borrower Age Limit",
            description="Borrower must be between 21-65 years old",
            condition=lambda data: 21 <= self._calculate_age(data.get('date_of_birth')) <= 65,
            severity="HIGH",
            action="REJECT"
        ))
        
        # POJK Rule 2: Maximum DTI (Debt-to-Income)
        self.add_rule(Rule(
            rule_id="POJK_DTI_001",
            name="Maximum DTI Ratio",
            description="Debt-to-Income ratio must not exceed 40%",
            condition=lambda data: self._calculate_dti(data) <= 0.40,
            severity="HIGH",
            action="REJECT"
        ))
        
        # POJK Rule 3: Minimum income requirement
        self.add_rule(Rule(
            rule_id="POJK_INCOME_001",
            name="Minimum Monthly Income",
            description="Borrower must have minimum monthly income of Rp 3,000,000",
            condition=lambda data: data.get('monthly_income', 0) >= 3000000,
            severity="MEDIUM",
            action="FLAG"
        ))
        
        # POJK Rule 4: Maximum loan-to-value for collateral
        self.add_rule(Rule(
            rule_id="POJK_LTV_001",
            name="Maximum Loan-to-Value Ratio",
            description="LTV must not exceed 80% for secured loans",
            condition=lambda data: not data.get('has_collateral') or self._calculate_ltv(data) <= 0.80,
            severity="HIGH",
            action="REJECT"
        ))
        
        # POJK Rule 5: Credit bureau requirements
        self.add_rule(Rule(
            rule_id="POJK_CREDIT_001",
            name="No Active Delinquencies",
            description="Borrower must not have active delinquent accounts",
            condition=lambda data: data.get('delinquent_accounts', 0) == 0,
            severity="HIGH",
            action="REJECT"
        ))
        
        # POJK Rule 6: DSCR requirement
        self.add_rule(Rule(
            rule_id="POJK_DSCR_001",
            name="Minimum DSCR",
            description="Debt Service Coverage Ratio must be at least 1.25",
            condition=lambda data: self._calculate_dscr(data) >= 1.25,
            severity="HIGH",
            action="REJECT"
        ))
    
    def _initialize_internal_rules(self):
        """Initialize internal lending policy rules"""
        
        # Internal Rule 1: Maximum loan amount
        self.add_rule(Rule(
            rule_id="INT_AMOUNT_001",
            name="Maximum Loan Amount",
            description="Loan amount must not exceed Rp 500,000,000",
            condition=lambda data: data.get('loan_amount', 0) <= 500000000,
            severity="HIGH",
            action="REJECT"
        ))
        
        # Internal Rule 2: Minimum credit score
        self.add_rule(Rule(
            rule_id="INT_CREDIT_001",
            name="Minimum Credit Score",
            description="Credit score must be at least 550",
            condition=lambda data: data.get('credit_score', 0) >= 550,
            severity="MEDIUM",
            action="FLAG"
        ))
        
        # Internal Rule 3: Maximum loan term
        self.add_rule(Rule(
            rule_id="INT_TERM_001",
            name="Maximum Loan Term",
            description="Loan term must not exceed 60 months (5 years)",
            condition=lambda data: data.get('loan_term_months', 0) <= 60,
            severity="MEDIUM",
            action="FLAG"
        ))
        
        # Internal Rule 4: Employment stability
        self.add_rule(Rule(
            rule_id="INT_EMPLOY_001",
            name="Employment Status",
            description="Borrower must have stable employment",
            condition=lambda data: self._check_employment_stability(data),
            severity="LOW",
            action="WARN"
        ))
        
        # Internal Rule 5: Multiple loan applications
        self.add_rule(Rule(
            rule_id="INT_INQUIRY_001",
            name="Recent Credit Inquiries",
            description="No more than 3 credit inquiries in last 6 months",
            condition=lambda data: data.get('inquiries_last_6m', 0) <= 3,
            severity="LOW",
            action="WARN"
        ))
    
    def add_rule(self, rule: Rule):
        """Add a rule to the engine"""
        self.rules.append(rule)
    
    def evaluate_all(self, data: Dict) -> Dict[str, Any]:
        """
        Evaluate all rules against application data
        
        Returns:
            Dict with pass/fail status, violated rules, and recommended action
        """
        violations = []
        warnings = []
        flags = []
        
        for rule in self.rules:
            passed = rule.evaluate(data)
            
            if not passed:
                violation_info = {
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity,
                    'action': rule.action
                }
                
                if rule.action == "REJECT":
                    violations.append(violation_info)
                elif rule.action == "FLAG":
                    flags.append(violation_info)
                elif rule.action == "WARN":
                    warnings.append(violation_info)
        
        # Determine overall result
        if violations:
            overall_status = "REJECT"
            decision = "Application must be rejected due to policy violations"
        elif flags:
            overall_status = "MANUAL_REVIEW"
            decision = "Application requires manual review due to flagged conditions"
        elif warnings:
            overall_status = "APPROVE_WITH_CONDITIONS"
            decision = "Application may proceed with additional monitoring"
        else:
            overall_status = "PASS"
            decision = "All policy rules satisfied"
        
        return {
            'overall_status': overall_status,
            'decision': decision,
            'violations': violations,
            'flags': flags,
            'warnings': warnings,
            'total_rules_evaluated': len(self.rules),
            'rules_passed': len(self.rules) - len(violations) - len(flags) - len(warnings),
            'evaluated_at': datetime.utcnow().isoformat()
        }
    
    def evaluate_specific_rules(
        self,
        data: Dict,
        rule_ids: List[str]
    ) -> Dict[str, bool]:
        """Evaluate specific rules by ID"""
        results = {}
        
        for rule in self.rules:
            if rule.rule_id in rule_ids:
                results[rule.rule_id] = rule.evaluate(data)
        
        return results
    
    # Helper calculation methods
    
    def _calculate_age(self, date_of_birth: Optional[date]) -> int:
        """Calculate age from date of birth"""
        if not date_of_birth:
            return 0
        
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.fromisoformat(date_of_birth).date()
        
        today = datetime.now().date()
        age = today.year - date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        
        return age
    
    def _calculate_dti(self, data: Dict) -> float:
        """Calculate Debt-to-Income ratio"""
        monthly_income = float(data.get('monthly_income', 0))
        loan_amount = float(data.get('loan_amount', 0))
        loan_term = data.get('loan_term_months', 12)
        existing_debt = float(data.get('total_debt', 0))
        
        if monthly_income == 0:
            return 1.0  # Max DTI if no income
        
        # Calculate monthly payment (simple division, in reality use amortization)
        monthly_payment = loan_amount / loan_term if loan_term > 0 else loan_amount
        
        # Assume existing debt is paid over 360 months
        existing_monthly_payment = existing_debt / 360
        
        total_monthly_debt = monthly_payment + existing_monthly_payment
        
        return total_monthly_debt / monthly_income
    
    def _calculate_dscr(self, data: Dict) -> float:
        """Calculate Debt Service Coverage Ratio"""
        monthly_income = float(data.get('monthly_income', 0))
        operating_income = float(data.get('operating_income', 0)) / 12 if data.get('operating_income') else 0
        
        loan_amount = float(data.get('loan_amount', 0))
        loan_term = data.get('loan_term_months', 12)
        existing_debt = float(data.get('total_debt', 0))
        
        # Total monthly income
        total_income = monthly_income + operating_income
        
        if total_income == 0:
            return 0
        
        # Total monthly debt service
        new_debt_service = loan_amount / loan_term if loan_term > 0 else loan_amount
        existing_debt_service = existing_debt / 360
        total_debt_service = new_debt_service + existing_debt_service
        
        if total_debt_service == 0:
            return 999  # Infinite coverage
        
        return total_income / total_debt_service
    
    def _calculate_ltv(self, data: Dict) -> float:
        """Calculate Loan-to-Value ratio"""
        loan_amount = float(data.get('loan_amount', 0))
        collateral_value = float(data.get('collateral_value', 0))
        
        if collateral_value == 0:
            return 1.0  # Max LTV if no collateral
        
        return loan_amount / collateral_value
    
    def _check_employment_stability(self, data: Dict) -> bool:
        """Check if borrower has stable employment"""
        occupation = data.get('occupation', '').lower()
        
        # Consider these occupations as stable
        stable_occupations = [
            'pegawai', 'karyawan', 'employee',
            'pns', 'civil servant', 'government',
            'professional', 'dokter', 'doctor',
            'engineer', 'teacher', 'guru'
        ]
        
        return any(occ in occupation for occ in stable_occupations)
    
    def export_rules_to_json(self) -> str:
        """Export all rules to JSON for documentation"""
        rules_list = []
        
        for rule in self.rules:
            rules_list.append({
                'rule_id': rule.rule_id,
                'name': rule.name,
                'description': rule.description,
                'severity': rule.severity,
                'action': rule.action
            })
        
        return json.dumps(rules_list, indent=2)
