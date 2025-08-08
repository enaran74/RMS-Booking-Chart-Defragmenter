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
        
        # Test recipient (for testing purposes)
        self.test_recipient = os.environ.get('TEST_RECIPIENT', "***REMOVED***")
        
        # Email statistics
        self.emails_sent = 0
        self.emails_failed = 0
        self.email_errors = []
        
        print(f"📧 Email Sender initialized")
        print(f"   📤 From: {self.sender_email}")
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
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Defragmentation Analysis - {property_name} - {analysis_start_date.strftime('%d/%m/%Y')} to {analysis_end_date.strftime('%d/%m/%Y')}"
        
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
                <h1>RMS Booking Chart Defragmentation Analysis for:</h1>
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