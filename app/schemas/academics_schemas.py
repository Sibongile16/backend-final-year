from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum
from uuid import UUID

class TermType(str, Enum):
    term1 = "term1"
    term2 = "term2"
    term3 = "term3"

class SubjectType(str, Enum):
    core = "core"
    elective = "elective"
    extracurricular = "extracurricular"

class AcademicTermBase(BaseModel):
    student_id: UUID
    term_type: TermType
    academic_year: str
    standard: int
    
    @field_validator('academic_year')
    def validate_academic_year(cls, v):
        if len(v) != 9 or not v.startswith('20') or not v[4] == '-':
            raise ValueError('Academic year must be in format "YYYY-YYYY"')
        return v

class AcademicTermCreate(AcademicTermBase):
    term_avg_score: Optional[float] = None
    present_days: Optional[int] = 0
    absent_days: Optional[int] = 0
    cumulative_present_days: Optional[int] = 0
    cumulative_absent_days: Optional[int] = 0

class AcademicTermResponse(AcademicTermBase):
    id: UUID
    term_id: str
    term_avg_score: Optional[float]
    present_days: int
    absent_days: int
    cumulative_present_days: int
    cumulative_absent_days: int
    created_at: datetime
    
    class Config:
        from_attrbutes = True

class SubjectScoreBase(BaseModel):
    academic_term_id: UUID
    subject_id: UUID
    score: float
    
    @field_validator('score')
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Score must be between 0 and 100')
        return v

class SubjectScoreCreate(SubjectScoreBase):
    grade: Optional[str] = None

class SubjectScoreResponse(SubjectScoreBase):
    id: UUID
    grade: Optional[str]
    
    class Config:
        from_attrbutes = True

class SubjectBase(BaseModel):
    name: str
    code: str
    type: SubjectType = SubjectType.core

class SubjectCreate(SubjectBase):
    description: Optional[str] = None

class SubjectResponse(SubjectBase):
    id: UUID
    description: Optional[str]
    
    class Config:
        from_attrbutes = True