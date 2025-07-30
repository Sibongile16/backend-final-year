# from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field
# from typing import List, Optional, Dict, Any
# import pandas as pd
# import numpy as np
# import joblib
# import logging
# from datetime import datetime, date
# from pathlib import Path
# import uvicorn
# from sqlalchemy import create_engine, select, func, and_, or_, case, text, Integer
# from sqlalchemy.orm import sessionmaker, Session
# from contextlib import asynccontextmanager
# import asyncio
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# import os
# from enum import Enum
# from models import (
#     Student, Guardian, Class, AttendanceRecord, 
#     AcademicPerformance, BullyingIncident, StudentClassHistory,
#     DropoutPrediction
# )

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Database configuration
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/school_db")
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Global variables for model artifacts
# model = None
# scaler = None
# feature_columns = None
# label_encoders = None

# class RiskLevel(str, Enum):
#     LOW = "low"
#     MEDIUM = "medium"
#     HIGH = "high"
#     CRITICAL = "critical"

# class PredictionRequest(BaseModel):
#     student_id: str
#     term_avg_score: float = Field(..., ge=0, le=600, description="Average score across all subjects")
#     school_attendance_rate: float = Field(..., ge=0, le=1, description="Attendance rate (0-1)")
#     bullying_incidents_total: int = Field(..., ge=0, description="Total bullying incidents")
#     class_repetitions: int = Field(..., ge=0, description="Number of class repetitions")
#     distance_to_school: float = Field(..., ge=0, description="Distance to school in km")
#     special_learning: bool = Field(..., description="Has special learning needs")
#     household_income: str = Field(..., description="Income level: low, medium, high")
#     orphan_status: str = Field(..., description="Orphan status: yes, no, partial")
#     standard: int = Field(..., ge=1, le=8, description="Current standard/grade")
#     age: float = Field(..., ge=5, le=18, description="Student age")
#     gender: str = Field(..., description="Gender: male, female")

# class PredictionResponse(BaseModel):
#     student_id: str
#     dropout_risk_probability: float
#     dropout_risk_binary: int
#     risk_level: RiskLevel
#     contributing_factors: List[str]
#     prediction_date: date
#     confidence_score: float
#     recommendations: List[str]

# class BatchPredictionRequest(BaseModel):
#     student_ids: List[str]
#     include_recommendations: bool = True

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()







# # Scheduler for batch predictions
# scheduler = AsyncIOScheduler()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     load_model_artifacts()
    
#     # Schedule batch predictions (daily at 2 AM)
#     scheduler.add_job(
#         run_batch_predictions,
#         'cron',
#         hour=2,
#         minute=0,
#         id='batch_predictions'
#     )
#     scheduler.start()
    
#     yield
    
#     # Shutdown
#     scheduler.shutdown()

# # FastAPI app
# app = FastAPI(
#     title="Student Dropout Risk Prediction API",
#     description="ML-powered API for predicting student dropout risk",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)