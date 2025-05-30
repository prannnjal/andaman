from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.validators import validate_email
from .models import CustomUser, Lead, CustomUser, LeadLogs
from .forms import InquiryForm, AgentForm, UpdateLeadStatusForm, CustomUserForm
from django.contrib.auth import authenticate, login
# Django's authenticate() function doesn't itself contain the authentication logic—it simply loops through all the backends listed in your AUTHENTICATION_BACKENDS setting and calls their authenticate() methods. 
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import now
from django.contrib import messages
from openpyxl import Workbook
from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate
from django.conf import settings
from django.http import JsonResponse
import pandas as pd
from django.db.models.functions import Coalesce
from django.db.models import ExpressionWrapper
from django.db.models import FloatField
from datetime import datetime
from django.forms.models import model_to_dict
import json
from datetime import datetime, date
from collections import defaultdict
import random
import string
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.views import PasswordResetView
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Count, Q
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from urllib.parse import urlencode

# =======================================================================================================================================================================
def is_authentic(user):
    return user.is_authenticated and user.expiration_time > timezone.now()

def is_admin(user):
    return is_authentic(user) and user.role=="Admin"

def is_agent_or_admin(user):
    return  is_authentic(user) and user.role in ["Admin", "Agent"]
    
def is_staff(user):
    return is_authentic(user) and user.role in ["Admin", "Agent", "Viewer"]


# =======================================================================================================================================================================

def Save_Lead_Logs(old_inquiry_instance, new_inquiry_instance, changed_by):    
    previous_data = model_to_dict(old_inquiry_instance) if old_inquiry_instance else {}
    new_data = model_to_dict(new_inquiry_instance)
    
    # Get all unique field names from both dictionaries
    all_fields = set(previous_data.keys()).union(set(new_data.keys()))
    
    # print("=======================> prev data = ",previous_data)
    # print("\n=======================> new data = ",new_data)
    # print("\n=======================> all_fields = ",all_fields)
    
    # Compare previous and new data to track changes
    changes = {
        field: {'old': previous_data.get(field, None), 'new': new_data.get(field, None)}
        for field in all_fields 
        if previous_data.get(field) != new_data.get(field)
    }
    
    # print("========================> changes = ", changes)
    
    # Save changes in LeadLogs only if there are differences
    if changes:
        # print("==========================> inside if changes")
        LeadLogs.objects.create(
            lead=new_inquiry_instance,
            changed_by=changed_by,
            changed_at=now(),
            previous_data=json.dumps(previous_data, default=str),  
            new_data=json.dumps(new_data, default=str)
        )
# =======================================================================================================================================================================

def agent_login(request):
    if request.method == 'POST':
                
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Django's authenticate() function doesn't itself contain the authentication logic—it simply loops through all the backends listed in your AUTHENTICATION_BACKENDS setting and calls their authenticate() methods. Authenticate user based on email and password. The authenticate is our custom def authenticate() function which we have created in our auth_backends.py file. 
        
        if username.isdigit() and len(username) == 10:
            # print("=======================> username = ",username," and password = ",password)
            user = authenticate(request, mobile_number=username, password=password)
        else:
            user = authenticate(request, email=username, password=password)
        

        if user is not None:
            if user.role in ["Admin", "Agent", "Viewer"] and user.expiration_time > timezone.now():                
                login(request, user)
                # The function sets a session cookie on the user's browser, and Django uses that cookie to identify the user in future requests. After this call, request.user will return the logged-in user on subsequent requests.
                
                messages.success(request, 'Login successful !')
                
                return redirect('dashboard')  # Redirect to the admin dashboard
            

            else:
                messages.error(request, 'You do not have permission to login')
                return redirect('login')

        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'inquiries/agent_login.html')

# =======================================================================================================================================================================

def Filter_By_Date(inquiries, choice, request_parameter, model_key):
    if request_parameter:
        date_val = datetime.strptime(request_parameter, "%Y-%m-%d").date()
        
        if(choice == "from"):
            inquiries = inquiries.filter(**{f"{model_key}__gte" : date_val})
        
        elif(choice == "to"):
            inquiries = inquiries.filter(**{f"{model_key}__lte" : date_val})
                                
    return inquiries
    
# ====================================================================================================================================================================== 
def Filter_Inquiries(request):
    query_params = request.GET
    # print("============================> query_params = ",query_params)
    
    user = request.user     # request.user returns the currently logged-in user, which is an instance of your CustomUser model (or User if you haven't switched to a custom model).    

    # Filter inquiries based on user type (staff or agent)
    if user.role=="Admin":        
        inquiries = Lead.objects.all()
        # print("=====================> after admin len(inquiries) filtered = ", len(inquiries)) 
    elif user.role=="Agent":  # Check if the user is linked to an Agent. Since Agent has a OneToOneField to CustomUser, we check if the user has an agent attribute before accessing user.agent.
        inquiries = Lead.objects.all()
        
        # inquiries = Lead.objects.filter(assigned_agent=user.agent)  # Agent has a OneToOneField linked to CustomUser. So you can simply access agent model instance of a user via user.agent.
    else:
        inquiries = Lead.objects.all()     # return an empty queryset if the user is neither an admin nor an agent
    
    
    
    #return inquiries    # remove later
    
    
    # Handle filters from the GET request
    lead_id = query_params.get('lead_id')  # returns a list of selected lead IDs
    # print("=================> lead_id in filter view = ",lead_id)
    if lead_id:
        lead_id = [(int(lead_id))]
        # lead_id = [int(i) for i in lead_id if i.isdigit()]
        inquiries = inquiries.filter(id__in=lead_id)
        # print("=====================> lead_id = ",lead_id," and after lead_id len(inquiries) filtered = ", len(inquiries))
        
    student_class = query_params.get('student_class')
    if student_class:        
        inquiries = inquiries.filter(student_class=student_class)
        # print("=====================> student_class = ",student_class," and after student_class len(inquiries) filtered = ", len(inquiries))         
        
    student_name = query_params.get('student_name')
    if student_name:
        inquiries = inquiries.filter(student_name__icontains=student_name)  # icontains = Partial match (case insensitive)
        
    parent_name = query_params.get('parent_name')
    if parent_name:
        inquiries = inquiries.filter(parent_name__icontains=parent_name)
        
    lead_email = query_params.get('lead_email')
    if lead_email:
        inquiries = inquiries.filter(email__icontains=lead_email)

    mobile_number = query_params.get('mobile_number')
    if mobile_number:
        inquiries = inquiries.filter(mobile_number__icontains=mobile_number)
    
    block = query_params.get('block')
    if block:
        inquiries = inquiries.filter(block__icontains=block)
            
    location_panchayat = query_params.get('location_panchayat')
    if location_panchayat:
        inquiries = inquiries.filter(location_panchayat__icontains=location_panchayat)
        
    inquiry_source = query_params.get('inquiry_source')
    if inquiry_source:
        inquiries = inquiries.filter(inquiry_source__icontains=inquiry_source)

    status = query_params.get('status')
    if status:
        inquiries = inquiries.filter(status=status)

    agent_id = query_params.get('agent_id')
    if agent_id:
        inquiries = inquiries.filter(assigned_agent_id=int(agent_id))  

    admin_id = query_params.get('admin_id')
    if admin_id:
        inquiries = inquiries.filter(admin_assigned__isnull=False,admin_assigned__id = admin_id)
     
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('inquiry_date_from'), 'inquiry_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('inquiry_date_to'), 'inquiry_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('registration_date_from'), 'registration_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('registration_date_to'), 'registration_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('admission_test_date_from'), 'admission_test_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('admission_test_date_to'), 'admission_test_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('admission_offered_date_from'), 'admission_offered_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('admission_offered_date_to'), 'admission_offered_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('admission_confirmed_date_from'), 'admission_confirmed_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('admission_confirmed_date_to'), 'admission_confirmed_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('rejected_date_from'), 'rejected_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('rejected_date_to'), 'rejected_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('follow_up_date_from'), 'follow_up_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('follow_up_date_to'), 'follow_up_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('last_inquiry_updation_from'), 'last_inquiry_updation')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('last_inquiry_updation_to'), 'last_inquiry_updation')
    
    inquiries = Filter_By_Date(inquiries, 'from', request.GET.get('last_follow_up_updation_from'), 'last_follow_up_updation')
    inquiries = Filter_By_Date(inquiries, 'to', request.GET.get('last_follow_up_updation_to'), 'last_follow_up_updation')   
    
    # print("=====================> inquiries filtered = ", inquiries) 
    # print("=====================> len(inquiries) filtered = ", len(inquiries)) 
    
    return inquiries
    
# =================================================================================================================================================================
    
@login_required
@user_passes_test(is_staff)
def inquiry_list(request):
    inquiries = Filter_Inquiries(request)
    
    # STEP 1: Load or store query parameters
    # if request.GET:
    #     request.session['last_inquiry_filters'] = request.GET.dict()
    #     query_params = request.GET
    # else:
    #     query_params = request.session.get('last_inquiry_filters', {})
        
        
    # print("==================> lead_ids selected = ",lead_ids_selected)
    
    return render(request, 'inquiries/inquiry_list.html', {
        'heading': request.GET.get('heading', "Leads List"),
        'inquiries': inquiries,
        'actions': ['Update', 'Delete', 'View Logs'],
        'dashboard_buttons': ["Add Inquiry", "Open Filters", "View / Hide Columns", "Dashboard"],
        'base_url_name': reverse('inquiry_list')
        # 'lead_ids_selected': lead_ids_selected,
    })

# =======================================================================================================================================================================


@login_required
@user_passes_test(is_admin)
def inquiries_updated_today_view(request):
    todays_date = now().date()
    
    inquiries = Filter_Inquiries(request)
    inquiries = inquiries.filter(last_inquiry_updation__gte=todays_date)
    
    # ?last_inquiry_updation_from={{todays_date}}&heading=Inquiries Updated Today"
        
    context = {
        'heading': 'Inquiries Updated Today',
        'inquiries': inquiries,
        'actions': ['Update', 'Delete', 'View Logs'],
        'dashboard_buttons': ["Add Inquiry", "Open Filters", "View / Hide Columns", "Dashboard"],
        'base_url_name': reverse('inquiries_updated_today')
    }

    return render(request, 'inquiries/inquiry_list.html', context)

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def follow_up_management(request):
    days = int(request.GET.get("days", "7"))
    follow_up_direction = request.GET.get("follow-up-direction", "next")
        
    follow_up_leads = Filter_Inquiries(request)
    
    # print("============================> inside followup management view and request = ", request)
         
    if(follow_up_direction == "previous"):
        date_to = date.today()
        date_from = date_to - timedelta(days=days)
        follow_up_leads = follow_up_leads.filter(
            last_follow_up_updation__gte=date_from, 
            last_follow_up_updation__lte=date_to
        )
        
    else:
        date_from = date.today()
        date_to = date_from + timedelta(days=days)
        follow_up_leads = follow_up_leads.filter(
            follow_up_date__gte=date_from, 
            follow_up_date__lte=date_to
        )
        
        
    follow_up_data = defaultdict(list)
    
    for lead in follow_up_leads:
        if follow_up_direction == "previous":
            follow_up_date = lead.last_follow_up_updation
        else:
            follow_up_date = lead.follow_up_date
            
        if follow_up_date:
            follow_up_date = str(follow_up_date)
            follow_up_date = datetime.strptime(follow_up_date, "%Y-%m-%d").strftime("%B %d, %Y")
            follow_up_data[follow_up_date].append(lead)
        
    follow_up_data = dict(follow_up_data)
        
    
    # ✅ Convert defaultdict to a regular dict and sort by date keys
    follow_up_data = dict(sorted(
        follow_up_data.items(),
        key=lambda x: datetime.strptime(x[0], "%B %d, %Y")  # Convert key back to date for sorting
    ))
    
    
    agents = CustomUser.objects.filter(role="Agent")
    lead_ids = Lead.objects.values_list('id', flat=True)
    students = Lead.objects.values_list('student_name', flat=True).distinct() 
    parents = Lead.objects.values_list('parent_name', flat=True).distinct() 
    locations_panchayats = Lead.objects.values_list('location_panchayat', flat=True).distinct()
    lead_emails = Lead.objects.values_list('email', flat=True).exclude(email__isnull=True)
    mobile_numbers = Lead.objects.values_list('mobile_number', flat=True).distinct()
    blocks = Lead.objects.values_list('block', flat=True).distinct()
    inquiry_sources = Lead.objects.values_list('inquiry_source', flat=True).distinct()
    statuses = Lead.objects.values_list('status', flat=True).distinct()
    student_classes = Lead.objects.values_list('student_class', flat=True).distinct()
    admins = CustomUser.objects.filter(role = "Admin")
    
    return render(request, 'inquiries/follow_up_management.html', {
            'lead_ids': lead_ids,
            'students': students,
            'parents': parents,            
            'follow_up_data':follow_up_data,            
            'Len_dict': len(follow_up_data),
            'agents': agents,
            'lead_emails': lead_emails,
            'mobile_numbers': mobile_numbers,
            'location_panchayats': locations_panchayats,
            'blocks': blocks,
            'inquiry_sources': inquiry_sources,
            'statuses': statuses,
            'student_classes': student_classes,
            'admins': admins,
            'follow_up_direction': follow_up_direction,
            'actions': ['Update', 'Delete', 'View Logs'],
            'base_url_name': reverse('follow_up_management'),
             
        })

# ======================================================================================================================================================================

@login_required
@user_passes_test(is_agent_or_admin)
def add_inquiry(request):
    if request.method == 'POST':
        form = UpdateLeadStatusForm(request.POST)

        if form.is_valid():
            inquiry = form.save(commit=False)
                        
            if request.POST.get('block') == "Other":
                inquiry.block = request.POST.get('manual_block')

            if request.POST.get('location_panchayat') == "Other":
                inquiry.location_panchayat = request.POST.get('manual_location_panchayat')
                
            if inquiry.follow_up_date:
                inquiry.last_follow_up_updation = inquiry.follow_up_date
                
            inquiry.last_inquiry_updation = now().date()              
        
            inquiry.save()
            
            Save_Lead_Logs(None, inquiry, request.user)

            # Get the assigned agent
            assigned_agent = inquiry.assigned_agent

            # Email recipient list
            recipient_list = []  # Default recipient email(s)
            if assigned_agent and assigned_agent.email:
                recipient_list.append(assigned_agent.email)
                # send_mail(
                #     subject='New Inquiry Arrived',
                #     message=f'A new inquiry has arrived.\n\nDetails:\n{inquiry}',
                #     from_email='uncertain30@gmail.com',  # Sender email
                #     recipient_list=recipient_list,  # Recipient email(s)
                #     fail_silently=False,
                # )
            
            # Add a success message
            messages.success(request, "Lead added successfully !")
            return redirect('add_inquiry')
        
        else:
            messages.error(request, "Some error occured, please ensure that the form is valid !")
      
    else:       # For GET request
        form = UpdateLeadStatusForm()
        
    return render(request, 'inquiries/update_status.html', {'form': form, 'title': 'Add new Inquiry'})

# ====================================================================================
            
@login_required
@user_passes_test(is_agent_or_admin)
def manage_lead_status(request, inquiry_id):
    # Fetch the Lead instance for the given inquiry_id
    inquiry = get_object_or_404(Lead, id=inquiry_id)    # fetches that instance from Lead model whose id is=inquiry_id
    
    

    if request.method == 'POST':
        # print("=====================> request  = ",request.POST)
        # Bind the form with POST data and the current inquiry instance. This ensures that the form updates the correct Lead object instead of creating a new one.
        form = InquiryForm(request.POST, instance=inquiry)
        
        if form.is_valid(): # Ensures all required fields are correctly filled.
            old_inquiry_instance = Lead.objects.get(id=inquiry.id)  # Fetch a fresh copy of the old data
    
            
            inquiry = form.save(commit=False)
            
            if inquiry.follow_up_date and inquiry.follow_up_date != old_inquiry_instance.follow_up_date:
                inquiry.last_follow_up_updation = now().date()
                
            inquiry.last_inquiry_updation = now().date()
            
                        
            if request.POST.get('block') == "Other":
                inquiry.block = request.POST.get('manual_block')

            if request.POST.get('location_panchayat') == "Other":
                inquiry.location_panchayat = request.POST.get('manual_location_panchayat')
                
            
            inquiry.save() 
            
            new_inquiry_instance = inquiry  # Store the new data after changes
            
            # Save logs of changes
            Save_Lead_Logs(old_inquiry_instance, new_inquiry_instance, request.user)
            
            messages.success(request, "Lead updated successfully !")
            
            return redirect('inquiry_list')  # Redirect back to the inquiry list after saving

        else:
            messages.error(request, "Error updating lead !")
    else:
        # Prefill form with the inquiry's current details
        form = InquiryForm(instance=inquiry)  # Ensure form is tied to the existing instance

    return render(request, 'inquiries/update_status.html', {'form': form, 'title': 'Update Lead Status', 'location_panchayat_context': inquiry.location_panchayat, 'block_context': inquiry.block})

# ====================================================================================
@login_required
@user_passes_test(is_staff)
def get_panchayats(request):
    block = request.GET.get('block', None)
    if block:
        file_path = "inquiries/static/Location_list.xlsx"
        df = pd.read_excel(file_path)

        # Filter by selected block
        filtered_block_bool = df["BLOCK"] == block   # returns [ True, False, True, False, True]
        filtered_block = df[filtered_block_bool]        # returns only those rows whose filtered_block_bool is True
        filtered_df = filtered_block[["S.N", "Location_Panchayat"]].dropna()    # Selects only the columns "S.N" and "Location_Panchayat". Drops rows with missing values (NaN) in "Location_Panchayat".

        
        # filtered_df = df[df["BLOCK"] == block][["S.N", "Location_Panchayat"]].dropna()

        # Convert to JSON with 'S.N' as ID
        data = [{'id': row["S.N"], 'name': row["Location_Panchayat"]} for _, row in filtered_df.iterrows()]

        return JsonResponse({'panchayats': data})

    return JsonResponse({'panchayats': []})

# ====================================================================================


@login_required
@user_passes_test(is_admin)
def remove_lead_from_agent_view(request):
    if request.method == 'POST':
        lead_id = request.POST.get('lead_id')  # Get the lead ID
        
        if not lead_id:
            messages.error(request, "Please select a lead to remove.")
            return redirect('remove_lead')
        
        lead = get_object_or_404(Lead, id=lead_id)
        lead.assigned_agent = None  # Remove the assigned agent
        
        lead.save()  # Save the updated object to the database
        
        # Add a success message
        messages.success(request, "Lead successfully removed from the agent.")
        
        return redirect('remove_lead')  # Redirect to the same page after removal
    
    else:
        agents = CustomUser.objects.filter(role='Agent').prefetch_related('assigned_agent')

        # agents = CustomUser.objects.prefetch_related('assigned_agent').filter(role='Agent').all()
        # print("=======================> agents prefetched in remove_lead_from_agent view = ", agents)
        '''
        This query retrieves all agents and their respective leads. Below is way to access it: 
        
        for agent in agents:
            print(agent.lead_set.all())
        '''
        return render(request, 'inquiries/remove_lead.html', {'agents': agents})

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def dashboard(request):
    # print("===========================> inside dashboard view")
    user = request.user  # Get the logged-in user

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.role == "Admin": 
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.all()
        # inquiries = Lead.objects.filter(assigned_agent__user=user)  # Agent sees only their assigned inquiries

    # Overall Counts
    total_inquiries = inquiries.filter(status='Inquiry').count()
    total_registrations = inquiries.filter(status='Registration').count()
    total_tests = inquiries.filter(status='Admission Test').count()
    total_admissions_offered = inquiries.filter(status='Admission Offered').count()
    total_admissions_confirmed = inquiries.filter(status='Admission Confirmed').count()
    rejected = inquiries.filter(status='Rejected').count()
        
    # Today's Counts
    today = now().date()
    # print("===============================> today date in dashboard = ", today)
    
    inquiries_today = inquiries.filter(status='Inquiry', inquiry_date=today).count()
    registrations_today = inquiries.filter(status='Registration', registration_date=today).count()
    tests_today = inquiries.filter(status='Admission Test', admission_test_date=today).count()
    admissions_offered_today = inquiries.filter(status='Admission Offered', admission_offered_date=today).count()
    admissions_confirmed_today = inquiries.filter(status='Admission Confirmed', admission_confirmed_date=today).count()
    rejected_today = inquiries.filter(status='Rejected', rejected_date=today).count()

    # Counts by Student Class
    '''
        1) values('student_class'): Groups the data by student_class.
        
        2) annotate(total=Count('id')): annotate allows you to perform aggregations (like SUM, COUNT, AVG, etc.) on groups of data.This query counts the number of inquiries for each student_class. The result will include a new field total, which stores the count.
        
        3) order_by('-total'): Sorts the results in descending order, so classes with the most inquiries appear first.
    '''

    # Inquiry Trends (Last 7 Days)
    '''
        1) filter(inquiry_date__gte=today - timedelta(days=7)):
            Filters inquiries where inquiry_date is greater than or equal to (≥) 7 days ago.
            timedelta(days=7) subtracts 7 days from today.
            
        2) annotate(day=TruncDate('inquiry_date')):
            Truncates the inquiry_date to just the date (removes time) and add this as new field day.            
            
        3) .values('day'): Groups the data by day. 
        
        4) .annotate(total=Count('id')):
            Counts the number of inquiries for each day and adds a new field total.
    '''    

    context = {
        # Overall Stats
        'todays_date': now().date().strftime('%Y-%m-%d'),
        'total_inquiries': total_inquiries,
        'total_registrations': total_registrations,
        'total_tests': total_tests,
        'total_admissions_offered': total_admissions_offered,
        'total_admissions_confirmed': total_admissions_confirmed,
        'rejected': rejected,

        # Today's Stats
        'inquiries_today': inquiries_today,
        'registrations_today': registrations_today,
        'tests_today': tests_today,
        'admissions_offered_today': admissions_offered_today,
        'admissions_confirmed_today': admissions_confirmed_today,
        'rejected_today': rejected_today,        
    }

    return render(request, 'inquiries/dashboard.html', context)

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def detailed_stats(request):
    user = request.user  # Get the logged-in user

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.role=="Admin":
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.all()
        # inquiries = Lead.objects.filter(assigned_agent__user=user)  # Agent sees only their assigned inquiries

    # Overall Counts
    total_inquiries = inquiries.filter(status='Inquiry').count()
    total_registrations = inquiries.filter(status='Registration').count()
    total_tests = inquiries.filter(status='Admission Test').count()
    total_admissions_offered = inquiries.filter(status='Admission Offered').count()
    total_admissions_confirmed = inquiries.filter(status='Admission Confirmed').count()
    rejected = inquiries.filter(status='Rejected').count()
        
    # Today's Counts
    today = now().date()
    inquiries_today = inquiries.filter(status='Inquiry', inquiry_date=today).count()
    registrations_today = inquiries.filter(status='Registration', registration_date=today).count()
    tests_today = inquiries.filter(status='Admission Test', admission_test_date=today).count()
    admissions_offered_today = inquiries.filter(status='Admission Offered', admission_offered_date=today).count()
    admissions_confirmed_today = inquiries.filter(status='Admission Confirmed', admission_confirmed_date=today).count()
    rejected_today = inquiries.filter(status='Rejected', rejected_date=today).count()

    # Counts by Student Class
    '''
        1) values('student_class'): Groups the data by student_class.
        
        2) annotate(total=Count('id')): annotate allows you to perform aggregations (like SUM, COUNT, AVG, etc.) on groups of data.This query counts the number of inquiries for each student_class. The result will include a new field total, which stores the count.
        
        3) order_by('-total'): Sorts the results in descending order, so classes with the most inquiries appear first.
    '''
    inquiries_by_class = inquiries.values('student_class').annotate(total=Count('id')).order_by('-total')

    # Counts by Inquiry Source
    inquiries_by_source = inquiries.values('inquiry_source').annotate(total=Count('id')).order_by('-total')

    # Counts by Location/Panchayat
    inquiries_by_location = inquiries.values('location_panchayat').annotate(total=Count('id')).order_by('-total')
    
    # Counts by Block
    inquiries_by_block = inquiries.values('block').annotate(total=Count('id')).order_by('-total')

    # Inquiry Trends (Last 7 Days)
    '''
        1) filter(inquiry_date__gte=today - timedelta(days=7)):
            Filters inquiries where inquiry_date is greater than or equal to (≥) 7 days ago.
            timedelta(days=7) subtracts 7 days from today.
            
        2) annotate(day=TruncDate('inquiry_date')):
            Truncates the inquiry_date to just the date (removes time) and add this as new field day.            
            
        3) .values('day'): Groups the data by day. 
        
        4) .annotate(total=Count('id')):
            Counts the number of inquiries for each day and adds a new field total.
    '''
    recent_trends = inquiries.filter(inquiry_date__gte=today - timedelta(days=7)).annotate(
        day=TruncDate('inquiry_date')
    ).values('day').annotate(total=Count('id')).order_by('day')

    # Most Recent Inquiries (Last 5)
    recent_inquiries = inquiries.order_by('-inquiry_date')[:5]

    context = {
        # Overall Stats       
        'total_inquiries': total_inquiries,
        'total_registrations': total_registrations,
        'total_tests': total_tests,
        'total_admissions_offered': total_admissions_offered,
        'total_admissions_confirmed': total_admissions_confirmed,
        'rejected': rejected,

        # Today's Stats
        'inquiries_today': inquiries_today,
        'registrations_today': registrations_today,
        'tests_today': tests_today,
        'admissions_offered_today': admissions_offered_today,
        'admissions_confirmed_today': admissions_confirmed_today,
        'rejected_today': rejected_today,

        # Detailed Stats
        'inquiries_by_class': inquiries_by_class,
        'inquiries_by_source': inquiries_by_source,
        'inquiries_by_location': inquiries_by_location,
        'inquiries_by_block': inquiries_by_block,

        # Trends and Recent Activity
        'recent_trends': recent_trends,
        'recent_inquiries': recent_inquiries,
    }
    
    # print("===============================> today date in detailed_stats = ", today)

    return render(request, 'inquiries/detailed_stats.html', context)

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def agent_performance(request):
    user = request.user  # Get the logged-in user
    
    # Get sorting parameters from request
    sort_column = request.GET.get("sort_column", "1")  # Default to sorting by agent name
    sort_order = request.GET.get("sort_order", "asc")  # Default to ascending order
    reverse_sort = True if sort_order == "desc" else False
    
   
    # If the user is an admin, get all agents; otherwise, get only the logged-in agent
    if user.role=="Admin":
        agents = CustomUser.objects.filter(role="Agent")  # Admins see all agents
    else:
        agents = CustomUser.objects.filter(role="Agent")
        # agents = Agent.objects.filter(user=user)  # Agents see only their own data

    # Initialize list to store agent performance data
    agent_data = []

    for agent in agents:
        # Total Leads Assigned
        total_leads = Lead.objects.filter(assigned_agent=agent).count()
        
        # Leads in Inquiry Status
        leads_inquiry = Lead.objects.filter(assigned_agent=agent, status='Inquiry').count()
        
        # Leads Converted to Admission Confirmed
        leads_to_admission_confirmed = Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed').count()
        
        # Leads Converted to Admission Offered
        leads_to_admission_offered = leads_to_admission_confirmed + Lead.objects.filter(assigned_agent=agent, status='Admission Offered').count()  
        
        # Leads Converted to Admission Test
        leads_to_admission_test = leads_to_admission_offered + Lead.objects.filter(assigned_agent=agent, status='Admission Test').count()  
        
        # Leads Converted to Registration Phase
        leads_to_registration = leads_to_admission_test + Lead.objects.filter(assigned_agent=agent, status='Registration').count()
              
        # Leads Lost
        leads_lost = Lead.objects.filter(assigned_agent=agent, status='Rejected').count()

        # Conversion Rates (Admission Offered and Confirmed)
        conversion_rate = leads_to_admission_confirmed / total_leads * 100 if total_leads > 0 else 0
       

        # Average Time to Conversion (from Inquiry to Admission Confirmed)
        total_days_to_conversion = sum(
            (lead.admission_confirmed_date - lead.inquiry_date).days
            for lead in Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed')
            if lead.inquiry_date and lead.admission_confirmed_date
        )
        conversions_count = Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed').count()
        average_days_to_conversion = round(total_days_to_conversion / conversions_count, 2) if conversions_count else 'N/A'
      

        # Collect data for each agent
        agent_data.append({
            'agent': agent,
            'total_leads': total_leads,
            'leads_inquiry': leads_inquiry,
            'leads_to_registration': leads_to_registration,
            'leads_to_admission_test':leads_to_admission_test,
            'leads_to_admission_offered': leads_to_admission_offered,
            'leads_to_admission_confirmed': leads_to_admission_confirmed,
            'leads_lost': leads_lost,
            'conversion_rate': conversion_rate,        
            'average_days_to_conversion': average_days_to_conversion,       
        })

    # Define valid sorting keys
    valid_sort_keys = {
        "1": lambda x: x["agent"].name.lower(),
        "2": lambda x: x["agent"].email.lower(),
        "3": lambda x: x["total_leads"],
        "4": lambda x: x["leads_inquiry"],
        "5": lambda x: x["leads_to_registration"],
        "6": lambda x: x["leads_to_admission_test"],
        "7": lambda x: x["leads_to_admission_offered"],
        "8": lambda x: x["leads_to_admission_confirmed"],
        "9": lambda x: x["leads_lost"],
        "10": lambda x: x["conversion_rate"],
        "11": lambda x: x["average_days_to_conversion"] if isinstance(x["average_days_to_conversion"], (int, float)) else float("inf"),
    }
        
    # Sort dynamically based on user selection
    if sort_column in valid_sort_keys:
        agent_data = sorted(agent_data, key=valid_sort_keys[sort_column], reverse=reverse_sort)

    # Render the performance template
    return render(request, 'inquiries/agent_performance.html', {
        'agent_data': agent_data,
        'sort_column': sort_column,
        'sort_order': sort_order
        }
    )


# ====================================================================================

@login_required
@user_passes_test(is_staff)
def export_inquiries_excel(request):
    user = request.user  # Get the logged-in user

    # If the user is an admin, get all inquiries; otherwise, get only the logged-in agent's inquiries
    if user.role=="Admin":
        inquiries = Lead.objects.all()
    else:
        inquiries = Lead.objects.all()
        
        # inquiries = Lead.objects.filter(assigned_agent__user=user)  # Filter only assigned inquiries for the agent

    # Create a workbook and select the active worksheet
    workbook = Workbook()   # Create a new Excel workbook
    worksheet = workbook.active  # Gets the default (active) sheet in the workbook.
    worksheet.title = "Inquiries"   # Rename the sheet to "Inquiries"

    # Add the header row
    headers = [
        'Student Name', 'Parent Name', 'Mobile Number', 'Email', 'Address', 'Block',
        'Location/Panchayat', 'Inquiry Source', 'Student Class', 'Status',
        'Remarks', 'Inquiry Date', 'Registration Date',
        'Admission Test Date', 'Admission Offered Date', 'Admission Confirmed Date', 
        'Rejected Date', 'Follow-up Date', 'Last Follow-up Updation', 'Last Inquiry Updation', 'Assigned Agent', 'Admin Assigned'
    ]
    worksheet.append(headers)

    # Add inquiry data to the worksheet
    for inquiry in inquiries:
        worksheet.append([
            inquiry.student_name,
            inquiry.parent_name,
            inquiry.mobile_number,
            inquiry.email,
            inquiry.address,
            inquiry.block,
            inquiry.location_panchayat,
            inquiry.inquiry_source,
            inquiry.student_class,
            inquiry.status,
            inquiry.remarks or "N/A",
            inquiry.inquiry_date if inquiry.inquiry_date else "N/A",            
            inquiry.registration_date if inquiry.registration_date else "N/A",
            inquiry.admission_test_date if inquiry.admission_test_date else "N/A",
            inquiry.admission_offered_date if inquiry.admission_offered_date else "N/A",
            inquiry.admission_confirmed_date if inquiry.admission_confirmed_date else "N/A",
            inquiry.rejected_date if inquiry.rejected_date else "N/A",
            inquiry.follow_up_date if inquiry.follow_up_date else "N/A",
            inquiry.last_follow_up_updation if inquiry.last_follow_up_updation else "N/A",
            inquiry.last_inquiry_updation if inquiry.last_inquiry_updation else "N/A",
            
            inquiry.assigned_agent.email if inquiry.assigned_agent else "N/A",
            inquiry.admin_assigned.email if inquiry.admin_assigned else "N/A"
        ])

    # Set the response content type and save the workbook to the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')   # This tells Django that the response contains an Excel file (.xlsx format).
    
    response['Content-Disposition'] = 'attachment; filename="inquiries.xlsx"'   # This forces a file download instead of displaying raw data in the browser. The file will be named inquiries.xlsx when downloaded.

    workbook.save(response)     # saving the Excel file directly into the HTTP response
    return response     # Sends the Excel file as a downloadable response to the user

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def export_users_excel(request): 
    school_users = CustomUser.objects.all()
   
    # Create a workbook and select the active worksheet
    workbook = Workbook()   # Create a new Excel workbook
    worksheet = workbook.active  # Gets the default (active) sheet in the workbook.
    worksheet.title = "Users"   # Rename the sheet to "Inquiries"

    # Add the header row
    headers = [
        'Name', 'Email', 'Mobile Number', 'Role', 'Expiration Date'
    ]
    worksheet.append(headers)

    # Add inquiry data to the worksheet
    for school_user in school_users:
        expiration_time = school_user.expiration_time
        if expiration_time:
            expiration_time = expiration_time.replace(tzinfo=None)
        else:
            expiration_time = "N/A"
    
        worksheet.append([
            school_user.name,                        
            school_user.email,
            school_user.mobile_number, 
            school_user.role,            
            expiration_time
        ])

    # Set the response content type and save the workbook to the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')   # This tells Django that the response contains an Excel file (.xlsx format).
    
    response['Content-Disposition'] = 'attachment; filename="inquiries.xlsx"'   # This forces a file download instead of displaying raw data in the browser. The file will be named inquiries.xlsx when downloaded.

    workbook.save(response)     # saving the Excel file directly into the HTTP response
    return response     # Sends the Excel file as a downloadable response to the user

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def assign_lead_to_agent_view(request):
    inquiries = Filter_Inquiries(request)
    agents = CustomUser.objects.filter(role="Agent")
    

    if request.method == 'POST':
        # print("=======================> request = ", request)
        inquiry_id = request.POST.get('inquiry_id')  # Get selected inquiry ID
        agent_id = request.POST.get('agent_id')  # Get selected agent ID

        # Validate input
        if not inquiry_id or not agent_id:
            messages.error(request, "Please select both an inquiry and an agent.")
            return redirect('assign_lead')

        try:
            # Get the inquiry and agent objects
            inquiry = get_object_or_404(Lead, id=inquiry_id)
            agent = get_object_or_404(CustomUser, id=agent_id)
            
            old_inquiry_instance = Lead.objects.get(id=inquiry_id)
                    
            # Assign the agent to the inquiry
            inquiry.assigned_agent = agent
            inquiry.save()
            
            new_inquiry_instance = inquiry
            
            Save_Lead_Logs(old_inquiry_instance, new_inquiry_instance, request.user)
            
            # Provide success feedback to the user
            messages.success(request, f"'{inquiry.student_name}' has been successfully assigned to Agent '{agent.name}'.")
            
            
            # Inside your POST block, before redirecting, we have to preserve the query parameters of filter component
            query_dict = request.POST.copy()
            query_dict.pop('inquiry_id', None)
            query_dict.pop('agent_id', None)
            query_dict.pop('csrfmiddlewaretoken', None)
            query_string = urlencode(query_dict)
            # print("=====================> query_dict = ",query_string)
            redirect_url = reverse('assign_lead')
            if query_string:
                redirect_url += f"?{query_string}"
                                                
                        
        except Exception as e:
            # Handle unexpected errors gracefully
            messages.error(request, f"An error occurred while assigning the lead: {str(e)}")
            redirect_url = reverse('assign_lead')
                    
                    
        return redirect(redirect_url)

    # If request is GET
    return render(request, 'inquiries/assign_lead.html', {
        'inquiries': inquiries,
        'agents': agents,
        'actions': ['Assign Agent'],
        'base_url_name': reverse('assign_lead'),
    })
    
# ====================================================================================

@login_required
@user_passes_test(is_agent_or_admin)
def delete_inquiry(request, id):
    # Get the inquiry by ID
    inquiry = get_object_or_404(Lead, id=id)

    # Delete the inquiry
    inquiry.delete()

    # Add a success message
    messages.success(request, "Inquiry deleted successfully!")

    # Redirect to the inquiry list
    return redirect('inquiry_list')

# ====================================================================================

# Helper function to send the email with the default password
def send_staff_welcome_email(agent, default_password):
    subject = "Welcome to the Team!"
    message = f"Hello {agent.name},\n\n" \
              f"Your account has been created successfully.\n\n" \
              f"Here are your login credentials:\n" \
              f"Phone: {agent.mobile_number}\n" \
              f"Password: {default_password}\n\n" \
              f"Please login and change your password after the first login.\n\n" \
              f"Best regards,\nThe Team"
    
    # send_mail(
    #     subject=subject,
    #     message=message,
    #     from_email=settings.DEFAULT_FROM_EMAIL,  # Default email set in settings.py
    #     recipient_list=[agent.email],
    #     fail_silently=False,
    # )
    

# Helper function to send the email with the default password
def send_custom_mail(subject, message, sender_mail): 
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,  # Default email set in settings.py
        recipient_list=[sender_mail],
        fail_silently=False,
    )

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def agent_list(request):
    # Get filter query parameters
    name_filter = request.GET.get('name', '')
    email_filter = request.GET.get('email', '')
    min_conversion_rate_filter = request.GET.get('min_conversion_rate', '')
    max_conversion_rate_filter = request.GET.get('max_conversion_rate', '')
    min_leads_converted_filter = request.GET.get('min_leads_converted', '')
    max_leads_converted_filter = request.GET.get('max_leads_converted', '')
    min_leads_handled_filter = request.GET.get('min_leads_handled', '')
    max_leads_handled_filter = request.GET.get('max_leads_handled', '')
        
    '''
    1) Coalesce() prevents division by zero by replacing lead_count = 0 with 1
    
    2) lead_count and converted_leads are not python variable but database generated values. So to use it in python, you have to access it using F(lead_count).
    
    3) output_field=FloatField() tells Django that the result of the expression will be a floating-point number (decimal).
    '''
    agents = CustomUser.objects.filter(role="Agent").annotate(
        lead_count=Count('assigned_agent'),       # total leads given agent is handling
        converted_leads=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Confirmed")),    # total leads an agent converted successfully
        conversion_rate=ExpressionWrapper(
            100.0*F("converted_leads")/Coalesce(F('lead_count'), 1),
            output_field=FloatField()
        )        
    )
    
    # Filter agents based on the query parameters
    if name_filter:
        agents = agents.filter(name__icontains=name_filter)
    if email_filter:
        agents = agents.filter(user__email__icontains=email_filter)            
            
    
    # Apply remaining filters    
    if min_leads_handled_filter:
        agents = agents.filter(lead_count__gte=int(min_leads_handled_filter))
    if max_leads_handled_filter:
        agents = agents.filter(lead_count__lte=int(max_leads_handled_filter))
    if min_leads_converted_filter:
        agents = agents.filter(converted_leads__gte=int(min_leads_converted_filter))
    if max_leads_converted_filter:
        agents = agents.filter(converted_leads__lte=int(max_leads_converted_filter))
    if min_conversion_rate_filter:
        agents = agents.filter(conversion_rate__gte=float(min_conversion_rate_filter))
    if max_conversion_rate_filter:
        agents = agents.filter(conversion_rate__lte=float(max_conversion_rate_filter))
        


    # Handle deletion of agents
    if request.method == 'POST':  # Handle agent deletion
        agent_id = request.POST.get('agent_id')  # Get the agent ID from the form
        agent = get_object_or_404(CustomUser, id=agent_id)        
        agent.delete()      
        messages.success(request, f"Agent '{agent.name}' has been deleted successfully.")
        return redirect('agent_list')  # Refresh the agent list after deletion

    
    
    # For GET request
    return render(request, 'inquiries/agent_list.html', {
        'agents': agents,
        'name_filter': name_filter,
        'email_filter': email_filter,
        'min_conversion_rate_filter' : min_conversion_rate_filter,
        "max_conversion_rate_filter" : max_conversion_rate_filter,
        "min_leads_converted_filter" : min_leads_converted_filter,
        "max_leads_converted_filter" : max_leads_converted_filter,
        "min_leads_handled_filter" : min_leads_handled_filter,
        "max_leads_handled_filter" : max_leads_handled_filter,
    })
    
# ====================================================================================
@login_required
@user_passes_test(is_staff)
def lead_logs_view(request, lead_id):
    lead = Lead.objects.get(id=lead_id)   
    logs = LeadLogs.objects.filter(lead_id=lead_id).order_by('-changed_at')  # Sort by changed_at (ascending)

    for log in logs:
        previous_data = json.loads(log.previous_data)  # Convert JSON string to python dictionary
        new_data = json.loads(log.new_data)  
        
        # print("TYPE prev:", type(previous_data))
        # print("TYPE new:", type(new_data))    
        # print("TYPE prevlog:", type(log.previous_data))
        # print("TYPE newlog:", type(log.new_data))  
        
        # print("==================> previous data = ",previous_data)
        # print("==================> new data = ",new_data)
        
        all_fields = set(previous_data.keys()).union(set(new_data.keys()))
                
        changes = {}

        # Identify changed fields        
        for field in all_fields:
            old_value = previous_data.get(field)
            new_value = new_data.get(field)
    
            if old_value != new_value:
                if(field == "assigned_agent" or field == "admin_assigned"):
                    old_user = CustomUser.objects.get(id=old_value) if old_value else None
                    new_user = CustomUser.objects.get(id=new_value) if new_value else None
                    
                    old_name_id = f"{old_user.name} (Id: {old_value})" if old_user else "N/A"
                    new_name_id = f"{new_user.name} (Id: {new_value})" if new_user else "N/A"
                
                    changes[field] = {
                        'old': old_name_id,
                        'new': new_name_id
                    }
                
                else:
                    changes[field] = {
                        'old': old_value,
                        'new': new_value
                    }

        log.changes = changes  # Attach changes to the log object

    return render(request, 'inquiries/lead_logs.html', {'lead': lead, 'logs': logs})

# ====================================================================================
def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + '@' + '#'
    return ''.join(random.choices(characters, k=length))


@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        # print("======================> the form is: ", form)
        if form.is_valid():
            # print("======================> form is valid")
            user = form.save(commit=False)
            random_password = generate_random_password()
            # print("=========================> settig random password as = ",random_password)
            user.set_password(random_password)
            user.save()
            
            send_staff_welcome_email(user, random_password)
            
            messages.success(request, 'User added successfully!')
            # print("===========> Messages: ", messages.get_messages(request))
            return redirect('add_user')  # Replace with your target redirect
        else:
            # print("======================> form is not valid")
            # print("================> Errors:", form.errors.as_json())
            errors = "\n".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
            messages.error(request, f"There was an error in your form:\n{errors}")
            return redirect('add_user')
    else:        
        form = CustomUserForm()
        users = CustomUser.objects.all()
        return render(request, 'inquiries/add_user.html', {'form': form, 'users': users})

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def manage_access(request):
    users = CustomUser.objects.all()
    
    if request.method == "POST":
        action = request.POST.get("action_type")
        user_id = request.POST.get("user_id")

        if action == "delete":
            user = get_object_or_404(CustomUser, id=user_id)
            user.delete()
            messages.success(request, "User deleted successfully.")
            return redirect("manage_access")

        elif action == "update":
            user = get_object_or_404(CustomUser, id=user_id)
            form = CustomUserForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "User updated successfully.")
                return render(request, 'inquiries/manage_access.html', {'form': form,'users': users})

            else:
                errors = "\n".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])              
                messages.error(request, f"Error updating user:\n{errors}")
                return render(request, 'inquiries/manage_access.html', {'form': form,'users': users})

    
    elif request.method == "GET" and "edit_user_id" in request.GET:
        user_id = request.GET.get("edit_user_id")
        user_to_edit = get_object_or_404(CustomUser, pk=user_id)
        form = CustomUserForm(instance=user_to_edit)        
        return render(request, 'inquiries/manage_access.html', {'form': form,'users': users})
        
    else:
        form = CustomUserForm()        
        return render(request, 'inquiries/manage_access.html', {'form': form,'users': users})
# ====================================================================================

# View to add agent
@login_required
@user_passes_test(is_admin)  # Make sure only admin can access this
def add_agent(request):
    if request.method == 'POST':
        form = AgentForm(request.POST)
        if form.is_valid():
            # Get the form data
            email = form.cleaned_data['email']
            # agent_name = form.cleaned_data['name']  # cleaned_data strips out unnecessary whitespace and converts data to the appropriate types.            
            # performance_score = form.cleaned_data['performance_score']
            
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "An agent with this email already exists.")
                return render(request, 'inquiries/add_agent.html', {'form': form})


            # Create the User for the agent with a default password
            default_password = 'DefaultPassword123!'
            #default_password = generate_random_password
            
            user = CustomUser.objects.create_user(username=email, email=email, password=default_password)

            # Create the agent object and associate with the user
            agent = form.save(commit=False)  # Don't save yet; we need to associate it with the user. We just need to create the instance of the Agent as of now.         
            agent.save()

            # Send the email with the default password
            send_staff_welcome_email(agent, default_password)

            # Show success message
            messages.success(request, f"Agent '{agent.name}' added successfully! The default password has been sent to their email.")
            return redirect('add_agent')  # Redirect to the same page after success
        else:
            messages.error(request, "Error adding agent. Please correct the errors below.")
    else:
        form = AgentForm()

    return render(request, 'inquiries/add_agent.html', {'form': form})


# ====================================================================================

def password_reset_request(request):
    if request.method == 'GET':
        return render(request, 'inquiries/registration/password_reset_request.html')

    elif request.method == 'POST':
        email = request.POST.get('email')
        user = CustomUser.objects.filter(email=email).first()

        if user:
            # Generate token and reset URL
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse('set_new_password', kwargs={'uidb64': uid, 'token': token})
            )
            
            # print("=========================> reset url = ", reset_url)

            # Render and send the email
            subject = "Reset Your Password"
            message = f"Please find the below link to reset your password:\n{reset_url}"                   

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)

            messages.success(request, "Reset link has been sent to the mail !")
            return render(request, 'inquiries/registration/password_reset_request.html')

        else:
            messages.error(request, "Mail not registered !")
            return render(request, 'inquiries/registration/password_reset_request.html')

# ====================================================================================

def set_new_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            if password1 != password2:
                return render(request, 'inquiries/registration/set_new_password.html', {'error': 'Passwords do not match.'})
            elif len(password1) < 5:
                return render(request, 'inquiries/registration/set_new_password.html', {'error': 'Password must be at least 5 characters.'})
            else:
                user.set_password(password1)
                user.save()
                return redirect('login')
        else:
            return render(request, 'inquiries/registration/set_new_password.html')
    else:
        return render(request, 'inquiries/registration/set_new_password.html', {'error': 'The reset link is invalid or has expired.'})

# ====================================================================================

def Prepare_Context_For_Filter_Leads_Component():
    agents = CustomUser.objects.filter(role="Agent")  
    lead_ids = Lead.objects.values_list('id', flat=True)
    students = Lead.objects.values_list('student_name', flat=True).distinct() 
    parents = Lead.objects.values_list('parent_name', flat=True).distinct() 
    locations_panchayats = Lead.objects.values_list('location_panchayat', flat=True).distinct()
    lead_emails = Lead.objects.values_list('email', flat=True).exclude(email__isnull=True)
    mobile_numbers = Lead.objects.values_list('mobile_number', flat=True).distinct()
    blocks = Lead.objects.values_list('block', flat=True).distinct()
    inquiry_sources = Lead.objects.values_list('inquiry_source', flat=True).distinct()
    statuses = Lead.objects.values_list('status', flat=True).distinct()
    student_classes = Lead.objects.values_list('student_class', flat=True).distinct()
    admins = CustomUser.objects.filter(role = "Admin")
    
    return {
        'lead_ids': lead_ids,
        'students': students,
        'parents': parents,
        'agents': agents,
        'lead_emails': lead_emails,
        'mobile_numbers': mobile_numbers,
        'location_panchayats': locations_panchayats,
        'blocks': blocks,
        'inquiry_sources': inquiry_sources,
        'statuses': statuses,
        'student_classes': student_classes,
        'admins': admins,
    }
    


def filter_inquiries_component(request):
    context = Prepare_Context_For_Filter_Leads_Component()
    return render(request, 'inquiries/Filter_Inquiries_Component.html', context)
    
# ====================================================================================

def hide_columns_component(request):
    table_class = request.GET.get('table_class')
    context = {
        'table_class': table_class,
        # any other context vars...
    } 
    return render(request, 'inquiries/Hide_Columns_Component.html', context)


def hide_agent_columns_component(request):
    table_class = request.GET.get('table_class')
    context = {
        'table_class': table_class,
        # any other context vars...
    } 
    return render(request, 'inquiries/agent/Hide_Columns_Component.html', context)
    
# ====================================================================================

# def Filter_By_Date(inquiries, choice, request_parameter, model_key):
#     if request_parameter:
#         date_val = datetime.strptime(request_parameter, "%Y-%m-%d").date()
        
#         if(choice == "from"):
#             inquiries = inquiries.filter(**{f"{model_key}__gte" : date_val})
        
#         elif(choice == "to"):
#             inquiries = inquiries.filter(**{f"{model_key}__lte" : date_val})
                                
#     return inquiries



def Filter_Agents_By_Numbers(agents, choice, request_parameter, status):
    if request_parameter:
        agents = agents.filter(role='Agent')
        number = int(request_parameter)

        # Annotate each agent with count of leads matching the status
        if status:
            agents = agents.annotate(
                total_count=Count('assigned_agent', filter=Q(assigned_agent__status=status))
            )
        else:
            agents = agents.annotate(
                total_count=Count('assigned_agent')
            )

        # Filter based on min or max
        if choice == "min":
            agents = agents.filter(total_count__gte=number)
        elif choice == "max":
            agents = agents.filter(total_count__lte=number)

    return agents



def Filter_Agents_By_Conversion_Rate(agents, choice, request_parameter):
    if request_parameter:
        agents = agents.filter(role='Agent')
        rate = float(request_parameter)

        # Annotate total and converted leads per agent
        agents = agents.annotate(
            total_leads=Count('assigned_agent'),
            confirmed_leads=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Confirmed")),
        ).annotate(
            conversion_rate=ExpressionWrapper(
                F('confirmed_leads') * 100.0 / F('total_leads'),
                output_field=FloatField()
            )
        )

        # Filter by conversion rate
        if choice == "min":
            agents = agents.filter(conversion_rate__gte=rate)
        elif choice == "max":
            agents = agents.filter(conversion_rate__lte=rate)

    return agents
    
# ====================================================================================================================================================================== 
def Filter_School_Users(users, request):
    # Handle filters from the GET request
    user_id = request.GET.get('user_id')
    # print("==============================> user_id = ", user_id)
    if user_id:
        users = users.filter(id=user_id)
        
    user_role = request.GET.get('user_role')    
    if user_role:        
        users = users.filter(role=user_role)
        
    user_name = request.GET.get('user_name')
    if user_name:
        users = users.filter(name__icontains=user_name)
        
    user_email = request.GET.get('user_email')
    if user_email:
        users = users.filter(email__icontains=user_email)

    mobile_number = request.GET.get('mobile_number')
    if mobile_number:
        users = users.filter(mobile_number__icontains=mobile_number)
        
    expiry = request.GET.get('expiry')
    if expiry=='Inactive':
        users = users.filter(expiration_time__lte=timezone.now())
    elif expiry == 'Active':
        users = users.filter(expiration_time__gt=timezone.now())
        
    users = Filter_By_Date(users, 'from', request.GET.get('expiration_date_from'), 'expiration_time')
    users = Filter_By_Date(users, 'to', request.GET.get('expiration_date_to'), 'expiration_time')
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('total_leads_assigned_min'), None)
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('total_leads_assigned_max'), None)
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_inquiry_min'), 'Inquiry')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_inquiry_max'), 'Inquiry')
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_inquiry_min'), 'Inquiry')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_inquiry_max'), 'Inquiry')
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_registration_min'), 'Registration')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_registration_max'), 'Registration')
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_admission_test_min'), 'Admission Test')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_admission_test_max'), 'Admission Test')
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_admission_offered_min'), 'Admission Offered')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_admission_offered_max'), 'Admission Offered')    
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_admission_confirmed_min'), 'Admission Confirmed')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_admission_confirmed_max'), 'Admission Confirmed')
    
    users = Filter_Agents_By_Numbers(users, 'min', request.GET.get('leads_in_rejected_min'), 'Rejected')
    users = Filter_Agents_By_Numbers(users, 'max', request.GET.get('leads_in_rejected_max'), 'Rejected')
    
    users = Filter_Agents_By_Conversion_Rate(users, 'min', request.GET.get('conversion_rate_min'))
    users = Filter_Agents_By_Conversion_Rate(users, 'max', request.GET.get('conversion_rate_max'))
    
    return users

# ====================================================================================

def Context_For_Filtering_School_Users(role):
    if role == "Agent":
        Filter_Objects = CustomUser.objects.filter(role='Agent')
    elif role == "Admin":
        Filter_Objects = CustomUser.objects.filter(role='Admin')
    else:
        Filter_Objects = CustomUser.objects
        
    user_ids = Filter_Objects.values_list('id', flat=True)
    names = Filter_Objects.values_list('name', flat=True).distinct() 
    roles = Filter_Objects.values_list('role', flat=True).distinct()        
    emails = Filter_Objects.values_list('email', flat=True).exclude(email__isnull=True)
    mobile_numbers = Filter_Objects.values_list('mobile_number', flat=True).distinct().exclude(mobile_number__isnull=True).exclude(mobile_number="")
    
    # print("==================> mobile numbers = ", mobile_numbers)
    # print("==================> emails = ", emails)
    # print("==================> roles = ", roles)
        
    return {
        'user_ids': user_ids,
        'names': names,
        'roles': roles,
        'emails': emails,        
        'mobile_numbers': mobile_numbers,  
        'status': ['Active', 'Inactive']      
    }
    
# ====================================================================================

def filter_agents_component(request):
    context = Context_For_Filtering_School_Users("Agent")
    return render(request, 'inquiries/agent/Filter_Agents_Component.html', context)

# ====================================================================================

def Annotate_Performance_Fields_for_Agents(agents):
    agents = agents.annotate(
        total_leads_in_inquiry_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Inquiry")),

        total_leads_in_registration_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Registration")),
        total_leads_in_admission_test_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Test")),
        total_leads_in_admission_offered_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Offered")),
        total_leads_in_admission_confirmed_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Confirmed")),
        total_leads_in_rejected_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Rejected")),
        
        total_leads_handled=Count('assigned_agent'),
        conversion_rate=ExpressionWrapper(
            F('total_leads_in_admission_confirmed_phase') * 100.0 / F('total_leads_handled'),
            output_field=FloatField()
        )
    )
    
    return agents
# ====================================================================================

@login_required
@user_passes_test(is_admin)
def assign_leads_to_agents_view(request):
    agents = CustomUser.objects.filter(role="Agent")
    agents = Filter_School_Users(agents, request)
    agents = Annotate_Performance_Fields_for_Agents(agents)
    
    context = {
        'agents': agents,
        'actions': ['Manage Leads'],
        'show_performance_metrics': True,
        'base_url_name': reverse('assign_leads_to_agents'),
    }

    return render(request, 'inquiries/agent/assign_leads_to_agent.html', context)

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def bulk_assign_leads_view(request, agent_id):
    agent = get_object_or_404(CustomUser, id=agent_id)    
    
    if request.method == 'POST':
        # Extract the list of selected leads IDs
        selected_raw = request.POST.get('selected_bulk_leads', '[]')  # stringified JSON from input field
        
        try:
            selected_bulk_leads = json.loads(selected_raw)  # converted to Python list
        except json.JSONDecodeError:
            selected_bulk_leads = []
            
        # print("=============================> selectedBulkLeads = ", selected_bulk_leads)        
        # print("=============================> type(selectedBulkLeads) = ", type(selected_bulk_leads))
        
        # Step 1: Assign the selected leads
        leads_to_assign = Lead.objects.filter(id__in=selected_bulk_leads)
        for lead in leads_to_assign:
            if lead.assigned_agent != agent:
                old_lead_instance = Lead.objects.get(id=lead.id)  # Clone before change
                lead.assigned_agent = agent
                lead.save()
                Save_Lead_Logs(old_lead_instance, lead, request.user)
        
        # Step 2: Unassign previously assigned leads that are now deselected
        previously_assigned = set(
        Lead.objects.filter(assigned_agent=agent).values_list('id', flat=True))
        currently_selected = set(map(int, selected_bulk_leads))
        lead_ids_to_unassign = previously_assigned - currently_selected
        lead_objects_to_unassign = Lead.objects.filter(id__in=lead_ids_to_unassign)
        
        for lead in lead_objects_to_unassign:
            old_lead_instance = Lead.objects.get(id=lead.id)
            lead.assigned_agent = None
            lead.save()
            Save_Lead_Logs(old_lead_instance, lead, request.user)
        
        messages.success(request, f"Leads updated for {agent.name}")
        return redirect('assign_leads_to_agents')

        
            
    inquiries = Filter_Inquiries(request)
    heading = f"Assign Leads to Agent: {agent.name} (Id: {agent.id})"
    actions = ['Bulk Assign Leads']
    pre_selected_leads = list(inquiries.filter(assigned_agent=agent).values_list('id', flat=True))
    
    # print("===========================> pre_selected_leads = ", pre_selected_leads)
    
    context = Prepare_Context_For_Filter_Leads_Component()
    
    context.update({
        'agent_id': agent.id,
        'inquiries': inquiries,
        'heading': heading,
        'actions': actions,
        'dashboard_buttons': ["Open Filters", "View / Hide Columns", "Dashboard", "Assign Leads"],
        'pre_selected_leads': pre_selected_leads,
        'base_url_name': reverse('bulk_assign_leads', args=[agent.id]),
    })
    
    return render(request, 'inquiries/inquiry_list.html', context)

# ====================================================================================