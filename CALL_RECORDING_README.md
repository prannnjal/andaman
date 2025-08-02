# Call Recording Feature

This document describes the call recording functionality that has been implemented for the CRM School system.

## Overview

The call recording feature allows agents to upload call recordings when updating leads and automatically extracts the call duration from the uploaded audio/video files.

## Features

### 1. Call Recording Upload
- Agents can upload call recordings when updating lead information
- Supports multiple audio/video formats: MP3, WAV, M4A, AAC, OGG, MP4, AVI, MOV
- File size limit: 50MB
- Automatic duration extraction from uploaded files

### 2. Call Duration Extraction
- Automatically extracts call duration from uploaded files using the `mutagen` library
- Supports various audio formats for accurate duration detection
- Displays duration in readable format (MM:SS or HH:MM:SS)

### 3. Call Recording Management
- View all call recordings for a specific lead
- Play recordings directly in the browser
- Download recordings
- Delete recordings (with permission checks)
- Add notes to each recording

### 4. Security & Permissions
- Only agents assigned to a lead can upload recordings for that lead
- Admins can view and manage all recordings
- Proper file validation and security checks

## Database Schema

### CallRecording Model
```python
class CallRecording(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='call_recordings')
    recording_file = models.FileField(upload_to='call_recordings/')
    duration = models.DurationField(blank=True, null=True)
    call_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
```

## File Structure

### New Files Created
- `inquiries/utils.py` - Utility functions for audio duration extraction
- `CALL_RECORDING_README.md` - This documentation file

### Modified Files
- `inquiries/models.py` - Added CallRecording model
- `inquiries/forms.py` - Added CallRecordingForm
- `inquiries/views.py` - Added API views for call recording management
- `inquiries/urls.py` - Added URL patterns for API endpoints
- `inquiries/templates/inquiries/add_update_lead.html` - Added call recording UI
- `school_inquiry_system/settings.py` - Added media settings
- `school_inquiry_system/urls.py` - Added media URL patterns
- `requirements.txt` - Added mutagen dependency

## Installation & Setup

### 1. Install Dependencies
```bash
pip install mutagen
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Media Directory
```bash
mkdir media
mkdir media/call_recordings
```

## Usage

### For Agents

1. **Upload Call Recording**
   - Go to the lead update page
   - Scroll to the "Call Recording" section
   - Click "Choose File" and select your audio/video file
   - Add optional notes about the call
   - The duration will be automatically extracted and displayed
   - Submit the form to save the recording

2. **View Previous Recordings**
   - Previous call recordings for the lead will be displayed
   - Click the play button to listen to recordings
   - Download recordings using the download button
   - Delete recordings using the delete button (if you have permission)

### For Admins

- Admins can view and manage all call recordings across all leads
- Full access to upload, download, and delete recordings

## API Endpoints

### Get Lead Recordings
```
GET /inquiries/api/lead/{lead_id}/recordings/
```
Returns JSON with all call recordings for a specific lead.

### Delete Recording
```
POST /inquiries/api/recording/{recording_id}/delete/
```
Deletes a specific call recording (requires CSRF token).

## Technical Details

### Audio Duration Extraction
The system uses the `mutagen` library to extract duration from various audio formats:

- **MP3**: Uses `mutagen.mp3.MP3`
- **WAV**: Uses `mutagen.wave.WAVE`
- **OGG**: Uses `mutagen.oggvorbis.OggVorbis`
- **Other formats**: Uses `mutagen.File` for generic support

### File Storage
- Files are stored in `media/call_recordings/`
- File paths are automatically generated to avoid conflicts
- Files are served through Django's media handling in development

### Security Features
- File type validation (only allowed extensions)
- File size limits (50MB maximum)
- Permission-based access control
- CSRF protection for all operations

## Error Handling

The system handles various error scenarios:

- **Invalid file types**: Shows validation error
- **File too large**: Shows size limit error
- **Duration extraction failure**: Continues without duration
- **Permission denied**: Returns 403 error
- **File not found**: Returns 404 error

## Testing

Run the test script to verify functionality:
```bash
python test_call_recording.py
```

This will test:
- Duration utility functions
- CallRecording model operations
- Lead-CallRecording relationships

## Browser Compatibility

The audio player supports all modern browsers:
- Chrome, Firefox, Safari, Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Enhancements

Potential improvements for the future:
- Audio transcription using speech-to-text
- Call quality analysis
- Integration with phone systems
- Call recording analytics
- Bulk upload functionality
- Advanced search and filtering

## Troubleshooting

### Common Issues

1. **Duration not extracted**
   - Check if the file format is supported
   - Verify the file is not corrupted
   - Check server logs for mutagen errors

2. **File upload fails**
   - Verify file size is under 50MB
   - Check file extension is allowed
   - Ensure media directory has write permissions

3. **Audio player not working**
   - Check browser compatibility
   - Verify file URL is accessible
   - Check if file format is supported by browser

### Debug Mode
Enable Django debug mode to see detailed error messages:
```python
DEBUG = True
```

## Support

For issues or questions about the call recording feature, please check:
1. This documentation
2. Django logs for error messages
3. Browser console for JavaScript errors
4. File permissions and storage settings 