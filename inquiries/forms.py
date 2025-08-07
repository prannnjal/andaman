# All these forms would be interated into their respective views in views.py file !!!

from django import forms
from .models import Lead, CustomUser, CallRecording     # what model a form would be integrated with so that when you submit that form, the changes are made to that model.
from django.contrib.auth.models import User
from datetime import date
from django.forms.widgets import DateTimeInput
from django.utils import timezone
from datetime import datetime

import pandas as pd
import os

# Load Excel file again for filtering location_panchayat dynamically
file_path = "inquiries/static/Location_list.xlsx"
df = pd.read_excel(file_path)

# ====================================================================================

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['student_name','parent_name','mobile_number','email','address','inquiry_source','student_class','status','remarks','inquiry_date','follow_up_date','registration_date','admission_test_date','admission_offered_date','admission_confirmed_date','rejected_date','admin_assigned']      # what fields from Lead model to be included in this form (assigned_agent removed for auto-assignment)
        
        labels = {
            'student_name': 'School Name',
            'parent_name': 'Concerned Person',
            'inquiry_source': 'Select Inquiry Source',
            'student_class': 'Select Student Class',
        }
        
    def __init__(self, *args, **kwargs):        # constructor
      
        super().__init__(*args, **kwargs)       # calling parent class constructor
        
        if not self.instance or not self.instance.pk:
            self.fields['inquiry_date'].initial = timezone.localdate()
        
        # Restrict status choices to only the new statuses
        self.fields['status'].choices = [
            ('DNP', 'DNP'),
            ('Not interested', 'Not interested'),
            ('Interested', 'Interested'),
            ('Follow Up', 'Follow Up'),
            ('Low Budget', 'Low Budget'),
            ('Meeting', 'Meeting'),
            ('Proposal', 'Proposal'),
        ]
        
        # Assign the 'date' widget to the date fields individually
        date_fields = [
            'inquiry_date', 'follow_up_date', 'registration_date', 
            'admission_test_date', 'admission_offered_date', 
            'admission_confirmed_date', 'rejected_date'
        ]
        for field in date_fields:
            self.fields[field].widget = forms.DateInput(attrs={'type': 'date'})                                        
        
        # Set placeholders for select fields
        # inquiry_source and student_class have choices, so we can set Select widgets
        self.fields['inquiry_source'].widget = forms.Select(choices=[('', 'Select Inquiry Source')] + list(self.fields['inquiry_source'].choices)[1:])
        
        self.fields['student_class'].widget = forms.Select(choices=[('', 'Select Student Class')] + list(self.fields['student_class'].choices)[1:])
        
        # Set admin_assigned field
        self.fields['admin_assigned'] = forms.ModelChoiceField(
            queryset=CustomUser.objects.filter(role="Admin"),
            required=False,  # 👈 Make it optional
            empty_label="Select the Admin"  # Replaces the default "--------" option
        )
        
        # Assign label_from_instance separately
        self.fields['admin_assigned'].label_from_instance = lambda admin: f"Id: {admin.id}, Name: {admin.name}, Phone: {admin.mobile_number}"
        
            
# ====================================================================================  

class UpdateLeadStatusForm(InquiryForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")  # Get the instance if provided
        super().__init__(*args, **kwargs)  # Call the parent constructor
        
        # Remove assigned_agent field for new inquiry creation (auto-assignment will handle this)
        if 'assigned_agent' in self.fields:
            del self.fields['assigned_agent']

# ====================================================================================

class AgentUpdateLeadForm(forms.ModelForm):
    """
    Form for agents to update lead status - restricted fields
    Agents can only modify: status, dates, remarks, and basic info
    Agents can see but cannot modify: inquiry_source, admin_assigned, assigned_agent
    """
    class Meta:
        model = Lead
        fields = [
            'student_name', 'parent_name', 'mobile_number', 'email', 'address',
            'inquiry_source', 'student_class', 'status', 'remarks',
            'inquiry_date', 'follow_up_date', 'registration_date', 
            'admission_test_date', 'admission_offered_date', 
            'admission_confirmed_date', 'rejected_date', 'admin_assigned', 'assigned_agent'
        ]
        
        labels = {
            'student_name': 'School Name',
            'parent_name': 'Concerned Person',
            'inquiry_source': 'Select Inquiry Source',
            'student_class': 'Select Student Class',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set placeholders for select fields
        # student_class has choices, so we can set Select widget
        self.fields['student_class'].widget = forms.Select(choices=[('', 'Select Student Class')] + list(self.fields['student_class'].choices)[1:])
        
        # Assign the 'date' widget to the date fields individually
        date_fields = [
            'inquiry_date', 'follow_up_date', 'registration_date', 
            'admission_test_date', 'admission_offered_date', 
            'admission_confirmed_date', 'rejected_date'
        ]
        for field in date_fields:
            self.fields[field].widget = forms.DateInput(attrs={'type': 'date'})
        
        # Make certain fields read-only for agents (but not disabled to allow form submission)
        readonly_fields = ['inquiry_source', 'admin_assigned', 'assigned_agent']
        for field_name in readonly_fields:
            if field_name in self.fields:
                # Make the field read-only but not disabled
                self.fields[field_name].widget.attrs['readonly'] = True
                self.fields[field_name].widget.attrs['style'] = 'background-color: #f8f9fa; color: #6c757d;'
                self.fields[field_name].help_text = "This field cannot be modified by agents"
                
                # Add visual indicator
                if hasattr(self.fields[field_name], 'label'):
                    self.fields[field_name].label = f"{self.fields[field_name].label} (Read-only)"

# ====================================================================================

class EditLeadForm(InquiryForm):
    """
    Form for editing existing leads - includes assigned_agent field for manual assignment
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add assigned_agent field back for editing
        self.fields['assigned_agent'] = forms.ModelChoiceField(
            queryset=CustomUser.objects.filter(role="Agent"),
            required=False,
            empty_label="Select the Agent"
        )
        
        # Assign label_from_instance for assigned_agent
        self.fields['assigned_agent'].label_from_instance = lambda agent: f"Id: {agent.id}, Name: {agent.name}, Phone: {agent.mobile_number}"
        
# ====================================================================================  

class AgentForm(forms.ModelForm):
    # Accessing fields from CustomUser model via the 'user' relation
    email = forms.EmailField(
        max_length=100,
        required=True,
        widget=forms.EmailInput()
    )
    
    mobile_number = forms.CharField(
        max_length=14,
        required=False,
        widget=forms.TextInput()
    )

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'mobile_number']     # fields to display in the form. email is not present in the Agent schema as a field, so it would be taken from above.
        
        labels = {
            'name': 'Agent Name',
            'email': 'Email Address',         
        }

    def save(self, commit=True):
        email = self.cleaned_data.get('email')
        user, created = CustomUser.objects.get_or_create(email=email, defaults={'username': email})
        
        agent = super().save(commit=False)
        agent.user = user  # Link the user to the agent

        if commit:
            user.save()  # Save user if newly created
            agent.save()  # Save agent

        return agent
    
    
# ====================================================================================  

class CustomUserForm(forms.ModelForm):
    expiration_time = forms.DateTimeField(
        widget=DateTimeInput(attrs={
            'type': 'datetime-local',  # HTML5 datetime picker
            'class': 'form-control',
        }),
        required=True,
        initial=timezone.make_aware(datetime(9999, 12, 31, 23, 59, 59))  # Set the default value to far future
    )
    
    # Password fields for admin to set custom password
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text='Enter a password for the user'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text='Confirm the password'
    )

    class Meta:
        model = CustomUser
        fields = [ 'mobile_number', 'email', 'expiration_time', 'role', 'name']
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long")
        
        return cleaned_data

# ====================================================================================

class UpdateUserForm(forms.ModelForm):
    """
    Form for updating existing users - makes passwords optional
    """
    expiration_time = forms.DateTimeField(
        widget=DateTimeInput(attrs={
            'type': 'datetime-local',  # HTML5 datetime picker
            'class': 'form-control',
        }),
        required=True,
        initial=timezone.make_aware(datetime(9999, 12, 31, 23, 59, 59))  # Set the default value to far future
    )
    
    # Password fields for admin to optionally change password
    password1 = forms.CharField(
        label='New Password (Optional)',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave blank to keep current password'
    )
    
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Confirm the new password'
    )

    class Meta:
        model = CustomUser
        fields = ['mobile_number', 'email', 'expiration_time', 'role', 'name']
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Only validate passwords if at least one is provided
        if password1 or password2:
            if not password1:
                raise forms.ValidationError("Please enter a new password")
            if not password2:
                raise forms.ValidationError("Please confirm the new password")
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long")
        
        return cleaned_data

# ====================================================================================

class TransferLeadForm(forms.Form):
    """
    Form for transferring leads between agents or to viewer status
    """
    TRANSFER_CHOICES = [
        ('agent', 'Transfer to Another Agent'),
        ('viewer', 'Make Available to All Agents (Viewer Status)'),
    ]
    
    transfer_type = forms.ChoiceField(
        choices=TRANSFER_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'onchange': 'toggleTargetAgent()'
        }),
        initial='agent',
        help_text='Choose how you want to transfer this lead'
    )
    
    target_agent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='Agent'),
        empty_label="Select an agent to transfer to",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'width: 100%;',
            'id': 'target-agent-select'
        }),
        help_text='Choose the agent you want to transfer this lead to',
        required=False
    )
    
    transfer_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter the reason for transferring this lead...'
        }),
        required=True,
        help_text='Please provide a reason for transferring this lead'
    )
    
    def __init__(self, *args, **kwargs):
        current_agent = kwargs.pop('current_agent', None)
        super().__init__(*args, **kwargs)
        
        if current_agent:
            # Exclude the current agent from the choices
            self.fields['target_agent'].queryset = CustomUser.objects.filter(
                role='Agent'
            ).exclude(id=current_agent.id)
    
    def clean(self):
        cleaned_data = super().clean()
        transfer_type = cleaned_data.get('transfer_type')
        target_agent = cleaned_data.get('target_agent')
        
        if transfer_type == 'agent' and not target_agent:
            raise forms.ValidationError("Please select an agent to transfer to.")
        
        return cleaned_data

# ====================================================================================

class CallRecordingForm(forms.ModelForm):
    """
    Form for uploading call recordings
    """
    class Meta:
        model = CallRecording
        fields = ['recording_file', 'notes']
        widgets = {
            'recording_file': forms.FileInput(attrs={
                'accept': '.mp3,.aac,audio/mp3,audio/aac',
                'class': 'form-control',
                'id': 'call-recording-input'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add notes about the call...',
                'class': 'form-control'
            })
        }
    
    def clean_recording_file(self):
        file = self.cleaned_data.get('recording_file')
        if file:
            # Check file size (limit to 50MB)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 50MB.")
            
            # Check file extension - only MP3 and AAC allowed
            allowed_extensions = ['.mp3', '.aac']
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Only MP3 (.mp3) and AAC (.aac) files are allowed for call recordings.")
        
        return file