import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID

from app.database import get_db
from app.models.all_models import AcademicTerm, Class, DailyAttendance, StudentStatus, Teacher, Student, TeacherClass, User, Guardian, DropoutPrediction
from app.utils.auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=["classes-v2"])

# Pydantic request models
class CreateClassRequest(BaseModel):
    class_name: str
    grade_level: str
    academic_year: str
    max_capacity: int
    teacher_id: Optional[str] = None
    description: Optional[str] = None

class UpdateClassRequest(BaseModel):
    class_name: Optional[str] = None
    grade_level: Optional[str] = None
    academic_year: Optional[str] = None
    max_capacity: Optional[int] = None
    teacher_id: Optional[str] = None
    description: Optional[str] = None

class AddStudentToClassRequest(BaseModel):
    student_id: str

# Pydantic response models matching your frontend schemas
class ClassResponse(BaseModel):
    id : UUID
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

class ClassWithStudentsResponse(BaseModel):
    id : UUID
    name: str
    code: str
    academic_year: str
    capacity: int
    student_count: int
    is_active: bool

    class Config:
        from_attributes = True

class GuardianInfo(BaseModel):
    first_name: str
    last_name: str
    relationship_to_student: str
    phone_number: str

class StudentInfo(BaseModel):
    id : UUID
    first_name: str
    last_name: str
    student_number: str
    age: int
    gender: str
    is_active: bool
    guardian: GuardianInfo

class TeacherInfo(BaseModel):
    id : UUID
    first_name: str
    last_name: str
    qualification: str
    experience_years: int
    phone_number: str

class ClassSummary(BaseModel):
    attendance_rate: float
    high_risk_students: int

class ClassFullDetailsResponse(BaseModel):
    id : UUID
    name: str
    code: str
    academic_year: str
    capacity: int
    students: List[StudentInfo]
    teachers: List[TeacherInfo]
    summary: ClassSummary

class ClassesListResponse(BaseModel):
    classes: List[ClassResponse]
    total_count: int

class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None

# Utility functions
def extract_grade_level(class_name: str) -> str:
    """Extract grade level from class name (e.g., 'Standard 1A' -> 'Standard 1')"""
    parts = class_name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}"  # e.g., "Standard 1"
    return class_name

def generate_class_code(class_name: str) -> str:
    """Generate class code from class name"""
    parts = class_name.replace(" ", "").upper()
    return parts[:10] if len(parts) <= 10 else parts[:10]

def calculate_attendance_rate(student_id: str, db: Session) -> float:
    """Calculate attendance rate for a student"""
    # Get latest academic term for the student
    latest_term = db.query(AcademicTerm).filter(
        AcademicTerm.student_id == student_id
    ).order_by(AcademicTerm.created_at.desc()).first()
    
    if not latest_term or not latest_term.present_days or not latest_term.absent_days:
        return 95.0  # Default rate
    
    total_days = latest_term.present_days + latest_term.absent_days
    if total_days == 0:
        return 95.0
    
    return (latest_term.present_days / total_days) * 100

def count_high_risk_students(class_id: str, db: Session) -> int:
    """Count high risk students in a class"""
    return db.query(func.count(DropoutPrediction.id)).join(Student).filter(
        and_(
            Student.class_id == class_id,
            DropoutPrediction.risk_level.in_(['HIGH', 'CRITICAL'])
        )
    ).scalar() or 0

# Create Class
@router.post("/classes", response_model=ClassResponse)
async def create_class(class_data: CreateClassRequest, db: Session = Depends(get_db)):
    """Create a new class"""
    try:
        # Generate class code
        class_code = generate_class_code(class_data.class_name)
        
        # Check if code already exists
        existing_class = db.query(Class).filter(Class.code == class_code).first()
        if existing_class:
            class_code = f"{class_code}{datetime.now().strftime('%H%M')}"
        
        # Create new class
        new_class = Class(
            name=class_data.class_name,
            code=class_code,
            academic_year=class_data.academic_year,
            capacity=class_data.max_capacity,
            is_active=True
        )
        
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        
        # Assign teacher if provided
        teacher_name = None
        if class_data.teacher_id:
            try:
                teacher_uuid = class_data.teacher_id
                teacher = db.query(Teacher).filter(Teacher.id == teacher_uuid).first()
                if teacher:
                    teacher_class = TeacherClass(
                        teacher_id=teacher_uuid,
                        class_id=new_class.id,
                        is_class_teacher=True
                    )
                    db.add(teacher_class)
                    db.commit()
                    teacher_name = f"{teacher.first_name} {teacher.last_name}"
            except ValueError:
                pass
        
        return ClassResponse(
            id=new_class.id,
            class_name=new_class.name,
            name=new_class.name,
            code=new_class.code,
            grade_level=class_data.grade_level,
            academic_year=new_class.academic_year,
            max_capacity=new_class.capacity,
            capacity=new_class.capacity,
            current_enrollment=0,
            teacher_id=class_data.teacher_id,
            teacher_name=teacher_name,
            description=class_data.description,
            is_active=new_class.is_active,
            created_at=datetime.now().isoformat() + "Z",
            updated_at=datetime.now().isoformat() + "Z"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating class: {str(e)}")

# Get All Classes with pagination
@router.get("/classes", response_model=ClassesListResponse)
async def get_classes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    teacher_id: Optional[str] = None,
    academic_year: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """
    Get all classes with pagination and filtering
    """
    try:
        # Base query with joins
        query = db.query(Class).options(
            joinedload(Class.teachers).joinedload(TeacherClass.teacher).joinedload(Teacher.user)
        )
        
        # Apply filters
        if academic_year:
            query = query.filter(Class.academic_year == academic_year)
        if is_active is not None:
            query = query.filter(Class.is_active == is_active)
        if teacher_id:
            try:
                teacher_uuid = UUID(teacher_id)
                query = query.join(TeacherClass).filter(TeacherClass.teacher_id == teacher_uuid)
            except ValueError:
                pass
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        classes = query.offset(offset).limit(limit).all()
        
        response_classes = []
        for class_obj in classes:
            # Get student count
            student_count = db.query(func.count(Student.id)).filter(
                Student.class_id == class_obj.id
            ).scalar() or 0
            
            # Get class teacher
            class_teacher = None
            teacher_id_str = None
            teacher_name = None
            
            for teacher_class in class_obj.teachers:
                if teacher_class.is_class_teacher:
                    class_teacher = teacher_class.teacher
                    teacher_id_str = str(class_teacher.id)
                    teacher_name = f"{class_teacher.first_name} {class_teacher.last_name}"
                    break
            
            if not class_teacher and class_obj.teachers:
                class_teacher = class_obj.teachers[0].teacher
                teacher_id_str = str(class_teacher.id)
                teacher_name = f"{class_teacher.first_name} {class_teacher.last_name}"
            
            class_data = ClassResponse(
                id=str(class_obj.id),
                class_name=class_obj.name,
                name=class_obj.name,
                code=class_obj.code,
                grade_level=extract_grade_level(class_obj.name),
                academic_year=class_obj.academic_year,
                max_capacity=class_obj.capacity or 40,
                capacity=class_obj.capacity or 40,
                current_enrollment=student_count,
                teacher_id=teacher_id_str,
                teacher_name=teacher_name,
                description=f"Primary class for {extract_grade_level(class_obj.name)} students",
                is_active=class_obj.is_active,
                created_at=datetime.now().isoformat() + "Z",
                updated_at=datetime.now().isoformat() + "Z"
            )
            response_classes.append(class_data)
        
        return ClassesListResponse(
            classes=response_classes,
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")

@router.get("/classes/with-students", response_model=List[ClassWithStudentsResponse])
async def get_classes_with_students(
    academic_year: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """
    Get simplified class information with student counts
    """
    try:
        # Base query
        query = db.query(Class)
        
        # Apply filters
        if academic_year:
            query = query.filter(Class.academic_year == academic_year)
        if is_active is not None:
            query = query.filter(Class.is_active == is_active)
        
        classes = query.all()
        
        response_data = []
        for class_obj in classes:
            # Get student count
            student_count = db.query(func.count(Student.id)).filter(
                Student.class_id == class_obj.id
            ).scalar() or 0
            
            class_data = ClassWithStudentsResponse(
                id=str(class_obj.id),
                name=class_obj.name,
                code=class_obj.code,
                academic_year=class_obj.academic_year,
                capacity=class_obj.capacity or 40,
                student_count=student_count,
                is_active=class_obj.is_active
            )
            response_data.append(class_data)
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes with students: {str(e)}")

@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class_by_id_new(class_id: str, db: Session = Depends(get_db)):
    """
    Get a specific class by ID
    """
    try:
        # Convert string ID to UUID if needed
        try:
            class_uuid = UUID(class_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid class ID format")
        
        class_obj = db.query(Class).options(
            joinedload(Class.teachers).joinedload(TeacherClass.teacher).joinedload(Teacher.user)
        ).filter(Class.id == class_uuid).first()
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Get student count
        student_count = db.query(func.count(Student.id)).filter(
            Student.class_id == class_obj.id
        ).scalar() or 0
        
        # Get class teacher
        class_teacher = None
        teacher_id = None
        teacher_name = None
        
        for teacher_class in class_obj.teachers:
            if teacher_class.is_class_teacher:
                class_teacher = teacher_class.teacher
                teacher_id = str(class_teacher.id)
                teacher_name = f"{class_teacher.first_name} {class_teacher.last_name}"
                break
        
        if not class_teacher and class_obj.teachers:
            class_teacher = class_obj.teachers[0].teacher
            teacher_id = str(class_teacher.id)
            teacher_name = f"{class_teacher.first_name} {class_teacher.last_name}"
        
        return ClassResponse(
            id=str(class_obj.id),
            class_name=class_obj.name,
            name=class_obj.name,
            code=class_obj.code,
            grade_level=extract_grade_level(class_obj.name),
            academic_year=class_obj.academic_year,
            max_capacity=class_obj.capacity or 40,
            capacity=class_obj.capacity or 40,
            current_enrollment=student_count,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            description=f"Primary class for {extract_grade_level(class_obj.name)} students",
            is_active=class_obj.is_active,
            created_at=datetime.now().isoformat() + "Z",
            updated_at=datetime.now().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving class: {str(e)}")

# Get Class Full Details
@router.get("/classes/{class_id}/full-details", response_model=ClassFullDetailsResponse)
async def get_class_full_details(class_id: str, db: Session = Depends(get_db)):
    """Get detailed class information including students, teachers, and summary"""
    try:
        class_uuid = UUID(class_id)
        
        # Get class with relationships
        class_obj = db.query(Class).options(
            joinedload(Class.students).joinedload(Student.guardian),
            joinedload(Class.teachers).joinedload(TeacherClass.teacher)
        ).filter(Class.id == class_uuid).first()
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Build students list
        students = []
        total_attendance = 0
        student_count = 0
        
        for student in class_obj.students:
            if student.guardian:
                attendance_rate = calculate_attendance_rate(str(student.id), db)
                total_attendance += attendance_rate
                student_count += 1
                
                student_info = StudentInfo(
                    id=str(student.id),
                    first_name=student.first_name,
                    last_name=student.last_name,
                    student_number=student.student_id,
                    age=student.age or 0,
                    gender=student.gender.value if student.gender else "unknown",
                    is_active=student.status == StudentStatus.ACTIVE,
                    guardian=GuardianInfo(
                        first_name=student.guardian.first_name,
                        last_name=student.guardian.last_name,
                        relationship_to_student=student.guardian.relationship_to_student.value,
                        phone_number=student.guardian.phone_number or ""
                    )
                )
                students.append(student_info)
        
        # Build teachers list
        teachers = []
        for teacher_class in class_obj.teachers:
            teacher = teacher_class.teacher
            teacher_info = TeacherInfo(
                id=str(teacher.id),
                first_name=teacher.first_name,
                last_name=teacher.last_name,
                qualification=teacher.qualification or "Not specified",
                experience_years=teacher.experience_years or 0,
                phone_number=teacher.phone_number or ""
            )
            teachers.append(teacher_info)
        
        # Calculate summary
        avg_attendance = total_attendance / student_count if student_count > 0 else 0
        high_risk_count = count_high_risk_students(class_id, db)
        
        summary = ClassSummary(
            attendance_rate=round(avg_attendance, 1),
            high_risk_students=high_risk_count
        )
        
        return ClassFullDetailsResponse(
            id=str(class_obj.id),
            name=class_obj.name,
            code=class_obj.code,
            academic_year=class_obj.academic_year,
            capacity=class_obj.capacity or 40,
            students=students,
            teachers=teachers,
            summary=summary
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid class ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving class details: {str(e)}")

# Update Class
@router.patch("/classes/{class_id}", response_model=ClassResponse)
async def update_class(class_id: str, class_data: UpdateClassRequest, db: Session = Depends(get_db)):
    """Update a class"""
    try:
        class_uuid = UUID(class_id)
        
        class_obj = db.query(Class).filter(Class.id == class_uuid).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Update fields
        if class_data.class_name is not None:
            class_obj.name = class_data.class_name
            class_obj.code = generate_class_code(class_data.class_name)
        if class_data.academic_year is not None:
            class_obj.academic_year = class_data.academic_year
        if class_data.max_capacity is not None:
            class_obj.capacity = class_data.max_capacity
        
        # Handle teacher assignment
        teacher_name = None
        if class_data.teacher_id is not None:
            # Remove existing class teacher assignment
            existing_assignment = db.query(TeacherClass).filter(
                and_(
                    TeacherClass.class_id == class_uuid,
                    TeacherClass.is_class_teacher == True
                )
            ).first()
            if existing_assignment:
                db.delete(existing_assignment)
            
            # Add new teacher assignment
            if class_data.teacher_id:
                try:
                    teacher_uuid = UUID(class_data.teacher_id)
                    teacher = db.query(Teacher).filter(Teacher.id == teacher_uuid).first()
                    if teacher:
                        new_assignment = TeacherClass(
                            teacher_id=teacher_uuid,
                            class_id=class_uuid,
                            is_class_teacher=True
                        )
                        db.add(new_assignment)
                        teacher_name = f"{teacher.first_name} {teacher.last_name}"
                except ValueError:
                    pass
        
        db.commit()
        db.refresh(class_obj)
        
        # Get current enrollment
        student_count = db.query(func.count(Student.id)).filter(
            Student.class_id == class_obj.id
        ).scalar() or 0
        
        return ClassResponse(
            id=str(class_obj.id),
            class_name=class_obj.name,
            name=class_obj.name,
            code=class_obj.code,
            grade_level=class_data.grade_level or extract_grade_level(class_obj.name),
            academic_year=class_obj.academic_year,
            max_capacity=class_obj.capacity,
            capacity=class_obj.capacity,
            current_enrollment=student_count,
            teacher_id=class_data.teacher_id,
            teacher_name=teacher_name,
            description=class_data.description,
            is_active=class_obj.is_active,
            created_at=datetime.now().isoformat() + "Z",
            updated_at=datetime.now().isoformat() + "Z"
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid class ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating class: {str(e)}")

# Delete Class
@router.delete("/classes/{class_id}", response_model=ClassResponse)
async def delete_class_new(class_id: str, db: Session = Depends(get_db)):
    """Delete a class (soft delete by setting is_active to False)"""
    try:
        class_uuid = UUID(class_id)
        
        class_obj = db.query(Class).filter(Class.id == class_uuid).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Get current data before deletion
        student_count = db.query(func.count(Student.id)).filter(
            Student.class_id == class_obj.id
        ).scalar() or 0
        
        # Get teacher info
        teacher_assignment = db.query(TeacherClass).options(
            joinedload(TeacherClass.teacher)
        ).filter(
            and_(
                TeacherClass.class_id == class_uuid,
                TeacherClass.is_class_teacher == True
            )
        ).first()
        
        teacher_id = None
        teacher_name = None
        if teacher_assignment:
            teacher_id = str(teacher_assignment.teacher.id)
            teacher_name = f"{teacher_assignment.teacher.first_name} {teacher_assignment.teacher.last_name}"
        
        # Soft delete
        class_obj.is_active = False
        db.commit()
        
        return ClassResponse(
            id=str(class_obj.id),
            class_name=class_obj.name,
            name=class_obj.name,
            code=class_obj.code,
            grade_level=extract_grade_level(class_obj.name),
            academic_year=class_obj.academic_year,
            max_capacity=class_obj.capacity,
            capacity=class_obj.capacity,
            current_enrollment=student_count,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            description=f"Primary class for {extract_grade_level(class_obj.name)} students",
            is_active=class_obj.is_active,
            created_at=datetime.now().isoformat() + "Z",
            updated_at=datetime.now().isoformat() + "Z"
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid class ID format")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting class: {str(e)}")

class GuardianResponse(BaseModel):
    first_name: str
    last_name: str
    relationship_to_student: str
    phone_number: str


class StudentClassListResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    student_number: str
    age: int
    gender: str
    is_active: bool
    attendance_status: Optional[str] = None
    guardian: GuardianResponse



    

# Get Class Students
@router.get("/classes/{class_id}/students", response_model=List[StudentClassListResponse])
async def get_class_students(
    class_id: str, 
    date: date = date.today(),  # Optional date parameter, defaults to today
    db: Session = Depends(get_db)
):
    """Get all students in a class with their attendance status for the specified date"""
    try:
        class_uuid = UUID(class_id)
        
        # Get all students in the class with their guardians
        students = db.query(Student).options(
            joinedload(Student.guardian)
        ).filter(Student.class_id == class_uuid).all()
        
        # Get attendance records for these students on the specified date
        attendance_records = db.query(DailyAttendance).filter(
            DailyAttendance.student_id.in_([s.id for s in students]),
            DailyAttendance.attendance_date == date
        ).all()
        
        # Create a mapping of student_id to attendance status
        attendance_map = {str(rec.student_id): rec.status.value.lower() for rec in attendance_records}
        
        student_list = []
        for student in students:
            # Get attendance status or None if no record exists
            status = attendance_map.get(str(student.id))
            
            student_data = {
                "id": str(student.id),
                "first_name": student.first_name,
                "last_name": student.last_name,
                "student_number": student.student_id,
                "age": student.age,
                "gender": student.gender.value if student.gender else None,
                "is_active": student.status == StudentStatus.ACTIVE,
                "attendance_status": status,  # Add the status field
                "guardian": {
                    "first_name": student.guardian.first_name if student.guardian else "",
                    "last_name": student.guardian.last_name if student.guardian else "",
                    "relationship_to_student": student.guardian.relationship_to_student.value if student.guardian else "",
                    "phone_number": student.guardian.phone_number if student.guardian else ""
                } if student.guardian else None
            }
            student_list.append(student_data)
        
        return student_list
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid class ID format")
    
    
# Add Student to Class
@router.post("/classes/{class_id}/students", response_model=SuccessResponse)
async def add_student_to_class(
    class_id: str, 
    request: AddStudentToClassRequest, 
    db: Session = Depends(get_db)
):
    """Add a student to a class"""
    try:
        class_uuid = UUID(class_id)
        student_uuid = UUID(request.student_id)
        
        # Check if class exists
        class_obj = db.query(Class).filter(Class.id == class_uuid).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Check if student exists
        student = db.query(Student).filter(Student.id == student_uuid).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check class capacity
        current_count = db.query(func.count(Student.id)).filter(
            Student.class_id == class_uuid
        ).scalar() or 0
        
        if current_count >= (class_obj.capacity or 40):
            raise HTTPException(status_code=400, detail="Class is at full capacity")
        
        # Assign student to class
        student.class_id = class_uuid
        db.commit()
        
        return SuccessResponse(success=True, message="Student added to class successfully")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding student to class: {str(e)}")

# Remove Student from Class
@router.delete("/classes/{class_id}/students/{student_id}", response_model=SuccessResponse)
async def remove_student_from_class(class_id: str, student_id: str, db: Session = Depends(get_db)):
    """Remove a student from a class"""
    try:
        class_uuid = UUID(class_id)
        student_uuid = UUID(student_id)
        
        # Check if student is in the class
        student = db.query(Student).filter(
            and_(
                Student.id == student_uuid,
                Student.class_id == class_uuid
            )
        ).first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found in this class")
        
        # Remove from class
        student.class_id = None
        db.commit()
        
        return SuccessResponse(success=True, message="Student removed from class successfully")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing student from class: {str(e)}")

# Additional useful endpoints
@router.get("/classes/academic-year/{academic_year}", response_model=List[ClassResponse])
async def get_classes_by_academic_year_new(academic_year: str, db: Session = Depends(get_db)):
    """
    Get all classes for a specific academic year
    """
    return await get_classes(academic_year=academic_year, db=db)

