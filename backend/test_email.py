#!/usr/bin/env python3
"""
Test script for email notification functionality
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_configuration():
    """Test email configuration and send a test email"""
    
    # Get email configuration
    email_enabled = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    username = os.getenv('EMAIL_USERNAME', 'amfogelson@gmail.com')
    password = os.getenv('EMAIL_PASSWORD', 'jhzu jiar pswo yqqt')
    email_from = os.getenv('EMAIL_FROM', 'amfogelson@gmail.com')
    email_to = os.getenv('EMAIL_TO', 'amfogelson@gmail.com')
    
    print("Email Configuration Test")
    print("=" * 40)
    print(f"Email Enabled: {email_enabled}")
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'Not set'}")
    print(f"From Email: {email_from}")
    print(f"To Email: {email_to}")
    print()
    
    if not email_enabled:
        print("❌ Email notifications are disabled")
        print("Set ENABLE_EMAIL_NOTIFICATIONS=true in your .env file")
        return False
    
    if not all([username, password, email_from, email_to]):
        print("❌ Email configuration incomplete")
        print("Please set all required email environment variables")
        return False
    
    try:
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = "Icon Manager - Email Test"
        
        body = f"""
This is a test email from the Icon Manager application.

Test Details:
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- SMTP Server: {smtp_server}
- Port: {smtp_port}

If you receive this email, the email notification system is working correctly!

Best regards,
Icon Manager System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print("Attempting to send test email...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        text = msg.as_string()
        server.sendmail(email_from, email_to, text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"Check your inbox at: {email_to}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        print("\nTroubleshooting tips:")
        print("1. For Gmail, make sure you're using an App Password")
        print("2. Check that your email and password are correct")
        print("3. Verify that 2-factor authentication is enabled for Gmail")
        print("4. Make sure the SMTP server and port are correct")
        return False

if __name__ == "__main__":
    test_email_configuration() 