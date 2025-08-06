import os
import json
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Lead, CustomUser
from datetime import datetime
import pandas as pd

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

class GoogleSheetsService:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using Service Account or OAuth2"""
        # First try Service Account (preferred method)
        service_account_path = os.path.join(settings.BASE_DIR, 'service-account-key.json')
        
        if os.path.exists(service_account_path):
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    service_account_path, scopes=SCOPES
                )
                self.service = build('sheets', 'v4', credentials=self.creds)
                return
            except Exception as e:
                print(f"Service account authentication failed: {e}")
        
        # Fallback to OAuth2
        token_path = os.path.join(settings.BASE_DIR, 'token.json')
        credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        
        if os.path.exists(token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                # If token is corrupted, delete it and start fresh
                os.remove(token_path)
                self.creds = None
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    # If refresh fails, delete token and start fresh
                    if os.path.exists(token_path):
                        os.remove(token_path)
                    self.creds = None
            
            if not self.creds:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        "credentials.json file not found. Please download it from Google Cloud Console "
                        "and place it in the project root directory. For better reliability, consider using a service account."
                    )
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    raise Exception(f"Authentication failed: {str(e)}")
            
            # Save the credentials for the next run
            try:
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
            except Exception as e:
                # If we can't save the token, continue anyway
                pass
        
        try:
            self.service = build('sheets', 'v4', credentials=self.creds)
        except Exception as e:
            raise Exception(f"Failed to build Google Sheets service: {str(e)}")
    
    def read_sheet(self, spreadsheet_id, range_name):
        """Read data from Google Sheet"""
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def validate_lead_data(self, row_data, headers):
        """Validate lead data from Google Sheets (allow empty optional fields)"""
        # Pad row_data to match headers length (so missing optional fields are treated as empty)
        if len(row_data) < len(headers):
            row_data = row_data + [''] * (len(headers) - len(row_data))
        # Only check required fields
        required_fields = ['student_name', 'parent_name', 'mobile_number', 'email', 'address', 'block', 'location_panchayat', 'inquiry_source', 'student_class']
        for field in required_fields:
            if field in headers:
                field_index = headers.index(field)
                if field_index >= len(row_data) or not row_data[field_index]:
                    return False, f"Required field '{field}' is empty"
        return True, "Data is valid"
    
    def parse_date(self, date_str):
        """Parse date string from Google Sheets"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            date_formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%Y',
                '%m-%d-%Y',
                '%Y/%m/%d'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
            
            # If none of the formats work, return None
            return None
        except:
            return None
    
    def import_leads_from_sheet(self, spreadsheet_id, range_name, admin_user):
        """Import leads from Google Sheets"""
        try:
            # Read data from Google Sheet
            sheet_data = self.read_sheet(spreadsheet_id, range_name)
            
            if not sheet_data:
                return {
                    'success': False,
                    'message': 'No data found in the specified range',
                    'imported_count': 0,
                    'errors': []
                }
            
            headers = sheet_data[0]
            data_rows = sheet_data[1:]
            
            # Validate headers
            expected_headers = [
                'student_name', 'parent_name', 'mobile_number', 'email', 'address',
                'block', 'location_panchayat', 'inquiry_source', 'student_class',
                'status', 'remarks', 'inquiry_date', 'registration_date',
                'admission_test_date', 'admission_offered_date', 'admission_confirmed_date',
                'rejected_date', 'follow_up_date'
            ]
            
            # Check if all required headers are present
            missing_headers = [h for h in expected_headers[:9] if h not in headers]
            if missing_headers:
                return {
                    'success': False,
                    'message': f'Missing required headers: {", ".join(missing_headers)}',
                    'imported_count': 0,
                    'errors': []
                }
            
            imported_count = 0
            errors = []
            
            for row_index, row_data in enumerate(data_rows, start=2):  # Start from 2 because row 1 is headers
                try:
                    # Validate row data
                    is_valid, validation_message = self.validate_lead_data(row_data, headers)
                    if not is_valid:
                        errors.append(f"Row {row_index}: {validation_message}")
                        continue
                    
                    # Create lead data dictionary
                    lead_data = {}
                    for i, header in enumerate(headers):
                        if i < len(row_data):
                            lead_data[header] = row_data[i].strip() if row_data[i] else ''
                    
                    # Check if lead already exists (by mobile number and email)
                    existing_lead = Lead.objects.filter(
                        mobile_number=lead_data.get('mobile_number', ''),
                        email=lead_data.get('email', '')
                    ).first()
                    
                    if existing_lead:
                        errors.append(f"Row {row_index}: Lead with mobile {lead_data.get('mobile_number')} and email {lead_data.get('email')} already exists")
                        continue
                    
                    # Create new lead
                    lead = Lead(
                        student_name=lead_data.get('student_name', ''),
                        parent_name=lead_data.get('parent_name', ''),
                        mobile_number=lead_data.get('mobile_number', ''),
                        email=lead_data.get('email', ''),
                        address=lead_data.get('address', ''),
                        block=lead_data.get('block', ''),
                        location_panchayat=lead_data.get('location_panchayat', ''),
                        inquiry_source=lead_data.get('inquiry_source', 'Advertisement'),
                        student_class=lead_data.get('student_class', 'Play School'),
                        status=lead_data.get('status', 'Inquiry'),
                        remarks=lead_data.get('remarks', ''),
                        inquiry_date=self.parse_date(lead_data.get('inquiry_date')),
                        registration_date=self.parse_date(lead_data.get('registration_date')),
                        admission_test_date=self.parse_date(lead_data.get('admission_test_date')),
                        admission_offered_date=self.parse_date(lead_data.get('admission_offered_date')),
                        admission_confirmed_date=self.parse_date(lead_data.get('admission_confirmed_date')),
                        rejected_date=self.parse_date(lead_data.get('rejected_date')),
                        follow_up_date=self.parse_date(lead_data.get('follow_up_date')),
                        admin_assigned=admin_user
                    )
                    
                    # Auto-assign agent
                    lead.auto_assign_agent()
                    lead.save()
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_index}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Successfully imported {imported_count} leads',
                'imported_count': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error importing leads: {str(e)}',
                'imported_count': 0,
                'errors': [str(e)]
            }
    
    def get_sheet_info(self, spreadsheet_id):
        """Get information about the Google Sheet"""
        try:
            sheet = self.service.spreadsheets()
            result = sheet.get(spreadsheetId=spreadsheet_id).execute()
            
            sheet_info = {
                'title': result.get('properties', {}).get('title', ''),
                'sheets': []
            }
            
            for sheet_data in result.get('sheets', []):
                sheet_info['sheets'].append({
                    'title': sheet_data.get('properties', {}).get('title', ''),
                    'sheet_id': sheet_data.get('properties', {}).get('sheetId', ''),
                    'grid_properties': sheet_data.get('properties', {}).get('gridProperties', {})
                })
            
            return sheet_info
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None 