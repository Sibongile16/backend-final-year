from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from enum import Enum
import uuid
from pytz import timezone

Base = declarative_base()

# Enum Classes
class UserRole(str, Enum):
    ADMIN = "admin"
    HEADTEACHER = "headteacher"
    TEACHER = "teacher"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class RelationshipType(str, Enum):
    PARENT = "parent"
    GUARDIAN = "guardian"
    RELATIVE = "relative"
    OTHER = "other"

class IncomeLevel(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class TransportMethod(str, Enum):
    WALKING = "walking"
    BICYCLE = "bicycle"
    PUBLIC_TRANSPORT = "public_transport"
    PRIVATE_TRANSPORT = "private_transport"

class StudentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    REPEATED = "repeated"
    TRANSFERRED = "transferred"
    DROPPED_OUT = "dropped_out"

class TermType(str, Enum):
    TERM1 = "term1"
    TERM2 = "term2"
    TERM3 = "term3"

class SubjectType(str, Enum):
    CORE = "core"
    ELECTIVE = "elective"
    EXTRACURRICULAR = "extracurricular"

class BullyingType(str, Enum):
    PHYSICAL = "physical"
    VERBAL = "verbal"
    CYBER = "cyber"
    SOCIAL_EXCLUSION = "social_exclusion"
    OTHER = "other"

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Model Classes
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    updated_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")), onupdate=datetime.now(timezone("Africa/Blantyre")))
    
    teacher = relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone_number = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(SQLEnum(Gender))
    address = Column(Text)
    hire_date = Column(Date)
    qualification = Column(String(100))
    experience_years = Column(Integer)
    is_active = Column(Boolean, default = True)
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    updated_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")), onupdate=datetime.now(timezone("Africa/Blantyre")))
    
    user = relationship("User", back_populates="teacher")
    classes = relationship("TeacherClass", back_populates="teacher")
    daily_attendance = relationship("DailyAttendance", back_populates="teacher")
    

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    academic_year = Column(String(9), nullable=False)
    capacity = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    teachers = relationship("TeacherClass", back_populates="class_")
    students = relationship("Student", back_populates="class_")
    daily_attendance = relationship("DailyAttendance", back_populates="class_")
    

class TeacherClass(Base):
    __tablename__ = "teacher_classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    is_class_teacher = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    
    teacher = relationship("Teacher", back_populates="classes")
    class_ = relationship("Class", back_populates="teachers")

class Guardian(Base):
    __tablename__ = "guardians"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    relationship_to_student = Column(SQLEnum(RelationshipType), nullable=False)
    phone_number = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    occupation = Column(String(100))
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    updated_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")), onupdate=datetime.now(timezone("Africa/Blantyre")))
    
    students = relationship("Student", back_populates="guardian")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(20), unique=True, nullable=False)  # From Excel
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    age = Column(Integer)
    gender = Column(SQLEnum(Gender), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    guardian_id = Column(UUID(as_uuid=True), ForeignKey("guardians.id"), nullable=False)
    home_address = Column(Text)
    distance_to_school = Column(Float)
    transport_method = Column(SQLEnum(TransportMethod))
    enrollment_date = Column(Date, nullable=False)
    start_year = Column(Integer)
    last_year = Column(Integer)
    status = Column(SQLEnum(StudentStatus), default=StudentStatus.ACTIVE)
    special_learning = Column(Boolean, default=False)
    textbook_availability = Column(Boolean, default=True)
    class_repetitions = Column(Integer, default=0)
    household_income = Column(SQLEnum(IncomeLevel))
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    updated_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")), onupdate=datetime.now(timezone("Africa/Blantyre")))
    
    class_ = relationship("Class", back_populates="students")
    guardian = relationship("Guardian", back_populates="students")
    academic_terms = relationship("AcademicTerm", back_populates="student")
    bullying_incidents = relationship("BullyingIncident", back_populates="student")
    dropout_predictions = relationship("DropoutPrediction", back_populates="student")
    daily_attendance = relationship("DailyAttendance", back_populates="student")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(SubjectType), default=SubjectType.CORE)
    
    scores = relationship("SubjectScore", back_populates="subject")

class AcademicTerm(Base):
    __tablename__ = "academic_terms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    term_id = Column(String(20), nullable=False)
    term_type = Column(SQLEnum(TermType), nullable=False)
    academic_year = Column(String(9), nullable=False)
    standard = Column(Integer, nullable=False)
    term_avg_score = Column(Float)
    present_days = Column(Integer)
    absent_days = Column(Integer)
    cumulative_present_days = Column(Integer)
    cumulative_absent_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    
    student = relationship("Student", back_populates="academic_terms")
    subject_scores = relationship("SubjectScore", back_populates="academic_term")
    bullying_records = relationship("BullyingRecord", back_populates="academic_term")

class SubjectScore(Base):
    __tablename__ = "subject_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    score = Column(Float, nullable=False)
    grade = Column(String(2))
    
    academic_term = relationship("AcademicTerm", back_populates="subject_scores")
    subject = relationship("Subject", back_populates="scores")

class BullyingRecord(Base):
    __tablename__ = "bullying_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.id"), nullable=False)
    incidents_reported = Column(Integer, default=0)
    incidents_addressed = Column(Integer, default=0)
    last_incident_date = Column(Date)
    
    academic_term = relationship("AcademicTerm", back_populates="bullying_records")

class BullyingIncident(Base):
    __tablename__ = "bullying_incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    incident_date = Column(Date, nullable=False)
    incident_type = Column(SQLEnum(BullyingType), nullable=False)
    description = Column(Text)
    location = Column(String(100))
    severity_level = Column(SQLEnum(SeverityLevel), nullable=False)
    reported_by_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"))
    action_taken = Column(Text)
    is_addressed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    updated_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")), onupdate=datetime.now(timezone("Africa/Blantyre")))
    
    student = relationship("Student", back_populates="bullying_incidents")
    teacher = relationship("Teacher")

class DropoutPrediction(Base):
    __tablename__ = "dropout_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    contributing_factors = Column(JSON)
    prediction_date = Column(Date, nullable=False)
    algorithm_version = Column(String(20))
    teacher_notified = Column(Boolean, default=False)
    intervention_recommended = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    
    student = relationship("Student", back_populates="dropout_predictions")
    

class PredictionTaskHistory(Base):
    __tablename__ = "prediction_task_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    total_students = Column(Integer)  # Added this column
    processed_count = Column(Integer)  # Added this column
    success_count = Column(Integer)
    failure_count = Column(Integer)
    status = Column(String(20))  # 'running', 'completed', 'failed'
    error_message = Column(Text)
    duration_seconds = Column(Integer)
    
    

class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"   # now uppercase
    ABSENT = "ABSENT"     # uppercase
    LATE = "LATE"         # uppercase

# Simple daily attendance model
class DailyAttendance(Base):
    """Simple daily attendance tracking for students"""
    __tablename__ = "daily_attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.ABSENT)
    notes = Column(Text)  # Optional notes (reason for absence, etc.)
    marked_by_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"))
    created_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")))
    updated_at = Column(DateTime, default=datetime.now(timezone("Africa/Blantyre")), onupdate=datetime.now(timezone("Africa/Blantyre")))
    
    
    # Ensure one attendance record per student per day
    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_date', name='unique_student_daily_attendance'),
    )
    student = relationship("Student", back_populates="daily_attendance")
    teacher = relationship("Teacher", back_populates="daily_attendance")
    class_ = relationship("Class", back_populates="daily_attendance")
