"""
Credit Scoring Model
XGBoost-based probability of default prediction
"""
from typing import Dict, Any
import numpy as np
import joblib
import os
from pathlib import Path


class CreditScoringModel:
    """
    XGBoost model for credit scoring
    
    Predicts probability of default (PD) based on:
    - Applicant demographics
    - Financial metrics
    - Credit bureau data
    - Bank statement analysis
    """
    
    def __init__(self):
        self.model = None
        self.model_version = "1.0.0"
        self.feature_names = []
        
        # Try to load pre-trained model
        self._load_model()
        
        # If no model, create a simple heuristic model
        if self.model is None:
            print("Warning: No pre-trained model found. Using heuristic model.")
            self.use_heuristic = True
        else:
            self.use_heuristic = False
    
    def _load_model(self):
        """Load pre-trained XGBoost model from ML/models directory"""
        model_path = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "xgboost_credit_model.pkl"
        
        if model_path.exists():
            try:
                self.model = joblib.load(model_path)
                print(f"✓ Model loaded from {model_path}")
                
                # Load feature names if available
                feature_path = model_path.parent / "feature_names.txt"
                if feature_path.exists():
                    with open(feature_path, 'r') as f:
                        self.feature_names = [line.strip() for line in f]
            
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict probability of default
        
        Args:
            features: Dictionary of engineered features
        
        Returns:
            Dict with probability_of_default, confidence, and feature importances
        """
        if self.use_heuristic:
            return self._heuristic_predict(features)
        
        # Convert features dict to array in correct order
        feature_array = self._features_to_array(features)
        
        # Predict
        proba = self.model.predict_proba([feature_array])[0]
        probability_of_default = proba[1]  # Probability of class 1 (default)
        
        # Get feature importances
        feature_importances = {}
        if hasattr(self.model, 'feature_importances_'):
            for name, importance in zip(self.feature_names, self.model.feature_importances_):
                feature_importances[name] = float(importance)
        
        return {
            "probability_of_default": float(probability_of_default),
            "confidence": 0.85,  # Model confidence (from validation)
            "feature_importances": feature_importances
        }
    
    def _heuristic_predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Simple heuristic model for when no trained model available
        Based on common credit risk factors
        """
        score = 0.5  # Start with neutral
        
        # Age factor (25-55 is optimal)
        age = features.get('age', 40)
        if 25 <= age <= 55:
            score -= 0.1
        else:
            score += 0.05
        
        # Income-to-loan ratio
        monthly_income = features.get('monthly_income', 0)
        loan_amount = features.get('loan_amount', 0)
        loan_term = features.get('loan_term_months', 12)
        
        if monthly_income > 0 and loan_term > 0:
            monthly_payment = loan_amount / loan_term
            payment_to_income = monthly_payment / monthly_income
            
            if payment_to_income < 0.3:  # < 30%
                score -= 0.15
            elif payment_to_income < 0.4:  # 30-40%
                score -= 0.05
            elif payment_to_income > 0.5:  # > 50%
                score += 0.15
        
        # Credit bureau score
        credit_score = features.get('credit_score', 0)
        if credit_score > 700:
            score -= 0.1
        elif credit_score < 500:
            score += 0.1
        
        # Delinquent accounts
        delinquent_accounts = features.get('delinquent_accounts', 0)
        score += delinquent_accounts * 0.1
        
        # Employment stability (inferred from occupation)
        occupation = features.get('occupation', '').lower()
        stable_occupations = ['pegawai', 'pns', 'karyawan', 'employee', 'civil servant']
        if any(occ in occupation for occ in stable_occupations):
            score -= 0.05
        
        # Clamp between 0 and 1
        probability_of_default = max(0.0, min(1.0, score))
        
        # Feature importances (heuristic)
        feature_importances = {
            "payment_to_income_ratio": 0.25,
            "credit_score": 0.20,
            "monthly_income": 0.15,
            "age": 0.10,
            "delinquent_accounts": 0.15,
            "loan_amount": 0.10,
            "occupation_stability": 0.05
        }
        
        return {
            "probability_of_default": probability_of_default,
            "confidence": 0.65,  # Lower confidence for heuristic
            "feature_importances": feature_importances
        }
    
    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dict to numpy array in correct order"""
        if not self.feature_names:
            # If no feature names, use all features in dict order
            return np.array(list(features.values()))
        
        # Ensure features are in correct order
        feature_array = []
        for feature_name in self.feature_names:
            feature_array.append(features.get(feature_name, 0))
        
        return np.array(feature_array)
