# Google Sheets Integration for CRM School

This integration allows you to import leads directly from Google Sheets into your CRM system.

## Features

- Import leads from Google Sheets with automatic validation
- Preview data before importing
- Automatic agent assignment based on workload
- Duplicate detection and handling
- Support for both OAuth2 and Service Account authentication
- Comprehensive error reporting

## Setup Instructions

### Option 1: Service Account (Recommended - No Verification Required)

**Step 1: Create a Service Account**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `gen-lang-client-0204356111`
3. Navigate to **"APIs & Services"** → **"Credentials"**
4. Click **"Create Credentials"** → **"Service Account"**
5. Fill in the service account details:
   - Name: `crm-sheets-integration`
   - Description: `Service account for CRM Google Sheets integration`
6. Click **"Create and Continue"**
7. Skip the optional steps and click **"Done"**

**Step 2: Create and Download Service Account Key**
1. In the service accounts list, click on your newly created service account
2. Go to the **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **"JSON"** format
5. Click **"Create"** - this will download a JSON file
6. Rename the downloaded file to `service-account-key.json`
7. Place it in your project root directory (same level as `manage.py`)

**Step 3: Share Your Google Sheet**
1. Open your Google Sheet
2. Click **"Share"** in the top right
3. Add the service account email (found in the JSON file, looks like `crm-sheets-integration@gen-lang-client-0204356111.iam.gserviceaccount.com`)
4. Give it **"Viewer"** access
5. Click **"Send"**

### Option 2: OAuth2 (Requires Verification for Production)

**Step 1: Add Test Users**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `gen-lang-client-0204356111`
3. Navigate to **"APIs & Services"** → **"OAuth consent screen"**
4. Scroll down to **"Test users"** section
5. Click **"Add Users"**
6. Add your email: `pranjalkumar445@gmail.com`
7. Click **"Save"**

**Step 2: Use Existing Credentials**
- The `credentials.json` file you already have should work for testing
- For production, you'll need to complete Google's verification process

## Required Sheet Format

Your Google Sheet must have the following headers in the first row:

### Required Headers:
- `student_name` - Student's full name
- `parent_name` - Parent's full name
- `mobile_number` - Contact mobile number
- `email` - Email address
- `address` - Complete address
- `block` - Block/location
- `location_panchayat` - Panchayat location
- `inquiry_source` - Source of inquiry
- `student_class` - Student's class/grade

### Optional Headers:
- `status` - Lead status
- `remarks` - Additional notes
- `inquiry_date` - Date of inquiry (YYYY-MM-DD format)
- `registration_date` - Registration date (YYYY-MM-DD format)
- `admission_test_date` - Admission test date (YYYY-MM-DD format)
- `admission_offered_date` - Date admission was offered (YYYY-MM-DD format)
- `admission_confirmed_date` - Date admission was confirmed (YYYY-MM-DD format)
- `rejected_date` - Date if rejected (YYYY-MM-DD format)
- `follow_up_date` - Follow-up date (YYYY-MM-DD format)

## Usage

### Step 1: Access the Integration
1. Log in as an Admin user
2. Go to Dashboard
3. Click "Google Sheets Import" in the "Manage Inquiries" section

### Step 2: Setup Instructions
1. Follow the setup instructions on the page
2. Download the template if needed
3. Prepare your Google Sheet with the correct headers

### Step 3: Preview Data
1. Go to "Preview Sheet Data"
2. Enter your Sheet ID and range
3. Review the data before importing

### Step 4: Import Leads
1. Go to "Import Leads"
2. Enter your Sheet ID and range
3. Click "Import Leads"
4. Review the results

## Authentication Methods

### Service Account (Recommended)
- **Pros**: No user verification required, works in production, more reliable
- **Cons**: Requires sharing sheets with service account email
- **File**: `service-account-key.json`

### OAuth2
- **Pros**: User-specific access, no need to share sheets
- **Cons**: Requires verification for production use, user must be added as test user
- **File**: `credentials.json`

## Error Handling

The integration includes comprehensive error handling for:
- Authentication failures
- Invalid sheet IDs or ranges
- Missing required fields
- Duplicate leads
- Invalid data formats
- Network connectivity issues

## Security Notes

- Keep your credential files secure
- Don't commit credential files to version control
- Use environment variables for production deployments
- Regularly rotate service account keys
- Monitor API usage in Google Cloud Console

## Troubleshooting

### "Access blocked: sheet has not completed the Google verification process"
**Solution**: Use a service account instead of OAuth2, or add your email as a test user in the OAuth consent screen.

### "credentials.json not found"
**Solution**: Download the credentials file from Google Cloud Console and place it in the project root.

### "Service account authentication failed"
**Solution**: Check that the service account key file is valid and the service account has access to the sheet.

### "Invalid sheet ID"
**Solution**: Verify the sheet ID from the Google Sheets URL and ensure the sheet is shared with the appropriate account.

## API Limits

- Google Sheets API has quotas and rate limits
- Monitor usage in Google Cloud Console
- Consider implementing rate limiting for large imports

## Support

For issues with the Google Sheets integration:
1. Check the error messages in the import results
2. Verify your sheet format matches the requirements
3. Ensure proper authentication setup
4. Check Google Cloud Console for API quotas and errors 