from datetime import date
from app.crud.prediction import fetch_student_data, save_prediction_to_db
from app.database import SessionLocal
from app.models.all_models import Student
from app.schemas.ml_model import PredictionResponse
from app.services.ml_model import generate_recommendations, get_contributing_factors
from app.utils.ml_model import determine_risk_level, preprocess_features
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import asyncio
import logging
from utils.ml_model import load_model_artifacts

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
model, scaler, feature_columns, label_encoders = load_model_artifacts()


async def run_batch_predictions():
    
    """Run batch predictions for all active students using SQLAlchemy ORM"""
    logger.info("Starting batch prediction job")
    
    try:
        db = SessionLocal()
        
        # Get all active students
        students = db.query(Student.id)\
                    .filter(Student.is_active == True)\
                    .all()
        
        for student in students:
            student_data = await fetch_student_data(str(student.id), db)
            if student_data:
                # Make prediction
                load_model_artifacts()
                features = preprocess_features(student_data)
                probability = model.predict_proba(features)[0][1]
                
                # Create prediction response
                prediction = PredictionResponse(
                    student_id=str(student.id),
                    dropout_risk_probability=float(probability),
                    dropout_risk_binary=int(probability >= 0.5),
                    risk_level=determine_risk_level(probability),
                    contributing_factors=get_contributing_factors(student_data, probability),
                    prediction_date=date.today(),
                    confidence_score=max(probability, 1-probability),
                    recommendations=generate_recommendations(
                        determine_risk_level(probability),
                        get_contributing_factors(student_data, probability)
                    )
                )
                
                # Save to database
                await save_prediction_to_db(prediction, db)
        
        db.close()
        logger.info("Batch prediction job completed")
        
    except Exception as e:
        logger.error(f"Error in batch prediction job: {e}")
        

@asynccontextmanager
async def lifespan():
    # Startup
    load_model_artifacts()
    
    # Schedule batch predictions
    scheduler.add_job(
        run_batch_predictions,
        'cron',
        hour=17,
        minute=8,
        id='batch_predictions'
    )
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()