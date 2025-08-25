from django.db import models
from django.contrib.auth.models import User, AbstractUser
import pandas as pd
from django.utils.timezone import now
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import string
import random
import os


# print("======================> os.getcwd = ", os.getcwd())


'''
[('A', 'Block A'), ('B', 'Block B'), ('C', 'Block C')]

Now, in a Django form, the dropdown will show: Block A
But the database will still store "A"
'''

def get_block_choices():
    try:
        # Load block and location_panchayat data from Excel
        file_path = os.path.join(os.path.dirname(__file__), "static", "Location_list.xlsx")
        df = pd.read_excel(file_path)
        block_choices = [(block, block) for block in df["BLOCK"].dropna().unique()]
        block_choices.append(("Other", "Other"))
        return block_choices
    except Exception as e:
        print(f"Warning: Could not load block choices from Excel: {e}")
        return [("Other", "Other")]



def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + '@' + '#'
    return ''.join(random.choices(characters, k=length))


class CustomUserManager(BaseUserManager):
    def create_user(self, mobile_number, email, password=None, **extra_fields):
        if not password:
            password = generate_random_password()
            
        # if not mobile_number:
        #     raise ValueError("Users must have a mobile number")
        
        if not email:
            raise ValueError("Users must have an email")

        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(mobile_number=mobile_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('name', 'Dejawoo Admin')
        extra_fields.setdefault('role', 'Admin')

        return self.create_user(mobile_number, email, password, **extra_fields)
    
    
    
ROLE_CHOICES = [
    ('Admin', 'Admin'),
    ('Agent', 'Agent'),
    ('Viewer', 'Viewer'),
    ('None', 'None'),
]


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=14, unique=True, null=True, blank=True)
    block = models.CharField(max_length=100, blank=True, null=True)
    location_panchayat = models.CharField(max_length=100, blank=True, null=True)
    date_joined = models.DateTimeField(default=now)
    
    # To let admin grant permission to a user:
    expiration_time = models.DateTimeField(default=timezone.make_aware(datetime(9999, 12, 31, 23, 59, 59)))  # Make it timezone-aware    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Viewer')
    name = models.CharField(max_length=100)

    # Removing the username field entirely
    # No username field is needed since we're using mobile_number as the unique identifier

    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['email']
    
    objects = CustomUserManager()

    def __str__(self):
        if self.role == "Admin":
            return f"Mobile Number: {self.mobile_number},\nEmail: {self.email} (Admin)"
        elif self.role == "Agent":
            return f"Mobile Number: {self.mobile_number},\nEmail: {self.email} (Agent)"
        else:
            return f"Mobile Number: {self.mobile_number},\nEmail: {self.email} (User)"
    
    

class School(models.Model):
    name = models.CharField(max_length=150, unique=True)
    address = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Lead(models.Model):
    STUDENT_CHOICES = [
        ('Play School', 'Play School'),
        ('Nursery', 'Nursery'),
        ('LKG', 'LKG'),
        ('UKG', 'UKG'),
        ('Grade 1', 'Grade 1'),
        ('Grade 2', 'Grade 2'),
        ('Grade 3', 'Grade 3'),
        ('Grade 4', 'Grade 4'),
        ('Grade 5', 'Grade 5'),
        ('Grade 6', 'Grade 6'),
        ('Grade 7', 'Grade 7'),
        ('Grade 8', 'Grade 8'),
        ('Grade 9', 'Grade 9'),
        ('Grade 10', 'Grade 10'),
        ('Grade 11', 'Grade 11'),
        ('Grade 12', 'Grade 12'),
    ]

    INQUIRY_CHOICES = [
        ('Advertisement', 'Advertisement'),
        ('Walk-in', 'Walk-in'),
        ('Online Form', 'Online Form'),  
        ('Referral', 'Referral'),
    ]

    STATUS_CHOICES = [
        ('DNP', 'DNP'),
        ('Not interested', 'Not interested'),
        ('Interested', 'Interested'),
        ('Follow Up', 'Follow Up'),
        ('Low Budget', 'Low Budget'),
        ('Meeting', 'Meeting'),
        ('Proposal', 'Proposal'),
    ]

    student_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    # no need to enforce unique constraint because the same person can ask more than 1 inquiries for his multiple children
    address = models.TextField(null=True, blank=True)
    block = models.CharField(choices=get_block_choices(), max_length=100, blank=False, null=False)
    location_panchayat = models.CharField(max_length=100, blank=False, null=False)
    inquiry_source = models.CharField(choices = INQUIRY_CHOICES, max_length=100)  # e.g., Advertisement, Walk-in, Online
    student_class = models.CharField(choices=STUDENT_CHOICES, max_length=30)
    status = models.CharField(choices=STATUS_CHOICES, max_length=100, default='Inquiry')  # Inquiry, Follow-up, Visit, etc.    
    remarks = models.TextField(blank=True, null=True)
    
    inquiry_date = models.DateField(null=True, blank=True)    
    registration_date = models.DateField(null=True, blank=True)
    admission_test_date = models.DateField(null=True, blank=True)
    admission_offered_date = models.DateField(null=True, blank=True)
    admission_confirmed_date = models.DateField(null=True, blank=True)
    rejected_date = models.DateField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    last_follow_up_updation = models.DateField(null=True, blank=True)
    last_inquiry_updation = models.DateField(null=True, blank=True)
    
    # Proposal tracking
    proposal_sent_date = models.DateTimeField(null=True, blank=True, help_text='When the last proposal was sent')
    proposal_sent_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals_sent',
        help_text='User who sent the last proposal'
    )
    

    
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    
    assigned_agent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        limit_choices_to={'role': 'Agent'},
        related_name='assigned_agent'       # for reverse relation
    )
    
    admin_assigned = models.ForeignKey(
        CustomUser,  # Refers to our Custom-User model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        limit_choices_to={'role': 'Admin'},  # Restrict to staff users (admins) in the dropdown of django forms. is_staff is a boolean field (True or False) in Django’s built-in User model. It is used to determine whether a user has access to the Django admin panel.
        related_name='admin_assigned'
    )
    
    # Transfer tracking fields
    transferred_from = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'Agent'},
        related_name='transferred_leads',
        help_text='Agent who transferred this lead'
    )
    
    transferred_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'Agent'},
        related_name='received_leads',
        help_text='Agent who received this transferred lead'
    )
    
    transfer_date = models.DateTimeField(null=True, blank=True, help_text='When the lead was transferred')
    
    transfer_reason = models.TextField(blank=True, null=True, help_text='Reason for transferring the lead')
    
    def __str__(self):
        return f"Name: {self.student_name},\nParent Name: {self.parent_name},Email:{self.email},Student Class:{self.student_class},\nmobile_number:{self.mobile_number},\nAddress:{self.address},\nBlock:{self.block},\nLocation:{self.location_panchayat},\nInquiry Source:{self.inquiry_source},\nStatus:{self.status}"
    
    @classmethod
    def get_agent_with_least_leads(cls):
        """
        Returns the agent with the least number of assigned leads.
        Returns None if no agents are available.
        """
        from django.db.models import Count
        
        agents = CustomUser.objects.filter(role='Agent')
        if not agents.exists():
            return None
        
        agents_with_counts = agents.annotate(
            lead_count=Count('assigned_agent')
        ).order_by('lead_count')
        
        return agents_with_counts.first()
    
    def auto_assign_agent(self):
        """
        Automatically assigns this lead to the agent with the least workload.
        Returns True if assignment was successful, False otherwise.
        """
        if self.assigned_agent:
            return False  # Already assigned
        
        agent = self.get_agent_with_least_leads()
        if agent:
            self.assigned_agent = agent
            return True
        return False
    

class LeadLogs(models.Model):
    lead = models.ForeignKey("Lead", on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=now)
    previous_data = models.JSONField(default=dict)  # Stores previous values
    new_data = models.JSONField(default=dict)   # Stores updated values
    
    def __str__(self):
        return f"Lead: {self.lead.student_name} - Changed by: {self.changed_by.name if self.changed_by else 'Unknown'} at {self.changed_at}"

# ====================================================================================

class CallRecording(models.Model):
    """
    Model to store call recordings and their metadata
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='call_recordings')
    recording_file = models.FileField(upload_to='call_recordings/', help_text='Upload call recording file')
    duration = models.DurationField(blank=True, null=True, help_text='Duration of the call (automatically extracted)')
    call_date = models.DateTimeField(auto_now_add=True, help_text='Date and time when recording was uploaded')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True, help_text='Additional notes about the call')
    
    class Meta:
        ordering = ['-call_date']
    
    def __str__(self):
        return f"Call Recording for {self.lead.student_name} - {self.call_date}"
    
    def get_duration_display(self):
        """Return duration in a readable format"""
        if self.duration:
            total_seconds = int(self.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        return "Unknown"


class CompanySettings(models.Model):
    """Model to store company information for proposals"""
    name = models.CharField(max_length=200, default='Your Educational Institution')
    address = models.TextField(default='Your Institution Address, City, State - PIN')
    phone = models.CharField(max_length=20, default='+91-XXXXXXXXXX')
    email = models.EmailField(default='info@yourinstitution.com')
    website = models.URLField(default='www.yourinstitution.com')
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Company Settings"
    
    def __str__(self):
        return f"Company Settings - {self.name}"
    
    @classmethod
    def get_settings(cls):
        """Get the first (and should be only) company settings instance"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Your Educational Institution',
                'address': 'Your Institution Address, City, State - PIN',
                'phone': '+91-XXXXXXXXXX',
                'email': 'info@yourinstitution.com',
                'website': 'www.yourinstitution.com'
            }
        )
        return settings