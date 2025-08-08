# Step 2: Holiday Integration Architecture Design
## Holiday-Aware Defragmentation Enhancement

**Date:** January 2025  
**Purpose:** Design the complete architecture for integrating holiday-aware defragmentation

---

## 🏗️ **Architecture Overview**

### **High-Level Design:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RMS Client    │    │  Holiday Client  │    │ Defrag Analyzer │
│                 │    │                  │    │                 │
│ • Properties    │    │ • Nager.Date API │    │ • Regular       │
│ • Reservations  │    │ • Holiday Data   │    │   Analysis      │
│ • Inventory     │    │ • State Mapping  │    │ • Holiday       │
└─────────────────┘    └──────────────────┘    │   Analysis      │
         │                       │              │ • Deduplication │
         └───────────────────────┼──────────────┘                 │
                                 │              ┌─────────────────┐
                                 └──────────────┤   Output Gen    │
                                                │                 │
                                                │ • Excel Report  │
                                                │ • Email Notify  │
                                                │ • Holiday Table │
                                                └─────────────────┘
```

---

## 🔧 **New Components Design**

### **1. Holiday Client (`holiday_client.py`)**

#### **Purpose:** 
- Fetch holiday data from Nager.Date API
- Manage holiday data caching
- Provide holiday-aware date range calculations

#### **Key Methods:**
```python
class HolidayClient:
    def __init__(self):
        self.base_url = "https://date.nager.at/api/v3"
        self.cache = {}
        self.cache_ttl = 86400  # 24 hours
        
    def get_holidays_for_state(self, state_code: str, year: int) -> List[Dict]:
        """Fetch holidays for a specific state and year"""
        
    def get_holiday_extended_dates(self, holiday_start: date, holiday_end: date, 
                                  extension_days: int = 7) -> Tuple[date, date]:
        """Calculate extended date range around holiday period"""
        
    def is_holiday_period(self, check_date: date, state_code: str) -> Optional[Dict]:
        """Check if a date falls within a holiday period"""
        
    def get_upcoming_holidays(self, state_code: str, days_ahead: int = 365) -> List[Dict]:
        """Get upcoming holidays within specified days"""
```

#### **API Integration:**
```python
# Nager.Date API endpoints
HOLIDAY_ENDPOINTS = {
    'public_holidays': '/PublicHolidays/{year}/{countryCode}',
    'available_countries': '/AvailableCountries',
    'country_info': '/CountryInfo/{countryCode}'
}

# Australian state to country mapping
STATE_COUNTRY_MAPPING = {
    'VIC': 'AU', 'TAS': 'AU', 'ACT': 'AU', 'NSW': 'AU',
    'QLD': 'AU', 'NT': 'AU', 'SA': 'AU', 'WA': 'AU'
}
```

### **2. Enhanced RMS Client (`rms_client.py`)**

#### **New Methods:**
```python
class RMSClient:
    def extract_state_code(self, property_data: Dict) -> Optional[str]:
        """Extract state code from property data"""
        
    def get_holiday_aware_date_range(self, property_state: str, 
                                   holiday_client: HolidayClient) -> Tuple[date, date]:
        """Calculate holiday-aware date range for property"""
        
    def fetch_property_with_state(self, property_id: int) -> Dict:
        """Fetch property data including state information"""
```

#### **State Code Extraction Strategy:**
```python
def extract_state_code(self, property_data: Dict) -> Optional[str]:
    """Extract state code from property data"""
    # Try multiple possible field names
    state_fields = ['state', 'stateCode', 'region', 'location', 'address']
    
    for field in state_fields:
        if field in property_data and property_data[field]:
            state_code = str(property_data[field]).upper()
            if state_code in STATE_COUNTRY_MAPPING:
                return state_code
    
    # Fallback: extract from property name or code
    property_name = property_data.get('name', '').upper()
    property_code = property_data.get('code', '').upper()
    
    # Look for state abbreviations in name/code
    for state_code in STATE_COUNTRY_MAPPING.keys():
        if state_code in property_name or state_code in property_code:
            return state_code
    
    return None
```

### **3. Enhanced Defragmentation Analyzer (`defrag_analyzer.py`)**

#### **New Methods:**
```python
class DefragmentationAnalyzer:
    def analyze_holiday_defragmentation(self, reservations_df: pd.DataFrame, 
                                      inventory_df: pd.DataFrame,
                                      holiday_periods: List[Dict],
                                      constraint_start_date: date,
                                      constraint_end_date: date) -> List[Dict]:
        """Analyze defragmentation specifically for holiday periods"""
        
    def deduplicate_moves(self, regular_moves: List[Dict], 
                         holiday_moves: List[Dict]) -> List[Dict]:
        """Remove duplicate moves between regular and holiday analysis"""
        
    def merge_move_lists(self, regular_moves: List[Dict], 
                        holiday_moves: List[Dict]) -> List[Dict]:
        """Merge regular and holiday moves with proper ordering"""
        
    def calculate_holiday_importance_score(self, holiday_data: Dict) -> float:
        """Calculate importance score for holiday period"""
```

#### **Holiday Analysis Logic:**
```python
def analyze_holiday_defragmentation(self, reservations_df, inventory_df, 
                                  holiday_periods, constraint_start_date, constraint_end_date):
    """Analyze defragmentation for holiday periods"""
    holiday_moves = []
    
    for holiday_period in holiday_periods:
        # Calculate extended date range for this holiday
        holiday_start = holiday_period['start_date']
        holiday_end = holiday_period['end_date']
        extended_start = holiday_start - timedelta(days=7)
        extended_end = holiday_end + timedelta(days=7)
        
        # Filter reservations for this extended period
        holiday_reservations = self._filter_reservations_for_period(
            reservations_df, extended_start, extended_end
        )
        
        # Run defragmentation analysis for this period
        period_moves = self._suggest_moves(
            holiday_reservations, inventory_df, extended_start, extended_end
        )
        
        # Add holiday metadata to moves
        for move in period_moves:
            move.update({
                'holiday_period': holiday_period['name'],
                'holiday_type': holiday_period['type'],
                'holiday_importance': holiday_period['importance'],
                'move_id': f"H{len(holiday_moves) + 1}.{move.get('move_id', '1')}"
            })
        
        holiday_moves.extend(period_moves)
    
    return holiday_moves
```

### **4. Enhanced Excel Generator (`excel_generator.py`)**

#### **New Methods:**
```python
class ExcelGenerator:
    def _add_holiday_moves_sheet(self, workbook, holiday_moves: List[Dict]):
        """Add holiday moves to Excel workbook"""
        
    def _create_holiday_summary_sheet(self, workbook, holiday_data: Dict):
        """Create holiday summary sheet"""
        
    def _format_holiday_moves_table(self, worksheet, holiday_moves: List[Dict]):
        """Format holiday moves table with styling"""
```

#### **Holiday Sheet Structure:**
```python
def _add_holiday_moves_sheet(self, workbook, holiday_moves):
    """Add holiday moves sheet to Excel workbook"""
    if not holiday_moves:
        return
    
    # Create holiday moves worksheet
    ws = workbook.create_sheet("Holiday Move Suggestions")
    
    # Headers
    headers = [
        'Move ID', 'Property', 'From Unit', 'To Unit', 'From Date', 'To Date',
        'Guest Name', 'Improvement Score', 'Holiday Period', 'Holiday Type',
        'Holiday Importance', 'Reasoning'
    ]
    
    # Add headers
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # Add holiday moves data
    for row, move in enumerate(holiday_moves, 2):
        ws.cell(row=row, column=1, value=move.get('move_id', ''))
        ws.cell(row=row, column=2, value=move.get('property', ''))
        ws.cell(row=row, column=3, value=move.get('from_unit', ''))
        ws.cell(row=row, column=4, value=move.get('to_unit', ''))
        ws.cell(row=row, column=5, value=move.get('from_date', ''))
        ws.cell(row=row, column=6, value=move.get('to_date', ''))
        ws.cell(row=row, column=7, value=move.get('guest_name', ''))
        ws.cell(row=row, column=8, value=move.get('improvement_score', 0))
        ws.cell(row=row, column=9, value=move.get('holiday_period', ''))
        ws.cell(row=row, column=10, value=move.get('holiday_type', ''))
        ws.cell(row=row, column=11, value=move.get('holiday_importance', ''))
        ws.cell(row=row, column=12, value=move.get('reasoning', ''))
```

### **5. Enhanced Email Sender (`email_sender.py`)**

#### **New Methods:**
```python
class EmailSender:
    def _add_holiday_moves_to_email(self, email_content: str, 
                                   holiday_moves: List[Dict]) -> str:
        """Add holiday moves table to email content"""
        
    def _create_holiday_moves_html_table(self, holiday_moves: List[Dict]) -> str:
        """Create HTML table for holiday moves"""
        
    def _format_holiday_email_content(self, property_name: str, 
                                    regular_moves: List[Dict],
                                    holiday_moves: List[Dict]) -> str:
        """Format email content with both regular and holiday moves"""
```

---

## 🔄 **Enhanced Data Flow**

### **1. Property Discovery with State Codes**
```python
# Enhanced property discovery
properties = rms_client.get_all_properties()
for property in properties:
    state_code = rms_client.extract_state_code(property)
    property['state_code'] = state_code
```

### **2. Holiday Data Fetching**
```python
# Fetch holiday data for each property's state
holiday_client = HolidayClient()
holiday_data = {}

for property in properties:
    state_code = property.get('state_code')
    if state_code:
        holidays = holiday_client.get_upcoming_holidays(state_code, days_ahead=365)
        holiday_data[property['id']] = holidays
```

### **3. Holiday-Aware Date Range Calculation**
```python
# Calculate extended date ranges for properties with holidays
for property in properties:
    state_code = property.get('state_code')
    if state_code and holiday_data.get(property['id']):
        # Calculate holiday-aware date range
        start_date, end_date = rms_client.get_holiday_aware_date_range(
            state_code, holiday_client
        )
        property['holiday_start_date'] = start_date
        property['holiday_end_date'] = end_date
```

### **4. Dual Analysis Execution**
```python
# Run both regular and holiday analysis
regular_moves = defrag_analyzer.analyze_defragmentation(
    reservations_df, inventory_df, constraint_start_date, constraint_end_date
)

holiday_moves = defrag_analyzer.analyze_holiday_defragmentation(
    reservations_df, inventory_df, holiday_periods, 
    constraint_start_date, constraint_end_date
)

# Deduplicate and merge moves
all_moves = defrag_analyzer.deduplicate_moves(regular_moves, holiday_moves)
```

### **5. Enhanced Output Generation**
```python
# Generate Excel with holiday moves
excel_generator._add_holiday_moves_sheet(workbook, holiday_moves)

# Send email with holiday moves
email_content = email_sender._add_holiday_moves_to_email(
    email_content, holiday_moves
)
```

---

## 📊 **Data Structures**

### **Holiday Period Structure:**
```python
{
    'name': 'Australia Day 2025',
    'type': 'Public Holiday',
    'importance': 'High',
    'start_date': date(2025, 1, 26),
    'end_date': date(2025, 1, 26),
    'extended_start': date(2025, 1, 19),
    'extended_end': date(2025, 2, 2),
    'state_code': 'VIC',
    'country_code': 'AU'
}
```

### **Enhanced Move Structure:**
```python
{
    # Regular move fields
    'property': 'SADE',
    'move_id': 'H1.1',  # Holiday prefix
    'from_unit': 'Cabin 1',
    'to_unit': 'Cabin 2',
    'from_date': '2025-01-20',
    'to_date': '2025-01-25',
    'guest_name': 'John Doe',
    'improvement_score': 0.85,
    'reasoning': 'Creates 3-night contiguous availability',
    
    # Holiday-specific fields
    'holiday_period': 'Australia Day 2025',
    'holiday_type': 'Public Holiday',
    'holiday_importance': 'High',
    'is_holiday_move': True
}
```

---

## 🧪 **Testing Strategy**

### **1. Unit Tests**
```python
def test_holiday_client_api_integration():
    """Test Nager.Date API integration"""
    
def test_state_code_extraction():
    """Test state code extraction from property data"""
    
def test_holiday_date_range_calculation():
    """Test holiday-aware date range calculation"""
    
def test_move_deduplication():
    """Test move deduplication logic"""
```

### **2. Integration Tests**
```python
def test_end_to_end_holiday_analysis():
    """Test complete holiday-aware analysis flow"""
    
def test_holiday_output_generation():
    """Test holiday moves in Excel and email output"""
```

### **3. Performance Tests**
```python
def test_holiday_api_performance():
    """Test holiday API response times and caching"""
    
def test_extended_analysis_performance():
    """Test performance impact of extended date ranges"""
```

---

## 🔧 **Configuration Options**

### **New Environment Variables:**
```bash
# Holiday analysis configuration
ENABLE_HOLIDAY_ANALYSIS=true
HOLIDAY_EXTENSION_DAYS=7
HOLIDAY_CACHE_TTL=86400
HOLIDAY_API_TIMEOUT=30

# Holiday importance thresholds
HOLIDAY_IMPORTANCE_HIGH=0.8
HOLIDAY_IMPORTANCE_MEDIUM=0.5
HOLIDAY_IMPORTANCE_LOW=0.2
```

### **Configuration File Extensions:**
```python
# config.env additions
HOLIDAY_ANALYSIS_ENABLED=true
HOLIDAY_EXTENSION_DAYS=7
HOLIDAY_CACHE_DURATION=86400
HOLIDAY_API_BASE_URL=https://date.nager.at/api/v3
```

---

## 📈 **Success Criteria for Step 2**

### **✅ Architecture Design Complete:**
- [x] **Holiday Client design** - Complete API integration strategy
- [x] **Enhanced RMS Client** - State code extraction and date range calculation
- [x] **Enhanced Defragmentation Analyzer** - Holiday analysis and deduplication
- [x] **Enhanced Output Generation** - Excel and email holiday integration
- [x] **Data flow design** - Complete integration flow mapped

### **✅ Technical Specifications:**
- [x] **API integration strategy** - Nager.Date API with caching
- [x] **State code mapping** - Australian states to country codes
- [x] **Date range extension logic** - Holiday-aware calculations
- [x] **Move deduplication strategy** - Prevent duplicate moves
- [x] **Output enhancement design** - Excel and email integration

### **✅ Implementation Ready:**
- [x] **Component interfaces defined** - Clear method signatures
- [x] **Data structures designed** - Holiday and enhanced move structures
- [x] **Testing strategy planned** - Unit, integration, and performance tests
- [x] **Configuration options** - Environment variables and settings

---

## 🚀 **Ready for Step 3**

**Step 2 Architecture Design Complete** ✅

The holiday integration architecture is fully designed with:

1. **Clear component boundaries** - Each module has specific responsibilities
2. **Well-defined interfaces** - Method signatures and data structures
3. **Comprehensive data flow** - From holiday API to enhanced output
4. **Robust testing strategy** - Unit, integration, and performance tests
5. **Flexible configuration** - Environment variables for customization

**Next:** Proceed to **Step 3: Implement Holiday Client and API Integration**
