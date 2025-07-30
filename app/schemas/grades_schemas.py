# schemas/grades.py

from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import List, Optional

class TermTypeEnum(str, Enum):
    TERM1 = "term1"
    TERM2 = "term2"
    TERM3 = "term3"


class SubjectScoreInput(BaseModel):
    subject_id: UUID
    score: float
    grade: Optional[str] = None

class EndOfTermReportInput(BaseModel):
    student_id: UUID
    academic_year: str
    term_type: TermTypeEnum
    standard: int
    present_days: int
    absent_days: int
    subject_scores: List[SubjectScoreInput]
    remarks: Optional[str] = None

