# Global variables for model artifacts
from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


model = None
scaler = None
feature_columns = None
label_encoders = None

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PredictionRequest(BaseModel):
    student_id: UUID
    term_avg_score: float = Field(..., ge=0, le=600, description="Average score across all subjects")
    school_attendance_rate: float = Field(..., ge=0, le=1, description="Attendance rate (0-1)")
    bullying_incidents_total: int = Field(..., ge=0, description="Total bullying incidents")
    class_repetitions: int = Field(..., ge=0, description="Number of class repetitions")
    distance_to_school: float = Field(..., ge=0, description="Distance to school in km")
    special_learning: bool = Field(..., description="Has special learning needs")
    household_income: str = Field(..., description="Income level: low, medium, high")
    orphan_status: str = Field(..., description="Orphan status: yes, no, partial")
    standard: int = Field(..., ge=1, le=8, description="Current standard/grade")
    age: float = Field(..., ge=5, le=18, description="Student age")
    gender: str = Field(..., description="Gender: male, female")

class PredictionResponse(BaseModel):
    student_id: UUID
    dropout_risk_probability: float
    dropout_risk_binary: int
    risk_level: RiskLevel
    contributing_factors: List[str]
    prediction_date: date
    confidence_score: float
    recommendations: List[str]

class BatchPredictionRequest(BaseModel):
    student_ids: List[UUID]
    include_recommendations: bool = True
    
class RiskDistributionItem(BaseModel):
    risk_level: str
    count: int

class RiskDistributionResponse(BaseModel):
    risk_distribution: List[RiskDistributionItem]
    

class StudentPredictionItem(BaseModel):
    risk_score: float
    risk_level: str
    contributing_factors: List[str]
    prediction_date: date
    recommendations: List[str]
    created_at: datetime

class StudentPredictionHistoryResponse(BaseModel):
    student_id: str
    predictions: List[StudentPredictionItem]
    
    
class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_processed: int
    

class SystemHealth(BaseModel):
    cpu_usage: float
    memory_usage: float
    status: str

class HealthCheckResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: datetime
    system: SystemHealth
    
    
class RealtimePrediction(BaseModel):
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="low/medium/high/critical")
    timestamp: datetime
    confidence: Optional[float] = Field(None, ge=0, le=1)
    factors: Optional[List[str]] = None
    error: Optional[str] = Field(None, description="Error message if prediction failed")

class StudentWithRisk(BaseModel):
    student_id: UUID
    fullname: str
    gender: str
    age: int
    status: str
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str]
    last_prediction_date: Optional[datetime]
    last_updated: datetime
    class_name: str
    realtime_prediction: Optional[RealtimePrediction] = None
    
    

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class RiskLevelEnum(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class SubjectScoreOut(BaseModel):
    subject: str
    score: float
    grade: str


class RealTimePrediction(BaseModel):
    risk_score: float = Field(..., description="Predicted dropout risk percentage")
    risk_level: RiskLevel
    contributing_factors: List[str]
    recommendations: List[str]
    prediction_time: datetime


class HistoricalPrediction(BaseModel):
    date: datetime
    risk_level: str
    score: float


class AcademicPerformance(BaseModel):
    current_term: Optional[str]
    average_score: Optional[float]
    subject_scores: List[SubjectScoreOut]


class StudentInfo(BaseModel):
    id: str
    student_id: str
    name: str
    age: int
    gender: str
    status: str
    class_: Optional[str] = Field(None, alias="class")


class RiskAssessment(BaseModel):
    real_time_prediction: RealTimePrediction
    historical_predictions: List[HistoricalPrediction]


class StudentDataResponse(BaseModel):
    student_info: StudentInfo
    academic_performance: AcademicPerformance
    risk_assessment: RiskAssessment
