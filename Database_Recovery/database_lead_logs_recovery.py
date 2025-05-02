import os
import django
import mysql.connector
from dotenv import load_dotenv
import sys
import json

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
from inquiries.models import Lead, CustomUser, LeadLogs

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
old_cursor.execute("SELECT * FROM inquiries_leadlogs")

old_users = old_cursor.fetchall()

# Insert into new DB using Django ORM
for user in old_users:
    try:
        # Fetch the assigned_agent and admin_assigned as CustomUser instances
        changed_by_user = CustomUser.objects.filter(id=user.get('changed_by_id')).first()
        lead = Lead.objects.filter(id=user.get('lead_id')).first()

        LeadLogs.objects.create( 
            lead=lead,
            changed_by=changed_by_user,            
            changed_at=user['changed_at'],
            previous_data=json.loads(user['previous_data']),
            new_data=json.loads(user['new_data'])
        )
        print(f"Migrated log with id: {user['id']}")
    except Exception as err:
        print(f"Error inserting log with id: {user['id']}: {err}")

# Cleanup
old_cursor.close()
old_db.close()
print("Data transfer complete!")