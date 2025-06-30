# Email Notification Setup Guide

This guide will help you set up email notifications for the Icon Manager feedback system.

## Overview

The Icon Manager now supports email notifications when users submit feedback. Administrators will receive an email notification containing the feedback details whenever a new submission is made.

## Setup Instructions

### 1. Create Environment File

Copy the example environment file and configure it with your email settings:

```bash
cp env.example .env
```

### 2. Configure Email Settings

Edit the `.env` file with your email configuration:

```env
# Email Configuration
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=admin@yourcompany.com

# Enable email notifications
ENABLE_EMAIL_NOTIFICATIONS=true
```

### 3. Gmail Setup (Recommended)

If using Gmail, you'll need to:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Navigate to Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use this password in your `.env` file (not your regular Gmail password)

### 4. Other Email Providers

For other email providers, adjust the SMTP settings:

**Outlook/Hotmail:**
```env
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
```

**Yahoo:**
```env
EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
```

**Custom SMTP Server:**
```env
EMAIL_SMTP_SERVER=your-smtp-server.com
EMAIL_SMTP_PORT=587
```

### 5. Test Email Configuration

Run the test script to verify your email setup:

```bash
cd IMbackend/backend
python test_email.py
```

This will:
- Check your email configuration
- Send a test email
- Provide troubleshooting tips if there are issues

### 6. Install Dependencies

Make sure you have the required dependencies:

```bash
pip install -r requirements.txt
```

## Email Notification Features

### What Gets Sent

When a user submits feedback, an email notification includes:
- Feedback ID
- Feedback type (New Addition, UX/UI Improvement, Bug Report)
- Timestamp
- Full feedback message
- Instructions for accessing the admin interface

### Email Format

```
Subject: New Feedback Submission - [Type] (ID: [ID])

New feedback has been submitted to the Icon Manager application.

Feedback Details:
- ID: [ID]
- Type: [Type]
- Timestamp: [Timestamp]
- Message: [Message]

You can view and manage this feedback through the admin interface.

Best regards,
Icon Manager System
```

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - For Gmail: Use an App Password, not your regular password
   - Check that 2-factor authentication is enabled
   - Verify username and password are correct

2. **"Connection refused"**
   - Check SMTP server and port settings
   - Verify firewall settings
   - Try different ports (587, 465, 25)

3. **"Email notifications disabled"**
   - Set `ENABLE_EMAIL_NOTIFICATIONS=true` in your `.env` file

4. **"Configuration incomplete"**
   - Make sure all required email variables are set
   - Check that `.env` file is in the correct location

### Testing

Use the test script to diagnose issues:

```bash
python test_email.py
```

The script will show your current configuration and attempt to send a test email.

## Security Considerations

1. **Never commit your `.env` file** to version control
2. **Use App Passwords** instead of regular passwords for Gmail
3. **Restrict access** to the admin email address
4. **Consider using environment variables** in production deployments

## Production Deployment

For production deployments:

1. Set environment variables in your hosting platform
2. Use a dedicated email service (SendGrid, Mailgun, etc.) for better reliability
3. Consider rate limiting to prevent spam
4. Monitor email delivery rates

## Disabling Email Notifications

To disable email notifications, set:

```env
ENABLE_EMAIL_NOTIFICATIONS=false
```

Or simply don't set the email configuration variables.

## Support

If you encounter issues:

1. Check the test script output for specific error messages
2. Verify your email provider's SMTP settings
3. Test with a simple email client first
4. Check server logs for detailed error information 