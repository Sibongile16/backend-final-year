from fastapi import APIRouter, Depends, HTTPException, status
from pytz import timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.crud.teacher import get_fullname
from app.database import get_db
from app.models.all_models import User, Teacher, UserRole
from app.utils.auth import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token, create_refresh_token, get_current_user, get_password_hash, verify_admin, verify_headteacher, verify_password, verify_token

# Router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserInfo(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    teacher_info: Optional[dict] = None

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint that returns JWT tokens
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "name":get_fullname(user.teacher) if user.teacher else str(user.username).upper(), "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(refresh_data.refresh_token, "refresh")
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "name":get_fullname(user.teacher), "username": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=UserInfo, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information
    """
    teacher_info = None
    if current_user.teacher:
        teacher_info = {
            "id": current_user.teacher.id,
            "first_name": current_user.teacher.first_name,
            "last_name": current_user.teacher.last_name,
            "phone_number": current_user.teacher.phone_number,
            "qualification": current_user.teacher.qualification,
            "experience_years": current_user.teacher.experience_years
        }
    
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        teacher_info=teacher_info
    )

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.now(timezone("Africa/Harare"))
    
    db.commit()
    
    return {"message": "Password updated successfully"}



# # User creation endpoint (for initial setup or admin use)
# class CreateUserRequest(BaseModel):
#     username: str
#     email: EmailStr
#     password: str
#     role: UserRole
#     teacher_info: Optional[dict] = None

# @router.post("/create-user")
# async def create_user(
#     user_data: CreateUserRequest,
#     current_user: User = Depends(verify_admin),  
#     db: Session = Depends(get_db)
# ):
#     """
#     Create a new user (only headteachers can create users)
#     """
#     # Check if username or email already exists
#     existing_user = db.query(User).filter(
#         (User.username == user_data.username) | (User.email == user_data.email)
#     ).first()
    
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Username or email already registered"
#         )
    
#     # Create new user
#     new_user = User(
#         username=user_data.username,
#         email=user_data.email,
#         password_hash=get_password_hash(user_data.password),
#         role=user_data.role
#     )
    
#     db.add(new_user)
#     db.flush()  # To get the user ID
    
#     # Create teacher profile if teacher info is provided
#     if user_data.teacher_info and user_data.role in [UserRole.TEACHER, UserRole.HEADTEACHER]:
#         teacher = Teacher(
#             user_id=new_user.id,
#             first_name=user_data.teacher_info.get("first_name", ""),
#             last_name=user_data.teacher_info.get("last_name", ""),
#             phone_number=user_data.teacher_info.get("phone_number"),
#             qualification=user_data.teacher_info.get("qualification"),
#             experience_years=user_data.teacher_info.get("experience_years", 0)
#         )
#         db.add(teacher)
    
#     db.commit()
    
#     return {"message": "User created successfully", "user_id": str(new_user.id)}