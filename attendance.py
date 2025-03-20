import datetime
import json
import os
from typing import Dict, List, Optional

class AttendanceSystem:
    """
    A system for managing daily attendance records with data persistence.
    """
    
    def __init__(self, data_file: str = "attendance_records.json"):
        """
        Initialize the attendance system with the specified data file.
        
        Args:
            data_file: Path to the JSON file for storing attendance data
        """
        self.data_file = data_file
        self.attendance_records = self._load_records()
        
    def _load_records(self) -> Dict:
        """Load attendance records from the data file or create a new structure."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print(f"Error reading {self.data_file}, creating new records.")
                return {"students": {}, "daily_records": {}}
        else:
            return {"students": {}, "daily_records": {}}
    
    def _save_records(self) -> None:
        """Save the current attendance records to the data file."""
        with open(self.data_file, 'w') as file:
            json.dump(self.attendance_records, file, indent=2)
    
    def add_student(self, student_id: str, name: str) -> None:
        """
        Add a new student to the system.
        
        Args:
            student_id: Unique identifier for the student
            name: Full name of the student
        """
        if student_id not in self.attendance_records["students"]:
            self.attendance_records["students"][student_id] = {
                "name": name,
                "registration_date": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            print(f"Added student: {name} (ID: {student_id})")
            self._save_records()
        else:
            print(f"Student ID {student_id} already exists.")
    
    def mark_attendance(self, student_id: str, date: Optional[str] = None, 
                        status: str = "present", notes: str = "") -> None:
        """
        Mark a student's attendance for a specific date.
        
        Args:
            student_id: The student's unique identifier
            date: Date string in YYYY-MM-DD format (defaults to today)
            status: Attendance status ('present', 'absent', 'late', 'excused')
            notes: Optional notes about the attendance record
        """
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            
        # Validate student exists
        if student_id not in self.attendance_records["students"]:
            print(f"Error: Student ID {student_id} not found.")
            return
            
        # Ensure the date entry exists
        if date not in self.attendance_records["daily_records"]:
            self.attendance_records["daily_records"][date] = {}
            
        # Update the record
        self.attendance_records["daily_records"][date][student_id] = {
            "status": status,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes
        }
        
        print(f"Marked {status} for {self.attendance_records['students'][student_id]['name']} on {date}")
        self._save_records()
    
    def bulk_attendance(self, date: Optional[str] = None, 
                         status_dict: Dict[str, str] = None) -> None:
        """
        Mark attendance for multiple students at once.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            status_dict: Dictionary mapping student IDs to their status
        """
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            
        if status_dict:
            for student_id, status in status_dict.items():
                self.mark_attendance(student_id, date, status)
        else:
            print("No attendance data provided.")
    
    def get_attendance_report(self, date: Optional[str] = None) -> Dict:
        """
        Generate an attendance report for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with attendance statistics
        """
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            
        if date not in self.attendance_records["daily_records"]:
            return {"date": date, "message": "No records for this date", "stats": {}}
            
        records = self.attendance_records["daily_records"][date]
        total_students = len(self.attendance_records["students"])
        recorded_students = len(records)
        
        status_counts = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        for student_id, data in records.items():
            if data["status"] in status_counts:
                status_counts[data["status"]] += 1
        
        return {
            "date": date,
            "total_students": total_students,
            "recorded_students": recorded_students,
            "missing_records": total_students - recorded_students,
            "stats": status_counts,
            "attendance_rate": round((status_counts["present"] / total_students * 100), 2) if total_students > 0 else 0
        }
    
    def get_student_attendance_history(self, student_id: str) -> Dict:
        """
        Get the complete attendance history for a specific student.
        
        Args:
            student_id: The student's unique identifier
            
        Returns:
            Dictionary with the student's attendance history
        """
        if student_id not in self.attendance_records["students"]:
            return {"error": f"Student ID {student_id} not found."}
            
        history = {}
        for date, records in self.attendance_records["daily_records"].items():
            if student_id in records:
                history[date] = records[student_id]
                
        return {
            "student_id": student_id,
            "name": self.attendance_records["students"][student_id]["name"],
            "history": history
        }


# Example usage
if __name__ == "__main__":
    # Initialize the system
    attendance = AttendanceSystem()
    
    # Add some students
    attendance.add_student("S001", "John Smith")
    attendance.add_student("S002", "Emma Johnson")
    attendance.add_student("S003", "Michael Brown")
    
    # Mark today's attendance
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    attendance.mark_attendance("S001", today, "present")
    attendance.mark_attendance("S002", today, "absent", "Called in sick")
    attendance.mark_attendance("S003", today, "late", "Bus delay")
    
    # Generate a report for today
    report = attendance.get_attendance_report(today)
    print(f"\nAttendance Report for {report['date']}:")
    print(f"Total students: {report['total_students']}")
    print(f"Records: {report['recorded_students']}")
    print(f"Missing: {report['missing_records']}")
    print(f"Attendance rate: {report['attendance_rate']}%")
    print("Status breakdown:", report['stats'])
    
    # Get history for a specific student
    history = attendance.get_student_attendance_history("S001")
    print(f"\nAttendance history for {history['name']}:")
    for date, record in history['history'].items():
        print(f"  {date}: {record['status']} - {record['notes']}")