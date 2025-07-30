from datetime import datetime
import logging
from uuid import UUID
from fastapi import HTTPException
from pytz import timezone
from sqlalchemy import func, and_, or_, case, text, Integer
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.models.all_models import (
    Student, Guardian, Class, AcademicTerm, Subject,
    SubjectScore, BullyingRecord, DropoutPrediction
)
from app.schemas.ml_model import PredictionResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_student_data(student_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Fetch student data from database and map to model-expected categories"""
    try:
        # Get the most recent academic term for the student
        current_term = db.query(AcademicTerm).filter(
            AcademicTerm.student_id == student_id
        ).order_by(
            AcademicTerm.academic_year.desc(),
            AcademicTerm.term_type.desc()
        ).first()

        if not current_term:
            logger.warning(f"No academic terms found for student {student_id}")
            return None

        # Get subject scores for the current term
        subject_scores = db.query(
            SubjectScore.score,
            Subject.name
        ).join(
            Subject,
            SubjectScore.subject_id == Subject.id
        ).filter(
            SubjectScore.academic_term_id == current_term.id
        ).all()

        # Calculate average score from subject scores
        avg_score = sum(score.score for score in subject_scores) / len(subject_scores) if subject_scores else 300

        # Get bullying records for the current term
        bullying_record = db.query(BullyingRecord).filter(
            BullyingRecord.academic_term_id == current_term.id
        ).first()

        # Get student and guardian information
        student = db.query(
            Student,
            Guardian
        ).join(
            Guardian,
            Student.guardian_id == Guardian.id
        ).filter(
            Student.id == student_id
        ).first()

        if not student:
            logger.error(f"Student {student_id} not found")
            return None

        student_obj, guardian = student

        # ===== VALUE MAPPING =====
        # 1. Map household_income to ['low', 'medium', 'high']
        income_mapping = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'very_low': 'low',
            'very_high': 'high'
        }
        household_income = income_mapping.get(
            (student_obj.household_income.value if student_obj.household_income else 'medium').lower(),
            'medium'  # default value
        )

        # 2. Map orphan_status to ['none', 'single', 'double']
        orphan_status = 'none'
        if guardian.relationship_to_student.value != 'parent':
            # Simplified logic - adjust based on your actual orphan status determination
            orphan_status = 'single'  
            # For actual implementation, you might need:
            # if both_parents_deceased: orphan_status = 'double'
            # else: orphan_status = 'single'

        # 3. Map gender to ['Male', 'Female']
        gender = student_obj.gender.value.capitalize()
        if gender not in ['Male', 'Female']:
            gender = 'Male'  # default value

        # Calculate age-grade mismatch
        expected_age = 6 + current_term.standard + (student_obj.class_repetitions or 0)
        age_grade_mismatch = student_obj.age > expected_age + 2 if student_obj.age else False

        return {
            'student_id': str(student_obj.id),
            'age': student_obj.age,
            'gender': gender,
            'distance_to_school': student_obj.distance_to_school or 5.0,
            'special_learning': student_obj.special_learning or False,
            'household_income': household_income,
            'orphan_status': orphan_status,
            'school_attendance_rate': current_term.present_days / (current_term.present_days + current_term.absent_days) 
                                    if (current_term.present_days + current_term.absent_days) > 0 else 0.8,
            'term_avg_score': avg_score,
            'bullying_incidents_total': bullying_record.incidents_reported if bullying_record else 0,
            'class_repetitions': student_obj.class_repetitions or 0,
            'standard': current_term.standard,
            'textbook_availability': student_obj.textbook_availability or False,
            'age_grade_mismatch': age_grade_mismatch
        }
        
    except Exception as e:
        logger.error(f"Error fetching student data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching student data: {str(e)}"
        )


async def save_prediction_to_db(prediction: PredictionResponse, db: Session):
    """Save prediction to database using SQLAlchemy ORM"""
    try:
        # Check if student exists
        student = db.query(Student).filter(Student.id == prediction.student_id).first()
        if not student:
            logger.error(f"Student {prediction.student_id} not found")
            raise ValueError(f"Student {prediction.student_id} not found")

        new_prediction = DropoutPrediction(
            student_id=prediction.student_id,
            risk_score=prediction.dropout_risk_probability * 100,
            risk_level=prediction.risk_level.value,
            contributing_factors=prediction.contributing_factors,
            prediction_date=prediction.prediction_date,
            algorithm_version='xgboost_v2.0', 
            teacher_notified=False,
            intervention_recommended='; '.join(prediction.recommendations),
            created_at=datetime.now(timezone("Africa/Blantyre"))
        )
        
        db.add(new_prediction)
        db.commit()
        logger.info(f"Prediction saved for student {prediction.student_id}")
        
    except Exception as e:
        logger.error(f"Error saving prediction: {e}", exc_info=True)
        db.rollback()  # Use async rollback if available
        raise
        
