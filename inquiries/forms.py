# All these forms would be interated into their respective views in views.py file !!!

from django import forms
from .models import Lead, Agent, CustomUser     # what model a form would be integrated with so that when you submit that form, the changes are made to that model.
from django.contrib.auth.models import User
from datetime import date
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
        user = kwargs.pop('user', None)  # Get the user from the kwargs. Django’s ModelForm does not accept user as a parameter by default. Pop and Extract user before calling super()
        
        instance = kwargs.get('instance')  # Get the existing instance, if available
        
        super().__init__(*args, **kwargs)       # calling parent class constructor
        
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
        self.fields['block'].widget = forms.Select(choices=[('', 'Select the Block')] + list(self.fields['block'].choices)[1:])
        
        # Set empty Location/Panchayat initially
        self.fields['location_panchayat'].widget = forms.Select(choices=[('', 'Select Block First')])       
        
        self.fields['inquiry_source'].widget = forms.Select(choices=[('', 'Select Inquiry Source')] + list(self.fields['inquiry_source'].choices)[1:])
        
        self.fields['student_class'].widget = forms.Select(choices=[('', 'Select Student Class')] + list(self.fields['student_class'].choices)[1:])
        
        self.fields['assigned_agent'].widget = forms.Select(choices=[('', 'Choose Agent')] + list(self.fields['assigned_agent'].choices)[1:])
        
        self.fields['admin_assigned'].widget = forms.Select(choices=[('', 'Choose Admin')] + list(self.fields['admin_assigned'].choices)[1:])

                

        # Restrict Assigned Agent field to only email of that agent in dropdown for non admin users                
        if user and not user.is_staff:
            self.fields['assigned_agent'].queryset = Agent.objects.filter(user=user)
            
# ====================================================================================  

class UpdateLeadStatusForm(InquiryForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")  # Get the instance if provided
        super().__init__(*args, **kwargs)  # Call the parent constructor
        

        

# ====================================================================================  

class AgentForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=100,
        required=True,
        widget=forms.EmailInput()
    )

    class Meta:
        model = Agent
        fields = ['name', 'email']     # fields to display in the form. email is not present in the Agent schema as a field, so it would be taken from above.
        
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