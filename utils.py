#!/usr/bin/env python3
"""
Utility Functions
Common utility functions used across the defragmentation system
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import os
import logging

def safe_surname(surname_value, status=None) -> str:
    """Safely handle surname values, including NaN, with special handling for maintenance and pencil"""
    if pd.isna(surname_value) or surname_value is None:
        # Special handling for maintenance and pencil reservations
        if status == 'Maintenance':
            return "Maint"
        elif status == 'Pencil':
            return "Pencil"
        else:
            return "Unknown"
    
    surname_str = str(surname_value)
    return surname_str[:8] if len(surname_str) > 8 else surname_str

def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parse date string in format 'DD/MM/YYYY HH:MM' or 'DD/MM/YYYY'"""
    try:
        return datetime.strptime(date_str.split()[0], '%d/%m/%Y').date()
    except:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
            print(f"Warning: Could not parse date: {date_str}")
            return None

def is_reservation_fixed(reservation_row) -> bool:
    """Check if a reservation is marked as fixed (cannot be moved)"""
    # Handle both string and boolean representations
    if 'Fixed' in reservation_row:
        fixed_value = reservation_row['Fixed']
        if isinstance(fixed_value, bool):
            return fixed_value
        elif isinstance(fixed_value, str):
            return fixed_value.lower() in ['true', '1', 'yes']
    return False

def get_date_range(start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
    """Generate list of dates between start and end (inclusive of start, exclusive of end)"""
    if not start_date or not end_date:
        return []
    
    dates = []
    current = start_date
    while current < end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates

def format_date_for_display(date_obj: datetime.date) -> str:
    """Format date object for display in DD/MM/YYYY format"""
    if not date_obj:
        return ""
    return date_obj.strftime('%d/%m/%Y')

def format_datetime_for_display(datetime_obj: datetime) -> str:
    """Format datetime object for display in DD/MM/YYYY HH:MM format"""
    if not datetime_obj:
        return ""
    return datetime_obj.strftime('%d/%m/%Y %H:%M')

def calculate_nights_between_dates(start_date: datetime.date, end_date: datetime.date) -> int:
    """Calculate number of nights between two dates"""
    if not start_date or not end_date:
        return 0
    
    nights = (end_date - start_date).days
    return max(0, nights)  # Ensure non-negative

def validate_date_range(start_date: datetime.date, end_date: datetime.date) -> bool:
    """Validate that start date is before end date"""
    if not start_date or not end_date:
        return False
    return start_date < end_date

def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string to maximum length with ellipsis"""
    if not text:
        return ""
    
    text_str = str(text)
    if len(text_str) <= max_length:
        return text_str
    
    return text_str[:max_length-3] + "..."

def format_currency(amount: float, currency_symbol: str = "$") -> str:
    """Format amount as currency"""
    if pd.isna(amount):
        return f"{currency_symbol}0.00"
    return f"{currency_symbol}{amount:,.2f}"

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format value as percentage"""
    if pd.isna(value):
        return "0.0%"
    return f"{value:.{decimal_places}f}%"

def clean_text_for_excel(text: str) -> str:
    """Clean text for safe Excel output"""
    if not text:
        return ""
    
    # Remove any characters that might cause Excel issues
    cleaned = str(text).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Remove excessive whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned

def generate_unique_filename(base_name: str, extension: str = "xlsx", 
                           include_timestamp: bool = True) -> str:
    """Generate unique filename with optional timestamp"""
    if include_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{extension}"
    else:
        return f"{base_name}.{extension}"

def log_message(message: str, level: str = "INFO") -> None:
    """Simple logging function"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validate that DataFrame contains required columns"""
    if df.empty:
        return False
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Warning: Missing required columns: {missing_columns}")
        return False
    
    return True

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero"""
    if denominator == 0:
        return default
    return numerator / denominator

def convert_to_int(value, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def convert_to_float(value, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def get_business_days_between(start_date: datetime.date, end_date: datetime.date) -> int:
    """Calculate number of business days between two dates"""
    if not start_date or not end_date or start_date >= end_date:
        return 0
    
    business_days = 0
    current_date = start_date
    
    while current_date < end_date:
        # Monday = 0, Sunday = 6
        if current_date.weekday() < 5:  # Monday to Friday
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"

def create_summary_stats(data_list: List[float]) -> dict:
    """Create summary statistics for a list of numbers"""
    if not data_list:
        return {
            'count': 0,
            'sum': 0,
            'mean': 0,
            'min': 0,
            'max': 0,
            'median': 0
        }
    
    return {
        'count': len(data_list),
        'sum': sum(data_list),
        'mean': sum(data_list) / len(data_list),
        'min': min(data_list),
        'max': max(data_list),
        'median': sorted(data_list)[len(data_list) // 2]
    }

class Logger:
    """Centralized logging utility for the defragmentation analyzer"""
    
    def __init__(self, log_file: str = None):
        """
        Initialize the logger
        
        Args:
            log_file: Path to the log file (default: auto-detect based on environment)
        """
        if log_file is None:
            # Auto-detect log file path based on environment
            if os.path.exists("/var/log/bookingchart-defragmenter"):
                # Linux server environment
                self.log_file = "/var/log/bookingchart-defragmenter/defrag_analyzer.log"
            else:
                # Development environment
                self.log_file = "defrag_analyzer.log"
        else:
            self.log_file = log_file
            
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup the logging configuration"""
        # Create logger
        self.logger = logging.getLogger('DefragAnalyzer')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, mode=0o755, exist_ok=True)
            except PermissionError:
                # Fallback to current directory if no permission
                self.log_file = "defrag_analyzer.log"
        
        # Create file handler (append mode)
        try:
            file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # Fallback to current directory if no permission
            fallback_log = "defrag_analyzer.log"
            print(f"Warning: Could not write to {self.log_file}: {e}")
            print(f"Falling back to: {fallback_log}")
            self.log_file = fallback_log
            file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Log session start
        self.info("=" * 80)
        self.info("NEW SESSION STARTED")
        self.info(f"Log file: {self.log_file}")
        self.info("=" * 80)
    
    def debug(self, message: str):
        """Log debug message"""
        if self.logger:
            self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        if self.logger:
            self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        if self.logger:
            self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        if self.logger:
            self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        if self.logger:
            self.logger.critical(message)
    
    def log_function_entry(self, function_name: str, **kwargs):
        """Log function entry with parameters"""
        params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.debug(f"ENTERING: {function_name}({params})")
    
    def log_function_exit(self, function_name: str, result=None):
        """Log function exit with result"""
        if result is not None:
            self.debug(f"EXITING: {function_name} -> {result}")
        else:
            self.debug(f"EXITING: {function_name}")
    
    def log_api_call(self, endpoint: str, method: str = "GET", status: Optional[str] = None, response_size: Optional[int] = None):
        """Log API call details"""
        status_info = f" - Status: {status}" if status else ""
        size_info = f" - Response size: {response_size}" if response_size else ""
        self.info(f"API CALL: {method} {endpoint}{status_info}{size_info}")
    
    def log_property_analysis_start(self, property_code: str, property_id: int, property_name: str):
        """Log start of property analysis"""
        self.info(f"PROPERTY ANALYSIS START: {property_code} (ID: {property_id}, Name: {property_name})")
    
    def log_property_analysis_complete(self, property_code: str, suggestions_count: int, excel_file: str):
        """Log completion of property analysis"""
        self.info(f"PROPERTY ANALYSIS COMPLETE: {property_code} - {suggestions_count} suggestions - Excel: {excel_file}")
    
    def log_error_with_context(self, error: Exception, context: str):
        """Log error with context information"""
        self.error(f"ERROR in {context}: {type(error).__name__}: {str(error)}")
    
    def log_performance_metric(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics"""
        details_info = f" - {details}" if details else ""
        self.info(f"PERFORMANCE: {operation} took {duration:.2f}s{details_info}")
    
    def log_data_summary(self, data_type: str, count: int, details: str = ""):
        """Log data summary information"""
        details_info = f" - {details}" if details else ""
        self.info(f"DATA SUMMARY: {data_type}: {count}{details_info}")
    
    def log_cache_operation(self, operation: str, cache_type: str, key: str, hit: bool = True):
        """Log cache operations"""
        status = "HIT" if hit else "MISS"
        self.debug(f"CACHE {status}: {operation} {cache_type} - {key}")
    
    def log_move_analysis(self, category: str, moves_found: int, rejected_count: int, skipped: bool = False):
        """Log move analysis results for a category"""
        if skipped:
            self.info(f"MOVE ANALYSIS: {category} - SKIPPED (sufficient availability)")
        else:
            self.info(f"MOVE ANALYSIS: {category} - {moves_found} moves found, {rejected_count} rejected")
    
    def log_excel_generation(self, filename: str, sheets: list):
        """Log Excel file generation"""
        sheets_info = ", ".join(sheets)
        self.info(f"EXCEL GENERATED: {filename} - Sheets: {sheets_info}")
    
    def log_email_operation(self, operation: str, recipient: str, success: bool, details: str = ""):
        """Log email operations"""
        status = "SUCCESS" if success else "FAILED"
        details_info = f" - {details}" if details else ""
        self.info(f"EMAIL {status}: {operation} to {recipient}{details_info}")

# Global logger instance
_logger_instance = None

def get_logger() -> Logger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance

def setup_logging(log_file: str = None) -> Logger:
    """Setup logging with custom log file"""
    global _logger_instance
    _logger_instance = Logger(log_file)
    return _logger_instance