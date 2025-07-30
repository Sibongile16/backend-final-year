# Malivenji Primary School Dropout Monitoring System - Database Design

## Core Entities and Relationships

### 1. **Users** (Authentication & Authorization)
```sql
users
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- role (enum: 'headteacher', 'deputy_headteacher', 'teacher')
- is_active (Boolean)
- created_at
- updated_at
```

### 2. **Teachers** (Profile Information)
```sql
teachers
- id (Primary Key)
- user_id (Foreign Key → users.id, Unique)
- first_name
- last_name
- phone_number
- date_of_birth
- gender (enum: 'male', 'female')
- address
- hire_date
- qualification
- experience_years
- created_at
- updated_at
```

### 3. **Subjects**
```sql
subjects
- id (Primary Key)
- name (e.g., 'English', 'Primary Science', 'Mathematics', etc.)
- code (e.g., 'ENG', 'SCI', 'MATH')
- description
- is_active (Boolean)
```

### 4. **Classes/Standards**
```sql
classes
- id (Primary Key)
- name (e.g., 'Standard 1', 'Standard 2', etc.)
- code (e.g., 'STD1', 'STD2')
- academic_year
- capacity (Maximum students)
- is_active (Boolean)
```

### 5. **Teacher-Subject Assignments**
```sql
teacher_subjects
- id (Primary Key)
- teacher_id (Foreign Key → teachers.id)
- subject_id (Foreign Key → subjects.id)
- academic_year
- created_at
```

### 6. **Teacher-Class Assignments**
```sql
teacher_classes
- id (Primary Key)
- teacher_id (Foreign Key → teachers.id)
- class_id (Foreign Key → classes.id)
- is_class_teacher (Boolean) -- Main class teacher vs subject teacher
- academic_year
- created_at
```

### 7. **Guardians**
```sql
guardians
- id (Primary Key)
- first_name
- last_name
- relationship_to_student (enum: 'parent', 'guardian', 'relative', 'other')
- phone_number
- email
- address
- occupation
- monthly_income_range (enum: 'below_50k', '50k_100k', '100k_200k', 'above_200k')
- education_level (enum: 'none', 'primary', 'secondary', 'tertiary')
- created_at
- updated_at
```

### 8. **Students** (Core Entity)
```sql
students
- id (Primary Key)
- student_number (Unique identifier)
- first_name
- last_name
- date_of_birth
- age (Calculated field)
- gender (enum: 'male', 'female')
- current_class_id (Foreign Key → classes.id)
- primary_guardian_id (Foreign Key → guardians.id)
- secondary_guardian_id (Foreign Key → guardians.id, Optional)
- home_address
- distance_to_school_km (Decimal)
- transport_method (enum: 'walking', 'bicycle', 'public_transport', 'private_transport')
- enrollment_date
- is_active (Boolean)
- special_needs (Text, Optional)
- medical_conditions (Text, Optional)
- created_at
- updated_at
```

### 9. **Student Class History** (Track repetitions and transfers)
```sql
student_class_history
- id (Primary Key)
- student_id (Foreign Key → students.id)
- class_id (Foreign Key → classes.id)
- academic_year
- enrollment_date
- completion_date (NULL if ongoing)
- status (enum: 'completed', 'repeated', 'transferred', 'dropped_out')
- reason_for_status_change (Text, Optional)
- created_at
```

### 10. **Attendance Records**
```sql
attendance_records
- id (Primary Key)
- student_id (Foreign Key → students.id)
- date
- status (enum: 'present', 'absent', 'late', 'excused')
- reason_for_absence (Text, Optional)
- recorded_by_teacher_id (Foreign Key → teachers.id)
- created_at
```

### 11. **Academic Performance**
```sql
academic_performance
- id (Primary Key)
- student_id (Foreign Key → students.id)
- subject_id (Foreign Key → subjects.id)
- assessment_type (enum: 'test', 'exam', 'assignment', 'continuous_assessment')
- assessment_name
- marks_obtained
- total_marks
- percentage
- grade (e.g., 'A', 'B', 'C', 'D', 'F')
- assessment_date
- academic_year
- term (enum: 'term1', 'term2', 'term3')
- teacher_id (Foreign Key → teachers.id)
- created_at
```

### 12. **Bullying Incidents**
```sql
bullying_incidents
- id (Primary Key)
- victim_student_id (Foreign Key → students.id)
- perpetrator_student_id (Foreign Key → students.id, Optional)
- incident_date
- incident_type (enum: 'physical', 'verbal', 'cyber', 'social_exclusion', 'other')
- description (Text)
- location (enum: 'classroom', 'playground', 'toilet', 'corridor', 'outside_school', 'other')
- severity_level (enum: 'low', 'medium', 'high', 'critical')
- reported_by_teacher_id (Foreign Key → teachers.id)
- action_taken (Text)
- follow_up_required (Boolean)
- follow_up_date (Date, Optional)
- status (enum: 'reported', 'investigating', 'resolved', 'escalated')
- created_at
- updated_at
```

### 13. **Dropout Risk Factors** (Additional tracking)
```sql
student_risk_factors
- id (Primary Key)
- student_id (Foreign Key → students.id)
- factor_type (enum: 'economic', 'family', 'academic', 'social', 'health', 'behavioral')
- factor_description
- severity_level (enum: 'low', 'medium', 'high')
- identified_date
- identified_by_teacher_id (Foreign Key → teachers.id)
- mitigation_actions (Text, Optional)
- is_resolved (Boolean)
- resolution_date (Date, Optional)
- created_at
- updated_at
```

### 14. **Dropout Predictions/Alerts**
```sql
dropout_predictions
- id (Primary Key)
- student_id (Foreign Key → students.id)
- risk_score (Decimal, 0-100)
- risk_level (enum: 'low', 'medium', 'high', 'critical')
- contributing_factors (JSON) -- Store array of factor types
- prediction_date
- algorithm_version
- teacher_notified (Boolean)
- intervention_recommended (Text)
- created_at
```

## Key Relationships Summary

1. **One-to-One**: Users ↔ Teachers
2. **Many-to-Many**: Teachers ↔ Subjects (through teacher_subjects)
3. **Many-to-Many**: Teachers ↔ Classes (through teacher_classes)
4. **One-to-Many**: Classes → Students
5. **One-to-Many**: Guardians → Students (primary/secondary guardian)
6. **One-to-Many**: Students → Attendance Records
7. **One-to-Many**: Students → Academic Performance
8. **One-to-Many**: Students → Student Class History
9. **One-to-Many**: Students → Bullying Incidents (as victim)
10. **One-to-Many**: Students → Risk Factors
11. **One-to-Many**: Students → Dropout Predictions

## Indexes for Performance
- Student number (unique)
- Teacher-Class assignments by academic year
- Student attendance by date range
- Academic performance by student and term
- Bullying incidents by date and severity
- Dropout predictions by risk level and date

## Additional Considerations

### Data Privacy & Security
- Implement row-level security for teachers to access only their assigned classes
- Encrypt sensitive personal information
- Audit trail for all data modifications

### Academic Year Management
- Most tables include academic_year field for historical data tracking
- Separate current vs historical data queries

### Reporting & Analytics
- Create views for common dropout risk analytics
- Aggregate tables for performance dashboards
- Regular calculation of attendance rates and academic averages

### Scalability
- Partition large tables (attendance, performance) by academic year
- Consider archiving old academic year data
- Implement proper foreign key constraints and cascading rules