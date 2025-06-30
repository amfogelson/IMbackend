# Icon Manager Backend

FastAPI backend for the Icon Manager application.

## Features

- SVG icon management and customization
- Color updates for icon groups
- Greyscale conversion for colorful icons
- PNG export functionality
- Flag management
- **Email notifications for feedback submissions** ✨

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure email notifications (optional):
```bash
cp env.example .env
# Edit .env with your email settings
# See EMAIL_SETUP.md for detailed instructions
```

3. Run the server:
```bash
python main.py
```

## Email Notifications

The backend now supports email notifications when users submit feedback. This feature:

- Sends immediate notifications to administrators
- Includes feedback details (ID, type, message, timestamp)
- Supports multiple email providers (Gmail, Outlook, etc.)
- Can be easily enabled/disabled via environment variables

### Quick Setup

1. Copy the environment template:
```bash
cp env.example .env
```

2. Configure your email settings in `.env`

3. Test the configuration:
```bash
python test_email.py
```

For detailed setup instructions, see [EMAIL_SETUP.md](EMAIL_SETUP.md).

## API Endpoints

- `GET /icons` - Get all icon folders
- `GET /colorful-icons` - Get all colorful icon folders
- `GET /flags` - Get all flag files
- `POST /update_color` - Update icon colors
- `POST /greyscale` - Convert colorful icons to greyscale
- `POST /revert` - Revert greyscale icons to color
- `POST /export-png` - Export icons as PNG
- `POST /feedback` - Submit feedback (with email notification)
- `GET /feedback` - Get all feedback (admin only)
- `PUT /feedback/{id}/status` - Update feedback status (admin only)

## Environment Variables

- `ENABLE_EMAIL_NOTIFICATIONS` - Enable/disable email notifications
- `EMAIL_SMTP_SERVER` - SMTP server address
- `EMAIL_SMTP_PORT` - SMTP server port
- `EMAIL_USERNAME` - Email username
- `EMAIL_PASSWORD` - Email password/app password
- `EMAIL_FROM` - From email address
- `EMAIL_TO` - Admin email address for notifications

## Development

The backend uses FastAPI with automatic reloading. Changes to `main.py` will trigger a server restart. 