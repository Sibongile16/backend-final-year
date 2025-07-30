from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID

from app.database import get_db
from app.routes.new_classes import extract_grade_level
from app.utils.auth import get_current_user
from app.models.all_models import (
    Subject, Teacher, TeacherClass, User, Student, Guardian, Class, Gender, RelationshipType, 
    TransportMethod, IncomeLevel, StudentStatus, AcademicTerm,
    SubjectScore, DropoutPrediction, UserRole, TermType
)
from pytz import timezone

router = APIRouter(prefix="/api/students", tags=["students"])

# Pydantic Models
class GuardianBase(BaseModel):
    first_name: str
    last_name: str
    relationship_to_student: RelationshipType
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None

    class Config:
        from_attributes = True

class GuardianCreate(GuardianBase):
    pass

class GuardianResponse(GuardianBase):
    id: UUID

class SubjectScoreResponse(BaseModel):
    subject_name: str
    score: float
    grade: str

class TermPerformanceResponse(BaseModel):
    term_id: UUID
    term_type: TermType
    academic_year: str
    standard: int
    term_avg_score: float
    present_days: int
    absent_days: int
    subject_scores: List[SubjectScoreResponse]

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    home_address: Optional[str] = None
    distance_to_school: Optional[float] = None
    transport_method: Optional[TransportMethod] = None
    enrollment_date: date
    special_learning: Optional[bool] = None
    textbook_availability: Optional[bool] = None
    class_repetitions: Optional[int] = None
    household_income: Optional[IncomeLevel] = None

    class Config:
        from_attributes = True

class StudentCreate(StudentBase):
    guardian_id: UUID
    class_id: Optional[UUID] = None

class StudentUpdate(BaseModel):
    student_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    home_address: Optional[str] = None
    distance_to_school: Optional[float] = None
    transport_method: Optional[TransportMethod] = None
    enrollment_date: Optional[date] = None
    special_learning: Optional[bool] = None
    textbook_availability: Optional[bool] = None
    class_repetitions: Optional[int] = None
    household_income: Optional[IncomeLevel] = None
    class_id: Optional[UUID] = None
    guardian_id: Optional[UUID] = None
    status: Optional[StudentStatus] = None

class StudentResponse(StudentBase):
    id: UUID
    age: int
    status: StudentStatus
    class_id: Optional[UUID] = None
    guardian_id: UUID

class StudentWithGuardianResponse(StudentResponse):
    guardian: GuardianResponse

class ClassResponse(BaseModel):
    id: UUID
    name: str
    code: str
    academic_year: str

    class Config:
        from_attributes = True

class StudentWithClassResponse(StudentResponse):
    current_class: Optional[ClassResponse] = None
    
    @classmethod
    def from_orm(cls, obj):
        # Custom from_orm to handle class relationship
        data = super().model_validate(obj)
        if obj.class_:
            data.current_class = ClassResponse(
                id=obj.class_.id,
                name=obj.class_.name,
                code=obj.class_.code,
                academic_year=obj.class_.academic_year
            )
        return data
    
    class Config:
        from_attributes = True

class StudentWithDetailsResponse(StudentWithGuardianResponse, StudentWithClassResponse):
    performance_history: Optional[List[TermPerformanceResponse]] = None

class StudentListResponse(BaseModel):
    students: List[StudentWithDetailsResponse]
    total_count: int

class StudentRiskResponse(BaseModel):
    id: UUID
    name: str
    risk_score: float
    risk_level: str
    absences: int
    current_class: Optional[str] = None
    last_term_avg: Optional[float] = None

class UploadResponse(BaseModel):
    message: str
    records_added: int
    records_updated: int = 0
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

# Helper Functions
def get_student_or_404(db: Session, student_id: UUID):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

def get_guardian_or_404(db: Session, guardian_id: UUID):
    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian not found")
    return guardian

def calculate_age(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_student_performance(db: Session, student_id: UUID):
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == student_id
    ).order_by(
        AcademicTerm.academic_year,
        AcademicTerm.term_type
    ).all()

    performance = []
    for term in terms:
        # Updated query to properly handle the joined data
        score_records = db.query(
            SubjectScore,
            Subject.name.label('subject_name')
        ).join(
            Subject,
            SubjectScore.subject_id == Subject.id
        ).filter(
            SubjectScore.academic_term_id == term.id
        ).all()

        subject_scores = []
        for score_record in score_records:
            # Access the score and subject_name correctly
            subject_score = score_record[0]
            subject_name = score_record[1]
            
            subject_scores.append(SubjectScoreResponse(
                subject_name=subject_name,
                score=subject_score.score,
                grade=subject_score.grade
            ))

        performance.append(TermPerformanceResponse(
            term_id=term.id,
            term_type=term.term_type,
            academic_year=term.academic_year,
            standard=term.standard,
            term_avg_score=term.term_avg_score,
            present_days=term.present_days,
            absent_days=term.absent_days,
            subject_scores=subject_scores
        ))

    return performance


# Student CRUD Endpoints
@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if student ID exists
    existing_student = db.query(Student).filter(
        Student.id == student_data.student_id
    ).first()
    
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this ID already exists"
        )
    
    # Validate guardian exists
    get_guardian_or_404(db, student_data.guardian_id)
    
    # Validate class exists if provided
    if student_data.class_id:
        class_ = db.query(Class).filter(Class.id == student_data.class_id).first()
        if not class_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
    
    # Calculate age
    age = calculate_age(student_data.date_of_birth)
    
    db_student = Student(
        **student_data.model_dump(),
        age=age,
        status=StudentStatus.ACTIVE
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.get("", response_model=StudentListResponse)
async def get_students(
    skip: int = 0,
    limit: int = 100,
    status: Optional[StudentStatus] = None,
    class_id: Optional[UUID] = None,
    gender: Optional[Gender] = None,
    include_performance: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(Student).options(
        joinedload(Student.guardian),
        joinedload(Student.class_)
    )
    
    if status is not None:
        query = query.filter(Student.status == status)
    
    if class_id:
        query = query.filter(Student.class_id == class_id)
    
    if gender:
        query = query.filter(Student.gender == gender)
    
    students = query.offset(skip).limit(limit).all()
    total_count = query.count()
    
    student_responses = []
    for student in students:
        # Use the custom from_orm method
        student_data = StudentWithDetailsResponse.from_orm(student)
        if include_performance:
            student_data.performance_history = get_student_performance(db, student.id)
        student_responses.append(student_data)
    
    return StudentListResponse(
        students=student_responses,
        total_count=total_count
    )

@router.get("/{student_id}", response_model=StudentWithDetailsResponse)
async def get_student(
    student_id: UUID,
    include_performance: bool = False,
    db: Session = Depends(get_db)
):
    student = db.query(Student).options(
        joinedload(Student.guardian),
        joinedload(Student.class_)
    ).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    response = StudentWithDetailsResponse.model_validate(student)
    if include_performance:
        response.performance_history = get_student_performance(db, student_id)
    
    return response

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    student_data: StudentUpdate,
    db: Session = Depends(get_db)
):
    db_student = get_student_or_404(db, student_id)
    
    # Validate student ID
    if student_data.student_id and student_data.student_id != db_student.id:
        existing = db.query(Student).filter(
            Student.student_id == student_data.student_id,
            Student.id != student_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists"
            )
    
    # Validate guardian exists
    if student_data.guardian_id:
        get_guardian_or_404(db, student_data.guardian_id)
    
    # Validate class exists
    if student_data.class_id:
        class_ = db.query(Class).filter(Class.id == student_data.class_id).first()
        if not class_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
    
    # Calculate age if DOB changes
    if student_data.date_of_birth:
        student_data.age = calculate_age(student_data.date_of_birth)
    
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_student, field, value)
    
    db.commit()
    db.refresh(db_student)
    return db_student

@router.delete("/{student_id}", response_model=StudentResponse)
async def delete_student(
    student_id: UUID,
    db: Session = Depends(get_db),
):
    
    db_student = get_student_or_404(db, student_id)
    db_student.status = StudentStatus.DROPPED_OUT
    db.commit()
    db.refresh(db_student)
    return db_student

# Risk Assessment Endpoints
@router.get("/{student_id}/risk", response_model=StudentRiskResponse)
async def get_student_risk(
    student_id: UUID,
    db: Session = Depends(get_db)
):
    student = get_student_or_404(db, student_id)
    
    # Get latest prediction
    prediction = db.query(DropoutPrediction).filter(
        DropoutPrediction.student_id == student_id
    ).order_by(DropoutPrediction.prediction_date.desc()).first()
    
    # Get latest term performance
    latest_term = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == student_id
    ).order_by(
        AcademicTerm.academic_year.desc(),
        AcademicTerm.term_type.desc()
    ).first()
    
    return StudentRiskResponse(
        id=student.id,
        name=f"{student.first_name} {student.last_name}",
        risk_score=prediction.risk_score if prediction else 0.0,
        risk_level=prediction.risk_level.value if prediction else "low",
        absences=latest_term.absent_days if latest_term else 0,
        current_class=student.class_.name if student.class_ else None,
        last_term_avg=latest_term.term_avg_score if latest_term else None
    )


def get_academic_year_dates(academic_year: str):
    try:
        start_year = int(academic_year.split('-')[0])
        return date(start_year, 9, 1), date(start_year + 1, 8, 31)
    except:
        current_year = datetime.now().year
        return date(current_year, 1, 1), date(current_year, 12, 31)
    



class ClassStudentResponse(BaseModel):
    id: UUID
    class_name: str
    name: str
    code: str
    grade_level: str
    academic_year: str
    max_capacity: int
    capacity: int
    current_enrollment: int
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/classes/students-by-teacher", response_model=List[ClassStudentResponse])
async def get_all_students_by_teacher(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all classes assigned to a specific teacher
    """
    try:
        # Verify user has teacher relationshi
        if not hasattr(current_user, 'teacher') or not current_user.teacher:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Only teachers can access this endpoint."
            )
        
        # Get classes where this teacher is assigned
        teacher_classes = db.query(TeacherClass).filter(
            TeacherClass.teacher_id == current_user.teacher.id
        ).all()
        
        class_ids = [tc.class_id for tc in teacher_classes]
        
        if not class_ids:
            return []
        
        # Get the classes with proper joins
        classes = db.query(Class).filter(Class.id.in_(class_ids)).all()
        
        response_data = []
        for class_obj in classes:
            # Get student count for this class
            student_count = db.query(func.count(Student.id)).filter(
                Student.class_id == class_obj.id
            ).scalar() or 0
            
            # Get teacher name
            teacher_name = f"{current_user.teacher.first_name} {current_user.teacher.last_name}"
            
            class_data = ClassStudentResponse(
                id=class_obj.id,  # Keep as UUID, Pydantic will handle conversion
                class_name=class_obj.name,
                name=class_obj.name,
                code=class_obj.code,
                grade_level=extract_grade_level(class_obj.name,class_obj.code),
                academic_year=class_obj.academic_year,
                max_capacity=class_obj.capacity or 40,
                capacity=class_obj.capacity or 40,
                current_enrollment=student_count,
                teacher_id=str(current_user.teacher.id),  # Convert UUID to string
                teacher_name=teacher_name,
                description=f"Primary class for {extract_grade_level(class_obj.name, class_obj.code)} students",
                is_active=class_obj.is_active,
                created_at=datetime.now().isoformat() + "Z",
                updated_at=datetime.now().isoformat() + "Z"
            )
            response_data.append(class_data)
        
        return response_data
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving teacher classes: {str(e)}")

@router.get("/classes", response_model=List[ClassStudentResponse])
async def get_teacher_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all classes assigned to the currently logged-in teacher.
    Only teachers can access this endpoint.
    """
    
    # Verify user is a teacher
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )
    
    # Get the teacher record for the current user
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher record not found"
        )
    
    # Query to get all classes assigned to this teacher with enrollment count
    classes_query = (
        db.query(
            Class,
            TeacherClass.is_class_teacher,
            func.count(Student.id).label('current_enrollment')
        )
        .join(TeacherClass, Class.id == TeacherClass.class_id)
        .outerjoin(Student, Class.id == Student.class_id)
        .filter(TeacherClass.teacher_id == teacher.id)
        .filter(Class.is_active == True)
        .group_by(Class.id, TeacherClass.is_class_teacher)
        .order_by(Class.name)
    )
    
    results = classes_query.all()
    
    # Format the response
    classes_response = []
    for class_obj, is_class_teacher, enrollment_count in results:
        # Extract grade level from class name or code (adjust logic as needed)
        grade_level = extract_grade_level(class_obj.name, class_obj.code)
        
        # Format timestamps
        created_at = class_obj.created_at.isoformat() if hasattr(class_obj, 'created_at') and class_obj.created_at else datetime.now().isoformat()
        updated_at = class_obj.updated_at.isoformat() if hasattr(class_obj, 'updated_at') and class_obj.updated_at else datetime.now().isoformat()
        
        class_response = ClassStudentResponse(
            id=class_obj.id,
            class_name=class_obj.name,
            name=class_obj.name,
            code=class_obj.code,
            grade_level=grade_level,
            academic_year=class_obj.academic_year,
            max_capacity=class_obj.capacity or 0,
            capacity=class_obj.capacity or 0,
            current_enrollment=enrollment_count or 0,
            teacher_id=str(teacher.id),
            teacher_name=f"{teacher.first_name} {teacher.last_name}",
            description=None,  # Add description field to Class model if needed
            is_active=class_obj.is_active,
            created_at=created_at,
            updated_at=updated_at
        )
        classes_response.append(class_response)
    
    return classes_response

def extract_grade_level(class_name: str, class_code: str) -> str:
    """
    Extract grade level from class name or code.
    Adjust this logic based on your naming convention.
    """
    # Example logic - adjust based on your actual naming convention
    import re
    
    # Try to extract from class name first
    grade_match = re.search(r'(Grade|Standard|Form|Year)\s*(\d+)', class_name, re.IGNORECASE)
    if grade_match:
        return f"Grade {grade_match.group(2)}"
    
    # Try to extract from class code
    grade_match = re.search(r'(\d+)', class_code)
    if grade_match:
        return f"Grade {grade_match.group(1)}"
    
    # Default fallback
    return "Unknown"

# Alternative endpoint if you want to include class teacher information
@router.get("/classes/detailed", response_model=List[ClassStudentResponse])
async def get_teacher_classes_detailed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about classes assigned to the currently logged-in teacher,
    including information about who the main class teacher is.
    """
    
    # Verify user is a teacher
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )
    
    # Get the teacher record for the current user
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher record not found"
        )
    
    # Query to get all classes with main class teacher info
    classes_query = (
        db.query(
            Class,
            TeacherClass.is_class_teacher,
            func.count(Student.id).label('current_enrollment')
        )
        .join(TeacherClass, Class.id == TeacherClass.class_id)
        .outerjoin(Student, Class.id == Student.class_id)
        .filter(TeacherClass.teacher_id == teacher.id)
        .filter(Class.is_active == True)
        .group_by(Class.id, TeacherClass.is_class_teacher)
        .order_by(Class.name)
    )
    
    results = classes_query.all()
    
    # For each class, get the main class teacher if current teacher is not the main teacher
    classes_response = []
    for class_obj, is_class_teacher, enrollment_count in results:
        teacher_name = f"{teacher.first_name} {teacher.last_name}"
        teacher_id_str = str(teacher.id)
        
        # If current teacher is not the main class teacher, get the main class teacher
        if not is_class_teacher:
            main_teacher = (
                db.query(Teacher)
                .join(TeacherClass, Teacher.id == TeacherClass.teacher_id)
                .filter(TeacherClass.class_id == class_obj.id)
                .filter(TeacherClass.is_class_teacher == True)
                .first()
            )
            if main_teacher:
                teacher_name = f"{main_teacher.first_name} {main_teacher.last_name}"
                teacher_id_str = str(main_teacher.id)
        
        grade_level = extract_grade_level(class_obj.name, class_obj.code)
        
        created_at = class_obj.created_at.isoformat() if hasattr(class_obj, 'created_at') and class_obj.created_at else datetime.now().isoformat()
        updated_at = class_obj.updated_at.isoformat() if hasattr(class_obj, 'updated_at') and class_obj.updated_at else datetime.now().isoformat()
        
        class_response = ClassStudentResponse(
            id=class_obj.id,
            class_name=class_obj.name,
            name=class_obj.name,
            code=class_obj.code,
            grade_level=grade_level,
            academic_year=class_obj.academic_year,
            max_capacity=class_obj.capacity or 0,
            capacity=class_obj.capacity or 0,
            current_enrollment=enrollment_count or 0,
            teacher_id=teacher_id_str,
            teacher_name=teacher_name,
            description=None,
            is_active=class_obj.is_active,
            created_at=created_at,
            updated_at=updated_at
        )
        classes_response.append(class_response)
    
    return classes_response