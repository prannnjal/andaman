from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser, Lead, CustomUser, LeadLogs
from .forms import InquiryForm, UpdateLeadStatusForm, EditLeadForm, AgentUpdateLeadForm, CustomUserForm, UpdateUserForm, TransferLeadForm
from django.contrib.auth import authenticate, login
# Django's authenticate() function doesn't itself contain the authentication logic—it simply loops through all the backends listed in your AUTHENTICATION_BACKENDS setting and calls their authenticate() methods. 
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
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
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.db.models import Case, When, Value
from django.db.models import Count, Q
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from urllib.parse import urlencode
from django.db.models.functions import Round

# ======================================================================================================================================================================
def is_authentic(user):
    return user.is_authenticated and user.expiration_time > timezone.now()

def is_admin(user):
    return is_authentic(user) and user.role=="Admin"

def is_agent_or_admin(user):
    return  is_authentic(user) and user.role in ["Admin", "Agent"]
    
def is_staff(user):
    return is_authentic(user) and user.role in ["Admin", "Agent", "Viewer"]


# ======================================================================================================================================================================

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
# ======================================================================================================================================================================

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

    return render(request, 'inquiries/agent/agent_login.html')

# ======================================================================================================================================================================

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
    elif user.role=="Agent":  # Agents can only see leads assigned to them
        inquiries = Lead.objects.filter(assigned_agent=user)
        # print("=====================> after agent len(inquiries) filtered = ", len(inquiries)) 
    else:
        inquiries = Lead.objects.all()     # return an empty queryset if the user is neither an admin nor an agent
    
    
    
    #return inquiries    # remove later
    
    
    # Handle filters from the GET request
    lead_ids = query_params.getlist('lead_id[]')  # returns a list of selected lead IDs
    # print("=================> lead_id in filter view = ",lead_ids)
    if lead_ids:
        # Convert all values to integers, ignore non-digit entries
        lead_ids = [int(i) for i in lead_ids if str(i).isdigit()]
        inquiries = inquiries.filter(id__in=lead_ids)
        
    student_classes = query_params.getlist('student_class[]')
    if student_classes:
        inquiries = inquiries.filter(student_class__in=student_classes)
   
        
    student_names = query_params.getlist('student_name[]')
    if student_names:
        inquiries = inquiries.filter(student_name__in=student_names)
        
    parent_names = query_params.getlist('parent_name[]')
    if parent_names:
        inquiries = inquiries.filter(parent_name__in=parent_names)
        
    lead_emails = query_params.getlist('lead_email[]')
    if lead_emails:
        inquiries = inquiries.filter(email__in=lead_emails)
                
    mobile_numbers = query_params.getlist('mobile_number[]')
    if mobile_numbers:
        inquiries = inquiries.filter(mobile_number__in=mobile_numbers)
    
    blocks = query_params.getlist('block[]')
    if blocks:
        inquiries = inquiries.filter(block__in=blocks)
            
    location_panchayats = query_params.getlist('location_panchayat[]')
    if location_panchayats:
        inquiries = inquiries.filter(location_panchayat__in=location_panchayats)
        
    inquiry_sources = query_params.getlist('inquiry_source[]')
    if inquiry_sources:
        inquiries = inquiries.filter(inquiry_source__in=inquiry_sources)

    statuses = query_params.getlist('status[]')
    if statuses:
        inquiries = inquiries.filter(status__in=statuses)

    agent_ids = query_params.getlist('agent_id[]')
    if agent_ids:
        inquiries = inquiries.filter(assigned_agent__id__in=[int(id) for id in agent_ids])

    admin_ids = query_params.getlist('admin_id[]')
    if admin_ids:
        inquiries = inquiries.filter(admin_assigned__id__in = [int(id) for id in admin_ids])
     
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
    
    return inquiries

    
# =================================================================================================================================================================
    
@login_required
@user_passes_test(is_staff)
def inquiry_list(request):
    inquiries = Filter_Inquiries(request)
    
    # STEP 1: Load cached or store query parameters
    # if request.GET:
    #     request.session['last_inquiry_filters'] = request.GET.dict()
    #     query_params = request.GET
    # else:
    #     query_params = request.session.get('last_inquiry_filters', {})
        

    
    return render(request, 'inquiries/inquiry_list.html', {
        'heading': request.GET.get('heading', "Leads List"),
        'inquiries': inquiries,
        'actions': ['Update', 'Delete', 'View Logs'],
        'dashboard_buttons': ["Add Inquiry", "Open Filters", "View / Hide Columns", "Dashboard"],
        'base_url_name': reverse('inquiry_list')
    })

# ======================================================================================================================================================================


@login_required
@user_passes_test(is_admin)
def inquiries_updated_today_view(request):
    todays_date = now().date()
    
    inquiries = Filter_Inquiries(request)    
    inquiries = inquiries.filter(last_inquiry_updation__gte=todays_date)
            
    context = {
        'heading': 'Inquiries Updated Today',
        'inquiries': inquiries,
        'actions': ['Update', 'Delete', 'View Logs'],
        'dashboard_buttons': ["Add Inquiry", "Open Filters", "View / Hide Columns", "Dashboard"],
        'base_url_name': reverse('inquiries_updated_today')
    }

    return render(request, 'inquiries/inquiry_list.html', context)

# ================================================================================================================================================================

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
    lead_emails = Lead.objects.values_list('email', flat=True).exclude(email__isnull=True).distinct()
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
            
            # Auto-assign agent if no agent is assigned
            if not inquiry.assigned_agent:
                auto_assigned_agent = auto_assign_agent_with_least_leads()
                if auto_assigned_agent:
                    inquiry.assigned_agent = auto_assigned_agent
                    messages.info(request, f"Lead automatically assigned to agent: {auto_assigned_agent.name}")
                else:
                    messages.warning(request, "No agents available for assignment.")
        
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
        
    return render(request, 'inquiries/add_update_lead.html', {'form': form, 'title': 'Add new Inquiry'})

# ================================================================================================================================================================
            
@login_required
@user_passes_test(is_agent_or_admin)
def manage_lead_status(request, inquiry_id):
    # Fetch the Lead instance for the given inquiry_id
    inquiry = get_object_or_404(Lead, id=inquiry_id)    # fetches that instance from Lead model whose id is=inquiry_id
    
    # Check if the current user can edit this lead
    if request.user.role == 'Agent' and inquiry.assigned_agent != request.user:
        messages.error(request, "You can only edit leads assigned to you.")
        return redirect('inquiry_list')

    if request.method == 'POST':
        # Use different forms based on user role
        if request.user.role == 'Admin':
            form = EditLeadForm(request.POST, instance=inquiry)
        else:
            form = AgentUpdateLeadForm(request.POST, instance=inquiry)
        
        if form.is_valid(): # Ensures all required fields are correctly filled.
            old_inquiry_instance = Lead.objects.get(id=inquiry.id)  # Fetch a fresh copy of the old data
    
            inquiry = form.save(commit=False)
            
            # For agents, preserve the read-only fields from the original instance
            if request.user.role == 'Agent':
                inquiry.inquiry_source = old_inquiry_instance.inquiry_source
                inquiry.admin_assigned = old_inquiry_instance.admin_assigned
                inquiry.assigned_agent = old_inquiry_instance.assigned_agent
            
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
        # Use different forms based on user role
        if request.user.role == 'Admin':
            form = EditLeadForm(instance=inquiry)
        else:
            form = AgentUpdateLeadForm(instance=inquiry)

    return render(request, 'inquiries/add_update_lead.html', {'form': form, 'title': 'Update Lead Status', 'location_panchayat_context': inquiry.location_panchayat, 'block_context': inquiry.block})

# ================================================================================================================================================================
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


# ================================================================================================================================================================

@login_required
@user_passes_test(is_staff)
def dashboard(request):
    # print("===========================> inside dashboard view")
    user = request.user  # Get the logged-in user

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.role == "Admin": 
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.filter(assigned_agent=user)  # Agent sees only their assigned inquiries

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

# ================================================================================================================================================================

@login_required
@user_passes_test(is_staff)
def detailed_stats(request):
    user = request.user  # Get the logged-in user

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.role=="Admin":
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.filter(assigned_agent=user)  # Agent sees only their assigned inquiries

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


# ================================================================================================================================================================

@login_required
@user_passes_test(is_staff)
def export_inquiries_excel(request):
    user = request.user  # Get the logged-in user

    # If the user is an admin, get all inquiries; otherwise, get only the logged-in agent's inquiries
    if user.role=="Admin":
        inquiries = Lead.objects.all()
    else:
        inquiries = Lead.objects.filter(assigned_agent=user)  # Filter only assigned inquiries for the agent

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

# ================================================================================================================================================================

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

# ================================================================================================================================================================

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
    
# ================================================================================================================================================================

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

# ================================================================================================================================================================

# Helper function to send the email with the default password
def send_staff_welcome_email(agent, custom_password):
    subject = "Welcome to the Team!"
    message = f"Hello {agent.name},\n\n" \
              f"Your account has been created successfully by the administrator.\n\n" \
              f"Here are your login credentials:\n" \
              f"Email: {agent.email}\n" \
              f"Phone: {agent.mobile_number}\n" \
              f"Password: {custom_password}\n\n" \
              f"Please login using either your email or phone number.\n" \
              f"You can change your password anytime using the 'Forgot Password' feature.\n\n" \
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

# ================================================================================================================================================================


# ================================================================================================================================================================
@login_required
@user_passes_test(is_staff)
def lead_logs_view(request, lead_id):
    lead = Lead.objects.get(id=lead_id)   
    logs = LeadLogs.objects.filter(lead_id=lead_id).order_by('-changed_at')  # Sort by changed_at (ascending)

    for log in logs:
        if isinstance(log.previous_data, str):
            previous_data = json.loads(log.previous_data)
        else:
            previous_data = log.previous_data
            
            
        if isinstance(log.new_data, str):
            new_data = json.loads(log.new_data)
        else:
            new_data = log.new_data
        
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
                    old_user = CustomUser.objects.filter(id=old_value).first() if old_value else None
                    new_user = CustomUser.objects.filter(id=new_value).first() if new_value else None
                    
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

# ================================================================================================================================================================
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
            
            # Use the custom password set by admin
            custom_password = form.cleaned_data['password1']
            user.set_password(custom_password)
            user.save()
            
            # Send welcome email with the custom password
            send_staff_welcome_email(user, custom_password)
            
            messages.success(request, f'User "{user.name}" added successfully with custom password!')
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
        return render(request, 'inquiries/agent/add_school_user.html', {'form': form, 'users': users})

# ================================================================================================================================================================

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

# ================================================================================================================================================================

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

# ================================================================================================================================================================

def Prepare_Context_For_Filter_Leads_Component(request):
    user = request.user
    
    # Filter data based on user role
    if user.role == "Admin":
        # Admin sees all data
        base_queryset = Lead.objects.all()
    else:
        # Agent sees only their assigned leads
        base_queryset = Lead.objects.filter(assigned_agent=user)
    
    agents = CustomUser.objects.filter(role="Agent")
    lead_ids = base_queryset.values_list('id', flat=True)
    students = base_queryset.values_list('student_name', flat=True).distinct()
    parents = base_queryset.values_list('parent_name', flat=True).distinct()
    locations_panchayats = base_queryset.values_list('location_panchayat', flat=True).distinct()
    lead_emails = base_queryset.values_list('email', flat=True).exclude(email__isnull=True).distinct()
    mobile_numbers = base_queryset.values_list('mobile_number', flat=True).distinct()
    blocks = base_queryset.values_list('block', flat=True).distinct()
    inquiry_sources = base_queryset.values_list('inquiry_source', flat=True).distinct()
    statuses = base_queryset.values_list('status', flat=True).distinct()
    student_classes = base_queryset.values_list('student_class', flat=True).distinct()
    admins = CustomUser.objects.filter(role = "Admin")
    
    # Store selected options of each select into a context variable
    query_params = request.GET
    
    selected_lead_ids = query_params.getlist('lead_id[]')
    selected_classes = query_params.getlist('student_class[]')
    selected_student_names = query_params.getlist('student_name[]')
    selected_parent_names = query_params.getlist('parent_name[]')
    selected_lead_emails = query_params.getlist('lead_email[]')
    selected_mobile_numbers = query_params.getlist('mobile_number[]')
    selected_blocks = query_params.getlist('block[]')
    selected_location_panchayats = query_params.getlist('location_panchayat[]')
    selected_inquiry_sources = query_params.getlist('inquiry_source[]')
    selected_statuses = query_params.getlist('status[]')
    selected_agent_ids = query_params.getlist('agent_id[]')
    selected_admin_ids = query_params.getlist('admin_id[]')
    
    # print("====================> selected_agent_ids = ", selected_agent_ids)
    
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
            
        # Store selected options of each select into a context variable
        "selected_lead_ids": selected_lead_ids,
        "selected_classes": selected_classes,
        "selected_student_names": selected_student_names,
        "selected_parent_names": selected_parent_names,
        "selected_lead_emails": selected_lead_emails,
        "selected_mobile_numbers": selected_mobile_numbers,
        "selected_blocks": selected_blocks,
        "selected_location_panchayats": selected_location_panchayats,
        "selected_inquiry_sources": selected_inquiry_sources,
        "selected_statuses": selected_statuses,
        "selected_agent_ids": selected_agent_ids,
        "selected_admin_ids": selected_admin_ids,
    }
    


def filter_inquiries_component(request):
    # print("🔍 =======================> Query Params:", request.GET)
    
    # lead_ids = request.GET.getlist('lead_id[]')
        

    context = Prepare_Context_For_Filter_Leads_Component(request)
    # print("🔍 =======================> context:", context)

    return render(request, 'inquiries/Filter_Inquiries_Component.html', context)
    
# ================================================================================================================================================================

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

# ================================================================================================================================================================

def Prepare_Context_For_Filtering_School_Users(role, request):
    if role == "Agent":
        Filter_Objects = CustomUser.objects.filter(role='Agent')
        heading = "Filter Agents"
    elif role == "Admin":
        Filter_Objects = CustomUser.objects.filter(role='Admin')
        heading = "Filter Admins"
    else:
        Filter_Objects = CustomUser.objects
        heading = "Filter Users"
        
    user_ids = Filter_Objects.values_list('id', flat=True)
    user_names = Filter_Objects.values_list('name', flat=True).distinct()
    user_emails = Filter_Objects.values_list('email', flat=True).exclude(email__isnull=True)
    mobile_numbers = Filter_Objects.values_list('mobile_number', flat=True).distinct().exclude(mobile_number__isnull=True).exclude(mobile_number="")
    # locations_panchayats = Filter_Objects.values_list('location_panchayat', flat=True).distinct()
    # blocks = Filter_Objects.values_list('block', flat=True).distinct()
    locations_panchayats = Filter_Objects.values_list('location_panchayat', flat=True).distinct()
    blocks = Filter_Objects.values_list('block', flat=True).distinct()
    
    roles = Filter_Objects.values_list('role', flat=True).distinct()
    
        
    # Store selected options of each select into a context variable
    query_params = request.GET
    
    selected_user_ids = query_params.getlist('user_id[]')
    selected_user_names = query_params.getlist('user_name[]')
    selected_user_emails = query_params.getlist('user_email[]')
    selected_mobile_numbers = query_params.getlist('mobile_number[]')
    selected_blocks = query_params.getlist('block[]')
    selected_locations_panchayats = query_params.getlist('location_panchayat[]')
    selected_roles = query_params.getlist('role[]')
    selected_statuses = query_params.getlist('status[]')
    
        
    return {
        'heading': heading,
        'user_ids': user_ids,
        'user_names': user_names,        
        'user_emails': user_emails,        
        'mobile_numbers': mobile_numbers,
        'locations_panchayats': locations_panchayats,
        'blocks': blocks,
        'roles': roles,
        'statuses': ['Active', 'Inactive'] ,
        
        # Store selected options of each select into a context variable
        'selected_user_ids': selected_user_ids,
        'selected_user_names': selected_user_names,
        'selected_user_emails': selected_user_emails,
        'selected_mobile_numbers': selected_mobile_numbers,
        'selected_blocks': selected_blocks,
        'selected_locations_panchayats': selected_locations_panchayats,
        'selected_roles': selected_roles,
        'selected_statuses': selected_statuses
    }
    
# ================================================================================================================================================================

def filter_agents_component(request):
    context = Prepare_Context_For_Filtering_School_Users("Agent", request)
    return render(request, 'inquiries/agent/Filter_Agents_Component.html', context)

# ================================================================================================================================================================

def Annotate_Performance_Fields_for_Agents(agents):
    agents = agents.annotate(
        total_leads_handled=Count('assigned_agent'),

        total_leads_in_inquiry_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Inquiry")),

        total_leads_in_registration_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Registration")),
        
        total_leads_in_admission_test_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Test")),
        
        total_leads_in_admission_offered_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Offered")),
        
        total_leads_in_admission_confirmed_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Admission Confirmed")),
        
        total_leads_in_rejected_phase=Count('assigned_agent', filter=Q(assigned_agent__status="Rejected")),
                
        conversion_rate = Case(
            When(total_leads_handled=0, then=Value(0.0)),
            default=Round(
                ExpressionWrapper(
                    F('total_leads_in_admission_confirmed_phase') * 100.0 / F('total_leads_handled'),
                    output_field=FloatField()
                ),
                precision=2
            ),
            output_field=FloatField()
        )
    )
    
    return agents

# ================================================================================================================================================================
def Filter_School_Users_By_Number(school_users, field, min_value, max_value):    
    if min_value:
        school_users = school_users.filter(**{f"{field}__gte": int(min_value)})
    
    if max_value:
        school_users = school_users.filter(**{f"{field}__lte": int(max_value)})
        
    return school_users
    
# ================================================================================================================================================================
def Filter_School_Users(school_users, request): # Make sure to run annotate function for Custom_User model first before calling this
    query_params = request.GET
    
    # Handle filters from the GET request
    user_ids = query_params.getlist('user_id[]')
    if user_ids:
        user_ids = [int(i) for i in user_ids if str(i).isdigit()]
        school_users = school_users.filter(id__in=user_ids)
            
    user_names = query_params.getlist('user_name[]')
    if user_names:
        school_users = school_users.filter(name__in=user_names)
          
    user_emails = query_params.getlist('user_email[]')
    if user_emails:
        school_users = school_users.filter(email__in=user_emails)
                
    mobile_numbers = query_params.getlist('mobile_number[]')
    if mobile_numbers:
        school_users = school_users.filter(mobile_number__in=mobile_numbers)
    
    blocks = query_params.getlist('block[]')
    if blocks:
        school_users = school_users.filter(block__in=blocks)
            
    location_panchayats = query_params.getlist('location_panchayat[]')
    if location_panchayats:
        school_users = school_users.filter(location_panchayat__in=location_panchayats)
        
    roles = query_params.getlist('role[]')
    if roles:
        school_users = school_users.filter(role__in=roles)
        
  
    statuses = query_params.getlist('status[]')
    if statuses:
        school_users = school_users.filter(status__in=statuses)

    # Filter dates
    school_users = Filter_By_Date(school_users, 'from', query_params.get('user_created_date_from'), 'date_joined')
    school_users = Filter_By_Date(school_users, 'to', query_params.get('user_created_date_to'), 'date_joined')
    
    school_users = Filter_By_Date(school_users, 'from', request.GET.get('expiration_date_from'), 'expiration_time')
    school_users = Filter_By_Date(school_users, 'to', request.GET.get('expiration_date_to'), 'expiration_time')
            
    
    # Filter numbers
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_handled', query_params.get('min_leads_handled'), query_params.get('max_leads_handled'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_admission_offered_phase', query_params.get('min_leads_converted'), query_params.get('max_leads_converted'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'conversion_rate', query_params.get('min_conversion_rate'), query_params.get('max_conversion_rate'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_inquiry_phase', query_params.get('min_leads_in_inquiry'), query_params.get('max_leads_in_inquiry'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_registration_phase', query_params.get('min_leads_in_registration'), query_params.get('max_leads_in_registration'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_admission_test_phase', query_params.get('min_leads_in_admission_test'), query_params.get('max_leads_in_admission_test'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_admission_offered_phase', query_params.get('min_leads_in_admission_offered'), query_params.get('max_leads_in_admission_offered'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_admission_confirmed_phase', query_params.get('min_leads_in_admission_confirmed'), query_params.get('max_leads_in_admission_confirmed'))
    
    school_users = Filter_School_Users_By_Number(school_users, 'total_leads_in_rejected_phase', query_params.get('min_leads_in_rejected'), query_params.get('max_leads_in_rejected'))
        
    return school_users
# ================================================================================================================================================================

@login_required
@user_passes_test(is_admin)
def school_users_list_view(request):
    users = CustomUser.objects.all()
    users = Annotate_Performance_Fields_for_Agents(users)
    users = Filter_School_Users(users, request)   # Run annotate part before calling it
    
    context = {
        'users': users,
        'actions': ['Manage Leads', 'Delete User', 'Update User'],
        'show_performance_metrics': True,
        'base_url_name': reverse('school_users_list'),
    }
    
    return render(request, 'inquiries/agent/school_users_list.html', context)

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def delete_school_user_view(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        user.delete()
    
    return redirect('school_users_list')

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
        return redirect('school_users_list')

        

    inquiries = Filter_Inquiries(request)
    heading = f"Assign Leads to Agent: {agent.name} (Id: {agent.id})"
    actions = ['Bulk Assign Leads']
    pre_selected_leads = list(inquiries.filter(assigned_agent=agent).values_list('id', flat=True))
    
    # print("===========================> pre_selected_leads = ", pre_selected_leads)
    
    context = Prepare_Context_For_Filter_Leads_Component(request)
    
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

@login_required
@user_passes_test(is_admin)
def auto_assign_unassigned_leads_view(request):
    """
    Bulk auto-assign all unassigned leads to agents with least workload
    """
    if request.method == 'POST':
        # Get all unassigned leads
        unassigned_leads = Lead.objects.filter(assigned_agent__isnull=True)
        
        if not unassigned_leads.exists():
            messages.info(request, "No unassigned leads found.")
            return redirect('inquiry_list')
        
        assigned_count = 0
        
        for lead in unassigned_leads:
            # Get agent with least leads for each lead
            auto_assigned_agent = auto_assign_agent_with_least_leads()
            if auto_assigned_agent:
                old_lead_instance = Lead.objects.get(id=lead.id)
                lead.assigned_agent = auto_assigned_agent
                lead.save()
                Save_Lead_Logs(old_lead_instance, lead, request.user)
                assigned_count += 1
        
        if assigned_count > 0:
            messages.success(request, f"Successfully auto-assigned {assigned_count} leads to agents.")
        else:
            messages.warning(request, "No agents available for assignment.")
        
        return redirect('inquiry_list')
    
    return redirect('inquiry_list')

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def update_school_user_view(request):
    print("=======================> inside update school user view")
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        print("==========================> user_id = ", user_id)
        user = get_object_or_404(CustomUser, id=user_id)
        form = UpdateUserForm(request.POST, instance=user)
        # print("==========================> form = ", form)
        
        if form.is_valid():
            # Save the user data
            updated_user = form.save(commit=False)
            
            # Handle password change if provided
            password1 = form.cleaned_data.get('password1')
            if password1:
                updated_user.set_password(password1)
                messages.success(request, f"User '{updated_user.name}' updated successfully with new password.")
            else:
                messages.success(request, f"User '{updated_user.name}' updated successfully.")
            
            updated_user.save()
            return render(request, 'inquiries/agent/Update_School_User_Component.html', {'form': form})

        else:
            errors = "\n".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
            messages.error(request, f"Error updating user:\n{errors}")
            return render(request, 'inquiries/agent/Update_School_User_Component.html', {'form': form})

    
    else:
        user_id = request.GET.get("edit_user_id")
        user_to_edit = get_object_or_404(CustomUser, pk=user_id)
        form = UpdateUserForm(instance=user_to_edit)
        return render(request, 'inquiries/agent/Update_School_User_Component.html', {'form': form})

# ====================================================================================



# ====================================================================================

def auto_assign_agent_with_least_leads():
    """
    Automatically assigns the agent with the least number of leads.
    Returns the agent object or None if no agents are available.
    """
    return Lead.get_agent_with_least_leads()

# ====================================================================================

@login_required
@user_passes_test(is_staff)
def log_call_view(request):
    """
    Log phone calls made by agents
    """
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        
        try:
            data = json.loads(request.body)
            student_name = data.get('student_name')
            phone_number = data.get('phone_number')
            agent_name = data.get('agent')
            timestamp = data.get('timestamp')
            
            # Log the call (you can save this to a database if needed)
            print(f"Call logged: Agent {agent_name} called {student_name} at {phone_number} on {timestamp}")
            
            # You can create a CallLog model to store this information
            # CallLog.objects.create(
            #     agent=request.user,
            #     student_name=student_name,
            #     phone_number=phone_number,
            #     call_time=timestamp
            # )
            
            return JsonResponse({'status': 'success', 'message': 'Call logged successfully'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed'}, status=405)

# ====================================================================================

@login_required
@user_passes_test(is_agent_or_admin)
def transfer_lead_view(request, lead_id):
    """
    Transfer a lead to another agent
    """
    lead = get_object_or_404(Lead, id=lead_id)
    
    # Check if the current user can transfer this lead
    if request.user.role == 'Agent' and lead.assigned_agent != request.user:
        messages.error(request, "You can only transfer leads assigned to you.")
        return redirect('inquiry_list')
    
    if request.method == 'POST':
        form = TransferLeadForm(request.POST, current_agent=request.user)
        if form.is_valid():
            target_agent = form.cleaned_data['target_agent']
            transfer_reason = form.cleaned_data['transfer_reason']
            
            # Store the old agent for logging
            old_agent = lead.assigned_agent
            
            # Update the lead
            lead.transferred_from = old_agent
            lead.transferred_to = target_agent
            lead.assigned_agent = target_agent
            lead.transfer_date = timezone.now()
            lead.transfer_reason = transfer_reason
            lead.save()
            
            # Log the transfer
            Save_Lead_Logs(
                old_inquiry_instance=Lead.objects.get(id=lead.id),  # Get fresh instance
                new_inquiry_instance=lead,
                changed_by=request.user
            )
            
            messages.success(
                request, 
                f"Lead '{lead.student_name}' successfully transferred from {old_agent.name if old_agent else 'Unassigned'} to {target_agent.name}"
            )
            return redirect('inquiry_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TransferLeadForm(current_agent=request.user)
    
    context = {
        'form': form,
        'lead': lead,
        'current_agent': request.user
    }
    
    return render(request, 'inquiries/transfer_lead.html', context)