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
STATUS_DATE_MAP = {
    'Inquiry': 'inquiry_date',
    'Registration': 'registration_date',
    'Admission Test': 'admission_test_date',
    'Admission Offered': 'admission_offered_date',
    'Admission Confirmed': 'admission_confirmed_date',
    'Rejected': 'rejected_date',
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
                student_name=row['student_name'],
                parent_name=row['parent_name'],
                mobile_number=row['mobile_number'],
                # email=row['email'] if pd.notna(row['email']) else None,
                address=row['address'] if pd.notna(row['address']) else None,
                block=row['block'],
                location_panchayat=row['location_panchayat'],
                inquiry_source=row['inquiry_source'],
                student_class=row['student_class'],
                status=row['status'],
                remarks=row['remarks'] if pd.notna(row['remarks']) else None,
                follow_up_date=parse_custom_date(row['follow_up_date']),
                assigned_agent_id = 4
            )

            # print(f"➡️ follow_up_date = {lead.follow_up_date}")

            status_date_field = STATUS_DATE_MAP.get(row['status'])
            if status_date_field and pd.notna(row['status_date']):
                setattr(lead, status_date_field, parse_custom_date(row['status_date']))

            lead.save()
            # print("+++++++++++++++> lead = ",lead)
            # print(f"✅ Record saved for: {row['student_name']}")
        
        except Exception as e:
            print(f"❌ Error saving record for: {row['student_name']}, Error: {e}")



if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dejawoo_data.xlsx')

    if os.path.exists(file_path):
        print("🚀 Importing data...")
        import_data_from_excel(file_path)
        print("✅ Import completed!")
    else:
        print(f"❌ File not found at path: {file_path}")
