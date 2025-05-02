import os
import django
import mysql.connector
from dotenv import load_dotenv
import sys

# Set up paths and environment
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ENV_PATH = os.path.join(PARENT_DIR, ".env")


# ✅ Add project root to sys.path so imports work
sys.path.insert(0, PARENT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_inquiry_system.settings")
os.chdir(PARENT_DIR)  # Important to ensure relative imports and settings work
django.setup()

# Now import Django models
from inquiries.models import Lead, CustomUser

# Load .env variables
load_dotenv(ENV_PATH, override=True)

# Database Credentials
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("HOST")

# Connect to old DB
old_db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database="inquiries_testing_3"
)

old_cursor = old_db.cursor(dictionary=True)

# Fetch data from old DB
old_cursor.execute("SELECT * FROM inquiries_lead")

old_users = old_cursor.fetchall()

# Insert into new DB using Django ORM
for user in old_users:
    try:
        # Fetch the assigned_agent and admin_assigned as CustomUser instances
        assigned_agent = CustomUser.objects.filter(id=user.get('assigned_agent_id')).first()
        admin_assigned = CustomUser.objects.filter(id=user.get('admin_assigned_id')).first()

        Lead.objects.create(
            id=user['id'],
            student_name=user['student_name'],
            parent_name=user['parent_name'],            
            mobile_number=user['mobile_number'],
            email=user['email'],
            address=user['address'],
            block=user['block'],
            location_panchayat=user['location_panchayat'],
            inquiry_source=user['inquiry_source'],
            student_class=user['student_class'],
            status=user['status'],
            remarks=user['remarks'],
            inquiry_date=user['inquiry_date'],
            registration_date=user['registration_date'],
            admission_test_date=user['admission_test_date'],
            admission_offered_date=user['admission_offered_date'],
            admission_confirmed_date=user['admission_confirmed_date'],
            rejected_date=user['rejected_date'],
            follow_up_date=user['follow_up_date'],
            admin_assigned=admin_assigned,
            assigned_agent=assigned_agent,
        )
        print(f"Migrated user with id: {user['id']}")
    except Exception as err:
        print(f"Error inserting user with id: {user['id']}: {err}")

# Cleanup
old_cursor.close()
old_db.close()
print("Data transfer complete!")