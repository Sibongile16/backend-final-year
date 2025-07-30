from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, case
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from uuid import UUID
from pydantic import BaseModel


from app.database import get_db
from app.utils.auth import get_current_user
from app.models.all_models import (
    AcademicTerm, StudentStatus, Subject, SubjectScore, TermType, User, Teacher, Student, Class, DropoutPrediction,
    TeacherClass, UserRole, RiskLevel, Gender
)
from pytz import timezone

router = APIRouter(prefix="/api/teachers", tags=["teachers"])

# Pydantic Models
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

class ClassResponse(BaseModel):
    id: UUID
    name: str
    code: str
    academic_year: str
    capacity: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True

class TeacherBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    gender: Optional[Gender] = None
    hire_date: Optional[date] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None

    class Config:
        from_attributes = True

class TeacherCreate(TeacherBase):
    user_id: UUID

class TeacherResponse(TeacherBase):
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True

class TeacherWithUserResponse(TeacherResponse):
    user: UserResponse

class TeacherWithClassesResponse(TeacherResponse):
    classes: List[ClassResponse]

    class Config:
        from_attributes = True

class SubjectScoreResponse(BaseModel):
    subject_name: str
    score: float
    grade: str

class StudentRiskResponse(BaseModel):
    id: UUID
    name: str
    age: int
    gender: str
    absences: int
    risk_score: float
    risk_level: str
    current_class_id: Optional[UUID] = None
    guardian_contact: Optional[str] = None
    term_scores: Optional[List[SubjectScoreResponse]] = None

    class Config:
        from_attributes = True

class StudentListResponse(BaseModel):
    students: List[StudentRiskResponse]
    total_count: int
    class_name: str
    academic_year: str
    teacher_name: str

class ClassSummaryResponse(BaseModel):
    class_name: str
    academic_year: str
    total_students: int
    capacity: Optional[int] = None
    risk_distribution: Dict[str, int]
    high_risk_students: int
    attendance_rate: Optional[float] = None
    average_scores: Optional[Dict[str, float]] = None

# Helper Functions
def get_teacher_or_404(db: Session, teacher_id: UUID):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher

def get_current_academic_year():
    blantyre_tz = timezone("Africa/Blantyre")
    now = datetime.now(blantyre_tz)
    return f"{now.year}-{now.year+1}" if now.month >= 9 else f"{now.year-1}-{now.year}"

def get_academic_year_dates(academic_year: str):
    try:
        start_year = int(academic_year.split('-')[0])
        return date(start_year, 9, 1), date(start_year + 1, 8, 31)
    except:
        current_year = datetime.now().year
        return date(current_year, 1, 1), date(current_year, 12, 31)

# Teacher CRUD Endpoints
@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create teacher profiles"
        )
    
    user = db.query(User).filter(User.id == teacher_data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    existing_teacher = db.query(Teacher).filter(Teacher.user_id == teacher_data.user_id).first()
    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher profile already exists for this user"
        )
    
    db_teacher = Teacher(**teacher_data.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@router.get("", response_model=List[TeacherResponse])
async def get_teachers(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Teacher)
    if is_active is not None:
        query = query.filter(Teacher.is_active == is_active)
    return query.offset(skip).limit(limit).all()

@router.get("/{teacher_id}", response_model=TeacherWithClassesResponse)
async def get_teacher(
    teacher_id: UUID,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).options(
        joinedload(Teacher.classes).joinedload(TeacherClass.class_)
    ).filter(Teacher.id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    
    if academic_year:
        teacher.classes = [
            tc for tc in teacher.classes 
            if tc.academic_year == academic_year
        ]
    
    return teacher

@router.get("/{teacher_id}/classes", response_model=List[ClassResponse])
async def get_teacher_classes(
    teacher_id: UUID,
    academic_year: Optional[str] = None,
    is_class_teacher: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Class).join(TeacherClass).filter(
        TeacherClass.teacher_id == teacher_id
    )
    
    if academic_year:
        query = query.filter(TeacherClass.academic_year == academic_year)
    
    if is_class_teacher is not None:
        query = query.filter(TeacherClass.is_class_teacher == is_class_teacher)
    
    return query.all()


# Updated Class Management Endpoints
@router.get("/class/{class_id}/students", response_model=StudentListResponse)
async def get_students_by_class(
    class_id: UUID,
    include_scores: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.HEADTEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only teachers and administrators can access this endpoint."
        )
    
    class_info = db.query(Class).options(
        joinedload(Class.teacher_classes).joinedload(TeacherClass.teacher)
    ).filter(Class.id == class_id).first()
    
    if not class_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    if current_user.role == UserRole.TEACHER:
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found")
        
        is_assigned = any(
            tc.teacher_id == teacher.id and tc.academic_year == class_info.academic_year
            for tc in class_info.teacher_classes
        )
        
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not assigned to this class."
            )
    
    # Get current term
    current_term = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == Student.id,
        AcademicTerm.academic_year == class_info.academic_year,
        AcademicTerm.term_type == TermType.TERM1  # Adjust based on your term logic
    ).subquery()
    
    students_query = db.query(
        Student,
        func.coalesce(current_term.c.absent_days, 0).label('absences')
    ).options(
        joinedload(Student.guardian)
    ).outerjoin(
        current_term,
        current_term.c.student_id == Student.id
    ).filter(
        Student.class_id == class_id,
        Student.status == StudentStatus.ACTIVE
    )
    
    students_data = students_query.all()
    student_ids = [str(student[0].id) for student in students_data]
    
    # Get latest predictions
    latest_predictions_subquery = db.query(
        DropoutPrediction.student_id,
        func.max(DropoutPrediction.prediction_date).label('latest_date')
    ).filter(DropoutPrediction.student_id.in_(student_ids)).group_by(DropoutPrediction.student_id).subquery()
    
    latest_predictions = db.query(DropoutPrediction).join(
        latest_predictions_subquery,
        and_(
            DropoutPrediction.student_id == latest_predictions_subquery.c.student_id,
            DropoutPrediction.prediction_date == latest_predictions_subquery.c.latest_date
        )
    ).all()
    
    predictions_dict = {pred.student_id: pred for pred in latest_predictions}
    
    # Get subject scores if requested
    scores_dict = {}
    if include_scores:
        scores_data = db.query(
            SubjectScore.academic_term_id,
            SubjectScore.subject_id,
            SubjectScore.score,
            SubjectScore.grade,
            Subject.name.label('subject_name')
        ).join(
            Subject,
            SubjectScore.subject_id == Subject.id
        ).filter(
            SubjectScore.academic_term_id.in_(
                db.query(AcademicTerm.id).filter(
                    AcademicTerm.student_id.in_(student_ids),
                    AcademicTerm.term_type == TermType.TERM1  # Current term
                )
            )
        ).all()
        
        for score in scores_data:
            if score.academic_term_id not in scores_dict:
                scores_dict[score.academic_term_id] = []
            scores_dict[score.academic_term_id].append(SubjectScoreResponse(
                subject_name=score.subject_name,
                score=score.score,
                grade=score.grade
            ))
    
    students_response = []
    for student, absences in students_data:
        prediction = predictions_dict.get(student.id)
        term_scores = None
        if include_scores:
            term_id = db.query(AcademicTerm.id).filter(
                AcademicTerm.student_id == student.id,
                AcademicTerm.term_type == TermType.TERM1  # Current term
            ).scalar()
            term_scores = scores_dict.get(term_id, [])
        
        students_response.append(StudentRiskResponse(
            id=student.id,
            name=f"{student.first_name} {student.last_name}",
            age=student.age or 0,
            gender=student.gender.value.title(),
            absences=absences,
            risk_score=round(prediction.risk_score, 2) if prediction else 0.0,
            risk_level=prediction.risk_level.value.title() if prediction else "Low",
            current_class_id=student.class_id,
            guardian_contact=student.guardian.phone_number if student.guardian else None,
            term_scores=term_scores
        ))
    
    students_response.sort(key=lambda x: (-x.risk_score, x.name))
    
    teacher_name = "N/A"
    for tc in class_info.teacher_classes:
        if tc.is_class_teacher:
            teacher_name = f"{tc.teacher.first_name} {tc.teacher.last_name}"
            break
    
    return StudentListResponse(
        students=students_response,
        total_count=len(students_response),
        class_name=class_info.name,
        academic_year=class_info.academic_year,
        teacher_name=teacher_name
    )

@router.get("/class/{class_id}/summary", response_model=ClassSummaryResponse)
async def get_class_summary(
    class_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.HEADTEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only teachers and administrators can access this endpoint."
        )
    
    class_info = db.query(Class).filter(Class.id == class_id).first()
    if not class_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    if current_user.role == UserRole.TEACHER:
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found")
        
        is_assigned = db.query(TeacherClass).filter(
            TeacherClass.teacher_id == teacher.id,
            TeacherClass.class_id == class_id,
            # TeacherClass.class_.academic_year == class_info.academic_year
        ).first()
        
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not assigned to this class."
            )
    
    total_students = db.query(Student).filter(
        Student.class_id == class_id,
        Student.status == StudentStatus.ACTIVE
    ).count()
    
    student_ids = db.query(Student.id).filter(
        Student.class_id == class_id,
        Student.status == StudentStatus.ACTIVE
    ).subquery()
    
    # Get risk distribution
    latest_predictions_subquery = db.query(
        DropoutPrediction.student_id,
        func.max(DropoutPrediction.prediction_date).label('latest_date')
    ).join(student_ids, DropoutPrediction.student_id == student_ids.c.id).group_by(
        DropoutPrediction.student_id
    ).subquery()
    
    risk_distribution = db.query(
        DropoutPrediction.risk_level,
        func.count(DropoutPrediction.student_id).label('count')
    ).join(
        latest_predictions_subquery,
        and_(
            DropoutPrediction.student_id == latest_predictions_subquery.c.student_id,
            DropoutPrediction.prediction_date == latest_predictions_subquery.c.latest_date
        )
    ).group_by(DropoutPrediction.risk_level).all()
    
    # Get attendance rate from AcademicTerm
    current_term_attendance = db.query(
        func.avg(AcademicTerm.present_days / (AcademicTerm.present_days + AcademicTerm.absent_days)).label('attendance_rate')
    ).join(
        Student,
        Student.id == AcademicTerm.student_id
    ).filter(
        Student.class_id == class_id,
        AcademicTerm.term_type == TermType.TERM1,  # Current term
        AcademicTerm.academic_year == class_info.academic_year
    ).scalar()
    
    attendance_rate = round(current_term_attendance * 100, 2) if current_term_attendance else None
    
    # Get average subject scores
    average_scores = {}
    subject_scores = db.query(
        Subject.name,
        func.avg(SubjectScore.score).label('avg_score')
    ).join(
        SubjectScore,
        SubjectScore.subject_id == Subject.id
    ).join(
        AcademicTerm,
        AcademicTerm.id == SubjectScore.academic_term_id
    ).join(
        Student,
        Student.id == AcademicTerm.student_id
    ).filter(
        Student.class_id == class_id,
        AcademicTerm.term_type == TermType.TERM1,  # Current term
        AcademicTerm.academic_year == class_info.academic_year
    ).group_by(Subject.name).all()
    
    for subject in subject_scores:
        average_scores[subject.name] = round(subject.avg_score, 2)
    
    risk_counts = {level.value: 0 for level in RiskLevel}
    risk_counts["none"] = 0
    
    for risk_item in risk_distribution:
        risk_counts[risk_item.risk_level.value] = risk_item.count
    
    students_without_predictions = total_students - sum(risk_counts.values())
    risk_counts["none"] = students_without_predictions
    
    return ClassSummaryResponse(
        class_name=class_info.name,
        academic_year=class_info.academic_year,
        total_students=total_students,
        capacity=class_info.capacity,
        risk_distribution=risk_counts,
        high_risk_students=risk_counts["high"] + risk_counts["critical"],
        attendance_rate=attendance_rate,
        average_scores=average_scores
    )