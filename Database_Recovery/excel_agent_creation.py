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

from django.contrib.auth import get_user_model
from inquiries.models import CustomUser

# Get the CustomUser model
CustomUser = get_user_model()

# List of agents to create
agents_data = [
    {"name": "Uzma", "email": "uzma95427@gmail.com", "role": "Agent", "mobile_number":"123"},
    {"name": "Sangam", "email": "sangamsanjana76@gmai.com", "role": "Agent", "mobile_number":"1223"},
    {"name": "Anisha", "email": "anishapantha91@gmail.com", "role": "Agent", "mobile_number":"323"},
    {"name": "Praveen Rifat", "email": "praveenrifat81@gmail.com", "role": "Agent", "mobile_number":"423"},
    {"name": "Chandan", "email": "eng.chandan@gmail.com", "role": "Agent", "mobile_number":"523"},
    {"name": "Swati", "email": "swati.og@gmail.com", "role": "Agent", "mobile_number":"623"},
]

def create_agents():
    for data in agents_data:
        try:
            if not CustomUser.objects.filter(email=data["email"]).exists():
                CustomUser.objects.create_user(
                mobile_number=data["mobile_number"],
                email=data["email"],
                password="12345",
                name=data["name"],
                role=data["role"]
                )
                print(f"✅ Created user: {data['name']}")
            else:
                print(f"⚠️ User with email {data['email']} already exists.")
                
        except Exception as e:
            print("==================> error: ",e)

if __name__ == "__main__":
    print("🚀 Creating agents...")
    create_agents()
    print("✅ Agent creation completed!")