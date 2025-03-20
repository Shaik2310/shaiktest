import datetime
import json
import os
from typing import Dict, List, Optional, Union


class AttendanceSystem:
    """
    A system for managing daily attendance records with multiple JSON files for data persistence.
    """
    
    def __init__(self, data_directory: str = "attendance_data"):
        """
        Initialize the attendance system with the specified data directory.
        
        Args:
            data_directory: Directory to store JSON files for attendance data
        """
        self.data_directory = data_directory
        self.students_file = os.path.join(data_directory, "students.json")
        self.attendance_file = os.path.join(data_directory, "attendance_records.json")
        self.reports_file = os.path.join(data_directory, "attendance_reports.json")
        self.config_file = os.path.join(data_directory, "system_config.json")
        
        # Ensure the data directory exists
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
        
        # Load all data files
        self.students = self._load_json_file(self.students_file, default={})
        self.attendance_records = self._load_json_file(self.attendance_file, default={})
        self.reports = self._load_json_file(self.reports_file, default={})
        self.config = self._load_json_file(self.config_file, default={
            "status_options": ["present", "absent", "late", "excused"],
            "default_status": "absent",
            "auto_backup": True,
            "backup_frequency_days": 7,
            "last_backup": None
        })
        
        # Perform auto backup check if enabled
        if self.config.get("auto_backup", True):
            self._check_auto_backup()
    
    def _load_json_file(self, file_path: str, default: Dict = None) -> Dict:
        """Load data from a JSON file or return default value if file doesn't exist."""
        if default is None:
            default = {}
            
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print(f"Error reading {file_path}, creating new file.")
                return default
        else:
            return default
    
    def _save_json_file(self, file_path: str, data: Dict) -> None:
        """Save data to a JSON file with formatting."""
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
    
    def _check_auto_backup(self) -> None:
        """Check if backup is needed and perform it if necessary."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        last_backup = self.config.get("last_backup")
        
        if not last_backup:
            self._create_backup(today)
            return
            
        # Calculate days since last backup
        last_date = datetime.datetime.strptime(last_backup, "%Y-%m-%d")
        current_date = datetime.datetime.strptime(today, "%Y-%m-%d")
        days_diff = (current_date - last_date).days
        
        if days_diff >= self.config.get("backup_frequency_days", 7):
            self._create_backup(today)
    
    def _create_backup(self, date_str: str) -> None:
        """Create backup of all JSON data files."""
        backup_dir = os.path.join(self.data_directory, "backups", date_str)
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Backup all data files
        for file_name, data in [
            ("students.json", self.students),
            ("attendance_records.json", self.attendance_records),
            ("attendance_reports.json", self.reports),
            ("system_config.json", self.config)
        ]:
            backup_path = os.path.join(backup_dir, file_name)
            with open(backup_path, 'w') as file:
                json.dump(data, file, indent=2)
                
        # Update last backup date
        self.config["last_backup"] = date_str
        self._save_json_file(self.config_file, self.config)
        print(f"Created backup in {backup_dir}")
    
    def add_student(self, student_id: str, name: str, additional_info: Dict = None) -> bool:
        """
        Add a new student to the system.
        
        Args:
            student_id: Unique identifier for the student
            name: Full name of the student
            additional_info: Optional dictionary of additional student information
            
        Returns:
            Boolean indicating success
        """
        if student_id in self.students:
            print(f"Student ID {student_id} already exists.")
            return False
            
        # Create student record
        student_data = {
            "name": name,
            "registration_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "status": "active"
        }
        
        # Add any additional information
        if additional_info:
            student_data.update(additional_info)
            
        # Add to students dictionary and save
        self.students[student_id] = student_data
        self._save_json_file(self.students_file, self.students)
        print(f"Added student: {name} (ID: {student_id})")
        return True
    
    def update_student_info(self, student_id: str, update_data: Dict) -> bool:
        """
        Update information for an existing student.
        
        Args:
            student_id: The student's unique identifier
            update_data: Dictionary of fields to update
            
        Returns:
            Boolean indicating success
        """
        if student_id not in self.students:
            print(f"Student ID {student_id} not found.")
            return False
            
        # Update fields
        for key, value in update_data.items():
            self.students[student_id][key] = value
            
        # Save changes
        self._save_json_file(self.students_file, self.students)
        print(f"Updated student information for ID: {student_id}")
        return True
    
    def get_attendance_date_key(self, date: Optional[str] = None) -> str:
        """Generate a consistent date key for attendance records."""
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        return date
    
    def mark_attendance(self, student_id: str, date: Optional[str] = None, 
                        status: str = "present", notes: str = "") -> bool:
        """
        Mark a student's attendance for a specific date.
        
        Args:
            student_id: The student's unique identifier
            date: Date string in YYYY-MM-DD format (defaults to today)
            status: Attendance status ('present', 'absent', 'late', 'excused')
            notes: Optional notes about the attendance record
            
        Returns:
            Boolean indicating success
        """
        date_key = self.get_attendance_date_key(date)
            
        # Validate student exists
        if student_id not in self.students:
            print(f"Error: Student ID {student_id} not found.")
            return False
        
        # Validate status is allowed
        valid_statuses = self.config.get("status_options", ["present", "absent", "late", "excused"])
        if status not in valid_statuses:
            print(f"Error: Invalid status. Must be one of {valid_statuses}")
            return False
            
        # Ensure the date entry exists
        if date_key not in self.attendance_records:
            self.attendance_records[date_key] = {}
            
        # Update the record
        self.attendance_records[date_key][student_id] = {
            "status": status,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": notes
        }
        
        # Save changes
        self._save_json_file(self.attendance_file, self.attendance_records)
        print(f"Marked {status} for {self.students[student_id]['name']} on {date_key}")
        return True
    
    def bulk_attendance(self, date: Optional[str] = None, 
                        status_dict: Dict[str, Union[str, Dict]] = None) -> Dict:
        """
        Mark attendance for multiple students at once.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            status_dict: Dictionary mapping student IDs to status or {status, notes} dict
            
        Returns:
            Dictionary with results summary
        """
        date_key = self.get_attendance_date_key(date)
        results = {"success": [], "failed": []}
            
        if not status_dict:
            print("No attendance data provided.")
            return results
            
        for student_id, data in status_dict.items():
            # Handle both simple string status and dict with status and notes
            if isinstance(data, str):
                status = data
                notes = ""
            elif isinstance(data, dict):
                status = data.get("status", "present")
                notes = data.get("notes", "")
            else:
                print(f"Invalid data format for student {student_id}")
                results["failed"].append(student_id)
                continue
                
            # Mark attendance
            success = self.mark_attendance(student_id, date_key, status, notes)
            if success:
                results["success"].append(student_id)
            else:
                results["failed"].append(student_id)
                
        # Generate a daily report after bulk update
        self._generate_daily_report(date_key)
        return results
    
    def _generate_daily_report(self, date_key: str) -> Dict:
        """Generate and save a report for the given date."""
        if date_key not in self.attendance_records:
            report = {
                "date": date_key,
                "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": "No records for this date",
                "stats": {}
            }
        else:
            records = self.attendance_records[date_key]
            total_students = len(self.students)
            recorded_students = len(records)
            
            # Count each status
            status_counts = {}
            for status in self.config.get("status_options", ["present", "absent", "late", "excused"]):
                status_counts[status] = 0
                
            for student_id, data in records.items():
                if data["status"] in status_counts:
                    status_counts[data["status"]] += 1
            
            # Calculate metrics
            attendance_rate = 0
            if total_students > 0:
                present_count = status_counts.get("present", 0)
                attendance_rate = round((present_count / total_students * 100), 2)
            
            report = {
                "date": date_key,
                "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_students": total_students,
                "recorded_students": recorded_students,
                "missing_records": total_students - recorded_students,
                "stats": status_counts,
                "attendance_rate": attendance_rate
            }
        
        # Save the report
        self.reports[date_key] = report
        self._save_json_file(self.reports_file, self.reports)
        return report
    
    def get_attendance_report(self, date: Optional[str] = None) -> Dict:
        """
        Get an attendance report for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with attendance statistics
        """
        date_key = self.get_attendance_date_key(date)
        
        # Check if we already have a generated report
        if date_key in self.reports:
            return self.reports[date_key]
            
        # Generate a new report
        return self._generate_daily_report(date_key)
    
    def get_student_attendance_history(self, student_id: str, 
                                       start_date: Optional[str] = None,
                                       end_date: Optional[str] = None) -> Dict:
        """
        Get the attendance history for a specific student within a date range.
        
        Args:
            student_id: The student's unique identifier
            start_date: Optional start date for the history (YYYY-MM-DD)
            end_date: Optional end date for the history (YYYY-MM-DD)
            
        Returns:
            Dictionary with the student's attendance history
        """
        if student_id not in self.students:
            return {"error": f"Student ID {student_id} not found."}
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # Default to 30 days before end date
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - datetime.timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")
            
        # Convert to datetime objects for comparison
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
        history = {}
        for date_key, records in self.attendance_records.items():
            # Skip dates outside range
            try:
                date_dt = datetime.datetime.strptime(date_key, "%Y-%m-%d")
                if date_dt < start_dt or date_dt > end_dt:
                    continue
            except ValueError:
                # Skip if date format is invalid
                continue
                
            if student_id in records:
                history[date_key] = records[student_id]
                
        # Calculate statistics
        total_days = len(history)
        status_counts = {}
        for status in self.config.get("status_options", ["present", "absent", "late", "excused"]):
            status_counts[status] = 0
            
        for date_key, record in history.items():
            if record["status"] in status_counts:
                status_counts[record["status"]] += 1
                
        # Calculate attendance rate
        attendance_rate = 0
        if total_days > 0:
            attendance_rate = round((status_counts.get("present", 0) / total_days * 100), 2)
                
        return {
            "student_id": student_id,
            "name": self.students[student_id]["name"],
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "stats": status_counts,
            "attendance_rate": attendance_rate,
            "history": history
        }
    
    def export_monthly_report(self, year: int, month: int, 
                             format_type: str = "json") -> str:
        """
        Export a monthly attendance report to a separate file.
        
        Args:
            year: Year as integer (e.g., 2025)
            month: Month as integer (1-12)
            format_type: Export format ('json' or 'csv')
            
        Returns:
            Path to the exported file
        """
        # Create year-month string
        month_str = f"{year}-{month:02d}"
        
        # Filter attendance records for the month
        monthly_data = {}
        monthly_students = {}
        
        for date_key, records in self.attendance_records.items():
            if date_key.startswith(month_str):
                monthly_data[date_key] = records
                
                # Track students with records this month
                for student_id in records:
                    monthly_students[student_id] = self.students.get(student_id, {"name": "Unknown"})
        
        # Prepare export data
        export_data = {
            "period": month_str,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "students": monthly_students,
            "attendance": monthly_data
        }
        
        # Create export directory if needed
        export_dir = os.path.join(self.data_directory, "exports")
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            
        # Export based on format
        if format_type.lower() == "json":
            export_path = os.path.join(export_dir, f"attendance_{month_str}.json")
            with open(export_path, 'w') as file:
                json.dump(export_data, file, indent=2)
        elif format_type.lower() == "csv":
            export_path = os.path.join(export_dir, f"attendance_{month_str}.csv")
            
            # Get all unique dates in the month
            all_dates = sorted(list(monthly_data.keys()))
            
            # Create CSV content
            import csv
            with open(export_path, 'w', newline='') as file:
                writer = csv.writer(file)
                
                # Write header row
                header = ["Student ID", "Name"] + all_dates
                writer.writerow(header)
                
                # Write data for each student
                for student_id, student_info in monthly_students.items():
                    row = [student_id, student_info.get("name", "Unknown")]
                    
                    # Add status for each date
                    for date in all_dates:
                        if date in monthly_data and student_id in monthly_data[date]:
                            row.append(monthly_data[date][student_id]["status"])
                        else:
                            row.append("N/A")
                            
                    writer.writerow(row)
        else:
            return f"Unsupported format: {format_type}"
            
        print(f"Exported {month_str} attendance to {export_path}")
        return export_path
    
    def update_system_config(self, config_updates: Dict) -> bool:
        """
        Update system configuration parameters.
        
        Args:
            config_updates: Dictionary of configuration parameters to update
            
        Returns:
            Boolean indicating success
        """
        for key, value in config_updates.items():
            self.config[key] = value
            
        self._save_json_file(self.config_file, self.config)
        print("Updated system configuration")
        return True


# Example usage
if __name__ == "__main__":
    # Initialize the system
    attendance = AttendanceSystem()
    
    # Add some students with additional information
    attendance.add_student("S001", "John Smith", {
        "grade": "10A",
        "contact": "john.smith@email.com",
        "parent_name": "David Smith",
        "parent_contact": "david.smith@email.com"
    })
    
    attendance.add_student("S002", "Emma Johnson", {
        "grade": "10A",
        "contact": "emma.j@email.com",
        "parent_name": "Laura Johnson",
        "parent_contact": "laura.j@email.com"
    })
    
    attendance.add_student("S003", "Michael Brown", {
        "grade": "10B",
        "contact": "michael.b@email.com",
        "parent_name": "Robert Brown",
        "parent_contact": "robert.b@email.com"
    })
    
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
    
    # Export monthly report
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    attendance.export_monthly_report(current_year, current_month)