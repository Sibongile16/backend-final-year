from datetime import date
from uuid import UUID
from pydantic import BaseModel

class StudentResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str

class StudentCreate(BaseModel):
    name: str
    email: str
    phone: str

class StudentUpdate(BaseModel):
    name: str
    email: str
    phone: str

class StudentDelete(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str

class StudentDropout(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    dropout_date: date
    reason: str

class StudentEnrollment(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    enrollment_date: date
    class_id: int
    class_name: str
    teacher_id: int
    teacher_name: str

class StudentAttendance(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    attendance_date: date
    status: str

class StudentProgress(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    progress: float

class StudentReport(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    report: str 