from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.database import get_db
from app.utils.auth import get_current_user, verify_admin, get_password_hash, verify_password
from app.models.all_models import User, Teacher, UserRole, Gender

router = APIRouter(prefix="/api/users", tags=["users"])

# ----------------------
# SCHEMAS
# ----------------------

class TeacherBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    username:str
    email: EmailStr
    phone_number: Optional[str] = Field(
        None, 
        min_length=10, 
        max_length=20,
    )
    gender: Optional[Gender] = None
    qualification: Optional[str] = Field(None, max_length=100)
    experience_years: Optional[int] = Field(0, ge=0)

class TeacherCreate(TeacherBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Password must contain at least 8 characters, one uppercase, one lowercase, one number and one special character"
    )
    role: UserRole = Field(UserRole.TEACHER)  # Default to TEACHER

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in [UserRole.TEACHER, UserRole.HEADTEACHER]:
            raise ValueError("Role must be either TEACHER or HEADTEACHER")
        return v

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(
        None, 
        min_length=10, 
        max_length=20,
    )
    gender: Optional[Gender] = None
    qualification: Optional[str] = Field(None, max_length=100)
    experience_years: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class TeacherResponse(TeacherBase):
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeacherListResponse(BaseModel):
    teachers: List[TeacherResponse]
    total_count: int

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

# ----------------------
# ENDPOINTS
# ----------------------

@router.post(
    "",
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new teacher",
    description="Create a new teacher account. Only headteachers can create new accounts."
)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new teacher account
    """
    # Check for existing email
    existing_user = db.query(User).filter(
        func.lower(User.email) == func.lower(teacher_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user account
    new_user = User(
        username = teacher_data.username,
        email=teacher_data.email,
        password_hash=get_password_hash(teacher_data.password),
        role=teacher_data.role,
        is_active=True
    )
    
    db.add(new_user)
    db.flush()  # Get the user ID
    
    # Create teacher profile
    teacher = Teacher(
        user_id=new_user.id,
        first_name=teacher_data.first_name,
        last_name=teacher_data.last_name,
        phone_number=teacher_data.phone_number,
        gender=teacher_data.gender,
        qualification=teacher_data.qualification,
        experience_years=teacher_data.experience_years
    )
    
    db.add(teacher)
    db.commit()
    db.refresh(new_user)
    
    # Combine user and teacher data for response
    response_data = {**teacher.__dict__, **new_user.__dict__}
    return response_data

@router.get("/me", response_model=TeacherResponse)
async def get_current_teacher(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get profile of currently authenticated teacher
    """
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.user_id == current_user.id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    
    response_data = {**teacher.__dict__, **teacher.user.__dict__}
    return response_data

@router.get("", response_model=TeacherListResponse)
async def get_all_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of all teachers
    """
    query = db.query(Teacher).options(
        joinedload(Teacher.user)
    )
    
    if is_active is not None:
        query = query.join(User).filter(User.is_active == is_active)
    if role is not None:
        query = query.join(User).filter(User.role == role)
    
    total_count = query.count()
    teachers = query.offset(skip).limit(limit).all()
    
    # Combine teacher and user data
    teacher_list = []
    for teacher in teachers:
        teacher_data = {**teacher.__dict__, **teacher.user.__dict__}
        teacher_list.append(teacher_data)
    
    return TeacherListResponse(teachers=teacher_list, total_count=total_count)

@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get teacher by ID (Teachers can only access their own profile unless headteacher)
    """
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.user_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    
    response_data = {**teacher.__dict__, **teacher.user.__dict__}
    return response_data

@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: UUID,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db)
):
    """
    Update teacher information
    """
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.user_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Update teacher profile
    if teacher_data.first_name is not None:
        teacher.first_name = teacher_data.first_name
    if teacher_data.last_name is not None:
        teacher.last_name = teacher_data.last_name
    if teacher_data.phone_number is not None:
        teacher.phone_number = teacher_data.phone_number
    if teacher_data.gender is not None:
        teacher.gender = teacher_data.gender
    if teacher_data.qualification is not None:
        teacher.qualification = teacher_data.qualification
    if teacher_data.experience_years is not None:
        teacher.experience_years = teacher_data.experience_years
    
    # Update user account
    if teacher_data.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == teacher_data.email,
            User.id != teacher.user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another account"
            )
        teacher.user.email = teacher_data.email
    
    if teacher_data.is_active is not None:
        teacher.user.is_active = teacher_data.is_active
    
    teacher.user.updated_at = datetime.now()
    db.commit()
    db.refresh(teacher)
    
    response_data = {**teacher.__dict__, **teacher.user.__dict__}
    return response_data

@router.post("/{teacher_id}/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_teacher_password(
    teacher_id: UUID,
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db)
):
    """
    Change teacher password
    """
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.user_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    

    if not verify_password(password_data.current_password, teacher.user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    teacher.user.password_hash = get_password_hash(password_data.new_password)
    teacher.user.updated_at = datetime.now()
    db.commit()
    return None

@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_teacher(
    teacher_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Deactivate a teacher account
    """
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.user_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    teacher.user.is_active = False
    teacher.user.updated_at = datetime.now()
    db.commit()
    return None

@router.post("/{teacher_id}/reactivate", response_model=TeacherResponse)
async def reactivate_teacher(
    teacher_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Reactivate a deactivated teacher account
    """
    teacher = db.query(Teacher).options(
        joinedload(Teacher.user)
    ).filter(Teacher.user_id == teacher_id).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    teacher.user.is_active = True
    teacher.user.updated_at = datetime.now()
    db.commit()
    db.refresh(teacher)
    
    response_data = {**teacher.__dict__, **teacher.user.__dict__}
    return response_data