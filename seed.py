# import logging
# from pytz import timezone
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
# from datetime import date, datetime
# import uuid
# from app.database import SessionLocal, engine
# from app.models.all_models import Base, User, Teacher, Class, TeacherClass, Guardian, Student, Subject, AcademicTerm, SubjectScore, BullyingIncident, DropoutPrediction
# from enum import Enum
# from app.schemas.related_schemas import GenderEnum, UserRoleEnum
# from app.utils.auth import get_password_hash

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('database_seed.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# def clear_database_tables(db):
#     """Clear all tables and enum types in the correct order"""
#     try:
#         logger.info("Dropping all tables and enums with CASCADE...")
        
#         # Disable foreign key checks temporarily (PostgreSQL)
#         db.execute(text("SET session_replication_role = 'replica';"))
        
#         # Drop all tables
#         tables = db.execute(text("""
#             SELECT table_name 
#             FROM information_schema.tables 
#             WHERE table_schema = 'public'
#             AND table_type = 'BASE TABLE'
#         """)).fetchall()
        
#         for table in tables:
#             table_name = table[0]
#             try:
#                 db.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
#                 logger.debug(f"Dropped table: {table_name}")
#             except Exception as e:
#                 logger.warning(f"Error dropping table {table_name}: {str(e)}")
#                 db.rollback()

#         # Drop all custom enum types
#         enums = db.execute(text("""
#             SELECT typname 
#             FROM pg_type 
#             WHERE typtype = 'e' 
#             AND typnamespace = (
#                 SELECT oid FROM pg_namespace WHERE nspname = 'public'
#             )
#         """)).fetchall()
        
#         for enum in enums:
#             enum_name = enum[0]
#             try:
#                 db.execute(text(f'DROP TYPE IF EXISTS "{enum_name}" CASCADE;'))
#                 logger.debug(f"Dropped enum: {enum_name}")
#             except Exception as e:
#                 logger.warning(f"Error dropping enum {enum_name}: {str(e)}")
#                 db.rollback()

#         # Re-enable foreign key constraints
#         db.execute(text("SET session_replication_role = 'origin';"))
#         db.commit()
#         logger.info("Successfully cleared all tables and enums")
        
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Error clearing tables/enums: {str(e)}", exc_info=True)
#         raise
    
    
# def seed_database():
#     db = SessionLocal()
    
#     try:
#         logger.info("Starting database seeding process...")
        
#         # Clear existing data
#         clear_database_tables(db)
        
#         # Recreate all tables
#         logger.info("Creating database tables...")
#         Base.metadata.create_all(bind=engine)
        
#         # 1. Create Users
#         logger.info("Creating users...")
#         users = [
#             User(
#                 id=uuid.uuid4(),
#                 username="admin_sibo",
#                 email="admin@malivenji.edu.mw",
#                 password_hash=get_password_hash("password1234"),
#                 role=UserRoleEnum.ADMIN.value,
#             ),
#             User(
#                 id=uuid.uuid4(),
#                 username="ht_kamanga",
#                 email="kamanga@malivenji.edu.mw",
#                 password_hash=get_password_hash("password1234"),
#                 role=UserRoleEnum.HEADTEACHER.value,
#             ),
#             User(
#                 id=uuid.uuid4(),
#                 username="teacher_mwawi",
#                 email="mwawi@malivenji.edu.mw",
#                 password_hash=get_password_hash("password1234"),
#                 role=UserRoleEnum.TEACHER.value,
#             ),
#             User(
#                 id=uuid.uuid4(),
#                 username="teacher_chimango",
#                 email="chimango@malivenji.edu.mw",
#                 password_hash=get_password_hash("password1234"),
#                 role=UserRoleEnum.TEACHER.value,
#             )
#         ]
#         db.add_all(users)
#         db.commit()
#         logger.info(f"Created {len(users)} users")

#         # 2. Create Teachers
#         logger.info("Creating teachers...")
#         teachers = [
#             Teacher(
#                 id=uuid.uuid4(),
#                 user_id=users[1].id,
#                 first_name="Edson",
#                 last_name="Kamanga",
#                 phone_number="+265 991 112 233",
#                 date_of_birth=date(1975, 5, 15),
#                 gender=GenderEnum.MALE.value,
#                 address="Hilltop, Mzuzu",
#                 hire_date=date(2010, 1, 10),
#                 qualification="Bachelor of Education",
#                 experience_years=13
#             ),
#             Teacher(
#                 id=uuid.uuid4(),
#                 user_id=users[2].id,
#                 first_name="Mwawi",
#                 last_name="Nyirenda",
#                 phone_number="+265 881 234 567",
#                 date_of_birth=date(1988, 3, 12),
#                 gender=GenderEnum.FEMALE.value,
#                 address="Chibavi, Mzuzu",
#                 hire_date=date(2016, 2, 1),
#                 qualification="Diploma in Primary Education",
#                 experience_years=7
#             ),
#             Teacher(
#                 id=uuid.uuid4(),
#                 user_id=users[3].id,
#                 first_name="Chimango",
#                 last_name="Mhango",
#                 phone_number="+265 992 345 678",
#                 date_of_birth=date(1992, 7, 25),
#                 gender="male",
#                 address="Zolozolo, Mzuzu",
#                 hire_date=date(2019, 1, 15),
#                 qualification="Bachelor of Education",
#                 experience_years=4
#             )
#         ]
#         db.add_all(teachers)
#         db.commit()
#         logger.info(f"Created {len(teachers)} teachers")

#         # 3. Create Classes with shortened codes
#         logger.info("Creating classes...")
#         classes = [
#             Class(
#                 id=uuid.uuid4(),
#                 name="Standard 1",
#                 code="STD1-2023",  # Shortened to fit varchar(10)
#                 academic_year="2023-2024",
#                 capacity=70,
#                 is_active=True
#             ),
#             Class(
#                 id=uuid.uuid4(),
#                 name="Standard 2",
#                 code="STD2-2023",  # Shortened to fit varchar(10)
#                 academic_year="2023-2024",
#                 capacity=70,
#                 is_active=True
#             ),
#             Class(
#                 id=uuid.uuid4(),
#                 name="Standard 5",
#                 code="STD5-2023",  # Shortened to fit varchar(10)
#                 academic_year="2023-2024",
#                 capacity=65,
#                 is_active=True
#             )
#         ]
#         db.add_all(classes)
#         db.commit()
#         logger.info(f"Created {len(classes)} classes")

#         # 4. Create Teacher-Class Assignments
#         logger.info("Creating teacher-class assignments...")
#         teacher_classes = [
#             TeacherClass(
#                 id=uuid.uuid4(),
#                 teacher_id=teachers[1].id,
#                 class_id=classes[0].id,
#                 is_class_teacher=True
#             ),
#             TeacherClass(
#                 id=uuid.uuid4(),
#                 teacher_id=teachers[2].id,
#                 class_id=classes[2].id,
#                 is_class_teacher=True
#             )
#         ]
#         db.add_all(teacher_classes)
#         db.commit()
#         logger.info(f"Created {len(teacher_classes)} teacher-class assignments")

#         # 5. Create Guardians
#         logger.info("Creating guardians...")
#         guardians = [
#             Guardian(
#                 id=uuid.uuid4(),
#                 first_name="Grace",
#                 last_name="Kanyinji",
#                 relationship_to_student="parent",
#                 phone_number="+265 888 112 233",
#                 email="gracek@gmail.com",
#                 address="Chibanja, Mzuzu",
#                 occupation="Shopkeeper"
#             ),
#             Guardian(
#                 id=uuid.uuid4(),
#                 first_name="Yohane",
#                 last_name="Jere",
#                 relationship_to_student="guardian",
#                 phone_number="+265 999 223 344",
#                 address="Masasa, Mzuzu",
#                 occupation="Farmer"
#             ),
#             Guardian(
#                 id=uuid.uuid4(),
#                 first_name="Tionge",
#                 last_name="Mvula",
#                 relationship_to_student="relative",
#                 phone_number="+265 997 334 455",
#                 email="tiongem@yahoo.com",
#                 address="Katoto, Mzuzu",
#                 occupation="Nurse"
#             )
#         ]
#         db.add_all(guardians)
#         db.commit()
#         logger.info(f"Created {len(guardians)} guardians")

#         # 6. Create Students with corrected status values
#         logger.info("Creating students...")
#         students = [
#             Student(
#                 id=uuid.uuid4(),
#                 student_id="MLV-2023-001",
#                 first_name="Tawonga",
#                 last_name="Kanyinji",
#                 date_of_birth=date(2016, 5, 15),
#                 age=7,
#                 gender="female",
#                 class_id=classes[0].id,
#                 guardian_id=guardians[0].id,
#                 home_address="Chibanja, Mzuzu",
#                 distance_to_school=1.2,
#                 transport_method="walking",
#                 enrollment_date=date(2023, 1, 9),
#                 start_year=2023,
#                 last_year=None,
#                 status="active",  # Changed to lowercase
#                 special_learning=False,
#                 textbook_availability=True,
#                 class_repetitions=0,
#                 household_income="medium",
#                 created_at=datetime.now(timezone("Africa/Blantyre")),
#                 updated_at=datetime.now(timezone("Africa/Blantyre"))
#             ),
#             Student(
#                 id=uuid.uuid4(),
#                 student_id="MLV-2023-002",
#                 first_name="Lusungu",
#                 last_name="Jere",
#                 date_of_birth=date(2014, 8, 22),
#                 age=9,
#                 gender="male",
#                 class_id=classes[2].id,
#                 guardian_id=guardians[1].id,
#                 home_address="Masasa, Mzuzu",
#                 distance_to_school=3.5,
#                 transport_method="bicycle",
#                 enrollment_date=date(2020, 1, 12),
#                 start_year=2020,
#                 last_year=None,
#                 status="active",  # Changed to lowercase
#                 special_learning=False,
#                 textbook_availability=False,
#                 class_repetitions=1,
#                 household_income="low",
#                 created_at=datetime.now(timezone("Africa/Blantyre")),
#                 updated_at=datetime.now(timezone("Africa/Blantyre"))
#             ),
#             Student(
#                 id=uuid.uuid4(),
#                 student_id="MLV-2023-003",
#                 first_name="Mphatso",
#                 last_name="Mvula",
#                 date_of_birth=date(2015, 11, 3),
#                 age=8,
#                 gender="female",
#                 class_id=classes[0].id,
#                 guardian_id=guardians[2].id,
#                 home_address="Katoto, Mzuzu",
#                 distance_to_school=2.8,
#                 transport_method="public_transport",
#                 enrollment_date=date(2023, 1, 10),
#                 start_year=2023,
#                 last_year=None,
#                 status="active",  # Changed to lowercase
#                 special_learning=False,
#                 textbook_availability=True,
#                 class_repetitions=0,
#                 household_income="high",
#                 created_at=datetime.now(timezone("Africa/Blantyre")),
#                 updated_at=datetime.now(timezone("Africa/Blantyre"))
#             )
#         ]
#         db.add_all(students)
#         db.commit()
#         logger.info(f"Created {len(students)} students")

#         # 7. Create Subjects
#         logger.info("Creating subjects...")
#         subjects = [
#             Subject(
#                 id=uuid.uuid4(),
#                 name="English",
#                 code="ENG",
#                 description="English language studies",
#                 type="core"
#             ),
#             Subject(
#                 id=uuid.uuid4(),
#                 name="Chichewa",
#                 code="CHI",
#                 description="Chichewa language studies",
#                 type="core"
#             ),
#             Subject(
#                 id=uuid.uuid4(),
#                 name="Mathematics",
#                 code="MATH",
#                 description="Mathematics studies",
#                 type="core"
#             ),
#             Subject(
#                 id=uuid.uuid4(),
#                 name="Science",
#                 code="SCI",
#                 description="Science and technology",
#                 type="core"
#             ),
#             Subject(
#                 id=uuid.uuid4(),
#                 name="Social Studies",
#                 code="SOC",
#                 description="Social and environmental studies",
#                 type="core"
#             ),
#             Subject(
#                 id=uuid.uuid4(),
#                 name="Physical Education",
#                 code="PE",
#                 description="Sports and physical activities",
#                 type="extracurricular"
#             )
#         ]
#         db.add_all(subjects)
#         db.commit()
#         logger.info(f"Created {len(subjects)} subjects")

#         # 8. Create Academic Terms with shortened term IDs
#         logger.info("Creating academic terms...")
#         academic_terms = [
#             AcademicTerm(
#                 id=uuid.uuid4(),
#                 student_id=students[0].id,
#                 term_id="STD1-T1-2023",  # Shortened term ID
#                 term_type="term1",
#                 academic_year="2023-2024",
#                 standard=1,
#                 term_avg_score=72.5,
#                 present_days=88,
#                 absent_days=2
#             ),
#             AcademicTerm(
#                 id=uuid.uuid4(),
#                 student_id=students[1].id,
#                 term_id="STD5-T1-2023",  # Shortened term ID
#                 term_type="term1",
#                 academic_year="2023-2024",
#                 standard=5,
#                 term_avg_score=54.0,
#                 present_days=70,
#                 absent_days=20
#             )
#         ]
#         db.add_all(academic_terms)
#         db.commit()
#         logger.info(f"Created {len(academic_terms)} academic terms")

#         # 9. Create Subject Scores
#         logger.info("Creating subject scores...")
#         subject_scores = [
#             SubjectScore(
#                 id=uuid.uuid4(),
#                 academic_term_id=academic_terms[0].id,
#                 subject_id=subjects[0].id,
#                 score=68,
#                 grade="C"
#             ),
#             SubjectScore(
#                 id=uuid.uuid4(),
#                 academic_term_id=academic_terms[0].id,
#                 subject_id=subjects[1].id,
#                 score=85,
#                 grade="A"
#             ),
#             SubjectScore(
#                 id=uuid.uuid4(),
#                 academic_term_id=academic_terms[0].id,
#                 subject_id=subjects[2].id,
#                 score=72,
#                 grade="B"
#             ),
#             SubjectScore(
#                 id=uuid.uuid4(),
#                 academic_term_id=academic_terms[1].id,
#                 subject_id=subjects[0].id,
#                 score=52,
#                 grade="D"
#             ),
#             SubjectScore(
#                 id=uuid.uuid4(),
#                 academic_term_id=academic_terms[1].id,
#                 subject_id=subjects[2].id,
#                 score=48,
#                 grade="E"
#             )
#         ]
#         db.add_all(subject_scores)
#         db.commit()
#         logger.info(f"Created {len(subject_scores)} subject scores")

#         # 10. Create Bullying Incidents
#         logger.info("Creating bullying incidents...")
#         bullying_incidents = [
#             BullyingIncident(
#                 id=uuid.uuid4(),
#                 student_id=students[1].id,
#                 incident_date=date(2023, 5, 20),
#                 incident_type="verbal",
#                 description="Called 'dumb' repeatedly by classmates for failing exams",
#                 location="Classroom during break",
#                 severity_level="medium",
#                 reported_by_teacher_id=teachers[1].id,
#                 action_taken="Peer counseling and parent meeting",
#                 is_addressed=True
#             ),
#             BullyingIncident(
#                 id=uuid.uuid4(),
#                 student_id=students[0].id,
#                 incident_date=date(2023, 6, 10),
#                 incident_type="physical",
#                 description="Pushed down during lunch queue at school feeding program",
#                 location="School kitchen area",
#                 severity_level="high",
#                 reported_by_teacher_id=teachers[2].id,
#                 action_taken="Disciplinary committee meeting held",
#                 is_addressed=True
#             )
#         ]
#         db.add_all(bullying_incidents)
#         db.commit()
#         logger.info(f"Created {len(bullying_incidents)} bullying incidents")

#         logger.info("Successfully completed database seeding!")
#         logger.info(f"Total records created: {sum([len(users), len(teachers), len(classes), len(teacher_classes), len(guardians), len(students), len(subjects), len(academic_terms), len(subject_scores), len(bullying_incidents)])}")

#     except Exception as e:
#         db.rollback()
#         logger.error(f"Error during database seeding: {str(e)}", exc_info=True)
#         raise
#     finally:
#         db.close()
#         logger.info("Database connection closed")

# if __name__ == "__main__":
#     try:
#         seed_database()
#     except Exception as e:
#         logger.critical(f"Fatal error in seeding process: {str(e)}", exc_info=True)
#         exit(1)

import random
from datetime import date, datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SessionLocal
from app.models.all_models import AcademicTerm, BullyingRecord, Class, Gender, Guardian, IncomeLevel, RelationshipType, Student, StudentStatus, Subject, SubjectScore, Teacher, TeacherClass, TransportMethod, User, UserRole
from app.schemas.academics_schemas import TermType
from app.utils.auth import get_password_hash


# # Initialize Faker with locale for Malawi
# fake = Faker(['en_US'])

# # Database connection (adjust as needed)

# def generate_malawian_names():
#     """Generate realistic Malawian names"""
#     first_names_male = [
#         "Chimwemwe", "Kondwani", "Mphatso", "Blessings", "Gift", "Precious", 
#         "Yamikani", "Limbani", "Chisomo", "Dalitso", "Pemphero", "Thokozani",
#         "Macheso", "Takondwa", "Chikondi", "Mavuto", "Zikomo", "Tamandani"
#     ]
    
#     first_names_female = [
#         "Chisomo", "Pemphero", "Mphatso", "Chimwemwe", "Kondwani", "Tamandani",
#         "Thokozani", "Dalitso", "Yamikani", "Limbani", "Takondwa", "Chikondi",
#         "Mercy", "Grace", "Faith", "Hope", "Joy", "Peace"
#     ]
    
#     last_names = [
#         "Banda", "Phiri", "Mwale", "Nyirenda", "Chirwa", "Mbewe", "Zulu",
#         "Kamanga", "Mhango", "Mvula", "Nkomo", "Gondwe", "Kachala", "Nyasulu",
#         "Munthali", "Kanyama", "Nkhoma", "Chiumia", "Kafoteka", "Masamba"
#     ]
    
#     return first_names_male, first_names_female, last_names

# def generate_student_id(standard, student_number, year="2024"):
#     """Generate student ID in format: STD1-2024-001"""
#     return f"STD{standard}-{year}-{student_number:03d}"

# def generate_guardian_data(last_name):
#     """Generate guardian data"""
#     first_names_male, first_names_female, _ = generate_malawian_names()
    
#     occupations = [
#         "Farmer", "Teacher", "Trader", "Nurse", "Driver", "Tailor", 
#         "Carpenter", "Mason", "Mechanic", "Shop Owner", "Security Guard",
#         "Cleaner", "Cook", "Gardener", "Fisherman", "Blacksmith"
#     ]
    
#     gender = random.choice([Gender.MALE, Gender.FEMALE])
#     first_name = random.choice(first_names_male if gender == Gender.MALE else first_names_female)
    
#     return {
#         'first_name': first_name,
#         'last_name': last_name,
#         'relationship_to_student': random.choice(list(RelationshipType)),
#         'phone_number': f"+265{random.randint(881000000, 999999999)}",
#         'email': f"{first_name.lower()}.{last_name.lower()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}",
#         'address': f"Area {random.randint(1, 50)}, {random.choice(['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba'])}",
#         'occupation': random.choice(occupations)
#     }

# def generate_student_data(standard, student_number, class_id, guardian_id):
#     """Generate student data"""
#     first_names_male, first_names_female, last_names = generate_malawian_names()
    
#     gender = random.choice([Gender.MALE, Gender.FEMALE])
#     first_name = random.choice(first_names_male if gender == Gender.MALE else first_names_female)
#     last_name = random.choice(last_names)
    
#     # Calculate age based on standard (typical age range)
#     base_age = 6 + standard - 1  # Standard 1 starts at age 6
#     age = random.randint(base_age, base_age + 3)
    
#     birth_year = 2024 - age
#     date_of_birth = date(birth_year, random.randint(1, 12), random.randint(1, 28))
    
#     return {
#         'student_id': generate_student_id(standard, student_number),
#         'first_name': first_name,
#         'last_name': last_name,
#         'date_of_birth': date_of_birth,
#         'age': age,
#         'gender': gender,
#         'class_id': class_id,
#         'guardian_id': guardian_id,
#         'home_address': f"Area {random.randint(1, 50)}, {random.choice(['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba'])}",
#         'distance_to_school': round(random.uniform(0.5, 15.0), 2),
#         'transport_method': random.choice(list(TransportMethod)),
#         'enrollment_date': date(2024, random.randint(1, 3), random.randint(1, 28)),
#         'start_year': 2024,
#         'last_year': 2024,
#         'status': StudentStatus.ACTIVE,
#         'special_learning': random.choice([True, False]) if random.random() < 0.1 else False,
#         'textbook_availability': random.choice([True, False]) if random.random() < 0.2 else True,
#         'class_repetitions': random.choice([0, 1, 2]) if random.random() < 0.15 else 0,
#         'household_income': random.choice(list(IncomeLevel))
#     }

# def generate_academic_term_data(student_id, term_type, standard):
#     """Generate academic term data"""
#     term_mapping = {
#         TermType.term1: "01",
#         TermType.term2: "02", 
#         TermType.term3: "03"
#     }
    
#     term_id = f"2024-{term_mapping[term_type]}-STD{standard}"
    
#     # Generate attendance (present days out of ~90 days per term)
#     total_days = random.randint(85, 95)
#     present_days = random.randint(70, total_days)
#     absent_days = total_days - present_days
    
#     return {
#         'student_id': student_id,
#         'term_id': term_id,
#         'term_type': term_type,
#         'academic_year': "2024-2025",
#         'standard': standard,
#         'present_days': present_days,
#         'absent_days': absent_days,
#         'cumulative_present_days': present_days,
#         'cumulative_absent_days': absent_days
#     }

# def generate_subject_scores(academic_term_id, subject_ids):
#     """Generate subject scores for a term"""
#     scores = []
#     term_scores = []
    
#     for subject_id in subject_ids:
#         # Generate realistic scores (0-100)
#         score = round(random.uniform(30, 95), 1)
#         term_scores.append(score)
        
#         # Assign grade based on score
#         if score >= 80:
#             grade = "A"
#         elif score >= 70:
#             grade = "B"
#         elif score >= 60:
#             grade = "C"
#         elif score >= 50:
#             grade = "D"
#         else:
#             grade = "F"
        
#         scores.append({
#             'academic_term_id': academic_term_id,
#             'subject_id': subject_id,
#             'score': score,
#             'grade': grade
#         })
    
#     return scores, sum(term_scores) / len(term_scores) if term_scores else 0

# def generate_bullying_record(academic_term_id):
#     """Generate bullying record data"""
#     incidents_reported = random.randint(0, 3) if random.random() < 0.3 else 0
#     incidents_addressed = random.randint(0, incidents_reported) if incidents_reported > 0 else 0
    
#     last_incident_date = None
#     if incidents_reported > 0:
#         last_incident_date = date(2024, random.randint(1, 12), random.randint(1, 28))
    
#     return {
#         'academic_term_id': academic_term_id,
#         'incidents_reported': incidents_reported,
#         'incidents_addressed': incidents_addressed,
#         'last_incident_date': last_incident_date
#     }

# def seed_students():
#     """Main seeding function"""
#     session = SessionLocal()
    
#     try:
#         # Get all classes for academic year 2024-2025
#         classes = session.query(Class).filter(
#             Class.academic_year == "2024-2025",
#             Class.is_active == True
#         ).all()
        
#         if not classes:
#             print("No classes found for academic year 2024-2025")
#             return
        
#         # Get all subjects
#         subjects = session.query(Subject).all()
#         subject_ids = [subject.id for subject in subjects]
        
#         if not subject_ids:
#             print("No subjects found in database")
#             return
        
#         print(f"Found {len(classes)} classes and {len(subjects)} subjects")
        
#         # Group classes by standard (assuming class names contain standard info)
#         classes_by_standard = {}
#         for class_obj in classes:
#             # Extract standard from class name (e.g., "Standard 1A" -> 1)
#             try:
#                 standard = int(class_obj.name.split()[1][0])  # Gets first digit
#                 if standard not in classes_by_standard:
#                     classes_by_standard[standard] = []
#                 classes_by_standard[standard].append(class_obj)
#             except (IndexError, ValueError):
#                 print(f"Could not extract standard from class name: {class_obj.name}")
#                 continue
        
#         total_students_created = 0
        
#         # Seed students for each standard (1-8)
#         for standard in range(1, 9):
#             if standard not in classes_by_standard:
#                 print(f"No classes found for Standard {standard}")
#                 continue
            
#             standard_classes = classes_by_standard[standard]
#             print(f"\nSeeding Standard {standard} - {len(standard_classes)} classes")
            
#             for class_obj in standard_classes:
#                 print(f"  Seeding class: {class_obj.name}")
                
#                 # Create 10 students per class
#                 for student_num in range(1, 11):
#                     # Create guardian
#                     guardian_data = generate_guardian_data(fake.last_name())
#                     guardian = Guardian(**guardian_data)
#                     session.add(guardian)
#                     session.flush()  # Get the guardian ID
                    
#                     # Create student
#                     student_data = generate_student_data(
#                         standard, 
#                         (total_students_created + student_num), 
#                         class_obj.id, 
#                         guardian.id
#                     )
#                     student = Student(**student_data)
#                     session.add(student)
#                     session.flush()  # Get the student ID
                    
#                     # Create academic terms (3 terms per year)
#                     for term_type in [TermType.term1, TermType.term2, TermType.term3]:
#                         term_data = generate_academic_term_data(student.id, term_type, standard)
#                         academic_term = AcademicTerm(**term_data)
#                         session.add(academic_term)
#                         session.flush()  # Get the term ID
                        
#                         # Generate subject scores
#                         scores_data, avg_score = generate_subject_scores(academic_term.id, subject_ids)
                        
#                         # Update term average
#                         academic_term.term_avg_score = round(avg_score, 2)
                        
#                         # Add subject scores
#                         for score_data in scores_data:
#                             subject_score = SubjectScore(**score_data)
#                             session.add(subject_score)
                        
#                         # Add bullying record
#                         bullying_data = generate_bullying_record(academic_term.id)
#                         bullying_record = BullyingRecord(**bullying_data)
#                         session.add(bullying_record)
                
#                 total_students_created += 10
#                 print(f"    Created 10 students for {class_obj.name}")
        
#         # Commit all changes
#         session.commit()
#         print(f"\n✅ Successfully seeded {total_students_created} students with complete academic data!")
#         print(f"📊 Each student has:")
#         print(f"   - 1 Guardian")
#         print(f"   - 3 Academic Terms")
#         print(f"   - {len(subject_ids)} Subject Scores per term")
#         print(f"   - 3 Bullying Records")
        
#     except Exception as e:
#         session.rollback()
#         print(f"❌ Error during seeding: {str(e)}")
#         raise
#     finally:
#         session.close()

# if __name__ == "__main__":
#     print("🌱 Starting student data seeding for academic year 2024-2025...")
#     print("📚 Standards 1-8, 10 students per class")
#     print("=" * 60)
    
#     seed_students()



def generate_malawian_teacher_names():
    """Generate realistic Malawian teacher names"""
    first_names_male = [
        "Chimwemwe", "Kondwani", "Mphatso", "Blessings", "Gift", "Precious", 
        "Yamikani", "Limbani", "Chisomo", "Dalitso", "Pemphero", "Thokozani",
        "Macheso", "Takondwa", "Chikondi", "Mavuto", "Zikomo", "Tamandani",
        "Patrick", "James", "John", "Peter", "Paul", "Michael", "David", "Samuel"
    ]
    
    first_names_female = [
        "Chisomo", "Pemphero", "Mphatso", "Chimwemwe", "Kondwani", "Tamandani",
        "Thokozani", "Dalitso", "Yamikani", "Limbani", "Takondwa", "Chikondi",
        "Mercy", "Grace", "Faith", "Hope", "Joy", "Peace", "Mary", "Sarah",
        "Ruth", "Esther", "Martha", "Elizabeth", "Catherine", "Agnes"
    ]
    
    last_names = [
        "Banda", "Phiri", "Mwale", "Nyirenda", "Chirwa", "Mbewe", "Zulu",
        "Kamanga", "Mhango", "Mvula", "Nkomo", "Gondwe", "Kachala", "Nyasulu",
        "Munthali", "Kanyama", "Nkhoma", "Chiumia", "Kafoteka", "Masamba",
        "Phiri", "Mkandawire", "Tembo", "Kaunda", "Mwanza", "Sakala"
    ]
    
    return first_names_male, first_names_female, last_names

def generate_teacher_qualifications():
    """Generate realistic teacher qualifications"""
    qualifications = [
        "Bachelor of Education (Primary)",
        "Bachelor of Education (Secondary)",
        "Diploma in Primary Education",
        "Diploma in Secondary Education",
        "Certificate in Primary Education",
        "Bachelor of Arts in Education",
        "Bachelor of Science in Education",
        "Master of Education",
        "Diploma in Early Childhood Development",
        "Bachelor of Education (Mathematics)",
        "Bachelor of Education (English)",
        "Bachelor of Education (Science)",
        "Certificate in Teacher Education",
        "Diploma in Special Needs Education"
    ]
    return random.choice(qualifications)

def generate_teacher_data(existing_usernames, existing_emails):
    """Generate teacher data"""
    first_names_male, first_names_female, last_names = generate_malawian_teacher_names()
    
    gender = random.choice([Gender.MALE, Gender.FEMALE])
    first_name = random.choice(first_names_male if gender == Gender.MALE else first_names_female)
    last_name = random.choice(last_names)
    
    # Generate unique username
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    username = base_username
    counter = 1
    while username in existing_usernames:
        username = f"{base_username}{counter}"
        counter += 1
    existing_usernames.add(username)
    
    # Generate unique email
    email = f"{username}@school.edu.mw"
    counter = 1
    while email in existing_emails:
        email = f"{username}{counter}@school.edu.mw"
        counter += 1
    existing_emails.add(email)
    
    # Generate realistic age and hire date
    age = random.randint(25, 60)
    birth_year = 2024 - age
    date_of_birth = date(birth_year, random.randint(1, 12), random.randint(1, 28))
    
    # Hire date (teachers hired in the last 1-20 years)
    years_ago = random.randint(1, 20)
    hire_date = date(2024 - years_ago, random.randint(1, 12), random.randint(1, 28))
    
    # Experience years (slightly less than years since hire)
    experience_years = max(1, years_ago + random.randint(-2, 3))
    
    user_data = {
        'username': username,
        'email': email,
        'password_hash': get_password_hash("password1234"),
        'role': UserRole.TEACHER,
        'is_active': True
    }
    
    teacher_data = {
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': f"+265{random.randint(881000000, 999999999)}",
        'date_of_birth': date_of_birth,
        'gender': gender,
        'address': f"Area {random.randint(1, 50)}, {random.choice(['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba'])}",
        'hire_date': hire_date,
        'qualification': generate_teacher_qualifications(),
        'experience_years': experience_years,
        'is_active': True
    }
    
    return user_data, teacher_data

def allocate_teachers_to_classes(session, teachers, classes):
    """Allocate teachers to classes with realistic distribution"""
    print("\n📋 Allocating teachers to classes...")
    
    # Clear existing teacher-class assignments
    session.query(TeacherClass).delete()
    session.flush()
    
    # Group classes by standard for better allocation
    classes_by_standard = {}
    for class_obj in classes:
        try:
            standard = int(class_obj.name.split()[1][0])
            if standard not in classes_by_standard:
                classes_by_standard[standard] = []
            classes_by_standard[standard].append(class_obj)
        except (IndexError, ValueError):
            print(f"Could not extract standard from class name: {class_obj.name}")
            continue
    
    teacher_allocations = []
    
    # Strategy: Each teacher gets 2-4 classes, with one being their main class
    for i, teacher in enumerate(teachers):
        # Determine how many classes this teacher will handle
        num_classes = random.randint(2, 4)
        
        # Select classes for this teacher
        available_classes = [c for c in classes if c.id not in [ta['class_id'] for ta in teacher_allocations]]
        
        if not available_classes:
            # If no classes available, pick from all classes (teachers can share)
            available_classes = classes
        
        # Prefer classes from same or adjacent standards for primary teachers
        teacher_classes = random.sample(available_classes, min(num_classes, len(available_classes)))
        
        # First class is the main class (class teacher)
        is_first = True
        for class_obj in teacher_classes:
            allocation = {
                'teacher_id': teacher.id,
                'class_id': class_obj.id,
                'is_class_teacher': is_first
            }
            teacher_allocations.append(allocation)
            is_first = False
            
            print(f"   {teacher.first_name} {teacher.last_name} -> {class_obj.name} {'(Class Teacher)' if allocation['is_class_teacher'] else ''}")
    
    # Ensure every class has at least one teacher
    unassigned_classes = [c for c in classes if c.id not in [ta['class_id'] for ta in teacher_allocations]]
    
    if unassigned_classes:
        print(f"\n⚠️  Assigning {len(unassigned_classes)} unassigned classes to available teachers...")
        for class_obj in unassigned_classes:
            # Assign to a random teacher
            teacher = random.choice(teachers)
            allocation = {
                'teacher_id': teacher.id,
                'class_id': class_obj.id,
                'is_class_teacher': False
            }
            teacher_allocations.append(allocation)
            print(f"   {teacher.first_name} {teacher.last_name} -> {class_obj.name} (Additional)")
    
    # Create TeacherClass records
    for allocation in teacher_allocations:
        teacher_class = TeacherClass(**allocation)
        session.add(teacher_class)
    
    return teacher_allocations

def seed_teachers_and_allocate():
    """Main function to seed teachers and allocate to classes"""
    session = SessionLocal()
    
    try:
        print("🎯 Starting teacher seeding and class allocation...")
        
        # Get existing teachers count
        existing_teachers = session.query(Teacher).all()
        existing_count = len(existing_teachers)
        print(f"📊 Current teachers in database: {existing_count}")
        
        # Get existing usernames and emails to avoid duplicates
        existing_users = session.query(User).all()
        existing_usernames = {user.username for user in existing_users}
        existing_emails = {user.email for user in existing_users}
        
        # Get all classes
        classes = session.query(Class).filter(
            Class.academic_year == "2024-2025",
            Class.is_active == True
        ).all()
        
        if not classes:
            print("❌ No classes found for academic year 2024-2025")
            return
        
        print(f"📚 Found {len(classes)} classes for allocation")
        
        # Calculate how many more teachers we need
        # Aim for 1 teacher per 2-3 classes, minimum 8 teachers for 8 standards
        target_teachers = max(8, len(classes) // 2)
        teachers_to_add = max(0, target_teachers - existing_count)
        
        print(f"🎯 Target teachers: {target_teachers}")
        print(f"➕ Teachers to add: {teachers_to_add}")
        
        # Add new teachers
        new_teachers = []
        if teachers_to_add > 0:
            print(f"\n👥 Adding {teachers_to_add} new teachers...")
            
            for i in range(teachers_to_add):
                # Generate teacher data
                user_data, teacher_data = generate_teacher_data(existing_usernames, existing_emails)
                
                # Create user
                user = User(**user_data)
                session.add(user)
                session.flush()  # Get user ID
                
                # Create teacher
                teacher_data['user_id'] = user.id
                teacher = Teacher(**teacher_data)
                session.add(teacher)
                session.flush()  # Get teacher ID
                
                new_teachers.append(teacher)
                print(f"   ✅ Added: {teacher.first_name} {teacher.last_name} ({teacher.qualification})")
        
        # Get all teachers (existing + new)
        all_teachers = session.query(Teacher).filter(Teacher.is_active == True).all()
        print(f"\n👥 Total active teachers: {len(all_teachers)}")
        
        # Allocate teachers to classes
        allocations = allocate_teachers_to_classes(session, all_teachers, classes)
        
        # Commit all changes
        session.commit()
        
        # Print summary
        print("\n" + "="*60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"👥 Total teachers: {len(all_teachers)}")
        print(f"➕ New teachers added: {len(new_teachers)}")
        print(f"📚 Classes allocated: {len(classes)}")
        print(f"🔗 Teacher-class assignments: {len(allocations)}")
        
        # Show class teacher assignments
        class_teachers = [a for a in allocations if a['is_class_teacher']]
        print(f"🏫 Class teachers assigned: {len(class_teachers)}")
        
        # Show teacher workload summary
        print("\n📊 Teacher Workload Summary:")
        teacher_workload = {}
        for allocation in allocations:
            teacher_id = allocation['teacher_id']
            if teacher_id not in teacher_workload:
                teacher_workload[teacher_id] = {'total': 0, 'main': 0}
            teacher_workload[teacher_id]['total'] += 1
            if allocation['is_class_teacher']:
                teacher_workload[teacher_id]['main'] += 1
        
        for teacher in all_teachers:
            if teacher.id in teacher_workload:
                workload = teacher_workload[teacher.id]
                print(f"   {teacher.first_name} {teacher.last_name}: {workload['total']} classes ({workload['main']} as class teacher)")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🏫 Teacher Seeding and Class Allocation Script")
    print("=" * 60)
    
    seed_teachers_and_allocate()