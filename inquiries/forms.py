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
        
        super().__init__(*args, **kwargs)       # calling parent class constructor
        
        # Assign the 'date' widget to the date fields individually
        date_fields = [
            'inquiry_date', 'follow_up_date', 'registration_date', 
            'admission_test_date', 'admission_offered_date', 
            'admission_confirmed_date', 'rejected_date'
        ]
        for field in date_fields:
            self.fields[field].widget = forms.DateInput(attrs={'type': 'date'})
                                
        # Set empty Location/Panchayat initially
        self.fields['location_panchayat'].widget = forms.Select(choices=[('', 'Select Block First')])
        
        # Restrict Assigned Agent field to only email of that agent in dropdown for non admin users                
        if user and not user.is_staff:
            self.fields['assigned_agent'].queryset = Agent.objects.filter(user=user)
            
# ====================================================================================

class ManageLeadStatusForm(forms.ModelForm):
    # assigned_agent = forms.ModelChoiceField(queryset=Agent.objects.all(), required=True)       # to customize assigned_agent field in the form
    
    class Meta:
        model = Lead
        fields = ['assigned_agent', 'status','remarks','inquiry_date','follow_up_date','registration_date','admission_test_date','admission_offered_date','admission_confirmed_date','rejected_date','admin_assigned']        
        
# ====================================================================================  
        
# class ReassignLeadForm(forms.ModelForm):
#     assigned_agent = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True), required=True)

#     class Meta:
#         model = Lead
#         fields = ['assigned_agent', 'email']
        
# ====================================================================================
        
# class RemoveAgentForm(forms.Form):
#     lead = forms.ModelChoiceField(
#         queryset=Lead.objects.none(),  # We'll set the queryset dynamically
#         empty_label="Select a lead to remove",
#         widget=forms.Select(attrs={'class': 'form-control'}),
#     )

#     def __init__(self, *args, **kwargs):
#         agent = kwargs.pop('agent', None)
#         super(RemoveAgentForm, self).__init__(*args, **kwargs)
#         if agent:            
#             self.fields['lead'].queryset = Lead.objects.filter(assigned_agent=agent)
            

# ====================================================================================

class AgentForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=100,
        required=True,
        widget=forms.EmailInput()
    )

    class Meta:
        model = Agent
        fields = ['name', 'email', 'performance_score']     # fields to display in the form. email is not present in the Agent schema as a field, so it would be taken from above.
        widgets = {
            'performance_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }
        labels = {
            'name': 'Agent Name',
            'email': 'Email Address',
            'performance_score': 'Performance Score (0-100)',
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
