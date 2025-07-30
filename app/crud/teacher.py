from datetime import datetime, date
from typing import Optional
from uuid import uuid4
from pytz import timezone
from sqlalchemy.orm import Session
from app.models.all_models import User, Teacher, UserRole
from pydantic import BaseModel, EmailStr

def get_fullname(staff: Teacher) -> str:
    """
    Utility function to get the full name of a teacher.
    """
    return f"{staff.first_name} {staff.last_name}"

def create_teacher_with_user(db:Session,
    username:str,
    email:EmailStr,
    password_hash:str,
    first_name:Optional[str]=None,
    last_name:Optional[str]=None,
    phone_number:Optional[str]=None,
    date_of_birth:Optional[date]=None,
    gender:Optional[str]=None,
    address:Optional[str]=None,
    hire_date:Optional[date]=None,
    qualification:Optional[str]=None,
    experience_years:Optional[int]=None,
):
    try:
        # Create User first
        new_user = User(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=password_hash,
            role=UserRole.TEACHER,
            is_active=True,
            created_at=datetime.now(timezone("Africa/Harare")),
            updated_at=datetime.now(timezone("Africa/Harare"))
        )
        
        # Create Teacher
        new_teacher = Teacher(
            id=uuid4(),
            user_id=new_user.id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            gender=gender,
            address=address,
            hire_date=hire_date or date.today(timezone("Africa/Harare")),  
            qualification=qualification,
            experience_years=experience_years,
            created_at=datetime.now(timezone("Africa/Harare")),
            updated_at=datetime.now(timezone("Africa/Harare"))
        )
        
        # Add to session and commit
        db.add(new_user)
        db.add(new_teacher)
        db.commit()
        
        return new_teacher
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
