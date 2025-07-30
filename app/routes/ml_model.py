from datetime import date, datetime
import logging
from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
import psutil
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session
from app.crud.prediction import fetch_student_data, save_prediction_to_db
from app.database import get_db
from app.models.all_models import AcademicTerm, BullyingIncident, Class, DropoutPrediction, Guardian, Student, Subject, SubjectScore
from app.schemas.ml_model import BatchPredictionRequest, BatchPredictionResponse, HealthCheckResponse, PredictionRequest, PredictionResponse, RiskDistributionResponse, StudentDataResponse, StudentPredictionHistoryResponse, StudentWithRisk
from app.services.ml_model import generate_recommendations, get_contributing_factors
from app.utils.ml_model import determine_risk_level, load_model_artifacts, preprocess_features
from app.utils.system_utils import determine_system_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

model, scaler, feature_columns, label_encoders = load_model_artifacts()
@router.get("/")
async def root():
    return {"message": "Student Dropout Risk Prediction API", "version": "1.0.0"}

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    system_status = determine_system_status(cpu, memory)

    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now(),
        "system": {
            "cpu_usage": cpu,
            "memory_usage": memory,
            "status": system_status
        }
    }

@router.get("/student/{student_id}", response_model=StudentDataResponse)
async def get_student_data_with_realtime_prediction(
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive student data including:
    - Basic info
    - Academic performance
    - Attendance
    - Bullying incidents
    - Real-time dropout prediction
    - Guardian info
    """
    try:
        # 1. Fetch student data from DB
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # 2. Fetch related data for prediction
        guardian = db.query(Guardian).filter(Guardian.id == student.guardian_id).first()
        class_info = db.query(Class).filter(Class.id == student.class_id).first()
        current_term = db.query(AcademicTerm).filter(
            AcademicTerm.student_id == student_id
        ).order_by(
            AcademicTerm.academic_year.desc(),
            AcademicTerm.term_type.desc()
        ).first()

        # 3. Prepare features for ML model
        features = await fetch_student_data(student_id, db)
        if not features:
            raise HTTPException(status_code=400, detail="Insufficient data for prediction")

        # 4. Make real-time prediction
        scaled_features = preprocess_features(features)
        probability = model.predict_proba(scaled_features)[0][1]
        risk_level = determine_risk_level(probability)
        contributing_factors = get_contributing_factors(features, probability)
        recommendations = generate_recommendations(risk_level, contributing_factors)

        # 5. Get additional data for response
        subject_scores = []
        if current_term:
            subject_scores = db.query(
                Subject.name,
                SubjectScore.score,
                SubjectScore.grade
            ).join(
                Subject,
                SubjectScore.subject_id == Subject.id
            ).filter(
                SubjectScore.academic_term_id == current_term.id
            ).all()

        bullying_incidents = db.query(BullyingIncident).filter(
            BullyingIncident.student_id == student_id
        ).order_by(BullyingIncident.incident_date.desc()).limit(5).all()

        # 6. Build response with real-time prediction
        response = {
            "student_info": {
                "id": str(student.id),
                "student_id": student.student_id,
                "name": f"{student.first_name} {student.last_name}",
                "age": student.age,
                "gender": student.gender.value,
                "status": student.status.value,
                "class": class_info.name if class_info else None,
            },
            "academic_performance": {
                "current_term": current_term.term_type.value if current_term else None,
                "average_score": current_term.term_avg_score if current_term else None,
                "subject_scores": [
                    {"subject": s.name, "score": s.score, "grade": s.grade} 
                    for s in subject_scores
                ],
            },
            "risk_assessment": {
                "real_time_prediction": {
                    "risk_score": float(probability * 100),  # Convert to percentage
                    "risk_level": risk_level.value,
                    "contributing_factors": contributing_factors,
                    "recommendations": recommendations,
                    "prediction_time": datetime.now().isoformat()
                },
                "historical_predictions": [
                    {
                        "date": p.prediction_date.isoformat(),
                        "risk_level": p.risk_level,
                        "score": p.risk_score
                    } 
                    for p in db.query(DropoutPrediction)
                    .filter(DropoutPrediction.student_id == student_id)
                    .order_by(DropoutPrediction.prediction_date.desc())
                    .limit(3)
                    .all()
                ]
            }
        }

        return response

    except Exception as e:
        logger.error(f"Error in real-time prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class/{class_id}/students", response_model=List[StudentWithRisk])
async def get_class_students_with_risk(
    class_id: str,
    realtime: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get students by class with risk data
    Returns:
    - student_id, fullname, gender, age, status
    - risk_score, risk_level (from latest prediction)
    - realtime prediction (if requested)
    - last_updated timestamp
    - class_name
    """
    try:
        # Verify class exists and get class name
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")

        # Get all students in the class
        students = db.query(Student).filter(Student.class_id == class_id).all()
        if not students:
            return []

        results = []
        for student in students:
            # Get latest prediction
            latest_prediction = db.query(DropoutPrediction).filter(
                DropoutPrediction.student_id == student.id
            ).order_by(DropoutPrediction.prediction_date.desc()).first()

            # Prepare base response
            student_data = {
                "student_id": student.id,
                "fullname": f"{student.first_name} {student.last_name}",
                "gender": student.gender.value,
                "age": student.age,
                "status": student.status.value,
                "risk_score": latest_prediction.risk_score if latest_prediction else None,
                "risk_level": latest_prediction.risk_level if latest_prediction else "unknown",
                "last_prediction_date": latest_prediction.prediction_date.isoformat() if latest_prediction else None,
                "last_updated": student.updated_at.isoformat(),
                "class_name": class_obj.name,
                "realtime_prediction": None
            }

            # Calculate realtime prediction if requested
            if realtime:
                try:
                    features = await fetch_student_data(str(student.id), db)
                    if features:
                        scaled_features = preprocess_features(features)
                        probability = model.predict_proba(scaled_features)[0][1]
                        
                        student_data["realtime_prediction"] = {
                            "risk_score": float(probability * 100),
                            "risk_level": determine_risk_level(probability).value,
                            "timestamp": datetime.now().isoformat(),
                            "confidence": max(probability, 1-probability),
                            "factors": get_contributing_factors(features, probability)
                        }
                except Exception as e:
                    logger.warning(f"Realtime prediction failed for {student.id}: {str(e)}")
                    student_data["realtime_prediction"] = {
                        "error": "Prediction unavailable"
                    }

            results.append(student_data)

        return results

    except Exception as e:
        logger.error(f"Error in class students endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/predict", response_model=PredictionResponse)
async def predict_dropout_risk(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Predict dropout risk for a single student"""
    student = db.query(Student).filter(Student.id == request.student_id).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {request.student_id} does not exist."
        )
    try:
        # Prepare features
        features_dict = request.model_dump()
        features = preprocess_features(features_dict)
        
        # Make prediction
        probability = model.predict_proba(features)[0][1]
        binary_prediction = int(probability >= 0.5)
        
        # Determine risk level
        risk_level = determine_risk_level(probability)
        
        # Get contributing factors
        contributing_factors = get_contributing_factors(features_dict, probability)
        
        # Generate recommendations
        recommendations = generate_recommendations(risk_level, contributing_factors)
        
        # Create response
        prediction_response = PredictionResponse(
            student_id=request.student_id,
            dropout_risk_probability=float(probability),
            dropout_risk_binary=binary_prediction,
            risk_level=risk_level,
            contributing_factors=contributing_factors,
            prediction_date=date.today(),
            confidence_score=max(probability, 1-probability),
            recommendations=recommendations
        )
        
        # Save to database in background
        background_tasks.add_task(save_prediction_to_db, prediction_response, db)
        
        return prediction_response
        
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_dropout_risk(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Predict dropout risk for multiple students"""
    try:
        predictions = []
        
        for student_id in request.student_ids:
            # Fetch student data from database
            student_data = await fetch_student_data(student_id, db)
            
            if student_data:
                # Make prediction
                features = preprocess_features(student_data)
                probability = model.predict_proba(features)[0][1]
                
                # Create prediction response
                prediction = PredictionResponse(
                    student_id=student_id,
                    dropout_risk_probability=float(probability),
                    dropout_risk_binary=int(probability >= 0.5),
                    risk_level=determine_risk_level(probability),
                    contributing_factors=get_contributing_factors(student_data, probability),
                    prediction_date=date.today(),
                    confidence_score=max(probability, 1-probability),
                    recommendations=generate_recommendations(
                        determine_risk_level(probability),
                        get_contributing_factors(student_data, probability)
                    ) if request.include_recommendations else []
                )
                
                predictions.append(prediction)
                
                # Save to database in background
                background_tasks.add_task(save_prediction_to_db, prediction, db)
        
        return {"predictions": predictions, "total_processed": len(predictions)}
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/{student_id}", response_model=StudentPredictionHistoryResponse)
async def get_student_predictions(
    student_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get historical predictions for a student using SQLAlchemy ORM"""
    try:
        predictions = db.query(
            DropoutPrediction.risk_score,
            DropoutPrediction.risk_level,
            DropoutPrediction.contributing_factors,
            DropoutPrediction.prediction_date,
            DropoutPrediction.intervention_recommended,
            DropoutPrediction.created_at
        )\
        .filter(DropoutPrediction.student_id == student_id)\
        .order_by(DropoutPrediction.created_at.desc())\
        .limit(limit)\
        .all()
        
        return {
            "student_id": student_id,
            "predictions": [
                {
                    "risk_score": pred.risk_score,
                    "risk_level": pred.risk_level,
                    "contributing_factors": pred.contributing_factors,
                    "prediction_date": pred.prediction_date,
                    "recommendations": pred.intervention_recommended,
                    "created_at": pred.created_at
                }
                for pred in predictions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/risk-distribution", response_model=RiskDistributionResponse)
async def get_risk_distribution(db: Session = Depends(get_db)):
    """Get distribution of risk levels across all students using SQLAlchemy ORM"""
    try:
        # Subquery to get latest prediction for each student
        latest_prediction_subq = (
            db.query(
                DropoutPrediction.student_id,
                func.max(DropoutPrediction.created_at).label('latest_prediction')
            )
            .group_by(DropoutPrediction.student_id)
            .subquery()
        )
        
        # Main query to count risk levels
        risk_counts = db.query(
            DropoutPrediction.risk_level,
            func.count().label('count')
        )\
        .join(
            latest_prediction_subq,
            and_(
                DropoutPrediction.student_id == latest_prediction_subq.c.student_id,
                DropoutPrediction.created_at == latest_prediction_subq.c.latest_prediction
            )
        )\
        .group_by(DropoutPrediction.risk_level)\
        .order_by(
            case(
                (DropoutPrediction.risk_level == 'low', 1),
                (DropoutPrediction.risk_level == 'medium', 2),
                (DropoutPrediction.risk_level == 'high', 3),
                (DropoutPrediction.risk_level == 'critical', 4),
                else_=5
            )
        )\
        .all()
        
        return {
            "risk_distribution": [
                {"risk_level": result.risk_level, "count": result.count}
                for result in risk_counts
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching risk distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
