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
from inquiries.models import Agent

# Get the CustomUser model
CustomUser = get_user_model()

# List of agents to create
agents_data = [
    # {"name": "Uzma", "email": "uzma95427@gmail.com"},
    # {"name": "Sangam", "email": "sangamsanjana76@gmai.com"},
    # {"name": "Anisha", "email": "anishapantha91@gmail.com"},
    # {"name": "Praveen Rifat", "email": "praveenrifat81@gmail.com"},
    # {"name": "Chandan", "email": "eng.chandan@gmail.com"},
    # {"name": "Swati", "email": "swati.og@gmail.com"},
    {"name": "Sushant", "email": "sushant889427@gmail.com"},
]

def create_agents():
    for agent_data in agents_data:
        try:
            # Create user if not exists
            user, created = CustomUser.objects.get_or_create(
                email=agent_data['email'],
                defaults={
                    "username": agent_data['email'].split('@')[0],
                    "is_staff": False,  # Mark as non-staff agent
                }
            )

            if created:
                print(f"✅ User created: {user.email}")
            else:
                print(f"⚠️ User already exists: {user.email}")

            # Create Agent instance if not exists
            agent, agent_created = Agent.objects.get_or_create(
                user=user,
                defaults={
                    "name": agent_data['name'],
                }
            )

            if agent_created:
                print(f"✅ Agent created: {agent.name} ({agent.user.email})")
            else:
                print(f"⚠️ Agent already exists: {agent.name} ({agent.user.email})")

        except Exception as e:
            print(f"❌ Error creating agent for {agent_data['name']} → {e}")

if __name__ == "__main__":
    print("🚀 Creating agents...")
    create_agents()
    print("✅ Agent creation completed!")
