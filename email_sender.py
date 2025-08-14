#!/usr/bin/env python3
"""
Email Sender Module
Handles sending property-specific emails with Excel attachments via Gmail SMTP
Compatible with Debian 12 Linux Server
"""

import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional

class EmailSender:
    def __init__(self):
        """Initialize email sender with Gmail configuration"""
        
        # Gmail SMTP configuration (with environment variable support)
        self.smtp_server = os.environ.get('SMTP_SERVER', "smtp.gmail.com")
        self.smtp_port = int(os.environ.get('SMTP_PORT', "587"))
        self.sender_email = os.environ.get('SENDER_EMAIL', "***REMOVED***")
        self.app_password = os.environ.get('APP_PASSWORD')
        
        # Custom display name for the sender (optional)
        self.sender_display_name = os.environ.get('SENDER_DISPLAY_NAME', "DHP Systems")
        
        # Test recipient (for testing purposes)
        self.test_recipient = os.environ.get('TEST_RECIPIENT', "***REMOVED***")
        
        # Email statistics
        self.emails_sent = 0
        self.emails_failed = 0
        self.email_errors = []
        
        print(f"📧 Email Sender initialized")
        print(f"   📤 From: \"{self.sender_display_name}\" <{self.sender_email}>")
        print(f"   📥 Test To: {self.test_recipient}")
        print(f"   🔧 SMTP: {self.smtp_server}:{self.smtp_port}")

    def send_property_analysis_email(self, property_name: str, property_id: int, 
                                   excel_file_path: str, suggestions: List[Dict],
                                   analysis_start_date, analysis_end_date,
                                   excel_success: bool, property_email: str = None, 
                                   is_training_mode: bool = False) -> bool:
        """Send property-specific analysis email with Excel attachment"""
        
        print(f"\n📧 SENDING PROPERTY ANALYSIS EMAIL")
        print("=" * 50)
        print(f"🏢 Property: {property_name}")
        print(f"📁 Excel File: {excel_file_path}")
        print(f"📊 Suggestions: {len(suggestions)}")
        
        try:
            # Determine recipient email based on training mode
            if is_training_mode:
                recipient_email = "operations@discoveryparks.com.au"
                recipient_display = f"{recipient_email} (training mode)"
            else:
                recipient_email = property_email if property_email else self.test_recipient
                recipient_display = property_email if property_email else f"{self.test_recipient} (test)"
            
            # Create email message
            msg = self._create_email_message(property_name, property_id, suggestions, 
                                           analysis_start_date, analysis_end_date, excel_success, recipient_email)
            
            # Add Excel attachment if file exists and was created successfully
            if excel_success and os.path.exists(excel_file_path):
                self._add_excel_attachment(msg, excel_file_path)
                print(f"✅ Excel file attached: {os.path.basename(excel_file_path)}")
            else:
                print(f"⚠️  No Excel file to attach (success: {excel_success}, exists: {os.path.exists(excel_file_path) if excel_file_path else False})")
            
            # Send email
            success = self._send_email(msg)
            
            if success:
                self.emails_sent += 1
                print(f"✅ Email sent successfully to {recipient_display}")
            else:
                self.emails_failed += 1
                print(f"❌ Email failed to send")
            
            return success
            
        except Exception as e:
            self.emails_failed += 1
            error_msg = f"Email error for {property_name}: {str(e)}"
            self.email_errors.append(error_msg)
            print(f"💥 {error_msg}")
            return False

    def _create_email_message(self, property_name: str, property_id: int, 
                            suggestions: List[Dict], analysis_start_date, 
                            analysis_end_date, excel_success: bool, recipient_email: str) -> MIMEMultipart:
        """Create the email message with HTML content"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f'"{self.sender_display_name}" <{self.sender_email}>'
        msg['To'] = recipient_email
        msg['Subject'] = f"RMS Booking Chart Fragmentation Report: {property_name}"
        
        # Create HTML content
        html_content = self._create_html_content(property_name, property_id, suggestions, 
                                               analysis_start_date, analysis_end_date, excel_success)
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        return msg

    def _create_html_content(self, property_name: str, property_id: int, 
                           suggestions: List[Dict], analysis_start_date, 
                           analysis_end_date, excel_success: bool) -> str:
        """Create HTML email content"""
        
        # Format dates
        start_date_str = analysis_start_date.strftime('%d/%m/%Y')
        end_date_str = analysis_end_date.strftime('%d/%m/%Y')
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Create suggestions summary
        if suggestions:
            suggestions_summary = f"""
            <h3>🔝 All Move Recommendations ({len(suggestions)} total):</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #F47425; color: white;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Order</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Res No</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Guest</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">From</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">To</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Score</th>
                </tr>
            """
            
            for suggestion in suggestions:
                suggestions_summary += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{suggestion['Sequential_Order']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{suggestion['Reservation_No']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{suggestion['Surname'][:15]}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{suggestion['Current_Unit'][:15]}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{suggestion['Suggested_Unit'][:15]}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{suggestion['Improvement_Score']}</td>
                </tr>
                """
            
            suggestions_summary += "</table>"
        else:
            suggestions_summary = "<p><strong>✅ No optimization needed - reservations are well organized!</strong></p>"
        
        # Create HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #F47425; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #F47425; padding: 15px; margin: 15px 0; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RMS Booking Chart Fragmentation Report for:</h1>
                <h1>{property_name}</h1>
            </div>
            
            <div class="content">
                <div class="summary-box">
                    <h3>📋 Analysis Summary</h3>
                    <p><strong>Property:</strong> {property_name}</p>
                    <p><strong>Analysis Period:</strong> {start_date_str} to {end_date_str}</p>
                    <p><strong>Total Suggestions:</strong> {len(suggestions)} optimization moves</p>
                    <p><strong>Excel Report:</strong> {'✅ Generated successfully' if excel_success else '❌ Generation failed'}</p>
                    <p><strong>Analysis Time:</strong> {current_time}</p>
                </div>
                
                <div class="summary-box">
                    <h3>📊 Implementation Notes</h3>
                    <ul>
                        <li>Apply moves in category-based order (Order column - e.g., 1.1, 1.2, 2.1, 2.2)</li>
                        <li>Each move considers the effect of previous moves</li>
                        <li>Only reservations entirely within analysis period are included</li>
                        <li>Fixed reservations are excluded from suggestions</li>
                        <li>Higher improvement scores = better defragmentation results</li>
                        <li>Real-time data from RMS API at time of analysis</li>
                        <li>Refer to attached excel file for full analysis and graphical booking chart guide</li>
                    </ul>
                </div>
                
                {suggestions_summary}
                
                <div class="summary-box">
                    <h3>📧 Contact Information</h3>
                    <p><strong>Operations Systems Manager:</strong> Mr Tim Curtis</p>
                    <p><strong>Email:</strong> operations@discoveryparks.com.au</p>
                    <p><strong>Generated by:</strong> RMS Multi-Property Defragmentation Analyzer</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This email was automatically generated by the Discovery Parks Defragmentation Analysis System.</p>
                <p>Please review the attached Excel file for detailed analysis and implementation guidance.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_holiday_enhanced_email(self, property_name: str, property_id: int, 
                                  excel_file_path: str, regular_suggestions: List[Dict],
                                  holiday_suggestions: List[Dict], holiday_data: Dict,
                                  analysis_start_date, analysis_end_date,
                                  excel_success: bool, property_email: str = None, 
                                  is_training_mode: bool = False) -> bool:
        """Send holiday-enhanced property analysis email with Excel attachment"""
        
        print(f"\n📧 SENDING HOLIDAY-ENHANCED PROPERTY ANALYSIS EMAIL")
        print("=" * 60)
        print(f"🏢 Property: {property_name}")
        print(f"📁 Excel File: {excel_file_path}")
        print(f"📊 Regular suggestions: {len(regular_suggestions)}")
        print(f"🎄 Holiday suggestions: {len(holiday_suggestions)}")
        
        try:
            # Determine recipient email based on training mode
            if is_training_mode:
                recipient_email = "operations@discoveryparks.com.au"
                recipient_display = f"{recipient_email} (training mode)"
            else:
                recipient_email = property_email if property_email else self.test_recipient
                recipient_display = property_email if property_email else f"{self.test_recipient} (test)"
            
            # Create email message
            msg = self._create_holiday_enhanced_email_message(
                property_name, property_id, regular_suggestions, holiday_suggestions, holiday_data,
                analysis_start_date, analysis_end_date, excel_success, recipient_email
            )
            
            # Add Excel attachment if file exists and was created successfully
            if excel_success and os.path.exists(excel_file_path):
                self._add_excel_attachment(msg, excel_file_path)
                print(f"✅ Excel file attached: {os.path.basename(excel_file_path)}")
            else:
                print(f"⚠️  No Excel file to attach (success: {excel_success}, exists: {os.path.exists(excel_file_path) if excel_file_path else False})")
            
            # Send email
            success = self._send_email(msg)
            
            if success:
                self.emails_sent += 1
                print(f"✅ Holiday-enhanced email sent successfully to {recipient_display}")
            else:
                self.emails_failed += 1
                print(f"❌ Holiday-enhanced email failed to send")
            
            return success
            
        except Exception as e:
            self.emails_failed += 1
            error_msg = f"Holiday-enhanced email error for {property_name}: {str(e)}"
            self.email_errors.append(error_msg)
            print(f"💥 {error_msg}")
            return False
    
    def _create_holiday_enhanced_email_message(self, property_name: str, property_id: int, 
                                             regular_suggestions: List[Dict], holiday_suggestions: List[Dict],
                                             holiday_data: Dict, analysis_start_date, 
                                             analysis_end_date, excel_success: bool, recipient_email: str) -> MIMEMultipart:
        """Create the holiday-enhanced email message with HTML content"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f'"{self.sender_display_name}" <{self.sender_email}>'
        msg['To'] = recipient_email
        msg['Subject'] = f"RMS Booking Chart Fragmentation Report: {property_name}"
        
        # Create HTML content
        html_content = self._create_holiday_enhanced_html_content(
            property_name, property_id, regular_suggestions, holiday_suggestions, holiday_data,
            analysis_start_date, analysis_end_date, excel_success
        )
        
        msg.attach(MIMEText(html_content, 'html'))
        return msg
    
    def _create_holiday_enhanced_html_content(self, property_name: str, property_id: int, 
                                            regular_suggestions: List[Dict], holiday_suggestions: List[Dict],
                                            holiday_data: Dict, analysis_start_date, 
                                            analysis_end_date, excel_success: bool) -> str:
        """Create HTML email content with holiday moves"""
        
        # Format dates
        start_date_str = analysis_start_date.strftime('%d/%m/%Y')
        end_date_str = analysis_end_date.strftime('%d/%m/%Y')
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Create holiday summary
        holiday_summary = ""
        if holiday_data and 'holiday_periods' in holiday_data:
            holiday_periods = holiday_data['holiday_periods']
            holiday_summary = f"""
            <div class="summary-box" style="border-left-color: #8B4513;">
                <h3>🎄 Holiday Analysis Summary</h3>
                <p><strong>Holiday Periods Analyzed:</strong> {len(holiday_periods)}</p>
                <p><strong>Holiday Moves Generated:</strong> {len(holiday_suggestions)}</p>
                <p><strong>Regular Moves Generated:</strong> {len(regular_suggestions)}</p>
                <p><strong>Total Moves:</strong> {len(regular_suggestions) + len(holiday_suggestions)}</p>
            </div>
            """
        
        # Create holiday moves table
        holiday_moves_table = ""
        if holiday_suggestions:
            holiday_moves_table = f"""
            <h3>🎄 Holiday Move Recommendations ({len(holiday_suggestions)} total):</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 12px;">
                <tr style="background-color: #8B4513; color: white;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Order</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Res No</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">Guest</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">From</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">To</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Category</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Status</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Arrive</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Depart</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Nights</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Holiday</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Importance</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Score</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">Reason</th>
                </tr>
            """
            
            for suggestion in holiday_suggestions:
                # Format dates for better readability
                arrive_date = suggestion.get('Arrive_Date', '')
                depart_date = suggestion.get('Depart_Date', '')
                if arrive_date:
                    arrive_date = arrive_date.strftime('%d/%m') if hasattr(arrive_date, 'strftime') else str(arrive_date)[:5]
                if depart_date:
                    depart_date = depart_date.strftime('%d/%m') if hasattr(depart_date, 'strftime') else str(depart_date)[:5]
                
                # Get holiday period info
                holiday_period = suggestion.get('holiday_period', '')
                if holiday_period:
                    holiday_period = holiday_period[:15]  # Truncate long holiday names
                
                holiday_moves_table += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center; font-weight: bold;">{suggestion.get('Sequential_Order', suggestion.get('move_id', ''))}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Reservation_No', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Surname', suggestion.get('guest_name', ''))[:20]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Current_Unit', suggestion.get('from_unit', ''))[:18]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Suggested_Unit', suggestion.get('to_unit', ''))[:18]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Category', '')[:15]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Status', '')[:10]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{arrive_date}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{depart_date}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Nights', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{holiday_period}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('holiday_importance', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center; font-weight: bold;">{suggestion.get('Improvement_Score', suggestion.get('improvement_score', 0))}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Reason', '')[:40]}</td>
                </tr>
                """
            
            holiday_moves_table += "</table>"
        
        # Create regular moves table
        regular_moves_table = ""
        if regular_suggestions:
            regular_moves_table = f"""
            <h3>📋 Regular Move Recommendations ({len(regular_suggestions)} total):</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 12px;">
                <tr style="background-color: #F47425; color: white;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Order</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Res No</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">Guest</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">From</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">To</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Category</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Status</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Arrive</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Depart</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Nights</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">Score</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">Reason</th>
                </tr>
            """
            
            for suggestion in regular_suggestions:
                # Format dates for better readability
                arrive_date = suggestion.get('Arrive_Date', '')
                depart_date = suggestion.get('Depart_Date', '')
                if arrive_date:
                    arrive_date = arrive_date.strftime('%d/%m') if hasattr(arrive_date, 'strftime') else str(arrive_date)[:5]
                if depart_date:
                    depart_date = depart_date.strftime('%d/%m') if hasattr(depart_date, 'strftime') else str(depart_date)[:5]
                
                regular_moves_table += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center; font-weight: bold;">{suggestion.get('Sequential_Order', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Reservation_No', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Surname', '')[:20]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Current_Unit', '')[:18]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Suggested_Unit', '')[:18]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Category', '')[:15]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Status', '')[:10]}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{arrive_date}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{depart_date}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">{suggestion.get('Nights', '')}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: center; font-weight: bold;">{suggestion.get('Improvement_Score', 0)}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: left;">{suggestion.get('Reason', '')[:40]}</td>
                </tr>
                """
            
            regular_moves_table += "</table>"
        
        # Create combined summary
        total_suggestions = len(regular_suggestions) + len(holiday_suggestions)
        if total_suggestions == 0:
            suggestions_summary = "<p><strong>✅ No optimization needed - reservations are well organized!</strong></p>"
        else:
            suggestions_summary = f"<p><strong>📊 Total Recommendations: {total_suggestions} moves</strong></p>"
        
        # Create HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #F47425; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #F47425; padding: 15px; margin: 15px 0; }}
                .holiday-box {{ background-color: #f8f9fa; border-left: 4px solid #8B4513; padding: 15px; margin: 15px 0; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RMS Booking Chart Fragmentation Report for:</h1>
                <h1>{property_name}</h1>
            </div>
            
            <div class="content">
                <div class="summary-box">
                    <h3>📋 Analysis Summary</h3>
                    <p><strong>Property:</strong> {property_name}</p>
                    <p><strong>Analysis Period:</strong> {start_date_str} to {end_date_str}</p>
                    <p><strong>Regular Suggestions:</strong> {len(regular_suggestions)} optimization moves</p>
                    <p><strong>Holiday Suggestions:</strong> {len(holiday_suggestions)} holiday-specific moves</p>
                    <p><strong>Total Suggestions:</strong> {total_suggestions} moves</p>
                    <p><strong>Excel Report:</strong> {'✅ Generated successfully' if excel_success else '❌ Generation failed'}</p>
                    <p><strong>Analysis Time:</strong> {current_time}</p>
                </div>
                
                {holiday_summary}
                
                <div class="summary-box">
                    <h3>📊 Implementation Notes</h3>
                    <ul>
                        <li><strong>🎄 Holiday moves are prioritized</strong> - Apply holiday moves first, then regular moves</li>
                        <li>Holiday moves consider extended periods (±7 days around holiday dates)</li>
                        <li>High importance holidays (Australia Day, Christmas, etc.) are marked as 'High'</li>
                        <li>Medium importance holidays (Queen's Birthday, Labour Day, etc.) are marked as 'Medium'</li>
                        <li>Apply moves in category-based order (Order column - e.g., 1.1, 1.2, 2.1, 2.2)</li>
                        <li>Each move considers the effect of previous moves</li>
                        <li>Only reservations entirely within analysis period are included</li>
                        <li>Fixed reservations are excluded from suggestions</li>
                        <li>Higher improvement scores = better defragmentation results</li>
                        <li>Real-time data from RMS API and Nager.Date API at time of analysis</li>
                        <li><strong>📋 Enhanced Email Tables:</strong> Move recommendations now include all columns from Excel (Category, Status, Dates, Nights, Reason)</li>
                        <li>Refer to attached excel file for full analysis and graphical booking chart guide</li>
                    </ul>
                </div>
                
                {holiday_moves_table}
                {regular_moves_table}
                {suggestions_summary}
                
                <div class="summary-box">
                    <h3>📧 Contact Information</h3>
                    <p><strong>Operations Systems Manager:</strong> Mr Tim Curtis</p>
                    <p><strong>Email:</strong> operations@discoveryparks.com.au</p>
                    <p><strong>Generated by:</strong> RMS Multi-Property Defragmentation Analyzer (Holiday-Enhanced)</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This email was automatically generated by the Discovery Parks Holiday-Enhanced Defragmentation Analysis System.</p>
                <p>Please review the attached Excel file for detailed analysis and implementation guidance.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content

    def send_consolidated_report_email(self, excel_file_path: str, property_count: int, 
                                     analysis_start_date, analysis_end_date, 
                                     total_suggestions: int, total_moves: int,
                                     excel_success: bool) -> bool:
        """Send consolidated analysis report email with Excel attachment"""
        
        # Get recipient email from environment variable
        recipient_email = os.environ.get('CONSOLIDATED_EMAIL_RECIPIENT', 'operations@discoveryparks.com.au')
        
        print(f"\n📧 SENDING CONSOLIDATED ANALYSIS REPORT EMAIL")
        print("=" * 60)
        print(f"📁 Excel File: {excel_file_path}")
        print(f"🏢 Properties Analyzed: {property_count}")
        print(f"📊 Total Suggestions: {total_suggestions}")
        print(f"🔄 Total Moves: {total_moves}")
        print(f"📧 Recipient: {recipient_email}")
        
        try:
            # Create email message
            msg = self._create_consolidated_report_email_message(
                excel_file_path, property_count, analysis_start_date, 
                analysis_end_date, total_suggestions, total_moves, excel_success
            )
            
            # Add Excel attachment if file exists and was created successfully
            if excel_success and os.path.exists(excel_file_path):
                self._add_excel_attachment(msg, excel_file_path)
                print(f"✅ Excel file attached: {os.path.basename(excel_file_path)}")
            else:
                print(f"⚠️  No Excel file to attach (success: {excel_success}, exists: {os.path.exists(excel_file_path) if excel_file_path else False})")
            
            # Send email
            success = self._send_email(msg)
            
            if success:
                self.emails_sent += 1
                print(f"✅ Consolidated report email sent successfully")
            else:
                self.emails_failed += 1
                print(f"❌ Consolidated report email failed to send")
            
            return success
            
        except Exception as e:
            self.emails_failed += 1
            error_msg = f"Consolidated report email error: {str(e)}"
            self.email_errors.append(error_msg)
            print(f"💥 {error_msg}")
            return False

    def _create_consolidated_report_email_message(self, excel_file_path: str, property_count: int,
                                                analysis_start_date, analysis_end_date, 
                                                total_suggestions: int, total_moves: int,
                                                excel_success: bool) -> MIMEMultipart:
        """Create the consolidated report email message with HTML content"""
        
        # Get recipient email from environment variable
        recipient_email = os.environ.get('CONSOLIDATED_EMAIL_RECIPIENT', 'operations@discoveryparks.com.au')
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f'"{self.sender_display_name}" <{self.sender_email}>'
        msg['To'] = recipient_email
        msg['Subject'] = f"RMS Multi-Property Defragmentation Analysis Report - {analysis_start_date.strftime('%d/%m/%Y')} to {analysis_end_date.strftime('%d/%m/%Y')}"
        
        # Create HTML content
        html_content = self._create_consolidated_report_html_content(
            excel_file_path, property_count, analysis_start_date, 
            analysis_end_date, total_suggestions, total_moves, excel_success
        )
        
        msg.attach(MIMEText(html_content, 'html'))
        return msg

    def _create_consolidated_report_html_content(self, excel_file_path: str, property_count: int,
                                               analysis_start_date, analysis_end_date, 
                                               total_suggestions: int, total_moves: int,
                                               excel_success: bool) -> str:
        """Create HTML content for consolidated report email"""
        
        # Format dates
        start_date_str = analysis_start_date.strftime('%d/%m/%Y')
        end_date_str = analysis_end_date.strftime('%d/%m/%Y')
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Create HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #F47425; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #F47425; padding: 15px; margin: 15px 0; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RMS Multi-Property Defragmentation Analysis Report</h1>
                <h2>Consolidated Summary</h2>
            </div>
            
            <div class="content">
                <div class="summary-box">
                    <h3>📋 Analysis Summary</h3>
                    <p><strong>Analysis Period:</strong> {start_date_str} to {end_date_str}</p>
                    <p><strong>Properties Analyzed:</strong> {property_count}</p>
                    <p><strong>Total Move Suggestions:</strong> {total_suggestions}</p>
                    <p><strong>Total Daily Moves:</strong> {total_moves}</p>
                    <p><strong>Excel Report:</strong> {'✅ Generated successfully' if excel_success else '❌ Generation failed'}</p>
                    <p><strong>Analysis Time:</strong> {current_time}</p>
                </div>
                
                <div class="summary-box">
                    <h3>📊 Report Contents</h3>
                    <p><strong>Sheet 1: Consolidated Daily Moves</strong></p>
                    <ul>
                        <li>Daily heatmap showing move opportunities for each property</li>
                        <li>Move counts and strategic importance levels</li>
                        <li>Row and column totals for easy analysis</li>
                        <li>Color-coded importance levels (High/Medium/Low/None)</li>
                    </ul>
                    
                    <p><strong>Sheet 2: Suggested Moves</strong></p>
                    <ul>
                        <li>Complete list of all suggested moves across all properties</li>
                        <li>Sorted by property code and move order</li>
                        <li>Detailed implementation guidance</li>
                    </ul>
                </div>
                
                <div class="summary-box">
                    <h3>🎯 Implementation Notes</h3>
                    <ul>
                        <li>Review the daily heatmap to identify high-priority dates</li>
                        <li>Focus on properties with High/Medium importance moves</li>
                        <li>Implement moves in category-based order within each property</li>
                        <li>Consider the cumulative effect of multiple moves</li>
                    </ul>
                </div>
                
                <div class="summary-box">
                    <h3>📧 Contact Information</h3>
                    <p><strong>Operations Systems Manager:</strong> Mr Tim Curtis</p>
                    <p><strong>Email:</strong> operations@discoveryparks.com.au</p>
                    <p><strong>Generated by:</strong> RMS Multi-Property Defragmentation Analyzer</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This email was automatically generated by the Discovery Parks Multi-Property Defragmentation Analysis System.</p>
                <p>Please review the attached Excel file for detailed analysis and implementation guidance.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content

    def _add_excel_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add Excel file as attachment"""
        
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            # Add header for file attachment
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            print(f"⚠️  Error attaching file {file_path}: {e}")

    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email via Gmail SMTP"""
        
        try:
            # Create secure SSL context with certificate verification disabled
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to Gmail SMTP server
            print(f"📡 Connecting to Gmail SMTP...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                
                # Login with app password
                print(f"🔐 Authenticating with Gmail...")
                server.login(self.sender_email, self.app_password)
                
                # Send email
                print(f"📤 Sending email...")
                text = msg.as_string()
                recipient_email = msg['To']
                server.sendmail(self.sender_email, recipient_email, text)
                
                return True
                
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {e}"
            self.email_errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipient email refused: {e}"
            self.email_errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
            
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"SMTP server disconnected: {e}"
            self.email_errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
            
        except Exception as e:
            error_msg = f"Email sending error: {e}"
            self.email_errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def get_email_stats(self) -> Dict:
        """Get email sending statistics"""
        return {
            'emails_sent': self.emails_sent,
            'emails_failed': self.emails_failed,
            'success_rate': (self.emails_sent / (self.emails_sent + self.emails_failed) * 100) if (self.emails_sent + self.emails_failed) > 0 else 0,
            'errors': self.email_errors
        }

    def print_email_summary(self):
        """Print email sending summary"""
        stats = self.get_email_stats()
        
        print(f"\n📧 EMAIL SENDING SUMMARY:")
        print("=" * 40)
        print(f"✅ Emails Sent: {stats['emails_sent']}")
        print(f"❌ Emails Failed: {stats['emails_failed']}")
        print(f"📈 Success Rate: {stats['success_rate']:.1f}%")
        
        if stats['errors']:
            print(f"\n⚠️  Email Errors:")
            for error in stats['errors']:
                print(f"   • {error}") 