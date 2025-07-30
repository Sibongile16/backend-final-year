# app/services/daily_predictions.py
import asyncio
import logging
from datetime import datetime, date
from typing import List
from fastapi import Depends
from pytz import timezone
from sqlalchemy.orm import Session
from app.crud.prediction import fetch_student_data, save_prediction_to_db
from app.database import get_db
from app.models.all_models import PredictionTaskHistory, Student
from app.schemas.ml_model import PredictionResponse
from app.services.ml_model import generate_recommendations, get_contributing_factors
from app.utils.ml_model import load_model_artifacts, preprocess_features, determine_risk_level

logger = logging.getLogger(__name__)

# Load model once when module loads
model, scaler, feature_columns, label_encoders = load_model_artifacts()

async def generate_student_prediction(student: Student, db: Session) -> bool:
    """Generate and save prediction for a single student"""
    try:
        # Fetch student data
        features = await fetch_student_data(str(student.id), db)
        if not features:
            logger.warning(f"Insufficient data for student {student.id}")
            return False

        # Make prediction
        scaled_features = preprocess_features(features)
        probability = model.predict_proba(scaled_features)[0][1]
        
        # Prepare prediction response
        prediction = PredictionResponse(
            student_id=student.id,
            dropout_risk_probability=float(probability),
            dropout_risk_binary=int(probability >= 0.5),
            risk_level=determine_risk_level(probability),
            contributing_factors=get_contributing_factors(features, probability),
            prediction_date=date.today(),
            confidence_score=max(probability, 1-probability),
            recommendations=generate_recommendations(
                determine_risk_level(probability),
                get_contributing_factors(features, probability)
            )
        )
        
        # Save to database - AWAIT THIS COROUTINE
        await save_prediction_to_db(prediction, db)
        return True
        
    except Exception as e:
        logger.error(f"Failed to predict for student {student.id}: {str(e)}")
        return False
    
async def generate_daily_predictions(db: Session, batch_size: int = 50):
    task_record = None
    try:
        # Get total students first
        total_students = db.query(Student).filter(
            Student.status == "active"
        ).count()

        # Create task record
        task_record = PredictionTaskHistory(
            started_at=datetime.now(timezone("Africa/Blantyre")),
            status='running',
            total_students=total_students,
            processed_count=0,
            success_count=0,
            failure_count=0
        )
        db.add(task_record)
        db.commit()
        
        if total_students == 0:
            logger.warning("No active students found")
            task_record.status = 'completed'
            task_record.completed_at = datetime.now(timezone("Africa/Blantyre"))
            db.commit()
            return

        students = db.query(Student).filter(
            Student.status == "active"
        ).all()

        for i in range(0, len(students), batch_size):
            batch = students[i:i + batch_size]
            tasks = [generate_student_prediction(student, db) for student in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update task record
            task_record.processed_count = min(i + batch_size, total_students)
            task_record.success_count = sum(1 for r in results if r is True)
            task_record.failure_count = len(results) - task_record.success_count
            db.commit()

        # Final update
        task_record.status = 'completed'
        task_record.completed_at = datetime.now(timezone("Africa/Blantyre"))
        task_record.duration_seconds = (
            task_record.completed_at - task_record.started_at
        ).total_seconds()
        db.commit()

    except Exception as e:
        logger.error(f"Prediction job failed: {str(e)}")
        if task_record:
            task_record.status = 'failed'
            task_record.error_message = str(e)[:500]
            if not task_record.completed_at:
                task_record.completed_at = datetime.now(timezone("Africa/Blantyre"))
            db.commit()
        raise


def get_last_run_time(db: Session = Depends(get_db)):
    last_run = db.query(PredictionTaskHistory).order_by(
        PredictionTaskHistory.completed_at.desc()
    ).first()
    
    if last_run:
        return {
            "last_run": last_run.completed_at,
            "status": last_run.status,
            "success_count": last_run.success_count,
            "failure_count": last_run.failure_count
        }
    return {"message": "No runs recorded"}