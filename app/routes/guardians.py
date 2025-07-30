from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.all_models import Guardian

router = APIRouter(prefix="/api/guardians", tags=["guardians"])

# Enums
class RelationshipType(str, Enum):
    PARENT = "parent"
    GUARDIAN = "guardian"
    RELATIVE = "relative"
    OTHER = "other"

class MonthlyIncomeRange(str, Enum):
    BELOW_50K = "below_50k"
    K50_100K = "50k_100k"
    K100_200K = "100k_200k"
    ABOVE_200K = "above_200k"

class EducationLevel(str, Enum):
    NONE = "none"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    POSTGRADUATE = "postgraduate"

# Pydantic Models
class GuardianBase(BaseModel):
    first_name: str
    last_name: str
    relationship_to_student: Optional[RelationshipType] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    monthly_income_range: Optional[MonthlyIncomeRange] = None
    education_level: Optional[EducationLevel] =None

    class Config:
        use_enum_values = True

class GuardianCreate(GuardianBase):
    pass

class GuardianUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    relationship_to_student: Optional[RelationshipType] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    monthly_income_range: Optional[MonthlyIncomeRange] = None
    education_level: Optional[EducationLevel] = None

    class Config:
        use_enum_values = True

class GuardianResponse(GuardianBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}

class GuardiansListResponse(BaseModel):
    guardians: List[GuardianResponse]
    total_count: int

class StudentResponse(BaseModel):
    id: UUID
    student_id: str
    first_name: str
    last_name: str
    status: str

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}

# Endpoints
@router.post("", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def create_guardian(
    guardian_data: GuardianCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new guardian
    """
    # Add your database creation logic here
    db_guardian = Guardian(**guardian_data.model_dump())
    db.add(db_guardian)
    db.commit()
    db.refresh(db_guardian)
    return db_guardian

@router.get("", response_model=GuardiansListResponse)
async def get_all_guardians(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get all guardians with pagination
    """
    total_count = db.query(Guardian).count()
    guardians = db.query(Guardian).offset((page-1)*limit).limit(limit).all()

    transformed_guardians = []
    for guardian in guardians:
        guardian_dict = {
            "id": guardian.id,
            "first_name": guardian.first_name,
            "last_name": guardian.last_name,
            "relationship_to_student": guardian.relationship_to_student,
            "phone_number": guardian.phone_number,
            "email": guardian.email,
            "address": guardian.address,
            "occupation": guardian.occupation,
            "monthly_income_range": None,
            "education_level": None,
            "created_at": guardian.created_at,
            "updated_at": guardian.updated_at
        }
        transformed_guardians.append(guardian_dict)
    
    return GuardiansListResponse(
        guardians=transformed_guardians,
        total_count=total_count
    )

@router.get("/{guardian_id}", response_model=GuardianResponse)
async def get_guardian_by_id(
    guardian_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific guardian by ID
    """
    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardian not found"
        )
    return guardian

@router.patch("/{guardian_id}", response_model=GuardianResponse)
async def update_guardian(
    guardian_id: UUID,
    guardian_data: GuardianUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a guardian's information
    """
    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardian not found"
        )
    
    update_data = guardian_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(guardian, field, value)
    
    guardian.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(guardian)
    return guardian

@router.delete("/{guardian_id}", response_model=GuardianResponse)
async def delete_guardian(
    guardian_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a guardian
    """
    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardian not found"
        )
    
    db.delete(guardian)
    db.commit()
    return guardian

@router.get("/{guardian_id}/students", response_model=List[StudentResponse])
async def get_guardian_students(
    guardian_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all students associated with a guardian
    """
    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardian not found"
        )
    
    return guardian.students