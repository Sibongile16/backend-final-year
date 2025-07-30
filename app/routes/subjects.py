# routers/subject_router.py

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import distinct
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.all_models import Class, Subject


router = APIRouter(prefix="/api/subs", tags=["Subjects"])

from pydantic import BaseModel
from uuid import UUID
from enum import Enum


class SubjectTypeEnum(str, Enum):
    core = "core"
    elective = "elective"
    extracurricular = "extracurricular"


class SubjectOut(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None = None
    type: SubjectTypeEnum

    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    subjects: List[SubjectOut]

class AcademicYearListResponse(BaseModel):
    academic_years: List[str]




@router.get("/subjects", response_model=SubjectListResponse)
def get_all_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).order_by(Subject.name.asc()).all()
    return {"subjects": subjects}


@router.get("/academic-years", response_model=AcademicYearListResponse)
def get_academic_years(db: Session = Depends(get_db)):
    years = db.query(distinct(Class.academic_year)).order_by(Class.academic_year.desc()).all()
    # Flatten result from list of tuples
    return {"academic_years": [y[0] for y in years]}