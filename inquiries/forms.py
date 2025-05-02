# All these forms would be interated into their respective views in views.py file !!!

from django import forms
from .models import Lead, CustomUser     # what model a form would be integrated with so that when you submit that form, the changes are made to that model.
from django.contrib.auth.models import User
from datetime import date
from django.forms.widgets import DateTimeInput
from django.utils import timezone
from datetime import datetime

import pandas as pd

# Load Excel file again for filtering location_panchayat dynamically
file_path = "inquiries/static/Location_list.xlsx"
df = pd.read_excel(file_path)

# ====================================================================================

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['student_name','parent_name','mobile_number','email','address','block','location_panchayat','inquiry_source','student_class','status','remarks','inquiry_date','follow_up_date','registration_date','admission_test_date','admission_offered_date','admission_confirmed_date','rejected_date','assigned_agent','admin_assigned']      # what fields from Lead model to be included in this form
        
    def __init__(self, *args, **kwargs):        # constructor
      
        super().__init__(*args, **kwargs)       # calling parent class constructor
        
        # Add current block to choices if it's missing
        # Handle "block" field: ensure saved value is shown even if not in choices
        if self.instance and self.instance.block:
            current_block = self.instance.block
            block_choices = list(self.fields['block'].choices)
            block_values = [choice[0] for choice in block_choices]
            if current_block not in block_values:
                block_choices.insert(1, (current_block, current_block))  # After the empty option
        else:
            block_choices = list(self.fields['block'].choices)
        
        
        # Assign the 'date' widget to the date fields individually
        date_fields = [
            'inquiry_date', 'follow_up_date', 'registration_date', 
            'admission_test_date', 'admission_offered_date', 
            'admission_confirmed_date', 'rejected_date'
        ]
        for field in date_fields:
            self.fields[field].widget = forms.DateInput(attrs={'type': 'date'})                                        
        
        # Modify the select field to have a default placeholder
        '''
        This explicitly sets the widget for the "admin_assigned" field to a dropdown menu (<select>).
        
        Even if Django already assigns a <select> by default, this ensures we customize its options.
        
        self.fields['admin_assigned'].choices contains all the options Django generates from the model.
        
        list(...)[1:] removes the first choice (which is usually an empty option added by Django automatically). Then, + appends the remaining choices so the field still works properly.
        '''
        # Set the final choices with the placeholder at the top
        self.fields['block'].choices = [('', 'Select the Block')] + block_choices[1:]
        
        # Set empty Location/Panchayat initially
        self.fields['location_panchayat'].widget = forms.Select(choices=[('', 'Select Block First')])       
        
        self.fields['inquiry_source'].widget = forms.Select(choices=[('', 'Select Inquiry Source')] + list(self.fields['inquiry_source'].choices)[1:])
        
        self.fields['student_class'].widget = forms.Select(choices=[('', 'Select Student Class')] + list(self.fields['student_class'].choices)[1:])
        
        # Set assigned_agent field
        self.fields['assigned_agent'] = forms.ModelChoiceField(
            queryset=CustomUser.objects.filter(role="Agent"),
            required=False,  # 👈 Make it optional
            empty_label="Select the Agent"  # Replaces the default "--------" option
        )
        
        # Set assigned_agent field
        self.fields['admin_assigned'] = forms.ModelChoiceField(
            queryset=CustomUser.objects.filter(role="Admin"),
            required=False,  # 👈 Make it optional
            empty_label="Select the Admin"  # Replaces the default "--------" option
        )
        
        
        # Assign label_from_instance separately
        self.fields['assigned_agent'].label_from_instance = lambda agent: f"Id: {agent.id}, Name: {agent.name}, Phone: {agent.mobile_number}"
        
        self.fields['admin_assigned'].label_from_instance = lambda admin: f"Id: {admin.id}, Name: {admin.name}, Phone: {admin.mobile_number}"
        
            
# ====================================================================================  

class UpdateLeadStatusForm(InquiryForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")  # Get the instance if provided
        super().__init__(*args, **kwargs)  # Call the parent constructor
        
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
        initial=timezone.now
        # initial=timezone.make_aware(datetime(9999, 12, 31, 23, 59, 59))  # Set the default value here
    )
   

    class Meta:
        model = CustomUser
        fields = [ 'mobile_number', 'email', 'expiration_time', 'role', 'name']