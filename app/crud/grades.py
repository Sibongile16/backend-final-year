# services/grades.py

from sqlalchemy.orm import Session
from app.models.all_models import SubjectScore, AcademicTerm, Subject, Student
from fastapi import HTTPException
import uuid

from app.schemas.grades_schemas import EndOfTermReportInput



def submit_end_of_term_report(db: Session, data: EndOfTermReportInput):
    # Check student
    student = db.query(Student).filter_by(id=data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if term already exists
    term = db.query(AcademicTerm).filter_by(
        student_id=data.student_id,
        academic_year=data.academic_year,
        term_type=data.term_type
    ).first()

    if term:
        raise HTTPException(status_code=400, detail="Report already exists for this term")

    # Calculate average score
    scores = [s.score for s in data.subject_scores]
    term_avg = sum(scores) / len(scores) if scores else None

    academic_term = AcademicTerm(
        id=uuid.uuid4(),
        student_id=data.student_id,
        academic_year=data.academic_year,
        term_type=data.term_type,
        standard=data.standard,
        present_days=data.present_days,
        absent_days=data.absent_days,
        cumulative_present_days=data.present_days,
        cumulative_absent_days=data.absent_days,
        term_avg_score=term_avg
    )
    db.add(academic_term)
    db.flush()  # Get academic_term.id before committing

    # Add subject scores
    for s in data.subject_scores:
        subject_score = SubjectScore(
            id=uuid.uuid4(),
            academic_term_id=academic_term.id,
            subject_id=s.subject_id,
            score=s.score,
            grade=s.grade
        )
        db.add(subject_score)

    db.commit()
    db.refresh(academic_term)
    return {"message": "Term report submitted", "academic_term_id": academic_term.id}