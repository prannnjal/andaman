import os
import sys
import django
import pandas as pd
from datetime import datetime

# Add project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_inquiry_system.settings')
django.setup()

from inquiries.models import Lead

# Status-to-date field mapping
STATUS_DATE_EXCEL_MAP = {
    'Inquiry': 'Inquiry Date',
    'Registration': 'Registration Date',
    'Admission Test': 'Admission Test Date',
    'Admission Offered': 'Admission Offered Date',
    'Admission Confirmed': 'Admission Confirmed Date',
    'Rejected': 'Rejected Date',
}

# Custom date parser to handle both string and float-based Excel dates
def parse_custom_date(date_value):
    try:
        # print("====================> date value = ", date_value)

        if pd.isna(date_value) or date_value is None:
            return None

        if isinstance(date_value, datetime):
            # If it's already a datetime object, return the date part
            return date_value.date()

        if isinstance(date_value, float) or isinstance(date_value, int):
            # Convert Excel date format (numeric)
            return pd.to_datetime(date_value, origin='1899-12-30', unit='D').date()
        
        if isinstance(date_value, str):
            date_value = date_value.strip()
            return datetime.strptime(date_value, '%d-%m-%Y').date()

        return None
    except Exception as e:
        print(f"❌ Error parsing date: {date_value} → {e}")
        return None


def import_data_from_excel(file_path):
    df = pd.read_excel(file_path)

    for index, row in df.iterrows():
        try:
            # Debugging step:
            # print(f"🛠️ Row {index + 1}: {row.to_dict()}")

            lead = Lead(
                student_name=row['Student Name'],
                parent_name=row['Parent Name'],
                mobile_number=row['Mobile Number'],
                # email=row['Email'] if pd.notna(row['Email']) else None,
                address=row['Address'] if pd.notna(row['Address']) else None,
                block=row['Block'],
                location_panchayat=row['Location/Panchayat'],
                inquiry_source=row['Inquiry Source'],
                student_class=row['Student Class'],
                status=row['Status'],
                remarks=row['Remarks'] if pd.notna(row['Remarks']) else None,
                follow_up_date=parse_custom_date(row['Follow-up Date']),
                assigned_agent_id = 4
            )

            # print(f"➡️ follow_up_date = {lead.follow_up_date}")

            status_date_field_excel = STATUS_DATE_EXCEL_MAP.get(row['Status'])
            status_date_field_djsngo_model = status_date_field_excel.strip().lower().replace(' ', '_')
            status_date_value_excel = row[status_date_field_excel]
            
            if status_date_field_excel and pd.notna(status_date_value_excel):
                setattr(lead, status_date_field_djsngo_model, parse_custom_date(status_date_value_excel))

            lead.save()
            # print("+++++++++++++++> lead = ",lead)
            # print(f"✅ Record saved for: {row['Student Name']}")
        
        except Exception as e:
            print(f"❌ Error saving record for: {row['Student Name']}, Error: {e}")



if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inquiries (1).xlsx')

    if os.path.exists(file_path):
        print("🚀 Importing data...")
        import_data_from_excel(file_path)
        print("✅ Import completed!")
    else:
        print(f"❌ File not found at path: {file_path}")