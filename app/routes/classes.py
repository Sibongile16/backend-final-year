from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.all_models import (
    Class, Student, Subject, TeacherClass, Teacher, Guardian,
    AcademicTerm, SubjectScore, StudentStatus
)
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date
from enum import Enum

router = APIRouter(prefix="/api/classes", tags=["classes"])


class ClassCreate(BaseModel):
    name: str
    code: str
    academic_year: str
    capacity: Optional[int] = None
    is_active: bool = True

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    academic_year: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None

class ClassResponse(BaseModel): 
    id: UUID
    name: str
    code: str
    academic_year: str
    capacity: Optional[int] = None
    is_active: bool
    
    class Config:
        from_attributes = True

class ClassListResponse(BaseModel):
    classes: List[ClassResponse]
    total_count: int

class StudentResponse(BaseModel):
    id: UUID
    student_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    gender: str
    home_address: Optional[str] = None
    enrollment_date: date
    status: StudentStatus
    
    class Config:
        from_attributes = True

class GuardianResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    relationship_to_student: str
    phone_number: Optional[str] = None
    
    class Config:
        from_attributes = True

class SubjectScoreResponse(BaseModel):
    subject_name: str
    score: float
    grade: str

class TermPerformanceResponse(BaseModel):
    term_id: str
    term_type: str
    academic_year: str
    standard: int
    term_avg_score: float
    present_days: int
    absent_days: int
    subject_scores: List[SubjectScoreResponse]

class StudentWithDetailsResponse(StudentResponse):
    guardian: GuardianResponse
    current_class: Optional[ClassResponse] = None
    performance_history: Optional[List[TermPerformanceResponse]] = None

class TeacherResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    
    class Config:
        from_attributes = True

class ClassWithStudentsResponse(ClassResponse):
    students: List[StudentWithDetailsResponse]

class ClassWithTeachersResponse(ClassResponse):
    teachers: List[TeacherResponse]

class ClassFullDetailsResponse(ClassResponse):
    students: List[StudentWithDetailsResponse]
    teachers: List[TeacherResponse]

# Helper function to get class or raise 404
def get_class_or_404(db: Session, class_id: UUID):
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return db_class

def get_student_performance(db: Session, student_id: UUID):
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == student_id
    ).order_by(
        AcademicTerm.academic_year,
        AcademicTerm.term_type
    ).all()

    performance = []
    for term in terms:
        scores = db.query(
            SubjectScore,
            Subject.name.label('subject_name')
        ).join(
            Subject,
            SubjectScore.subject_id == Subject.id
        ).filter(
            SubjectScore.academic_term_id == term.id
        ).all()

        performance.append(TermPerformanceResponse(
            term_id=term.term_id,
            term_type=term.term_type.value,
            academic_year=term.academic_year,
            standard=term.standard,
            term_avg_score=term.term_avg_score,
            present_days=term.present_days,
            absent_days=term.absent_days,
            subject_scores=[
                SubjectScoreResponse(
                    subject_name=score.subject_name,
                    score=score.score,
                    grade=score.grade
                ) for score in scores
            ]
        ))

    return performance

# Create a new class
# @router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
# async def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
#     # Check if class with same code and academic year already exists
#     existing_class = db.query(Class).filter(
#         Class.code == class_data.code,
#         Class.academic_year == class_data.academic_year
#     ).first()
    
#     if existing_class:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Class with this code already exists for the academic year"
#         )
    
#     db_class = Class(**class_data.model_dump())
#     db.add(db_class)
#     db.commit()
#     db.refresh(db_class)
#     return db_class

# Get all classes
# @router.get("/", response_model=ClassListResponse)
# async def get_classes(
#     skip: int = 0,
#     limit: int = 100,
#     is_active: Optional[bool] = None,
#     academic_year: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     query = db.query(Class)
    
#     if is_active is not None:
#         query = query.filter(Class.is_active == is_active)
    
#     if academic_year:
#         query = query.filter(Class.academic_year == academic_year)
    
#     classes = query.offset(skip).limit(limit).all()
#     total_count = query.count()
    
#     return ClassListResponse(classes=classes, total_count=total_count)

# Get a class by ID
@router.get("/{class_id}", response_model=ClassResponse)
async def get_class_by_id(class_id: UUID, db: Session = Depends(get_db)):
    return get_class_or_404(db, class_id)

# Update a class
@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: UUID, 
    class_data: ClassUpdate, 
    db: Session = Depends(get_db)
):
    db_class = get_class_or_404(db, class_id)
    
    update_data = class_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_class, field, value)
    
    db.commit()
    db.refresh(db_class)
    return db_class

# Delete a class (soft delete by setting is_active=False)
@router.delete("/{class_id}", response_model=ClassResponse)
async def delete_class(class_id: UUID, db: Session = Depends(get_db)):
    db_class = get_class_or_404(db, class_id)
    db_class.is_active = False
    db.commit()
    db.refresh(db_class)
    return db_class

# Get classes by academic year
@router.get("/academic-year/{academic_year}", response_model=ClassListResponse)
async def get_classes_by_academic_year(
    academic_year: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    classes = db.query(Class).filter(
        Class.academic_year == academic_year
    ).offset(skip).limit(limit).all()
    
    total_count = db.query(Class).filter(
        Class.academic_year == academic_year
    ).count()
    
    return ClassListResponse(classes=classes, total_count=total_count)

# Get classes with students
@router.get("/with-students", response_model=List[ClassWithStudentsResponse])
async def get_classes_with_all_students(
    academic_year: Optional[str] = None,
    is_active: Optional[bool] = None,
    include_performance: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Class).options(
        joinedload(Class.students).joinedload(Student.guardian),
        joinedload(Class.students).joinedload(Student.class_)
    )
    
    if academic_year:
        query = query.filter(Class.academic_year == academic_year)
    
    if is_active is not None:
        query = query.filter(Class.is_active == is_active)
    
    classes = query.all()
    
    response = []
    for class_ in classes:
        class_data = ClassWithStudentsResponse.from_orm(class_)
        students_with_performance = []
        
        for student in class_.students:
            student_data = StudentWithDetailsResponse.from_orm(student)
            if include_performance:
                student_data.performance_history = get_student_performance(db, student.id)
            students_with_performance.append(student_data)
        
        class_data.students = students_with_performance
        response.append(class_data)
    
    return response

# Get students by class ID
# @router.get("/{class_id}/students", response_model=List[StudentWithDetailsResponse])
# async def get_students_by_class_id(
#     class_id: UUID,
#     is_active: Optional[bool] = None,
#     include_performance: bool = False,
#     db: Session = Depends(get_db)
# ):
#     query = db.query(Student).filter(
#         Student.class_id == class_id
#     ).options(
#         joinedload(Student.guardian),
#         joinedload(Student.class_)
#     )
    
#     if is_active is not None:
#         query = query.filter(Student.status == StudentStatus.ACTIVE if is_active else Student.status != StudentStatus.ACTIVE)
    
#     students = query.all()
    
#     response = []
#     for student in students:
#         student_data = StudentWithDetailsResponse.from_orm(student)
#         if include_performance:
#             student_data.performance_history = get_student_performance(db, student.id)
#         response.append(student_data)
    
#     return response

# Get teachers assigned to a class
@router.get("/{class_id}/teachers", response_model=List[TeacherResponse])
async def get_class_teachers(
    class_id: UUID,
    academic_year: Optional[str] = None,
    is_class_teacher: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Teacher).join(TeacherClass).filter(
        TeacherClass.class_id == class_id
    )
    
    if academic_year:
        query = query.filter(TeacherClass.academic_year == academic_year)
    
    if is_class_teacher is not None:
        query = query.filter(TeacherClass.is_class_teacher == is_class_teacher)
    
    teachers = query.all()
    return teachers

# Get class with students and teachers
@router.get("/{class_id}/full-details", response_model=ClassFullDetailsResponse)
async def get_class_full_details_new(
    class_id: UUID,
    include_performance: bool = False,
    db: Session = Depends(get_db)
):
    db_class = db.query(Class).options(
        joinedload(Class.students).joinedload(Student.guardian),
        joinedload(Class.teacher_classes).joinedload(TeacherClass.teacher)
    ).filter(Class.id == class_id).first()
    
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    response = ClassFullDetailsResponse.from_orm(db_class)
    
    # Process students with performance data if requested
    students_with_performance = []
    for student in db_class.students:
        student_data = StudentWithDetailsResponse.from_orm(student)
        if include_performance:
            student_data.performance_history = get_student_performance(db, student.id)
        students_with_performance.append(student_data)
    
    response.students = students_with_performance
    response.teachers = [teacher for tc in db_class.teacher_classes for teacher in [tc.teacher]]
    
    return response