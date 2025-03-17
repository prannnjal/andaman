from django.db import models
from django.contrib.auth.models import User, AbstractUser
import pandas as pd
from django.utils.timezone import now
import json

# print("======================> os.getcwd = ", os.getcwd())

# Load block and location_panchayat data from Excel
file_path = "inquiries/static/Location_list.xlsx"
df = pd.read_excel(file_path)


# Extract unique blocks
BLOCK_CHOICES = [(block, block) for block in df["BLOCK"].dropna().unique()]
BLOCK_CHOICES.append(("Other", "Other"))  # Add the 'Other' option
'''
[('A', 'Block A'), ('B', 'Block B'), ('C', 'Block C')]

Now, in a Django form, the dropdown will show: Block A
But the database will still store "A"
'''

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Enforce unique email. This thing was missing in default Django User model, thats why we needed to implement our Custom User model

    USERNAME_FIELD = 'email'  # Use email as the primary identifier
    '''
    By default, Django uses username for authentication.
    Here, we override it so users log in using their email instead.
    '''
    REQUIRED_FIELDS = ['username']  # 'username' is required when creating a user via createsuperuser
            
    def __str__(self):
        if self.is_staff:
            return f"Username: {self.username},\nEmail: {self.email} (Admin)"
        else:
            return f"Username: {self.username},\nEmail: {self.email} (Agent)"
    
    
class Agent(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)     # I want to link Agent to CustomUser model and also want to store additional fields for the Agents
    name = models.CharField(max_length=100)
    # email = models.EmailField(max_length=100, unique=True)
    performance_score = models.IntegerField(default=100)
    mobile_number = models.CharField(max_length=14, null=True, blank=True)


    def __str__(self):
        return f"Name: {self.name},\nEmail: {self.user.email}"
    

class Lead(models.Model):
    STUDENT_CHOICES = [
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
        ('Inquiry', 'Inquiry'),
        ('Registration', 'Registration'),
        ('Admission Test', 'Admission Test'),
        ('Admission Offered', 'Admission Offered'),
        ('Admission Confirmed', 'Admission Confirmed'),
        ('Rejected', 'Rejected'),
    ]

    student_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=100, blank=True, null=True)
    # no need to enforce unique constraint because the same person can ask more than 1 inquiries for his multiple children
    address = models.TextField(null=True, blank=True)    
    block = models.CharField(choices=BLOCK_CHOICES, max_length=100, blank=False, null=False)
    location_panchayat = models.CharField(max_length=100, blank=False, null=False)
    inquiry_source = models.CharField(choices = INQUIRY_CHOICES, max_length=100)  # e.g., Advertisement, Walk-in, Online
    student_class = models.CharField(choices=STUDENT_CHOICES, max_length=10)
    status = models.CharField(choices=STATUS_CHOICES, max_length=100, default='Inquiry')  # Inquiry, Follow-up, Visit, etc.    
    remarks = models.TextField(blank=True, null=True)
    
    inquiry_date = models.DateField(null=True, blank=True)    
    registration_date = models.DateField(null=True, blank=True)
    admission_test_date = models.DateField(null=True, blank=True)
    admission_offered_date = models.DateField(null=True, blank=True)
    admission_confirmed_date = models.DateField(null=True, blank=True)
    rejected_date = models.DateField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    
    assigned_agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None  
    )
    
    admin_assigned = models.ForeignKey(
        CustomUser,  # Refers to our Custom-User model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        limit_choices_to={'is_staff': True}  # Restrict to staff users (admins) in the dropdown of django forms. is_staff is a boolean field (True or False) in Django’s built-in User model. It is used to determine whether a user has access to the Django admin panel.
    )
    
   
    def __str__(self):
        return f"Name: {self.student_name},\nParent Name: {self.parent_name},Email:{self.email},Student Class:{self.student_class},\nmobile_number:{self.mobile_number},\nAddress:{self.address},\nBlock:{self.block},\nLocation:{self.location_panchayat},\nInquiry Source:{self.inquiry_source},\nStatus:{self.status}"
    

class LeadLogs(models.Model):
    lead = models.ForeignKey("Lead", on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=now)
    previous_data = models.JSONField(default=dict)  # Stores previous values
    new_data = models.JSONField(default=dict)   # Stores updated values
    
    def __str__(self):
        return f"The Lead with ID = {self.lead.id} was changed by {self.changed_by} at {self.changed_at}"