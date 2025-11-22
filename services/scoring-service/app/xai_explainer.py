"""
XAI Explainer
SHAP-based explainability for credit scoring decisions
"""
from typing import Dict, List, Any
import numpy as np


class XAIExplainer:
    """
    Explainable AI using SHAP (SHapley Additive exPlanations)
    
    Provides:
    - Feature importances
    - SHAP values for individual predictions
    - Natural language explanations
    - Top positive/negative factors
    """
    
    def __init__(self, credit_model):
        self.model = credit_model
        self.shap_explainer = None
        
        # Try to initialize SHAP explainer
        try:
            import shap
            # For tree-based models
            if hasattr(credit_model.model, 'predict_proba'):
                self.shap_explainer = shap.TreeExplainer(credit_model.model)
            self.shap_available = True
        except:
            print("Warning: SHAP not available. Using basic explanations.")
            self.shap_available = False
    
    def explain(self, features: Dict[str, Any]) -> Dict:
        """
        Generate comprehensive explanation for prediction
        
        Args:
            features: Engineered features dictionary
        
        Returns:
            Dict with feature importances, SHAP values, and natural language explanation
        """
        if self.shap_available and self.shap_explainer:
            return self._shap_explain(features)
        else:
            return self._basic_explain(features)
    
    def _shap_explain(self, features: Dict[str, Any]) -> Dict:
        """SHAP-based explanation"""
        import shap
        
        # Convert features to array
        feature_array = np.array(list(features.values())).reshape(1, -1)
        feature_names = list(features.keys())
        
        # Get SHAP values
        shap_values = self.shap_explainer.shap_values(feature_array)
        
        # If binary classification, shap_values might be a list
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Use positive class
        
        # Get SHAP values for this prediction
        shap_vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values
        
        # Create SHAP value dict
        shap_dict = {
            name: float(val)
            for name, val in zip(feature_names, shap_vals)
        }
        
        # Get feature importances from model
        feature_importances = {}
        if hasattr(self.model.model, 'feature_importances_'):
            for name, importance in zip(feature_names, self.model.model.feature_importances_):
                feature_importances[name] = float(importance)
        else:
            # Use SHAP values as importances
            feature_importances = {k: abs(v) for k, v in shap_dict.items()}
        
        # Get top factors
        sorted_shap = sorted(shap_dict.items(), key=lambda x: x[1], reverse=True)
        
        top_positive = [
            {
                "feature": name,
                "shap_value": value,
                "feature_value": features.get(name, 0),
                "impact": "Reduces default risk"
            }
            for name, value in sorted_shap[:5] if value > 0
        ]
        
        top_negative = [
            {
                "feature": name,
                "shap_value": value,
                "feature_value": features.get(name, 0),
                "impact": "Increases default risk"
            }
            for name, value in sorted(sorted_shap, key=lambda x: x[1])[:5] if value < 0
        ]
        
        # Generate natural language explanation
        explanation_text = self._generate_explanation(
            features, top_positive, top_negative
        )
        
        return {
            "feature_importances": feature_importances,
            "shap_values": shap_dict,
            "top_positive_factors": top_positive,
            "top_negative_factors": top_negative,
            "explanation_text": explanation_text
        }
    
    def _basic_explain(self, features: Dict[str, Any]) -> Dict:
        """Basic explanation without SHAP"""
        # Use heuristic importance scores
        important_features = {
            'payment_to_income_ratio': features.get('payment_to_income_ratio', 0),
            'credit_score': features.get('credit_score', 0),
            'delinquent_accounts': features.get('delinquent_accounts', 0),
            'monthly_income': features.get('monthly_income', 0),
            'debt_to_equity': features.get('debt_to_equity', 0),
            'current_ratio': features.get('current_ratio', 0),
            'age': features.get('age', 0),
'dscr': features.get('dscr', 0),
        }
        
        # Simulate SHAP values (higher feature value = higher/lower risk)
        shap_values = {}
        for feature, value in important_features.items():
            if feature in ['credit_score', 'monthly_income', 'current_ratio', 'dscr']:
                # Higher is better -> negative SHAP (reduces risk)
                shap_values[feature] = -value / 1000
            else:
                # Higher is worse -> positive SHAP (increases risk)
                shap_values[feature] = value / 1000
        
        # Feature importances (heuristic)
        feature_importances = {
            'payment_to_income_ratio': 0.25,
            'credit_score': 0.20,
            'delinquent_accounts': 0.15,
            'monthly_income': 0.12,
            'dscr': 0.10,
            'debt_to_equity': 0.08,
            'current_ratio': 0.05,
            'age': 0.05
        }
        
        # Top factors
        sorted_shap = sorted(shap_values.items(), key=lambda x: x[1], reverse=True)
        
        top_positive = [
            {
                "feature": self._humanize_feature_name(name),
                "shap_value": value,
                "feature_value": features.get(name, 0),
                "impact": "Reduces default risk"
            }
            for name, value in sorted_shap[:3] if value < 0
        ]
        
        top_negative = [
            {
                "feature": self._humanize_feature_name(name),
                "shap_value": value,
                "feature_value": features.get(name, 0),
                "impact": "Increases default risk"
            }
            for name, value in sorted(sorted_shap, key=lambda x: x[1])[:3] if value > 0
        ]
        
        # Generate explanation
        explanation_text = self._generate_explanation(
            features, top_positive, top_negative
        )
        
        return {
            "feature_importances": feature_importances,
            "shap_values": shap_values,
            "top_positive_factors": top_positive,
            "top_negative_factors": top_negative,
            "explanation_text": explanation_text
        }
    
    def _generate_explanation(
        self,
        features: Dict,
        top_positive: List[Dict],
        top_negative: List[Dict]
    ) -> str:
        """Generate natural language explanation"""
        explanation = "## Credit Score Explanation\n\n"
        
        # Overall assessment
        dti = features.get('payment_to_income_ratio', 0)
        credit_score = features.get('credit_score', 0)
        
        explanation += "### Overall Assessment\n"
        
        if dti > 0.5:
            explanation += "- **High Debt-to-Income Ratio** ({:.1%}): Monthly loan payment consumes significant portion of income.\n".format(dti)
        elif dti > 0.4:
            explanation += "- **Moderate Debt-to-Income Ratio** ({:.1%}): Monthly payment is within acceptable range but close to limit.\n".format(dti)
        else:
            explanation += "- **Healthy Debt-to-Income Ratio** ({:.1%}): Borrower has sufficient income to service debt.\n".format(dti)
        
        if credit_score > 700:
            explanation += "- **Strong Credit History** (Score: {}): Excellent track record of debt repayment.\n".format(int(credit_score))
        elif credit_score > 600:
            explanation += "- **Fair Credit History** (Score: {}): Reasonable credit profile with some minor issues.\n".format(int(credit_score))
        else:
            explanation += "- **Weak Credit History** (Score: {}): Poor credit profile indicates higher risk.\n".format(int(credit_score))
        
        # Positive factors
        if top_positive:
            explanation += "\n### Positive Factors (Risk Reducers)\n"
            for factor in top_positive[:3]:
                explanation += f"- **{factor['feature']}**: {self._format_value(factor['feature'], factor['feature_value'])}\n"
        
        # Negative factors
        if top_negative:
            explanation += "\n### Risk Factors (Risk Increasers)\n"
            for factor in top_negative[:3]:
                explanation += f"- **{factor['feature']}**: {self._format_value(factor['feature'], factor['feature_value'])}\n"
        
        # Recommendation
        explanation += "\n### Recommendation\n"
        
        delinquencies = features.get('delinquent_accounts', 0)
        if delinquencies > 0:
            explanation += f"- **Caution**: Borrower has {int(delinquencies)} delinquent account(s). Requires careful review.\n"
        
        if dti > 0.4:
            explanation += "- **Consider**: Reducing loan amount or extending term to improve payment-to-income ratio.\n"
        
        return explanation
    
    def _humanize_feature_name(self, feature_name: str) -> str:
        """Convert feature name to human-readable format"""
        name_map = {
            'payment_to_income_ratio': 'Payment-to-Income Ratio',
            'credit_score': 'Credit Score',
            'delinquent_accounts': 'Delinquent Accounts',
            'monthly_income': 'Monthly Income',
            'dscr': 'Debt Service Coverage Ratio',
            'debt_to_equity': 'Debt-to-Equity Ratio',
            'current_ratio': 'Current Ratio',
            'age': 'Borrower Age',
            'loan_amount': 'Loan Amount',
            'total_debt': 'Total Existing Debt'
        }
        return name_map.get(feature_name, feature_name.replace('_', ' ').title())
    
    def _format_value(self, feature_name: str, value: Any) -> str:
        """Format feature value for display"""
        if feature_name in ['payment_to_income_ratio', 'debt_to_equity']:
            return f"{value:.1%}" if value > 0 else "0%"
        elif feature_name in ['credit_score', 'age', 'delinquent_accounts']:
            return str(int(value))
        elif feature_name in ['monthly_income', 'loan_amount', 'total_debt']:
            return f"Rp {value:,.0f}"
        elif feature_name == 'dscr':
            return f"{value:.2f}x"
        else:
            return f"{value:.2f}"
