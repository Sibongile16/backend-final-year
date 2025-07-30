from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.database import get_db
from app.models.all_models import AcademicTerm, Class, Student, Subject, SubjectScore
from app.routes.classes import SubjectScoreResponse
from app.schemas.academics_schemas import AcademicTermCreate, AcademicTermResponse, SubjectCreate, SubjectResponse, SubjectScoreCreate, SubjectType, TermType

router = APIRouter(prefix="/api/academics", tags=["academics"])

# Academic Term Endpoints
@router.post("/terms/", response_model=AcademicTermResponse, status_code=status.HTTP_201_CREATED)
def create_academic_term(term: AcademicTermCreate, db: Session = Depends(get_db)):
    # Check if student exists
    student = db.query(Student).filter(Student.id == term.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {term.student_id} not found"
        )
    
    # Check if term already exists for this student
    existing_term = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == term.student_id,
        AcademicTerm.term_type == term.term_type,
        AcademicTerm.academic_year == term.academic_year
    ).first()
    
    if existing_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Academic term already exists for this student"
        )
    
    # Create new term
    db_term = AcademicTerm(
        id=uuid.uuid4(),
        student_id=term.student_id,
        term_id=f"{term.academic_year}-{term.term_type.value}",
        term_type=term.term_type,
        academic_year=term.academic_year,
        standard=term.standard,
        term_avg_score=term.term_avg_score,
        present_days=term.present_days,
        absent_days=term.absent_days,
        cumulative_present_days=term.cumulative_present_days,
        cumulative_absent_days=term.cumulative_absent_days,
        created_at=datetime.now()
    )
    
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    
    return db_term

@router.get("/terms/", response_model=List[AcademicTermResponse])
def get_academic_terms(
    student_id: uuid.UUID = None,
    academic_year: str = None,
    term_type: TermType = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(AcademicTerm)
    
    if student_id:
        query = query.filter(AcademicTerm.student_id == student_id)
    if academic_year:
        query = query.filter(AcademicTerm.academic_year == academic_year)
    if term_type:
        query = query.filter(AcademicTerm.term_type == term_type)
    
    return query.offset(skip).limit(limit).all()

@router.get("/terms/{term_id}", response_model=AcademicTermResponse)
def get_academic_term(term_id: uuid.UUID, db: Session = Depends(get_db)):
    term = db.query(AcademicTerm).filter(AcademicTerm.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic term not found"
        )
    return term


# Subject Endpoints
@router.post("/subjects/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    # Check if subject with same name or code already exists
    existing_subject = db.query(Subject).filter(
        (Subject.name == subject.name) | (Subject.code == subject.code)
    ).first()
    
    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject with this name or code already exists"
        )
    
    db_subject = Subject(
        id=uuid.uuid4(),
        name=subject.name,
        code=subject.code,
        description=subject.description,
        type=subject.type
    )
    
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    
    return db_subject

@router.get("/subjects/", response_model=List[SubjectResponse])
def get_subjects(
    type: SubjectType = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Subject)
    
    if type:
        query = query.filter(Subject.type == type)
    
    return query.offset(skip).limit(limit).all()

@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: uuid.UUID, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return subject

# Student Academic Summary
@router.get("/students/{student_id}/summary")
def get_student_academic_summary(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get all academic terms for the student
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == student_id
    ).order_by(AcademicTerm.academic_year, AcademicTerm.term_type).all()
    
    # Get all subject scores for each term
    term_summaries = []
    for term in terms:
        scores = db.query(SubjectScore).filter(
            SubjectScore.academic_term_id == term.id
        ).all()
        
        term_summaries.append({
            "term": term,
            "scores": scores
        })
    
    # Get current class information
    current_class = None
    if student.class_id:
        current_class = db.query(Class).filter(Class.id == student.class_id).first()
    
    return {
        "student": student,
        "current_class": current_class,
        "academic_history": term_summaries
    }