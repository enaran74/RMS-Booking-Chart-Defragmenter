# BookingChartDefragmenter

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A sophisticated Python application designed to optimize accommodation bookings across multiple properties by analyzing reservation patterns and suggesting strategic moves to maximize revenue potential. **Now enhanced with holiday-aware analysis for optimal booking optimization during peak holiday periods.**

## Table of Contents
- [Quick Start](#quick-start)
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Service Management](#service-management)
- [Deployment](#deployment)
- [Docker Deployment](#docker-deployment)
- [Contributing](#contributing)
- [License](#license)

**Developed by:** Mr Tim Curtis, Operations Systems Manager  
**Organization:** Discovery Holiday Parks  
**Date:** 2025

## Quick Start

### Prerequisites
- Python 3.8+
- RMS API access credentials

## Installation

### Option 1: Development Installation (Mac/Linux)

For development and testing on your local machine:

```bash
# Clone the repository
git clone https://github.com/your-username/BookingChartDefragmenter.git
cd BookingChartDefragmenter

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp env.example .env
# Edit .env with your RMS credentials
```

### Option 2: Production Installation (Linux Server)

For production deployment on Linux servers (Debian/Ubuntu):

```bash
# Clone the repository
git clone https://github.com/your-username/BookingChartDefragmenter.git
cd BookingChartDefragmenter

# Run the automated installation script
sudo chmod +x install.sh
sudo ./install.sh

# Configure the application
sudo nano /etc/bookingchart-defragmenter/config.env

# Start the service
sudo systemctl start bookingchart-defragmenter.service
sudo systemctl enable bookingchart-defragmenter.service
```

The installation script automatically:
- ✅ Creates service user (`defrag`)
- ✅ Sets up Python virtual environment
- ✅ Installs system dependencies
- ✅ Configures systemd service
- ✅ Sets up cron job (daily at 2:00 AM)
- ✅ Creates log directories and permissions
- ✅ Generates configuration template

### Option 3: Docker Deployment

For containerized deployment:

```bash
# Clone the repository
git clone https://github.com/your-username/BookingChartDefragmenter.git
cd BookingChartDefragmenter

# Prepare environment file
cp env.example .env
# Edit .env with your RMS credentials

# Build and run with Docker Compose
docker-compose up -d
```

### Basic Usage
```bash
# Analyze all properties
python3 start.py --agent-id YOUR_ID --agent-password "YOUR_PASS" --client-id YOUR_CLIENT_ID --client-password "YOUR_CLIENT_PASS" -p ALL

# Analyze specific properties
python3 start.py --agent-id YOUR_ID --agent-password "YOUR_PASS" --client-id YOUR_CLIENT_ID --client-password "YOUR_CLIENT_PASS" -p PROP1,PROP2
```

## Overview

The RMS Multi-Property Defragmentation Analyzer is a sophisticated Python application designed to optimize Discovery Holiday Parks' extensive network of holiday and caravan parks across Australia.

This system analyzes reservation patterns and suggests strategic reservation moves to maximize revenue potential across our diverse property portfolio. The system connects to RMS (Reservation Management System) APIs to fetch real-time data and generates comprehensive Excel reports with visual charts and actionable recommendations for our operations teams.

## Features

### Core Functionality
- **Flexible Property Selection**: Analyze specific properties, multiple properties, or all properties via command-line arguments
- **Real-Time Data Integration**: Connects to RMS API to fetch live inventory and reservation data with comprehensive caching
- **Defragmentation Analysis**: Identifies fragmented booking patterns and suggests optimal accommodation moves
- **🎄 Holiday-Aware Analysis**: Integrates holiday period data for state-specific optimization during peak periods
- **Revenue Optimization**: Helps maximize occupancy and revenue by consolidating available nights
- **Visual Reporting**: Generates detailed Excel workbooks with interactive charts and move suggestions
- **Optional Email Notifications**: Sends professional HTML emails with Excel attachments (configurable)
- **Endpoint Monitoring**: Comprehensive tracking of API usage and limits across all properties
- **Consolidated Analysis**: Creates summary Excel file with two sheets: daily move opportunities heatmap across all properties, and a comprehensive table of all suggested moves for potential ingestion into the Discovery Holiday Parks Data Lake.

### Service Management
- **Two-Tier Service Architecture**: Environment setup service + on-demand analysis execution
- **Automated Scheduling**: Daily analysis via cron job (2:00 AM)
- **Health Monitoring**: Comprehensive health checks and diagnostics
- **Easy Updates**: Automated update process with rollback capability
- **Public Repository**: No SSH keys required for updates

### Key Features

#### 🔍 **Intelligent Defragmentation Algorithm**
- Analyzes reservation patterns across all accommodation categories (cabins, sites, glamping, etc.)
- Identifies fragmented availability (scattered single nights)
- Suggests strategic moves to create longer contiguous availability blocks
- Considers fixed reservations (cannot be moved) and reservation status
- Uses sequential optimization to maximize overall property efficiency
- **Category-Based Move Ordering**: Moves numbered by category (1.1, 1.2, 2.1, 2.2, etc.)

#### 📊 **Comprehensive Data Analysis**
- Fetches live inventory data (accommodation units, sites, categories)
- Retrieves current reservations with status and guest information
- Analyzes 31-day forward-looking periods
- Filters by active categories and available units
- Handles multiple reservation statuses (Confirmed, Unconfirmed, Arrived, Maintenance, Pencil, etc.)
- **Active Data Filtering**: Only processes active properties, categories, and areas (excludes inactive items)

#### 🎯 **Smart Move Suggestions**
- Prioritizes moves by improvement score
- Considers the impact of sequential moves
- Excludes fixed reservations from suggestions
- **Excludes Maintenance and Pencil bookings** (cannot be moved)
- Provides detailed reasoning for each suggested move
- Orders suggestions for optimal implementation

#### 📧 **Email Notification System**
- **Optional Email Sending**: Controlled via `-e` command-line flag
- **Professional HTML Emails**: Branded with Discovery Parks styling
- **Excel Attachments**: Automatically attaches generated analysis files

## Service Management

### Management Commands (Linux Server)
```bash
# Service management
sudo /opt/bookingchart-defragmenter/manage.sh start    # Start service (environment only)
sudo /opt/bookingchart-defragmenter/manage.sh stop     # Stop service
sudo /opt/bookingchart-defragmenter/manage.sh restart  # Restart service
sudo /opt/bookingchart-defragmenter/manage.sh status   # Check service status
sudo /opt/bookingchart-defragmenter/manage.sh logs     # View live logs

# Analysis execution
sudo /opt/bookingchart-defragmenter/manage.sh run      # Run analysis manually
sudo /opt/bookingchart-defragmenter/manage.sh health   # Health check
sudo /opt/bookingchart-defragmenter/manage.sh update   # Update from GitHub
```

### Service Architecture
The application uses a **two-tier service architecture**:

1. **Service Wrapper** (`service_wrapper.sh`):
   - ✅ Sets up environment and verifies configuration
   - ✅ Does NOT run analysis automatically
   - ✅ Stays running for systemd management
   - ✅ Fast startup (~30 seconds)

2. **Analysis Execution**:
   - 📅 **Scheduled**: Daily at 2:00 AM via cron
   - 🖱️ **Manual**: Run with `manage.sh run`
   - ⚡ **Non-blocking**: Updates don't interfere with analysis

### Health Monitoring
```bash
# Comprehensive health check
sudo /opt/bookingchart-defragmenter/health_check.sh

# Service diagnostics
sudo /opt/bookingchart-defragmenter/debug_service.sh
```

## Deployment

### Development → Production Workflow
```
📱 Mac (Development) → 🌐 GitHub → 🥧 Raspberry Pi (Production)
```

### Automated Updates
```bash
# Update from GitHub (no authentication required)
sudo /opt/bookingchart-defragmenter/manage.sh update
```

### Safety Features
- ✅ **Automatic Backup** - Previous version saved before update
- ✅ **Configuration Preservation** - Credentials stay safe
- ✅ **Auto-Rollback** - Reverts if update fails
- ✅ **Health Verification** - Ensures service starts properly
- ✅ **Public Repository** - No authentication required for updates

## Architecture

### Core Components

#### 1. **MultiPropertyAnalyzer** (`start.py`)
- Main orchestration class
- Handles multi-property processing
- Manages authentication and property discovery
- Provides progress tracking and user control
- Coordinates the entire analysis workflow
- Generates consolidated Excel summary

#### 2. **RMSClient** (`rms_client.py`)
- Handles RMS (Reservation Management System) API authentication and communication
- Fetches live inventory and reservation data
- Manages API sessions and token handling
- Filters and validates property data
- Converts API responses to standardized formats
- Implements comprehensive caching system

#### 3. **DefragmentationAnalyzer** (`defrag_analyzer.py`)
- Core optimization algorithm
- Builds occupancy matrices
- Calculates fragmentation scores
- Identifies optimal move sequences

#### 4. **ExcelGenerator** (`excel_generator.py`)
- Creates comprehensive Excel workbooks
- Generates visual charts and heatmaps
- Builds detailed move suggestions tables
- Applies professional styling and formatting

#### 5. **EmailSender** (`email_sender.py`)
- Sends professional HTML email notifications
- Handles Excel file attachments
- Manages email templates and branding
- Supports training mode email routing

#### 6. **HolidayClient** (`holiday_client.py`)
- **🎄 Holiday Data Integration**: Fetches holiday periods from Nager.Date API
- **State-Specific Analysis**: Provides holiday data for all Australian states
- **Extended Period Analysis**: Analyzes ±7 days around holiday periods for optimal optimization
- **Importance-Based Prioritization**: Categorizes holidays by importance (High/Medium/Low)
- **Caching System**: Efficient caching of holiday data to reduce API calls
- **Date Range Calculation**: Provides holiday-aware date ranges for analysis

#### 7. **Logger** (`utils.py`)
- **Comprehensive Logging System**: Detailed logging of all application activities
- **Append Mode**: Log file grows with each run, preserving historical data
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Performance Tracking**: Timing information for all major operations
- **API Call Logging**: Detailed tracking of all RMS API interactions
- **Error Context**: Rich error information with context for troubleshooting
- **Data Summaries**: Counts and statistics for all data processing steps
- **Function Entry/Exit**: Tracks function calls and return values
- **Cache Operations**: Logs cache hits, misses, and operations
- **Move Analysis**: Detailed logging of defragmentation analysis results
- **Excel Generation**: Tracks Excel file creation and sheet generation
- **Email Operations**: Logs email sending attempts and results
- **Holiday Analysis Logging**: Tracks holiday period detection and analysis
- Handles move validation and simulation
- Implements category-based move ordering

#### 4. **ExcelGenerator** (`excel_generator.py`)
- Creates comprehensive Excel workbooks
- Generates visual charts and heatmaps
- Builds detailed suggestion tables
- Applies formatting and styling
- Adds interactive elements and tooltips
- Implements merged cells for multi-night bookings

#### 5. **EmailSender** (`email_sender.py`)
- Sends professional HTML emails
- Handles Excel file attachments
- Manages SMTP connections
- Provides email statistics and error handling
- Supports training mode email routing

### Data Flow

```
1. Authentication → RMS API
2. Property Discovery → Get all available properties
3. For each property:
   a. Fetch Inventory Data → Categories, Units, Availability
   b. Fetch Reservation Data → Current bookings, status, guest info
   c. 📅 Regular Analysis → Analyze 31-day defragmentation opportunities
   d. 🎄 Holiday Analysis → Fetch 2-month forward holiday periods and perform holiday-aware optimization
   e. 🔄 Smart Deduplication → Remove duplicate moves between regular and holiday analysis
   f. Merge Move Suggestions → Combine regular and holiday moves with prioritization
   g. Generate Excel Report → Visual charts + move suggestions + holiday information
   h. Send Email (if enabled) → Property-specific notifications with holiday data
4. Generate Consolidated Excel → Summary across all properties (daily heatmap + suggested moves table)
5. Summary Report → Overall success metrics with holiday analysis results
```

### 🎄 Holiday Analysis System

The system now includes comprehensive holiday-aware analysis with **2-month forward planning** for optimal booking optimization during peak holiday periods:

#### **Dual Analysis Approach**
The system performs two distinct types of analysis:

**📅 Regular 31-Day Analysis:**
- **Period**: Next 31 days from today
- **Purpose**: Immediate optimization for current bookings
- **Scope**: All reservations within the 31-day window
- **Frequency**: Daily analysis for ongoing optimization

**🎄 2-Month Forward Holiday Analysis:**
- **Period**: Next 60 days from today (2 months forward)
- **Purpose**: Early optimization for upcoming holiday periods
- **Scope**: Holiday periods only, with ±7 days extension around each holiday
- **Frequency**: Daily analysis to catch holidays as they approach

#### **Holiday Data Integration**
- **Nager.Date API**: Fetches real-time holiday data for all Australian states
- **State-Specific Analysis**: Automatically detects property state and fetches relevant holidays
- **2-Month Forward Window**: Analyzes holidays in a 60-day forward-looking window
- **Extended Period Analysis**: Analyzes ±7 days around each holiday for comprehensive optimization
- **Importance-Based Prioritization**: Holidays categorized as High/Medium/Low importance

#### **Smart Deduplication System**
- **Overlap Detection**: Automatically detects when holiday periods overlap with regular 31-day analysis
- **Enhanced Deduplication**: Removes duplicate move suggestions between holiday and regular analysis
- **50% Overlap Threshold**: Considers moves duplicate if date ranges overlap by more than 50%
- **Priority Preservation**: Holiday moves are prioritized over regular moves in final output

#### **Holiday-Aware Optimization**
- **Peak Period Focus**: Prioritizes optimization during holiday periods when demand is highest
- **Extended Date Ranges**: Analyzes extended periods around holidays for better optimization
- **State-Specific Holidays**: Considers state-specific holidays (e.g., Melbourne Cup Day in VIC)
- **Move Prioritization**: Holiday moves are prioritized over regular moves in the final output
- **Early Planning**: 2-month advance notice allows for strategic holiday optimization

#### **Enhanced Outputs**
- **Holiday-Enhanced Excel Reports**: 4-sheet workbooks including holiday-specific information
- **Holiday Move Suggestions**: Dedicated sheet for holiday-specific move recommendations
- **Holiday Summary**: Comprehensive overview of holiday periods and analysis
- **Enhanced Email Notifications**: Separate tables for regular and holiday moves
- **Overlap Indicators**: Clear marking of moves that overlap with regular analysis periods

## Key Algorithms

### Defragmentation Scoring
- **Fragmentation Score**: Calculates how fragmented availability is within each category
- **Contiguous Availability**: Identifies blocks of available nights
- **Move Impact Analysis**: Simulates the effect of each potential move
- **Sequential Optimization**: Considers the cumulative effect of multiple moves

### Move Validation
- **Availability Check**: Ensures target accommodation unit is available for the entire stay
- **Status Filtering**: Only moves confirmed/unconfirmed reservations
- **Fixed Reservation Protection**: Excludes reservations marked as fixed
- **Maintenance & Pencil Protection**: Excludes Maintenance and Pencil bookings (cannot be moved)
- **Date Range Validation**: Only considers moves within analysis period

### Smart Deduplication Logic
- **Overlap Detection**: Automatically identifies when holiday periods overlap with regular 31-day analysis
- **Enhanced Duplicate Detection**: Uses advanced logic to identify duplicate moves between holiday and regular analysis
- **50% Overlap Threshold**: Considers moves duplicate if their date ranges overlap by more than 50%
- **Priority-Based Deduplication**: Holiday moves are preserved over regular moves when duplicates are found
- **Move ID Tracking**: Unique identifiers for holiday moves (H2M{number}.{subnumber}) vs regular moves
- **Overlap Flagging**: Moves are marked with `overlaps_regular_analysis` flag for transparency

### Data Filtering
- **Active Properties Only**: Excludes properties marked as inactive (`inactive: false`)
- **Active Categories Only**: Excludes categories marked as inactive (`inactive: false`) or not available for booking (`availableToIbe: false`)
- **Active Areas Only**: Excludes areas marked as inactive (`inactive: false`) or with statistics disabled (`statisticsStatus: false`)
- **Reservation-Area Alignment**: Excludes reservations associated with excluded areas to ensure data consistency

### API Efficiency & Caching
- **Comprehensive Caching System**: Categories and areas cached per property with 5-minute TTL
- **API Call Reduction**: Reduces API calls by approximately 50% through intelligent caching
- **Cache Management**: Automatic cache invalidation and property-specific cache clearing
- **Performance Monitoring**: Real-time tracking of cache hit rates and API usage

## Output Files

### Individual Property Excel Files
Each property generates an Excel file named: `{PropertyCode}-Defragmentation-Analysis.xlsx`

**Note**: Files are overwritten on each run to maintain clean file management and ensure the latest analysis is always available.

#### Sheet 1: Visual Chart
- **Daily Heatmap**: Red gradient showing move opportunities for each day
- **Move Count Row**: Number of available moves per day with color coding
- **Category-Specific Importance Levels**: Individual rows for each accommodation category showing Low/Medium/High importance per day, based on fragmentation and availability patterns
- **Booking Grid**: Visual representation of all reservations by accommodation unit and date
- **Merged Cells**: Multi-night bookings are displayed as horizontal blocks spanning consecutive dates
- **Category Headers**: Merged across entire chart width with left-justified text for better readability
- **Compact Layout**: No blank rows between categories for efficient space usage
- **Black Borders**: Clear boundaries around each reservation for easy visual separation
- **Color-Coded Status**: Different colors for various reservation types (Confirmed, Unconfirmed, Arrived, Maintenance, Pencil)
- **Fixed Bookings**: 🎯 Dart icon prefix indicates fixed reservations (cannot be moved)
- **Move Indicators**: Red cells with directional arrows and numbers (⬆️ 1, ⬇️ 2) showing suggested moves
- **Directional Arrows**: ⬆️ for moves up in chart, ⬇️ for moves down in chart (positioned before move number)
- **Interactive Tooltips**: Detailed information on hover including span duration, importance levels, and category strategic weighting

#### Sheet 2: Move Suggestions
- **Category-Based Order**: Numbered moves by category (1.1, 1.2, 2.1, 2.2, etc.)
- **Reservation Details**: Guest name, current accommodation unit, suggested unit
- **Improvement Score**: Quantified benefit of each move
- **Implementation Notes**: Detailed reasoning and instructions

#### Sheet 3: Holiday Move Suggestions 🎄
- **Holiday-Specific Moves**: Dedicated sheet for moves optimized for holiday periods
- **Holiday Period Information**: Shows which holiday period each move is optimized for
- **Importance Levels**: Holiday importance (High/Medium/Low) for each move
- **Extended Period Analysis**: Moves optimized for ±7 days around holiday periods
- **Priority Indicators**: Holiday moves are clearly marked and prioritized

#### Sheet 4: Holiday Summary 📅
- **Holiday Periods Overview**: Complete list of holidays detected for the property's state
- **Analysis Periods**: Extended periods analyzed around each holiday
- **Importance Classification**: Holiday importance levels and reasoning
- **State Information**: Property state and holiday data source
- **Implementation Notes**: Guidance for holiday-specific optimization

### Consolidated Excel File
After processing all properties, generates: `Full_Defragmentation_Analysis.xlsx`

#### Sheet 1: Consolidated Daily Moves
- **Two Rows Per Property**: Each property has two rows - one for move counts and one for opportunity scores
- **Move Counts Row**: Shows the number of moves available for each property/date (e.g., "QROC Moves")
- **Move Scores Row**: Shows the total move opportunity score with heatmap coloring (e.g., "QROC Move Score")
- **Daily Move Opportunities**: Columns show each day with both move counts and opportunity scores
- **Red Heatmap**: Color intensity on Move Scores rows indicates opportunity density
- **Interactive Tooltips**: Detailed information for each cell including moves available, total opportunity score, and average move value
- **Legend**: Explains color coding for opportunity score levels
- **Scoring Logic Explanation**: Detailed explanation of how Total Move Opportunity Score and Average Move Value are calculated

#### Sheet 2: Suggested_Moves
- **All Properties Combined**: Complete collection of suggested reservation moves across all analyzed parks
- **Property Information**: PropertyId, PropertyCode, PropertyName columns for easy identification
- **Move Details**: Reservation number, guest surname, current unit, suggested unit
- **Categorization**: Category, status, arrival/departure dates, nights, improvement score
- **Implementation Guidance**: Reason for each move and implementation notes
- **Sorted by Property**: Organized by property code then move order for easy implementation

## Usage

### Prerequisites
- Python 3.7+
- RMS API access credentials
- Required Python packages: `pandas`, `openpyxl`, `requests`, `numpy`

## Installation

### From Source
```bash
# Clone the repository
git clone https://github.com/your-username/BookingChartDefragmenter.git
cd BookingChartDefragmenter

# Install dependencies
pip install -r requirements.txt
```

### Manual Installation
```bash
pip install pandas openpyxl requests numpy
```

## Configuration
The system requires RMS credentials to be provided as command-line arguments:
- **Agent ID and Password** (MANDATORY)
- **Client ID and Password** (MANDATORY)
- API base URL (hardcoded)
- Timezone settings (hardcoded)
- Database selection (Live Production or Training via `-t` flag)

**Security Note**: Credentials are no longer hardcoded in the source code and must be provided at runtime for better security.

## Usage

### Command Line Interface

#### Basic Analysis (No Emails)
```bash
# Analyze specific properties
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -p SADE,QROC,TCRA

# Analyze single property
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -p SADE

# Analyze all properties
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -p ALL
```

#### Analysis with Email Notifications
```bash
# Analyze all properties with email notifications
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -e -p ALL

# Analyze specific properties with email notifications
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -e -p SADE,QROC,TCRA

# Analyze single property with email notification
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -e -p SADE
```

#### Training Database Analysis
```bash
# Analyze all properties using training database
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -t -p ALL

# Analyze specific properties using training database
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -t -p SADE,QROC,TCRA

# Analyze with training database and email notifications
python3 start.py --agent-id ***REMOVED*** --agent-password "********" --client-id ***REMOVED*** --client-password "********" -t -e -p ALL
# Note: Training mode emails are sent to operations@discoveryparks.com.au
```

**Note**: Replace the example credentials with your actual RMS credentials. All credential arguments are MANDATORY.

#### Help and Examples
```bash
# Show help
python3 start.py -h

# If no arguments provided, shows usage examples
python3 start.py
```

#### Command Line Arguments
**MANDATORY Arguments:**
- `--agent-id`: RMS Agent ID
- `--agent-password`: RMS Agent Password
- `--client-id`: RMS Client ID
- `--client-password`: RMS Client Password

**Optional Arguments:**
- `-p, --properties`: Property codes to analyze (comma-separated) or ALL for all properties
- `-e, --email`: Send email notifications with Excel attachments after each property analysis
- `-t, --training`: Use training database instead of live production data (emails sent to operations@discoveryparks.com.au)

#### Environment Variables
**Email Configuration:**
- `ENABLE_EMAILS`: Enable/disable property-specific email notifications
- `SEND_CONSOLIDATED_EMAIL`: Enable/disable consolidated report email
- `CONSOLIDATED_EMAIL_RECIPIENT`: Email address for consolidated reports (default: operations@discoveryparks.com.au)
- `SENDER_EMAIL`: Gmail account for SMTP authentication
- `SENDER_DISPLAY_NAME`: Custom display name for email sender
- `APP_PASSWORD`: Gmail app password for SMTP authentication

### Analysis Process
The system will:
1. Authenticate with RMS API (Live Production or Training database)
2. Discover and filter properties based on target codes
3. Analyze each property sequentially with progress tracking
4. Generate Excel reports for each property
5. Send email notifications (if enabled)
6. Generate consolidated Excel summary (two sheets: daily heatmap + suggested moves)
7. Provide comprehensive summaries and endpoint usage statistics

### Email Behavior
- **Live Mode**: Emails are sent to each property's individual email address (e.g., `rockhampton@discoveryparks.com.au`)
- **Training Mode**: All emails are sent to `operations@discoveryparks.com.au` for centralized review
- **Contact Information**: All emails include contact details for the Operations Systems Manager

## Business Value

### Revenue Optimization
- **Increased Occupancy**: Consolidates scattered availability into bookable blocks
- **Higher ADR Potential**: Longer stays typically command higher rates
- **Reduced Turnover**: Fewer single-night stays means less housekeeping and site maintenance costs
- **Better Guest Experience**: Guests prefer longer stays in the same accommodation
- **🎄 Peak Period Optimization**: Maximizes revenue during high-demand holiday periods
- **Holiday Rate Optimization**: Better positioning for premium holiday pricing
- **Extended Stay Opportunities**: Creates longer booking blocks during peak periods
- **🔄 Strategic Planning**: 2-month advance notice for holiday optimization
- **No Duplicate Suggestions**: Smart deduplication prevents redundant move recommendations

### Operational Efficiency
- **Automated Analysis**: No manual review of booking patterns required
- **Visual Decision Support**: Clear charts and recommendations
- **Multi-Property Scalability**: Handles entire property portfolios with flexible selection
- **Real-Time Data**: Always works with current reservation status
- **API Efficiency**: Comprehensive caching reduces API calls by ~50%
- **Progress Tracking**: Real-time progress indicators and comprehensive summaries
- **Safe Testing**: Training database option for testing without affecting live data
- **🎄 Holiday-Aware Automation**: Automatic holiday period detection and analysis
- **State-Specific Optimization**: Automatic property state detection for holiday analysis
- **Holiday Period Intelligence**: No manual holiday calendar management required

### Strategic Planning
- **Forward-Looking Analysis**: 31-day optimization window
- **Category-Level Optimization**: Considers accommodation type preferences (cabins, sites, glamping, etc.)
- **Category-Based Implementation**: Ordered moves within each category for maximum impact
- **Risk Management**: Respects fixed reservations, maintenance schedules, and guest preferences
- **🎄 Holiday Period Planning**: Strategic optimization during peak demand periods
- **State-Specific Strategy**: Considers state-specific holidays and peak periods
- **Extended Period Analysis**: ±7 days around holidays for comprehensive optimization
- **Holiday Priority Management**: Prioritizes moves during high-importance holiday periods

## Technical Specifications

### API Integration
- **RMS REST API**: Full integration with Reservation Management System
- **Real-Time Data**: Live inventory and reservation information
- **Authentication**: Secure token-based authentication
- **Error Handling**: Robust error handling and retry logic

### Data Processing
- **Pandas DataFrames**: Efficient data manipulation and analysis
- **Date Range Processing**: Handles complex date calculations
- **Memory Optimization**: Processes large datasets efficiently
- **Data Validation**: Comprehensive input validation and cleaning

### Excel Generation
- **OpenPyXL**: Professional Excel workbook creation
- **Visual Styling**: Professional formatting and color schemes
- **Interactive Elements**: Comments and tooltips for user guidance
- **Multi-Sheet Workbooks**: Organized information presentation

## Example Output

### **📅 Dual Analysis Example**

**Current Date:** January 15, 2025  
**Property:** SADE (South Australia)

**📅 Regular 31-Day Analysis:**
- **Period:** January 15, 2025 → February 15, 2025
- **Moves Generated:** 12 regular optimization moves
- **Focus:** Immediate optimization for current bookings

**🎄 2-Month Forward Holiday Analysis:**
- **Period:** January 15, 2025 → March 16, 2025
- **Holidays Found:** Australia Day (Jan 27, 2025)
- **Overlap Detection:** Australia Day period overlaps with regular analysis
- **Moves Generated:** 3 holiday-specific moves
- **Deduplication:** 1 duplicate move removed (same move suggested by both analyses)

**🔄 Final Result:**
- **Total Moves:** 14 unique moves (12 regular + 2 holiday after deduplication)
- **Priority Order:** Holiday moves first, then regular moves by improvement score
- **No Duplicates:** Smart deduplication prevents redundant suggestions

### **Console Output Example:**
```
🎄 2-Month Forward Holiday Analysis: 1 periods, 3 holiday moves
📋 Total Merged Suggestions: 14 moves
🔄 Duplicates removed: 1
🎄 Overlapping holiday moves: 1
⚠️  Holiday period overlaps with regular analysis - will deduplicate moves
```

### Excel Files
The system generates files like:
- `QROC-Defragmentation-Analysis.xlsx` (individual property)
- `TCRA-Defragmentation-Analysis.xlsx` (individual property)
- `Full_Defragmentation_Analysis.xlsx` (consolidated summary with two sheets)

Each individual property file contains:
- Visual booking charts with color-coded status
- Daily heatmap showing move opportunities
- Detailed move suggestion tables
- Implementation instructions and legends

The consolidated file (`Full_Defragmentation_Analysis.xlsx`) contains:
- **Sheet 1: Consolidated Daily Moves** - Property-by-property heatmap of daily move opportunities with two rows per property:
  - `{ParkCode} Moves` - Number of moves available for each day
  - `{ParkCode} Move Importance` - Strategic importance level (High/Medium/Low/None) for each day based on category importance
  - **Row Totals** - Total moves for each property across all dates (right column)
  - **Column Totals** - Total moves across all properties for each date (bottom row)
  - **Grand Total** - Total moves across all properties and all dates (bottom right corner)
- **Sheet 2: Suggested_Moves** - Complete collection of all suggested moves across all properties in a single table

### Email Notifications
When enabled, sends professional HTML emails with:
- Discovery Parks branded styling
- Property-specific analysis summaries
- **🎄 Holiday-Enhanced Content**: Separate tables for regular and holiday moves
- **Holiday Summary Section**: Overview of holiday periods and analysis
- Complete move recommendation tables
- Excel file attachments
- Implementation guidance
- **Holiday-Specific Subject Lines**: Clear identification of holiday-enhanced analysis

#### Consolidated Report Email
When `SEND_CONSOLIDATED_EMAIL=true` is set, the system also sends:
- **Multi-Property Summary Report** to the address specified in `CONSOLIDATED_EMAIL_RECIPIENT`
- **Consolidated Excel File** (`Full_Defragmentation_Analysis.xlsx`) as attachment
- **Cross-Property Analysis** showing total opportunities and strategic priorities
- **Implementation Guidance** for operations team coordination

**Default recipient**: `operations@discoveryparks.com.au` (configurable)

### Console Output
Comprehensive progress tracking and summaries:
- Real-time progress bars for overall and individual property analysis
- **📅 Regular Analysis Status**: 31-day defragmentation analysis progress
- **🎄 2-Month Forward Holiday Analysis Status**: Holiday period detection and analysis progress
- **State Code Detection**: Automatic property state identification for holiday analysis
- **Holiday Move Counts**: Separate counts for regular and holiday moves
- **🔄 Deduplication Status**: Overlap detection and duplicate removal statistics
- **Overlap Indicators**: Clear marking of holiday periods that overlap with regular analysis
- Cache performance statistics
- Email sending status
- Database mode indicator (Live Production or Training)
- Endpoint usage summary table with limit monitoring
- API efficiency metrics
- **Holiday Summary**: Overview of holiday periods found and analyzed in 2-month window

### Logging System
The application maintains a comprehensive log file (`defrag_analyzer.log`) that captures all activities:
- **Session Tracking**: Each run is clearly marked with session boundaries
- **Performance Metrics**: Detailed timing for all major operations
- **API Interactions**: Complete logging of all RMS API calls with status codes and response sizes
- **Data Processing**: Counts and summaries of all data processing steps
- **Error Tracking**: Detailed error information with context for troubleshooting
- **Function Flow**: Entry and exit logging for all major functions
- **Cache Operations**: Tracking of cache hits, misses, and operations
- **Move Analysis**: Detailed results of defragmentation analysis
- **📅 Regular Analysis Logging**: Complete tracking of 31-day defragmentation analysis
- **🎄 2-Month Forward Holiday Analysis Logging**: Complete tracking of holiday period detection, API calls, and analysis results
- **State Code Detection**: Logging of property state identification for holiday analysis
- **🔄 Deduplication Logging**: Detailed tracking of overlap detection and duplicate removal
- **Holiday Move Merging**: Detailed logging of move deduplication and prioritization
- **Excel Generation**: File creation and sheet generation tracking
- **Email Operations**: Success/failure logging for email sending

**Log File Location**: `defrag_analyzer.log` (in the same directory as the script)
**Log Format**: Timestamp - Logger Name - Level - Message
**Append Mode**: Log file grows with each run, preserving historical data
**Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Docker Deployment

The project includes Docker support for easy deployment:

```bash
# Build the Docker image
docker build -t booking-defragmenter .

# Run with environment variables
docker run -e AGENT_ID=your_id -e AGENT_PASSWORD=your_pass \
           -e CLIENT_ID=your_client_id -e CLIENT_PASSWORD=your_client_pass \
           -e TARGET_PROPERTIES=ALL \
           booking-defragmenter

# Or use docker-compose
docker-compose up
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/BookingChartDefragmenter.git
cd BookingChartDefragmenter

# Install development dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest

# Run the application in development mode
python3 start.py --help
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support and Maintenance

### Error Handling
- Comprehensive error logging and reporting
- Graceful handling of API failures
- Data validation and sanitization
- User-friendly error messages

### Performance Optimization
- Efficient algorithms for large datasets
- Memory-conscious data processing
- Progress tracking for long-running operations
- Configurable analysis parameters
- Comprehensive caching system reducing API calls by ~50%
- Real-time endpoint monitoring and limit tracking

### Documentation Maintenance
- **README Updates**: This README file should be updated whenever code changes impact functionality, features, or business logic
- **Version Control**: All documentation changes should be committed alongside code changes
- **Change Tracking**: Significant updates to the system should be reflected in this documentation

## Troubleshooting

### Common Issues:

1. **Authentication Failed**
   - Verify RMS API credentials
   - Check network connectivity
   - Ensure credentials are properly escaped in config

2. **Permission Denied**
   - Check file permissions: `ls -la /opt/bookingchart-defragmenter/`
   - Verify service user: `id defrag`
   - Fix permissions: `sudo chown -R defrag:defrag /opt/bookingchart-defragmenter/`

3. **Service Won't Start**
   - Check service status: `sudo systemctl status bookingchart-defragmenter.service`
   - View logs: `sudo journalctl -u bookingchart-defragmenter.service`
   - Verify configuration: `sudo cat /etc/bookingchart-defragmenter/config.env`

4. **Network Connectivity Issues** (for updates)
   - Check internet connection: `ping github.com`
   - Verify firewall allows HTTPS (port 443)
   - Test: `curl -I https://github.com`

5. **Docker Issues**
   - Check container logs: `docker-compose logs bookingchart-defragmenter`
   - Verify environment variables: `docker-compose config`
   - Rebuild container: `docker-compose up -d --build`

### If Update Fails:
The script automatically rolls back, but you can check:

```bash
# Check service status
sudo /opt/bookingchart-defragmenter/manage.sh status

# View recent logs
sudo /opt/bookingchart-defragmenter/manage.sh logs

# Manual rollback (if needed)
sudo systemctl stop bookingchart-defragmenter.service
sudo mv /opt/bookingchart-defragmenter-backup /opt/bookingchart-defragmenter
sudo systemctl start bookingchart-defragmenter.service
```

### Log Analysis

```bash
# Search for errors
grep -i error /var/log/bookingchart-defragmenter/defrag_analyzer.log

# Search for specific property
grep "SADE" /var/log/bookingchart-defragmenter/defrag_analyzer.log

# View recent activity
tail -100 /var/log/bookingchart-defragmenter/defrag_analyzer.log

# Live logs
sudo /opt/bookingchart-defragmenter/manage.sh logs

# Historical logs
sudo journalctl -u bookingchart-defragmenter.service -n 100
```

### Performance Monitoring

```bash
# Check disk usage
df -h /var/log/bookingchart-defragmenter

# Check memory usage
free -h

# Check process status
ps aux | grep python3
```

## File Locations

- **Application**: `/opt/bookingchart-defragmenter/`
- **Configuration**: `/etc/bookingchart-defragmenter/config.env`
- **Logs**: `/var/log/bookingchart-defragmenter/`
- **Service**: `/etc/systemd/system/bookingchart-defragmenter.service`
- **Backups**: `/opt/bookingchart-defragmenter-backup/` (temporary)

## Security Notes

- 🔒 **Credentials Never Change** - Update preserves all API credentials
- 🔒 **Service User** - Runs as non-root `defrag` user
- 🔒 **File Permissions** - Maintained during updates
- 🔒 **Configuration Files** - Protected and preserved

## Advanced Usage

### Branch Strategy

- **`main`** - Production-ready code (default for updates)
- **`develop`** - Development/testing code
- **Feature branches** - For experimental features

### Update from different branches:
```bash
# Production updates (stable)
sudo /opt/bookingchart-defragmenter/manage.sh update main

# Test new features
sudo /opt/bookingchart-defragmenter/manage.sh update develop
```

### Manual Git Update (if needed):
```bash
cd /opt/bookingchart-defragmenter
sudo git pull origin main
sudo systemctl restart bookingchart-defragmenter.service
```

### Check Current Version:
```bash
cd /opt/bookingchart-defragmenter
git log --oneline -1
```

### Configuration Changes:
```bash
sudo nano /etc/bookingchart-defragmenter/config.env
sudo /opt/bookingchart-defragmenter/manage.sh restart
```
