# Email Configuration Setup Guide for Proposal System

## Problem: "Mail Not Sent" Issue

The issue you're experiencing is due to missing email configuration. The system requires Gmail SMTP credentials to send emails.

## 🚨 **Current Issue**
Your environment variables `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are not set, which is why emails aren't being sent.

## 📧 **How to Fix Email Configuration**

### Step 1: Create Environment Variables

**On Windows (PowerShell):**
```powershell
# Set environment variables for current session
$env:EMAIL_HOST_USER="your_email@gmail.com"
$env:EMAIL_HOST_PASSWORD="your_app_specific_password"

# Set permanently for user
[Environment]::SetEnvironmentVariable("EMAIL_HOST_USER", "your_email@gmail.com", "User")
[Environment]::SetEnvironmentVariable("EMAIL_HOST_PASSWORD", "your_app_specific_password", "User")
```

**On Windows (Command Prompt):**
```cmd
set EMAIL_HOST_USER=your_email@gmail.com
set EMAIL_HOST_PASSWORD=your_app_specific_password
```

### Step 2: Get Gmail App-Specific Password

1. **Enable 2-Factor Authentication:**
   - Go to [Google Account Settings](https://myaccount.google.com)
   - Click "Security" → "2-Step Verification"
   - Follow the setup process

2. **Generate App Password:**
   - In Google Account Settings → Security
   - Click "2-Step Verification"
   - Scroll down to "App passwords"
   - Select "Mail" and your device
   - Copy the 16-character password (use this as `EMAIL_HOST_PASSWORD`)

### Step 3: Configure Your Credentials

Replace these values:
- `your_email@gmail.com` → Your actual Gmail address
- `your_app_specific_password` → The 16-character password from Step 2

### Step 4: Restart Django Server

After setting environment variables:
```bash
python manage.py runserver
```

## 🧪 **Test Email Configuration**

1. Go to any proposal sending page
2. Click the **"Test Email"** button (yellow button)
3. Enter a test email address
4. Click "Send Test Email"
5. Check if you receive the test email

## 📋 **Common Issues & Solutions**

### Issue: "EMAIL_HOST_USER not set"
**Solution:** Environment variable not configured
- Follow Step 1 above
- Restart Django server

### Issue: "EMAIL_HOST_PASSWORD not set"
**Solution:** App-specific password not configured
- Follow Step 2 above
- Use the 16-character app password, not your regular Gmail password

### Issue: "Authentication failed"
**Solution:** 
- Ensure 2-Factor Authentication is enabled
- Use app-specific password, not regular password
- Check that EMAIL_HOST_USER is your correct Gmail address

### Issue: "Connection refused"
**Solution:**
- Check internet connection
- Verify Gmail SMTP settings (already configured in Django)
- Try with a different email provider if needed

## 🔧 **Alternative Email Configuration**

If Gmail doesn't work, you can use other email providers by updating `settings.py`:

**For Outlook/Hotmail:**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**For Yahoo:**
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

## ✅ **Verification Steps**

1. Set environment variables ✓
2. Restart Django server ✓
3. Use "Test Email" feature ✓
4. Try sending a proposal ✓

## 📞 **Quick Test**

Run this in your Django shell to test:
```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test email.',
    settings.EMAIL_HOST_USER,
    ['test@example.com'],
    fail_silently=False,
)
```

If this works, your configuration is correct!

## 🎯 **Final Notes**

- Always use app-specific passwords for Gmail
- Never share your EMAIL_HOST_PASSWORD
- Environment variables are case-sensitive
- Restart Django after setting environment variables

Once configured, the proposal system will send professional PDF proposals via email automatically!
