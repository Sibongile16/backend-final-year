import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from app.config import settings
from typing import Dict, Any
from app.schemas.ml_model import RiskLevel
logger = logging.getLogger(__name__)

# Global variables for model artifacts
model = None
scaler = None
feature_columns = None
label_encoders = None

def load_model_artifacts():
    """Load trained model and preprocessing artifacts"""
    global model, scaler, feature_columns, label_encoders
    
    model_path = Path("app/saved_model")
    
    try:
        # Load model
        model = joblib.load(model_path / "dropout_model.pkl")
        
        # Load scaler
        scaler = joblib.load(model_path / "scaler.pkl")
        
        # Load feature columns
        feature_columns = joblib.load(model_path / "feature_columns.pkl")
        
        # Load label encoders
        label_encoders = joblib.load(model_path / "label_encoders.pkl")
        
        logger.info("Model artifacts loaded successfully")
        
        return model, scaler, feature_columns, label_encoders
    except Exception as e:
        logger.error(f"Error loading model artifacts: {e}")
        raise

def determine_risk_level(probability: float) -> RiskLevel:
    """Determine risk level based on probability"""
    if probability < 0.3:
        return RiskLevel.LOW
    elif probability < 0.6:
        return RiskLevel.MEDIUM
    elif probability < 0.8:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL
    
    
def preprocess_features(data: Dict[str, Any]) -> np.ndarray:
    """Preprocess features for prediction"""
    model, scaler, feature_columns, label_encoders = load_model_artifacts()
    # Create DataFrame
    df = pd.DataFrame([data])
    
    # Encode categorical variables
    if 'household_income' in df.columns:
        df['household_income'] = label_encoders['household_income'].transform(df['household_income'].astype(str))
    
    if 'orphan_status' in df.columns:
        df['orphan_status'] = label_encoders['orphan_status'].transform(df['orphan_status'].astype(str))
    
    if 'gender' in df.columns:
        df['gender'] = label_encoders['gender'].transform(df['gender'].astype(str))
    
    # Convert special_learning to int
    df['special_learning'] = df['special_learning'].astype(int)
    
    # Ensure correct feature order
    df = df[feature_columns]
    
    # Scale features
    scaled_features = scaler.transform(df)
    
    return scaled_features
