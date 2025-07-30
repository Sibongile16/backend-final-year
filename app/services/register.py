from datetime import date, datetime
from typing import List, Dict, Optional
from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status as httpStatus

from app.models.all_models import (
    AttendanceStatus, 
    DailyAttendance, 
    Student, 
    StudentStatus
)

class AttendanceService:
    """Service class for attendance operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def mark_student_attendance(self, student_id: str, attendance_date: date, 
                              status: AttendanceStatus, notes: str = None, 
                              teacher_id: str = None) -> DailyAttendance:
        """Mark or update attendance for a student on a specific date"""
        
        # Check if attendance already exists for this student and date
        existing = self.db.query(DailyAttendance).filter(
            DailyAttendance.student_id == student_id,
            DailyAttendance.attendance_date == attendance_date
        ).first()
        
        if existing:
            # Update existing record
            existing.status = status
            existing.notes = notes
            existing.marked_by_teacher_id = teacher_id
            existing.updated_at = datetime.now(timezone("Africa/Blantyre"))
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Get student's class
            student = self.db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise HTTPException(
                    status_code=httpStatus.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )
            
            # Create new attendance record
            attendance = DailyAttendance(
                student_id=student_id,
                class_id=student.class_id,
                attendance_date=attendance_date,
                status=status,
                notes=notes,
                marked_by_teacher_id=teacher_id
            )
            
            self.db.add(attendance)
            self.db.commit()
            self.db.refresh(attendance)
            return attendance
    
    def mark_class_attendance(self, class_id: str, attendance_date: date, 
                            attendance_data: List[Dict], teacher_id: str = None) -> List[DailyAttendance]:
        """Mark attendance for multiple students in a class"""
        records = []
        
        for data in attendance_data:
            try:
                # Convert string status to enum if needed
                status = data['status']
                if isinstance(status, str):
                    status = AttendanceStatus[status.upper()]
                
                record = self.mark_student_attendance(
                    student_id=data['student_id'],
                    attendance_date=attendance_date,
                    status=status,
                    notes=data.get('notes'),
                    teacher_id=teacher_id
                )
                records.append(record)
            except HTTPException as e:
                # Skip failed records but continue with others
                continue
            except KeyError:
                raise HTTPException(
                    status_code=httpStatus.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid attendance status: {data['status']}"
                )
        
        return records
    
    def get_class_attendance_for_date(self, class_id: str, attendance_date: date) -> Dict:
        """Get attendance for all students in a class for a specific date"""
        # Get all active students in the class
        students = self.db.query(Student).filter(
            Student.class_id == class_id,
            Student.status == StudentStatus.ACTIVE
        ).all()
        
        if not students:
            raise HTTPException(
                status_code=httpStatus.HTTP_404_NOT_FOUND,
                detail="No active students found in this class"
            )
        
        # Get attendance records for this date
        attendance_records = self.db.query(DailyAttendance).filter(
            DailyAttendance.class_id == class_id,
            DailyAttendance.attendance_date == attendance_date
        ).all()
        
        # Create a map of student_id to attendance record
        attendance_map = {str(record.student_id): record for record in attendance_records}
        
        # Build the result
        student_attendance = []
        present_count = 0
        absent_count = 0
        late_count = 0
        
        for student in students:
            attendance_record = attendance_map.get(str(student.id))
            if attendance_record:
                status = attendance_record.status
                notes = attendance_record.notes
            else:
                status = AttendanceStatus.ABSENT  # Default to absent if not marked
                notes = None
            
            student_attendance.append({
                'student_id': str(student.id),
                'student_name': f"{student.first_name} {student.last_name}",
                'student_number': student.student_id,
                'status': status.value.lower(),  # Return lowercase for consistency
                'notes': notes
            })
            
            # Count totals
            if status == AttendanceStatus.PRESENT:
                present_count += 1
            elif status == AttendanceStatus.ABSENT:
                absent_count += 1
            elif status == AttendanceStatus.LATE:
                late_count += 1
        
        total_students = len(students)
        attendance_percentage = (present_count + late_count) / total_students * 100 if total_students > 0 else 0
        
        return {
            'class_id': class_id,
            'date': attendance_date.isoformat(),
            'total_students': total_students,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'attendance_percentage': round(attendance_percentage, 1),
            'student_attendance': student_attendance
        }
    
    def get_student_attendance_history(self, student_id: str, 
                                     start_date: date = None, 
                                     end_date: date = None) -> List[Dict]:
        """Get attendance history for a specific student"""
        # Check if student exists
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=httpStatus.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        query = self.db.query(DailyAttendance).filter(
            DailyAttendance.student_id == student_id
        )
        
        if start_date:
            query = query.filter(DailyAttendance.attendance_date >= start_date)
        if end_date:
            query = query.filter(DailyAttendance.attendance_date <= end_date)
        
        records = query.order_by(DailyAttendance.attendance_date.desc()).all()
        
        history = []
        for record in records:
            history.append({
                'date': record.attendance_date.isoformat(),
                'status': record.status.value.lower(),  # Return lowercase for consistency
                'notes': record.notes
            })
        
        return history
    
    def get_attendance_summary(self, student_id: str, start_date: date, end_date: date) -> Dict:
        """Get simple attendance summary for a student"""
        # Check if student exists
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=httpStatus.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        records = self.db.query(DailyAttendance).filter(
            DailyAttendance.student_id == student_id,
            DailyAttendance.attendance_date >= start_date,
            DailyAttendance.attendance_date <= end_date
        ).all()
        
        total_days = len(records)
        present_days = len([r for r in records if r.status == AttendanceStatus.PRESENT])
        late_days = len([r for r in records if r.status == AttendanceStatus.LATE])
        absent_days = len([r for r in records if r.status == AttendanceStatus.ABSENT])
        
        # Count present + late as attended
        attended_days = present_days + late_days
        attendance_percentage = (attended_days / total_days * 100) if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': absent_days,
            'attendance_percentage': round(attendance_percentage, 1)
        }
    
    def get_class_attendance_summary(self, class_id: str, start_date: date, end_date: date) -> Dict:
        """Get attendance summary for entire class over a date range"""
        records = self.db.query(DailyAttendance).filter(
            DailyAttendance.class_id == class_id,
            DailyAttendance.attendance_date >= start_date,
            DailyAttendance.attendance_date <= end_date
        ).all()
        
        # Group by student
        student_data = {}
        for record in records:
            student_id = str(record.student_id)
            if student_id not in student_data:
                student_data[student_id] = {
                    'total': 0, 'present': 0, 'late': 0, 'absent': 0
                }
            
            student_data[student_id]['total'] += 1
            if record.status == AttendanceStatus.PRESENT:
                student_data[student_id]['present'] += 1
            elif record.status == AttendanceStatus.LATE:
                student_data[student_id]['late'] += 1
            else:
                student_data[student_id]['absent'] += 1
        
        # Calculate class averages
        total_records = len(records)
        total_present = len([r for r in records if r.status == AttendanceStatus.PRESENT])
        total_late = len([r for r in records if r.status == AttendanceStatus.LATE])
        total_absent = len([r for r in records if r.status == AttendanceStatus.ABSENT])
        
        class_attendance_rate = ((total_present + total_late) / total_records * 100) if total_records > 0 else 0
        
        return {
            'class_id': class_id,
            'date_range': f"{start_date.isoformat()} to {end_date.isoformat()}",
            'total_records': total_records,
            'present_total': total_present,
            'late_total': total_late,
            'absent_total': total_absent,
            'class_attendance_percentage': round(class_attendance_rate, 1),
            'unique_students': len(student_data)
        }