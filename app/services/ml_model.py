import logging
from typing import List, Dict, Any
from app.schemas.ml_model import RiskLevel, PredictionResponse
from datetime import date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_contributing_factors(features: Dict[str, Any], probability: float) -> List[str]:
    """Identify contributing factors based on feature values"""
    factors = []
    
    if features['term_avg_score'] < 300:
        factors.append("Low academic performance")
    
    if features['school_attendance_rate'] < 0.8:
        factors.append("Poor attendance")
    
    if features['class_repetitions'] > 0:
        factors.append("Grade repetition history")
    
    if features['bullying_incidents_total'] > 5:
        factors.append("High bullying incidents")
    
    if features['household_income'] == 'low':
        factors.append("Low household income")
    
    if features['distance_to_school'] > 7:
        factors.append("Long distance to school")
    
    if features['special_learning']:
        factors.append("Special learning needs")
    
    # Age-grade mismatch
    expected_age = 6 + features['standard'] + features['class_repetitions']
    if features['age'] > expected_age + 2:
        factors.append("Age-grade mismatch")
    
    return factors

def generate_recommendations(risk_level: RiskLevel, factors: List[str]) -> List[str]:
    """Generate intervention recommendations based on risk level and factors"""
    recommendations = []
    
    if "Low academic performance" in factors:
        recommendations.append("Provide additional tutoring support")
        recommendations.append("Implement personalized learning plans")
    
    if "Poor attendance" in factors:
        recommendations.append("Conduct home visits to understand barriers")
        recommendations.append("Implement attendance monitoring system")
    
    if "High bullying incidents" in factors:
        recommendations.append("Immediate counseling and peer mediation")
        recommendations.append("Enhanced supervision and anti-bullying programs")
    
    if "Low household income" in factors:
        recommendations.append("Connect family with social services")
        recommendations.append("Provide school feeding programs")
    
    if "Long distance to school" in factors:
        recommendations.append("Explore transport assistance options")
        recommendations.append("Consider boarding arrangements")
    
    if "Special learning needs" in factors:
        recommendations.append("Develop individualized education plan")
        recommendations.append("Provide specialized learning resources")
    
    # Risk level specific recommendations
    if risk_level == RiskLevel.CRITICAL:
        recommendations.append("URGENT: Schedule immediate intervention meeting")
        recommendations.append("Assign dedicated case manager")
    elif risk_level == RiskLevel.HIGH:
        recommendations.append("Schedule weekly check-ins")
        recommendations.append("Involve parents/guardians in intervention plan")
    
    return recommendations