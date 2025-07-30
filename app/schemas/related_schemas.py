
from enum import Enum


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    HEADTEACHER = "headteacher"
    TEACHER = "teacher"

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"

class RelationshipTypeEnum(str, Enum):
    PARENT = "parent"
    GUARDIAN = "guardian"
    RELATIVE = "relative"
    OTHER = "other"

class IncomeLevelEnum(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class TransportMethodEnum(str, Enum):
    WALKING = "walking"
    BICYCLE = "bicycle"
    PUBLIC_TRANSPORT = "public_transport"
    PRIVATE_TRANSPORT = "private_transport"

class StudentStatusEnum(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    REPEATED = "repeated"
    TRANSFERRED = "transferred"
    DROPPED_OUT = "dropped_out"

class TermTypeEnum(str, Enum):
    TERM1 = "term1"
    TERM2 = "term2"
    TERM3 = "term3"

class SubjectTypeEnum(str, Enum):
    CORE = "core"
    ELECTIVE = "elective"
    EXTRACURRICULAR = "extracurricular"

class BullyingTypeEnum(str, Enum):
    PHYSICAL = "physical"
    VERBAL = "verbal"
    CYBER = "cyber"
    SOCIAL_EXCLUSION = "social_exclusion"
    OTHER = "other"

class SeverityLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
