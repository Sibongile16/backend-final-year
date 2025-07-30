# routers/grades.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.crud.grades import submit_end_of_term_report
from app.database import get_db
from app.schemas.grades_schemas import EndOfTermReportInput



router = APIRouter(prefix="/api/reports", tags=["End-of-Term Reports"])

@router.post("/submit-student-grades")
def submit_term_report(data: EndOfTermReportInput, db: Session = Depends(get_db)):
    return submit_end_of_term_report(db, data)