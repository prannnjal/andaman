from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import CustomUser, Lead, CustomUser, LeadLogs, Hotel, CompanySettings, Package, PackageDay, RoomCategory, ItineraryBuilder, ItineraryDay, EventPlace, HotelBooking
from .forms import InquiryForm, UpdateLeadStatusForm, SimpleInquiryForm, EditLeadForm, AgentUpdateLeadForm, CustomUserForm, UpdateUserForm, TransferLeadForm
from django.contrib.auth import authenticate, login
# Django's authenticate() function doesn't itself contain the authentication logic—it simply loops through all the backends listed in your AUTHENTICATION_BACKENDS setting and calls their authenticate() methods. 
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
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
import os
from django.db.models import Avg, Sum
from .proposal_generator import ProposalGenerator

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

def Filter_By_When(inquiries, when_filter):
    """
    Filter inquiries by relative time periods based on inquiry_date
    """
    from datetime import timedelta
    today = timezone.now().date()
    
    if when_filter == 'today':
        inquiries = inquiries.filter(inquiry_date=today)
    elif when_filter == 'yesterday':
        yesterday = today - timedelta(days=1)
        inquiries = inquiries.filter(inquiry_date=yesterday)
    elif when_filter == 'this_week':
        # Get start of current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        inquiries = inquiries.filter(inquiry_date__gte=start_of_week, inquiry_date__lte=today)
    elif when_filter == 'last_week':
        # Get start of last week (Monday)
        start_of_last_week = today - timedelta(days=today.weekday() + 7)
        end_of_last_week = start_of_last_week + timedelta(days=6)
        inquiries = inquiries.filter(inquiry_date__gte=start_of_last_week, inquiry_date__lte=end_of_last_week)
    elif when_filter == 'this_month':
        # Get start of current month
        start_of_month = today.replace(day=1)
        inquiries = inquiries.filter(inquiry_date__gte=start_of_month, inquiry_date__lte=today)
    elif when_filter == 'last_month':
        # Get start of last month
        if today.month == 1:
            start_of_last_month = today.replace(year=today.year-1, month=12, day=1)
        else:
            start_of_last_month = today.replace(month=today.month-1, day=1)
        # Get end of last month
        if today.month == 1:
            end_of_last_month = today.replace(year=today.year-1, month=12, day=1) - timedelta(days=1)
        else:
            end_of_last_month = today.replace(month=today.month, day=1) - timedelta(days=1)
        inquiries = inquiries.filter(inquiry_date__gte=start_of_last_month, inquiry_date__lte=end_of_last_month)
    elif when_filter == 'this_year':
        # Get start of current year
        start_of_year = today.replace(month=1, day=1)
        inquiries = inquiries.filter(inquiry_date__gte=start_of_year, inquiry_date__lte=today)
    elif when_filter == 'last_year':
        # Get start of last year
        start_of_last_year = today.replace(year=today.year-1, month=1, day=1)
        end_of_last_year = today.replace(year=today.year-1, month=12, day=31)
        inquiries = inquiries.filter(inquiry_date__gte=start_of_last_year, inquiry_date__lte=end_of_last_year)
    elif when_filter == 'last_7_days':
        # Last 7 days including today
        start_date = today - timedelta(days=6)
        inquiries = inquiries.filter(inquiry_date__gte=start_date, inquiry_date__lte=today)
    elif when_filter == 'last_30_days':
        # Last 30 days including today
        start_date = today - timedelta(days=29)
        inquiries = inquiries.filter(inquiry_date__gte=start_date, inquiry_date__lte=today)
    elif when_filter == 'last_90_days':
        # Last 90 days including today
        start_date = today - timedelta(days=89)
        inquiries = inquiries.filter(inquiry_date__gte=start_date, inquiry_date__lte=today)
    
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
    elif user.role=="Agent":  # Agents can see their assigned leads + viewer leads
        # Use Q objects to combine queries instead of union
        from django.db.models import Q
        inquiries = Lead.objects.filter(
            Q(assigned_agent=user) | Q(assigned_agent__isnull=True)
        )
        # print("=====================> after agent len(inquiries) filtered = ", len(inquiries)) 
    else:
        inquiries = Lead.objects.all()     # return an empty queryset if the user is neither an admin nor an agent
    
    
    
    #return inquiries    # remove later
    
    
    # Handle filters from the GET request
    # If segment=schools and no school selected, return empty list
    segment = query_params.get('segment')
    if segment == 'schools' and not query_params.getlist('school_id[]'):
        return Lead.objects.none()
    lead_ids = query_params.getlist('lead_id[]')  # returns a list of selected lead IDs
    # print("=================> lead_id in filter view = ",lead_ids)
    if lead_ids:
        # Convert all values to integers, ignore non-digit entries
        lead_ids = [int(i) for i in lead_ids if str(i).isdigit()]
        inquiries = inquiries.filter(id__in=lead_ids)
        
    travel_types = query_params.getlist('travel_type[]')
    if travel_types:
        inquiries = inquiries.filter(travel_type__in=travel_types)
   
        
    customer_names = query_params.getlist('customer_name[]')
    if customer_names:
        inquiries = inquiries.filter(customer_name__in=customer_names)
        
    destinations = query_params.getlist('destination[]')
    if destinations:
        inquiries = inquiries.filter(destination__in=destinations)
        
    lead_emails = query_params.getlist('lead_email[]')
    if lead_emails:
        inquiries = inquiries.filter(email__in=lead_emails)
                
    mobile_numbers = query_params.getlist('mobile_number[]')
    if mobile_numbers:
        inquiries = inquiries.filter(mobile_number__in=mobile_numbers)
    

            

        
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

    # Filter by school ids (new Schools segment)
    school_ids = query_params.getlist('school_id[]')
    if school_ids:
        try:
            school_ids = [int(i) for i in school_ids]
            inquiries = inquiries.filter(school_id__in=school_ids)
        except Exception:
            pass
     
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
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('last_follow_up_updation_from'), 'last_follow_up_updation')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('last_follow_up_updation_to'), 'last_follow_up_updation')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('last_inquiry_updation_from'), 'last_inquiry_updation')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('last_inquiry_updation_to'), 'last_inquiry_updation')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('rejected_date_from'), 'rejected_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('rejected_date_to'), 'rejected_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('follow_up_date_from'), 'follow_up_date')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('follow_up_date_to'), 'follow_up_date')
    
    inquiries = Filter_By_Date(inquiries, 'from', query_params.get('last_inquiry_updation_from'), 'last_inquiry_updation')
    inquiries = Filter_By_Date(inquiries, 'to', query_params.get('last_inquiry_updation_to'), 'last_inquiry_updation')
    
    inquiries = Filter_By_Date(inquiries, 'from', request.GET.get('last_follow_up_updation_from'), 'last_follow_up_updation')
    inquiries = Filter_By_Date(inquiries, 'to', request.GET.get('last_follow_up_updation_to'), 'last_follow_up_updation')   
    
    # Handle "when" filter for relative time periods
    when_filter = query_params.get('when_filter')
    if when_filter:
        inquiries = Filter_By_When(inquiries, when_filter)
    
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
        

    
    # Add call recording information for each lead
    for inquiry in inquiries:
        # Get call recordings for this lead
        call_recordings = inquiry.call_recordings.all()
        inquiry.call_recordings_count = call_recordings.count()
        
        # Get all call recordings with details for display
        inquiry.all_call_recordings = []
        for recording in call_recordings:
            inquiry.all_call_recordings.append({
                'id': recording.id,
                'duration': recording.get_duration_display(),
                'notes': recording.notes,
                'call_date': recording.call_date,
                'file_url': recording.recording_file.url,
                'filename': recording.recording_file.name.split('/')[-1],
                'uploaded_by': recording.uploaded_by.name if recording.uploaded_by else 'Unknown'
            })
        
        # Get the latest call recording for summary
        latest_recording = call_recordings.first()
        if latest_recording:
            inquiry.latest_call_duration = latest_recording.get_duration_display()
            inquiry.latest_call_notes = latest_recording.notes
            inquiry.latest_call_date = latest_recording.call_date
        else:
            inquiry.latest_call_duration = None
            inquiry.latest_call_notes = None
            inquiry.latest_call_date = None
    
    # Distinct lists for filters - Travel CRM
    customers = Lead.objects.values_list('customer_name', flat=True).distinct()
    destinations = Lead.objects.values_list('destination', flat=True).distinct()
    travel_types = Lead.objects.values_list('travel_type', flat=True).distinct()

    return render(request, 'inquiries/inquiry_list.html', {
        'heading': request.GET.get('heading', "Travel Leads"),
        'inquiries': inquiries,
        'actions': ['Update', 'Delete', 'View Logs', 'Itinerary'],
        'dashboard_buttons': ["Add Lead", "Open Filters", "View / Hide Columns", "Dashboard"],
        'base_url_name': reverse('inquiry_list'),
        'customers': customers,
        'destinations': destinations,
        'travel_types': travel_types,
    })

# ======================================================================================================

@login_required
@user_passes_test(is_admin)
def hotel_list_create_view(request):
    """Hotel management view - uses admin panel for now"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        if name:
            hotel, created = Hotel.objects.get_or_create(name=name, defaults={
                'address': address,
                'city': city,
                'state': 'India',
                'contact_number': '0000000000',
                'created_by': request.user
            })
            if created:
                messages.success(request, f"Hotel '{name}' created successfully.")
            else:
                messages.info(request, f"Hotel '{name}' already exists.")
        else:
            messages.error(request, 'Hotel name is required.')
        return redirect('hotel_list_create')
    hotels = Hotel.objects.all().order_by('name')
    return render(request, 'inquiries/hotels.html', {'hotels': hotels})


@login_required
@user_passes_test(is_admin)
def assign_leads_to_hotel_view(request):
    """Placeholder for hotel assignment - not currently used in Travel CRM"""
    messages.info(request, 'Hotel assignment feature coming soon. Use admin panel for now.')
    return redirect('dashboard')

# ======================================================================================================================================================================


@login_required
@user_passes_test(is_admin)
def inquiries_updated_today_view(request):
    todays_date = now().date()
    
    inquiries = Filter_Inquiries(request)    
    inquiries = inquiries.filter(last_inquiry_updation__gte=todays_date)
    
    # Add call recording information for each lead
    for inquiry in inquiries:
        # Get call recordings for this lead
        call_recordings = inquiry.call_recordings.all()
        inquiry.call_recordings_count = call_recordings.count()
        
        # Get all call recordings with details for display
        inquiry.all_call_recordings = []
        for recording in call_recordings:
            inquiry.all_call_recordings.append({
                'id': recording.id,
                'duration': recording.get_duration_display(),
                'notes': recording.notes,
                'call_date': recording.call_date,
                'file_url': recording.recording_file.url,
                'filename': recording.recording_file.name.split('/')[-1],
                'uploaded_by': recording.uploaded_by.name if recording.uploaded_by else 'Unknown'
            })
        
        # Get the latest call recording for summary
        latest_recording = call_recordings.first()
        if latest_recording:
            inquiry.latest_call_duration = latest_recording.get_duration_display()
            inquiry.latest_call_notes = latest_recording.notes
            inquiry.latest_call_date = latest_recording.call_date
        else:
            inquiry.latest_call_duration = None
            inquiry.latest_call_notes = None
            inquiry.latest_call_date = None
            
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
    customers = Lead.objects.values_list('customer_name', flat=True).distinct() 
    destinations = Lead.objects.values_list('destination', flat=True).distinct() 

    lead_emails = Lead.objects.values_list('email', flat=True).exclude(email__isnull=True).distinct()
    mobile_numbers = Lead.objects.values_list('mobile_number', flat=True).distinct()
    cities = Lead.objects.values_list('city', flat=True).distinct()
    inquiry_sources = Lead.objects.values_list('inquiry_source', flat=True).distinct()
    statuses = Lead.objects.values_list('status', flat=True).distinct()
    travel_types = Lead.objects.values_list('travel_type', flat=True).distinct()
    admins = CustomUser.objects.filter(role = "Admin")
    
    return render(request, 'inquiries/follow_up_management.html', {
            'lead_ids': lead_ids,
            'customers': customers,
            'destinations': destinations,            
            'follow_up_data':follow_up_data,            
            'Len_dict': len(follow_up_data),
            'agents': agents,
            'lead_emails': lead_emails,
            'mobile_numbers': mobile_numbers,
            'cities': cities,
            'inquiry_sources': inquiry_sources,
            'statuses': statuses,
            'travel_types': travel_types,
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
        form = SimpleInquiryForm(request.POST)

        if form.is_valid():
            inquiry = form.save(commit=False)
            
            # Set default values for required fields not in the simplified form
            inquiry.destination = "To Be Determined"
            inquiry.travel_type = "Family"
            inquiry.number_of_travelers = 1
            inquiry.status = "New Lead"
            inquiry.inquiry_source = "Website"  # Default value
            inquiry.inquiry_date = now().date()
            inquiry.last_inquiry_updation = now().date()
            
            # Auto-assign agent logic
            if not inquiry.assigned_agent:
                if request.user.role == 'Agent':
                    # If agent is creating the inquiry, assign it to themselves
                    inquiry.assigned_agent = request.user
                    messages.success(request, f"Lead automatically assigned to you ({request.user.name})")
                else:
                    # If admin is creating, use the existing auto-assignment logic
                    auto_assigned_agent = auto_assign_agent_with_least_leads()
                    if auto_assigned_agent:
                        inquiry.assigned_agent = auto_assigned_agent
                        messages.info(request, f"Lead automatically assigned to agent: {auto_assigned_agent.name}")
                    else:
                        messages.warning(request, "No agents available for assignment.")
        
            inquiry.save()
            
            # Check if new lead has "Not interested" status and was automatically transferred
            if (inquiry.status == "Not interested" and 
                inquiry.transferred_to and 
                inquiry.transferred_to.role == 'Viewer'):
                
                messages.info(request, f"Lead automatically transferred to viewer: {inquiry.transferred_to.name} due to 'Not interested' status.")
            
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
            if request.user.role == 'Agent':
                messages.success(request, f"Lead added successfully and assigned to you ({request.user.name})!")
            else:
                messages.success(request, "Lead added successfully!")
            return redirect('add_inquiry')
        
        else:
            messages.error(request, "Some error occured, please ensure that the form is valid !")
      
    else:       # For GET request
        form = SimpleInquiryForm()
        
    return render(request, 'inquiries/simple_add_lead.html', {'form': form, 'title': 'Add New Travel Lead'})

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
            
            inquiry.save() 
            
            # Handle call recording upload (separate from lead form)
            call_recording_file = request.FILES.get('call_recording')
            call_notes = request.POST.get('call_notes')
            call_duration_seconds = request.POST.get('call_duration_seconds')
            
            if call_recording_file:
                try:
                    from .models import CallRecording
                    from .utils import extract_audio_duration, format_duration
                    
                    # Create call recording instance
                    call_recording = CallRecording.objects.create(
                        lead=inquiry,
                        recording_file=call_recording_file,
                        notes=call_notes,
                        uploaded_by=request.user
                    )
                    
                    # Extract duration using multiple methods
                    duration_seconds = None
                    
                    # Method 1: Use JavaScript-extracted duration if available
                    if call_duration_seconds and call_duration_seconds.strip():
                        try:
                            duration_seconds = float(call_duration_seconds)
                            print(f"Using JavaScript-extracted duration: {duration_seconds} seconds")
                        except ValueError:
                            print(f"Invalid JavaScript duration value: {call_duration_seconds}")
                    
                    # Method 2: Extract duration from file using mutagen
                    if not duration_seconds:
                        try:
                            # Ensure the file is saved and accessible
                            if call_recording.recording_file and hasattr(call_recording.recording_file, 'path'):
                                file_path = call_recording.recording_file.path
                                duration_seconds = extract_audio_duration(file_path)
                                if duration_seconds:
                                    print(f"Using mutagen-extracted duration: {duration_seconds} seconds")
                            else:
                                print("Recording file not accessible for duration extraction")
                        except Exception as e:
                            print(f"Error extracting duration with mutagen: {str(e)}")
                    
                    # Save duration if we have it
                    if duration_seconds and duration_seconds > 0:
                        call_recording.duration = format_duration(duration_seconds)
                        call_recording.save()
                        print(f"Saved duration: {call_recording.duration}")
                    else:
                        print("No valid duration extracted")
                        
                except Exception as e:
                    print(f"Error creating call recording: {str(e)}")
                    # Continue without call recording if creation fails
            
            new_inquiry_instance = inquiry  # Store the new data after changes
            
            # Check if status was changed to "Not interested" and lead was automatically transferred
            if (old_inquiry_instance.status != "Not interested" and 
                new_inquiry_instance.status == "Not interested" and
                new_inquiry_instance.transferred_to and 
                new_inquiry_instance.transferred_to.role == 'Viewer'):
                
                messages.info(request, f"Lead automatically transferred to viewer: {new_inquiry_instance.transferred_to.name} due to 'Not interested' status.")
            
            # Save logs of changes
            Save_Lead_Logs(old_inquiry_instance, new_inquiry_instance, request.user)
            
            messages.success(request, "Lead updated successfully !")
            
            return redirect('inquiry_list')  # Redirect back to the inquiry list after saving

        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
            error_message = "Error updating lead! "
            if form.errors:
                error_message += "Please check the following fields: " + ", ".join(form.errors.keys())
            else:
                error_message += "Please check the form and try again."
            messages.error(request, error_message)
    else:
        # Use different forms based on user role
        if request.user.role == 'Admin':
            form = EditLeadForm(instance=inquiry)
        else:
            form = AgentUpdateLeadForm(instance=inquiry)

    # Get existing itineraries for this lead
    existing_itineraries = ItineraryBuilder.objects.filter(lead=inquiry).order_by('-created_at')
    
    return render(request, 'inquiries/add_update_lead.html', {
        'form': form, 
        'title': 'Update Lead Status',
        'lead': inquiry,
        'existing_itineraries': existing_itineraries
    })

# ======================== ITINERARY BUILDER VIEWS ========================

@login_required
@user_passes_test(is_agent_or_admin)
def itinerary_create(request, lead_id):
    """Create new itinerary for a lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    # Check permission
    if request.user.role == 'Agent' and lead.assigned_agent != request.user:
        messages.error(request, "You can only create itineraries for leads assigned to you.")
        return redirect('inquiry_list')
    
    if request.method == 'POST':
        package_id = request.POST.get('package')
        pax = request.POST.get('pax')
        num_cabs = request.POST.get('num_cabs', 1)
        duration = request.POST.get('duration_days')
        
        if not all([package_id, pax, duration]):
            messages.error(request, "Please fill all required fields.")
            return redirect('itinerary_create', lead_id=lead_id)
        
        package = get_object_or_404(Package, id=package_id)
        
        # Create itinerary
        itinerary = ItineraryBuilder.objects.create(
            lead=lead,
            package=package,
            pax=int(pax),
            number_of_cabs=int(num_cabs),
            duration_days=int(duration),
            created_by=request.user
        )
        
        # Auto-generate itinerary days from package template
        for package_day in package.package_days.all():
            ItineraryDay.objects.create(
                itinerary=itinerary,
                day_number=package_day.day_number,
                title=package_day.title,
                description=package_day.description,
                cab_price=package_day.cab_price * int(num_cabs),
                ferry_price=package_day.ferry_price * int(pax),
                speedboat_price=package_day.speedboat_price * int(pax),
                entry_tickets=package_day.entry_tickets * int(pax),
                activities=package_day.activities
            )
        
        # Calculate initial pricing
        itinerary.calculate_total()
        itinerary.save()
        
        messages.success(request, f"Itinerary created successfully! {itinerary.itinerary_days.count()} days generated.")
        return redirect('itinerary_detail', itinerary_id=itinerary.id)
    
    # GET request - show form
    packages = Package.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'inquiries/itinerary_create.html', {
        'lead': lead,
        'packages': packages
    })


@login_required
@user_passes_test(is_agent_or_admin)
def itinerary_detail(request, itinerary_id):
    """View and customize itinerary"""
    itinerary = get_object_or_404(ItineraryBuilder, id=itinerary_id)
    
    # Check permission
    if request.user.role == 'Agent' and itinerary.lead.assigned_agent != request.user:
        messages.error(request, "You can only view itineraries for your assigned leads.")
        return redirect('inquiry_list')
    
    # Get all hotels for customization
    hotels = Hotel.objects.filter(is_active=True).order_by('name')
    
    # Get itinerary days
    itinerary_days = itinerary.itinerary_days.all().order_by('day_number')
    
    return render(request, 'inquiries/itinerary_detail.html', {
        'itinerary': itinerary,
        'lead': itinerary.lead,
        'itinerary_days': itinerary_days,
        'hotels': hotels
    })


@login_required
@user_passes_test(is_agent_or_admin)
def itinerary_day_update(request, day_id):
    """Update a specific itinerary day with hotel, dates, events and pricing"""
    day = get_object_or_404(ItineraryDay, id=day_id)
    
    # Check permission
    if request.user.role == 'Agent' and day.itinerary.lead.assigned_agent != request.user:
        messages.error(request, "You can only edit itineraries for your assigned leads.")
        return redirect('inquiry_list')
    
    if request.method == 'POST':
        # Update dates
        travel_date = request.POST.get('travel_date')
        check_in_date = request.POST.get('check_in_date')
        check_out_date = request.POST.get('check_out_date')
        
        if travel_date:
            day.travel_date = travel_date
        if check_in_date:
            day.check_in_date = check_in_date
        if check_out_date:
            day.check_out_date = check_out_date
        
        # Update hotel and room
        hotel_id = request.POST.get('hotel')
        room_category_id = request.POST.get('room_category')
        
        if hotel_id:
            day.hotel = Hotel.objects.get(id=hotel_id)
        if room_category_id:
            day.room_category = RoomCategory.objects.get(id=room_category_id)
        
        # Update room details
        day.number_of_rooms = int(request.POST.get('number_of_rooms', 1))
        day.extra_mattress = int(request.POST.get('extra_mattress', 0))
        day.is_hotel_booked = request.POST.get('is_hotel_booked') == 'on'
        
        # Update transportation
        day.cab_price = float(request.POST.get('cab_price', 0))
        day.ferry_price = float(request.POST.get('ferry_price', 0))
        day.speedboat_price = float(request.POST.get('speedboat_price', 0))
        day.entry_tickets = float(request.POST.get('entry_tickets', 0))
        
        # Update activities and events
        day.activities = request.POST.get('activities', '')
        
        # Update additional charges
        day.additional_charges = float(request.POST.get('additional_charges', 0))
        day.additional_charges_description = request.POST.get('additional_charges_description', '')
        
        day.save()
        
        # Create hotel booking if marked as booked
        if day.is_hotel_booked and day.hotel and day.room_category and day.check_in_date and day.check_out_date:
            booking, created = HotelBooking.objects.get_or_create(
                itinerary_day=day,
                hotel=day.hotel,
                room_category=day.room_category,
                check_in_date=day.check_in_date,
                check_out_date=day.check_out_date,
                defaults={
                    'number_of_rooms': day.number_of_rooms,
                    'extra_mattress': day.extra_mattress,
                    'booking_status': 'Confirmed',
                }
            )
            if not created:
                booking.number_of_rooms = day.number_of_rooms
                booking.extra_mattress = day.extra_mattress
                booking.save()
        
        # Recalculate itinerary total
        day.itinerary.calculate_total()
        day.itinerary.save()
        
        messages.success(request, f"Day {day.day_number} updated successfully! Total price recalculated.")
        return redirect('itinerary_detail', itinerary_id=day.itinerary.id)
    
    # Get available hotels and event places for the context
    hotels = Hotel.objects.filter(is_active=True)
    event_places = EventPlace.objects.filter(is_active=True)
    
    context = {
        'day': day,
        'hotels': hotels,
        'event_places': event_places,
        'itinerary': day.itinerary,
    }
    
    return render(request, 'inquiries/itinerary_day_edit.html', context)


@login_required
@user_passes_test(is_agent_or_admin)
def get_room_categories(request, hotel_id):
    """AJAX view to get room categories for a hotel"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        room_categories = hotel.room_categories.filter(is_available=True)
        
        data = {
            'room_categories': [
                {
                    'id': room.id,
                    'room_type': room.room_type,
                    'price_per_night': str(room.price_per_night),
                    'max_occupancy': room.max_occupancy,
                    'extra_mattress_price': str(room.extra_mattress_price),
                }
                for room in room_categories
            ]
        }
        return JsonResponse(data)
    except Hotel.DoesNotExist:
        return JsonResponse({'error': 'Hotel not found'}, status=404)


@login_required
@user_passes_test(is_agent_or_admin)
def check_hotel_availability(request, hotel_id, room_category_id, check_in_date, check_out_date):
    """AJAX view to check hotel availability for specific dates"""
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        room_category = RoomCategory.objects.get(id=room_category_id)
        
        # Check for existing bookings that overlap with the requested dates
        overlapping_bookings = HotelBooking.objects.filter(
            hotel=hotel,
            room_category=room_category,
            booking_status__in=['Confirmed', 'Pending'],
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        )
        
        available = overlapping_bookings.count() == 0
        
        data = {
            'available': available,
            'hotel_name': hotel.name,
            'room_type': room_category.room_type,
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'message': 'Available' if available else 'Dates already booked'
        }
        
        return JsonResponse(data)
    except (Hotel.DoesNotExist, RoomCategory.DoesNotExist):
        return JsonResponse({'error': 'Hotel or room category not found'}, status=404)


@login_required
@user_passes_test(is_agent_or_admin)
def itinerary_update_markup(request, itinerary_id):
    """Update markup percentage for itinerary"""
    itinerary = get_object_or_404(ItineraryBuilder, id=itinerary_id)
    
    if request.method == 'POST':
        markup = float(request.POST.get('markup_percentage', 0))
        itinerary.markup_percentage = markup
        itinerary.calculate_total()
        itinerary.save()
        
        messages.success(request, f"Markup updated to {markup}%. Total price: ₹{itinerary.total_price:,.0f}")
        return redirect('itinerary_detail', itinerary_id=itinerary.id)
    
    return redirect('itinerary_detail', itinerary_id=itinerary.id)


@login_required
@user_passes_test(is_agent_or_admin)
def itinerary_delete(request, itinerary_id):
    """Delete an itinerary"""
    itinerary = get_object_or_404(ItineraryBuilder, id=itinerary_id)
    lead_id = itinerary.lead.id
    
    # Check permission
    if request.user.role == 'Agent' and itinerary.lead.assigned_agent != request.user:
        messages.error(request, "You can only delete itineraries for your assigned leads.")
        return redirect('inquiry_list')
    
    itinerary.delete()
    messages.success(request, "Itinerary deleted successfully.")
    return redirect('update_status', inquiry_id=lead_id)


@login_required
@user_passes_test(is_agent_or_admin)
def get_room_categories_ajax(request, hotel_id):
    """AJAX endpoint to get room categories for a hotel"""
    hotel = get_object_or_404(Hotel, id=hotel_id)
    room_categories = hotel.room_categories.filter(is_available=True)
    
    data = [{
        'id': room.id,
        'room_type': room.room_type,
        'price_per_night': str(room.price_per_night),
        'extra_mattress_price': str(room.extra_mattress_price),
        'max_occupancy': room.max_occupancy
    } for room in room_categories]
    
    return JsonResponse({'room_categories': data})

# ================================================================================================================================================================
@login_required
@user_passes_test(is_staff)
def get_panchayats(request):
    file_path = "inquiries/static/Location_list.xlsx"
    df = pd.read_excel(file_path)

    # Get all location/panchayat data without block filtering
    filtered_df = df[["S.N", "Location_Panchayat"]].dropna()    # Selects only the columns "S.N" and "Location_Panchayat". Drops rows with missing values (NaN) in "Location_Panchayat".

    # Convert to JSON with 'S.N' as ID
    data = [{'id': row["S.N"], 'name': row["Location_Panchayat"]} for _, row in filtered_df.iterrows()]

    return JsonResponse({'panchayats': data})


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

    # Overall Counts - Travel CRM
    new_leads = inquiries.filter(status='New Lead').count()
    itinerary_sent = inquiries.filter(status='Itinerary Sent').count()
    bookings_confirmed = inquiries.filter(status='Booking Confirmed').count()
    trips_completed = inquiries.filter(status='Trip Completed').count()
    rejected = inquiries.filter(status='Not interested').count()
    
    # Status Type Counts
    dnp_count = inquiries.filter(status='DNP').count()
    not_interested_count = inquiries.filter(status='Not interested').count()
    interested_count = inquiries.filter(status='Interested').count()
    follow_up_count = inquiries.filter(status='Follow Up').count()
    budget_discussion_count = inquiries.filter(status='Budget Discussion').count()
    negotiation_count = inquiries.filter(status='Negotiation').count()
    
    # Total Leads Count
    total_leads = inquiries.count()
        
    # Today's Counts
    today = now().date()
    
    inquiries_today = inquiries.filter(status='New Lead', inquiry_date=today).count()
    itinerary_sent_today = inquiries.filter(status='Itinerary Sent', itinerary_sent_date__date=today).count()
    bookings_today = inquiries.filter(status='Booking Confirmed', booking_date=today).count()
    trips_completed_today = inquiries.filter(status='Trip Completed').count()  # No specific date for this
    
    # Call Recording Statistics (for admins only)
    call_recording_stats = {}
    if user.role == "Admin":
        from .models import CallRecording
        from django.db.models import Avg, Sum, Count
        from datetime import timedelta
        
        total_recordings = CallRecording.objects.count()
        recordings_today = CallRecording.objects.filter(call_date__date=today).count()
        leads_with_recordings = Lead.objects.filter(call_recordings__isnull=False).distinct().count()
        total_leads = Lead.objects.count()
        recording_coverage = round((leads_with_recordings / total_leads * 100) if total_leads > 0 else 0, 1)
        
        # Duration statistics
        recordings_with_duration = CallRecording.objects.filter(duration__isnull=False)
        avg_duration = recordings_with_duration.aggregate(avg=Avg('duration'))['avg']
        total_duration = recordings_with_duration.aggregate(total=Sum('duration'))['total']
        
        # Duration distribution (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        recent_recordings = CallRecording.objects.filter(
            call_date__date__gte=thirty_days_ago,
            duration__isnull=False
        )
        
        # Duration categories
        short_calls = recent_recordings.filter(duration__lte=timedelta(minutes=2)).count()
        medium_calls = recent_recordings.filter(
            duration__gt=timedelta(minutes=2),
            duration__lte=timedelta(minutes=5)
        ).count()
        long_calls = recent_recordings.filter(duration__gt=timedelta(minutes=5)).count()
        
        # Format duration for display
        def format_duration(duration):
            if duration:
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                if hours > 0:
                    return f"{hours}h {minutes}m {seconds}s"
                else:
                    return f"{minutes}m {seconds}s"
            return "N/A"
        
        call_recording_stats = {
            'total_recordings': total_recordings,
            'recordings_today': recordings_today,
            'leads_with_recordings': leads_with_recordings,
            'total_leads': total_leads,
            'recording_coverage': recording_coverage,
            'avg_duration': format_duration(avg_duration),
            'total_duration': format_duration(total_duration),
            'short_calls': short_calls,
            'medium_calls': medium_calls,
            'long_calls': long_calls,
            'recent_recordings_count': recent_recordings.count(),
        }

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
        # Overall Stats - Travel CRM
        'todays_date': now().date().strftime('%Y-%m-%d'),
        'new_leads': new_leads,
        'itinerary_sent': itinerary_sent,
        'bookings_confirmed': bookings_confirmed,
        'trips_completed': trips_completed,
        'rejected': rejected,
        
        # Status Type Stats
        'dnp_count': dnp_count,
        'not_interested_count': not_interested_count,
        'interested_count': interested_count,
        'follow_up_count': follow_up_count,
        'budget_discussion_count': budget_discussion_count,
        'negotiation_count': negotiation_count,
        'total_leads': total_leads,

        # Today's Stats
        'inquiries_today': inquiries_today,
        'itinerary_sent_today': itinerary_sent_today,
        'bookings_today': bookings_today,
        'trips_completed_today': trips_completed_today,
        
        # Call Recording Stats (for admins)
        'call_recording_stats': call_recording_stats,
    }

    return render(request, 'inquiries/dashboard.html', context)

# ================================================================================================================================================================

@login_required
@user_passes_test(is_staff)
def lead_status_data(request):
    """
    Fetch and display comprehensive lead status data
    """
    user = request.user
    
    # Get all leads if user is admin, else filter by assigned_agent
    if user.role == "Admin":
        leads = Lead.objects.all()
    else:
        leads = Lead.objects.filter(assigned_agent=user)
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    agent_filter = request.GET.get('agent')
    
    # Apply filters
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            leads = leads.filter(inquiry_date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            leads = leads.filter(inquiry_date__lte=to_date)
        except ValueError:
            pass
    
    if agent_filter and user.role == "Admin":
        leads = leads.filter(assigned_agent__id=agent_filter)
    
    # Status statistics
    status_stats = {}
    for status_choice in Lead.STATUS_CHOICES:
        status_code, status_name = status_choice
        count = leads.filter(status=status_code).count()
        status_stats[status_code] = {
            'name': status_name,
            'count': count,
            'percentage': round((count / leads.count() * 100) if leads.count() > 0 else 0, 1)
        }
    
    # Agent statistics (for admins only)
    agent_stats = {}
    if user.role == "Admin":
        agents = CustomUser.objects.filter(role='Agent')
        for agent in agents:
            agent_leads = leads.filter(assigned_agent=agent)
            agent_status_counts = {}
            for status_choice in Lead.STATUS_CHOICES:
                status_code, status_name = status_choice
                agent_status_counts[status_code] = agent_leads.filter(status=status_code).count()
            
            agent_stats[agent.id] = {
                'name': agent.name or agent.email or agent.mobile_number,
                'total_leads': agent_leads.count(),
                'status_counts': agent_status_counts
            }
    
    # Recent leads by status
    recent_leads = {}
    for status_choice in Lead.STATUS_CHOICES:
        status_code, status_name = status_choice
        recent_leads[status_code] = leads.filter(status=status_code).order_by('-inquiry_date')[:5]
    
    # Date range statistics
    today = now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    weekly_stats = {}
    monthly_stats = {}
    
    for status_choice in Lead.STATUS_CHOICES:
        status_code, status_name = status_choice
        weekly_stats[status_code] = leads.filter(
            status=status_code,
            inquiry_date__gte=week_ago
        ).count()
        monthly_stats[status_code] = leads.filter(
            status=status_code,
            inquiry_date__gte=month_ago
        ).count()
    
    # Transfer statistics
    transfer_stats = {
        'total_transfers': leads.filter(transferred_to__isnull=False).count(),
        'transfers_this_month': leads.filter(
            transferred_to__isnull=False,
            transfer_date__gte=month_ago
        ).count(),
        'most_transferred_status': leads.filter(
            transferred_to__isnull=False
        ).values('status').annotate(
            count=Count('id')
        ).order_by('-count').first()
    }
    
    context = {
        'status_stats': status_stats,
        'agent_stats': agent_stats,
        'recent_leads': recent_leads,
        'weekly_stats': weekly_stats,
        'monthly_stats': monthly_stats,
        'transfer_stats': transfer_stats,
        'total_leads': leads.count(),
        'status_choices': Lead.STATUS_CHOICES,
        'agents': CustomUser.objects.filter(role='Agent') if user.role == "Admin" else None,
        'filters': {
            'status': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'agent': agent_filter
        }
    }
    
    return render(request, 'inquiries/lead_status_data.html', context)

# ================================================================================================================================================================

@login_required
@user_passes_test(is_staff)
def detailed_stats(request):
    user = request.user  # Get the logged-in user
    
    # Get date filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.role=="Admin":
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.filter(assigned_agent=user)  # Agent sees only their assigned inquiries
    
    # Apply date filters if provided
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            inquiries = inquiries.filter(inquiry_date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            inquiries = inquiries.filter(inquiry_date__lte=to_date)
        except ValueError:
            pass

    # Overall Counts - Travel CRM
    new_leads = inquiries.filter(status='New Lead').count()
    itinerary_sent = inquiries.filter(status='Itinerary Sent').count()
    bookings_confirmed = inquiries.filter(status='Booking Confirmed').count()
    trips_completed = inquiries.filter(status='Trip Completed').count()
    rejected = inquiries.filter(status='Not interested').count()
        
    # Today's Counts
    today = now().date()
    inquiries_today = inquiries.filter(status='New Lead', inquiry_date=today).count()
    itinerary_sent_today = inquiries.filter(status='Itinerary Sent', itinerary_sent_date__date=today).count()
    bookings_today = inquiries.filter(status='Booking Confirmed', booking_date=today).count()
    trips_completed_today = inquiries.filter(status='Trip Completed').count()

    # Counts by Travel Type
    '''
        1) values('travel_type'): Groups the data by travel_type.
        
        2) annotate(total=Count('id')): annotate allows you to perform aggregations (like SUM, COUNT, AVG, etc.) on groups of data.This query counts the number of inquiries for each travel_type. The result will include a new field total, which stores the count.
        
        3) order_by('-total'): Sorts the results in descending order, so types with the most inquiries appear first.
    '''
    inquiries_by_travel_type = inquiries.values('travel_type').annotate(total=Count('id')).order_by('-total')

    # Counts by Inquiry Source
    inquiries_by_source = inquiries.values('inquiry_source').annotate(total=Count('id')).order_by('-total')


    


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
        # Overall Stats - Travel CRM
        'new_leads': new_leads,
        'itinerary_sent': itinerary_sent,
        'bookings_confirmed': bookings_confirmed,
        'trips_completed': trips_completed,
        'rejected': rejected,

        # Today's Stats
        'inquiries_today': inquiries_today,
        'itinerary_sent_today': itinerary_sent_today,
        'bookings_today': bookings_today,
        'trips_completed_today': trips_completed_today,

        # Detailed Stats
        'inquiries_by_travel_type': inquiries_by_travel_type,
        'inquiries_by_source': inquiries_by_source,



        # Trends and Recent Activity
        'recent_trends': recent_trends,
        'recent_inquiries': recent_inquiries,
        
        # Date Filter Parameters
        'date_from': date_from,
        'date_to': date_to,
    }
    
    # print("===============================> today date in detailed_stats = ", today)

    return render(request, 'inquiries/detailed_stats.html', context)


# ================================================================================================================================================================

@login_required
@user_passes_test(is_staff)
def export_inquiries_excel(request):
    user = request.user  # Get the logged-in user
    
    # Get date filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # If the user is an admin, get all inquiries; otherwise, get only the logged-in agent's inquiries
    if user.role=="Admin":
        inquiries = Lead.objects.all()
    else:
        inquiries = Lead.objects.filter(assigned_agent=user)  # Filter only assigned inquiries for the agent
    
    # Apply date filters if provided
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            inquiries = inquiries.filter(inquiry_date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            inquiries = inquiries.filter(inquiry_date__lte=to_date)
        except ValueError:
            pass

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

    lead_emails = base_queryset.values_list('email', flat=True).exclude(email__isnull=True).distinct()
    mobile_numbers = base_queryset.values_list('mobile_number', flat=True).distinct()

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

    selected_inquiry_sources = query_params.getlist('inquiry_source[]')
    selected_statuses = query_params.getlist('status[]')
    selected_agent_ids = query_params.getlist('agent_id[]')
    selected_admin_ids = query_params.getlist('admin_id[]')
    selected_when_filter = query_params.get('when_filter')
    
    # print("====================> selected_agent_ids = ", selected_agent_ids)
    
    return {
        'lead_ids': lead_ids,
        'students': students,
        'parents': parents,
        'agents': agents,
        'lead_emails': lead_emails,
        'mobile_numbers': mobile_numbers,
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
        "selected_inquiry_sources": selected_inquiry_sources,
        "selected_statuses": selected_statuses,
        "selected_agent_ids": selected_agent_ids,
        "selected_admin_ids": selected_admin_ids,
        "selected_when_filter": selected_when_filter,
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
    
    # Get date filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Apply date filters if provided
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            users = users.filter(date_joined__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            users = users.filter(date_joined__date__lte=to_date)
        except ValueError:
            pass
    
    users = Annotate_Performance_Fields_for_Agents(users)
    users = Filter_School_Users(users, request)   # Run annotate part before calling it
    
    context = {
        'users': users,
        'actions': ['Manage Leads', 'Delete User', 'Update User'],
        'show_performance_metrics': True,
        'base_url_name': reverse('school_users_list'),
        'date_from': date_from,
        'date_to': date_to,
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
    if request.user.role == 'Agent':
        # Agents can transfer leads assigned to them OR viewer leads
        if lead.assigned_agent != request.user and lead.status != 'Viewer':
            messages.error(request, "You can only transfer leads assigned to you or viewer leads.")
            return redirect('inquiry_list')
    
    if request.method == 'POST':
        form = TransferLeadForm(request.POST, current_agent=request.user)
        if form.is_valid():
            transfer_type = form.cleaned_data['transfer_type']
            transfer_reason = form.cleaned_data['transfer_reason']
            
            # Store the old agent for logging
            old_agent = lead.assigned_agent
            
            if transfer_type == 'agent':
                target_agent = form.cleaned_data['target_agent']
                # Update the lead for agent transfer
                lead.transferred_from = old_agent
                lead.transferred_to = target_agent
                lead.assigned_agent = target_agent
                lead.transfer_date = timezone.now()
                lead.transfer_reason = transfer_reason
                
                # If this was a viewer lead, change status to 'Inquiry' when transferred
                if lead.status == 'Viewer':
                    lead.status = 'Inquiry'
                
            elif transfer_type == 'viewer':
                # Transfer to viewer status (make available to all agents)
                lead.transferred_from = old_agent
                lead.transferred_to = None  # No specific agent
                lead.assigned_agent = None  # Unassigned
                lead.status = 'Viewer'  # Set to viewer status
                lead.transfer_date = timezone.now()
                lead.transfer_reason = transfer_reason
            
            lead.save()
            
            # Log the transfer
            Save_Lead_Logs(
                old_inquiry_instance=Lead.objects.get(id=lead.id),  # Get fresh instance
                new_inquiry_instance=lead,
                changed_by=request.user
            )
            
            # Create appropriate success message
            if transfer_type == 'agent':
                if old_agent:
                    message = f"Lead '{lead.student_name}' successfully transferred from {old_agent.name} to {target_agent.name}"
                else:
                    message = f"Lead '{lead.student_name}' successfully claimed by {target_agent.name}"
                
                if lead.status == 'Inquiry':
                    message += " (Status changed from Viewer to Inquiry)"
            else:  # transfer_type == 'viewer'
                if old_agent:
                    message = f"Lead '{lead.student_name}' successfully made available to all agents (Viewer status) by {old_agent.name}"
                else:
                    message = f"Lead '{lead.student_name}' successfully made available to all agents (Viewer status)"
            
            messages.success(request, message)
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

# ====================================================================================

@login_required
@user_passes_test(is_agent_or_admin)
def lead_recordings_api(request, lead_id):
    """
    API endpoint to get call recordings for a lead
    """
    from django.http import JsonResponse
    from .models import CallRecording
    
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        
        # Check if user has permission to view this lead
        if request.user.role == 'Agent' and lead.assigned_agent != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        recordings = CallRecording.objects.filter(lead=lead)
        recordings_data = []
        
        for recording in recordings:
            recordings_data.append({
                'id': recording.id,
                'filename': os.path.basename(recording.recording_file.name),
                'file_url': recording.recording_file.url,
                'duration_display': recording.get_duration_display(),
                'call_date': recording.call_date.strftime('%Y-%m-%d %H:%M'),
                'uploaded_by_name': recording.uploaded_by.name if recording.uploaded_by else 'Unknown',
                'notes': recording.notes
            })
        
        return JsonResponse({'recordings': recordings_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ====================================================================================

@login_required
@user_passes_test(is_agent_or_admin)
def delete_recording_api(request, recording_id):
    """
    API endpoint to delete a call recording
    """
    from django.http import JsonResponse
    from .models import CallRecording
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        recording = get_object_or_404(CallRecording, id=recording_id)
        
        # Check if user has permission to delete this recording
        if request.user.role == 'Agent' and recording.lead.assigned_agent != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Delete the file from storage
        if recording.recording_file:
            if os.path.exists(recording.recording_file.path):
                os.remove(recording.recording_file.path)
        
        recording.delete()
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ======================================================================================================================================================================

@login_required
@user_passes_test(is_admin)
def call_duration_analytics_view(request):
    """
    Detailed call duration analytics for admins
    """
    from .models import CallRecording
    from django.db.models import Avg, Sum, Count, Q
    from datetime import timedelta
    
    today = now().date()
    
    # Get date filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Get all recordings with duration
    recordings_with_duration = CallRecording.objects.filter(duration__isnull=False)
    
    # Apply date filters if provided
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            recordings_with_duration = recordings_with_duration.filter(call_date__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            recordings_with_duration = recordings_with_duration.filter(call_date__date__lte=to_date)
        except ValueError:
            pass
    
    # Overall statistics
    total_recordings = CallRecording.objects.count()
    recordings_with_duration_count = recordings_with_duration.count()
    avg_duration = recordings_with_duration.aggregate(avg=Avg('duration'))['avg']
    total_duration = recordings_with_duration.aggregate(total=Sum('duration'))['total']
    
    # Duration distribution
    short_calls = recordings_with_duration.filter(duration__lte=timedelta(minutes=2)).count()
    medium_calls = recordings_with_duration.filter(
        duration__gt=timedelta(minutes=2),
        duration__lte=timedelta(minutes=5)
    ).count()
    long_calls = recordings_with_duration.filter(duration__gt=timedelta(minutes=5)).count()
    
    # Time-based analysis (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    recent_recordings = recordings_with_duration.filter(call_date__date__gte=thirty_days_ago)
    recent_avg_duration = recent_recordings.aggregate(avg=Avg('duration'))['avg']
    
    # Agent performance by call duration
    agent_stats = []
    from .models import CustomUser
    agents = CustomUser.objects.filter(role='Agent')
    
    for agent in agents:
        agent_recordings = recordings_with_duration.filter(uploaded_by=agent)
        agent_count = agent_recordings.count()
        if agent_count > 0:
            agent_avg = agent_recordings.aggregate(avg=Avg('duration'))['avg']
            agent_total = agent_recordings.aggregate(total=Sum('duration'))['total']
            
            # Agent duration distribution
            agent_short_calls = agent_recordings.filter(duration__lte=timedelta(minutes=2)).count()
            agent_medium_calls = agent_recordings.filter(
                duration__gt=timedelta(minutes=2),
                duration__lte=timedelta(minutes=5)
            ).count()
            agent_long_calls = agent_recordings.filter(duration__gt=timedelta(minutes=5)).count()
            
            # Calculate percentages
            agent_short_percent = (agent_short_calls / agent_count * 100) if agent_count > 0 else 0
            agent_medium_percent = (agent_medium_calls / agent_count * 100) if agent_count > 0 else 0
            agent_long_percent = (agent_long_calls / agent_count * 100) if agent_count > 0 else 0
            
            # Recent activity (last 30 days)
            agent_recent_recordings = agent_recordings.filter(call_date__date__gte=thirty_days_ago)
            agent_recent_count = agent_recent_recordings.count()
            agent_recent_avg = agent_recent_recordings.aggregate(avg=Avg('duration'))['avg']
            
            agent_stats.append({
                'agent': agent,
                'count': agent_count,
                'avg_duration': agent_avg,
                'total_duration': agent_total,
                'short_calls': agent_short_calls,
                'medium_calls': agent_medium_calls,
                'long_calls': agent_long_calls,
                'short_percent': agent_short_percent,
                'medium_percent': agent_medium_percent,
                'long_percent': agent_long_percent,
                'recent_count': agent_recent_count,
                'recent_avg_duration': agent_recent_avg,
            })
    
    # Sort agents by total calls (most active first)
    agent_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # Format duration helper function
    def format_duration(duration):
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
        return "N/A"
    
    # Recent recordings with details
    recent_recordings_list = recent_recordings.select_related('lead', 'uploaded_by').order_by('-call_date')[:20]
    
    context = {
        'total_recordings': total_recordings,
        'recordings_with_duration_count': recordings_with_duration_count,
        'avg_duration': format_duration(avg_duration),
        'total_duration': format_duration(total_duration),
        'short_calls': short_calls,
        'medium_calls': medium_calls,
        'long_calls': long_calls,
        'recent_avg_duration': format_duration(recent_avg_duration),
        'recent_recordings_count': recent_recordings.count(),
        'agent_stats': agent_stats,
        'recent_recordings_list': recent_recordings_list,
        'format_duration': format_duration,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'inquiries/call_duration_analytics.html', context)

# ======================================================================================================================================================================
# Google Sheets Integration Views
# ======================================================================================================================================================================

@login_required
@user_passes_test(is_admin)
def google_sheets_import_view(request):
    """View for importing leads from Google Sheets"""
    from .google_sheets_service import GoogleSheetsService
    
    context = {
        'title': 'Import Leads from Google Sheets',
        'error_message': None,
        'success_message': None,
        'import_result': None,
        'available_agents': CustomUser.objects.filter(role='Agent').order_by('name'),
        'schools': School.objects.all().order_by('name')
    }
    
    if request.method == 'POST':
        spreadsheet_id = request.POST.get('spreadsheet_id', '').strip()
        range_name = request.POST.get('range_name', '').strip()
        agent_id = request.POST.get('agent_id', '').strip()
        segment = request.POST.get('segment', 'cnb-leads')
        school_id = request.POST.get('school_id', '').strip()
        
        if not spreadsheet_id:
            context['error_message'] = 'Please provide a valid Google Sheets ID'
        elif not range_name:
            context['error_message'] = 'Please provide a valid range (e.g., Sheet1!A1:Z1000)'
        else:
            try:
                # Initialize Google Sheets service
                sheets_service = GoogleSheetsService()
                
                # Get selected agent if specified
                selected_agent = None
                if agent_id:
                    try:
                        selected_agent = CustomUser.objects.get(id=agent_id, role='Agent')
                    except CustomUser.DoesNotExist:
                        context['error_message'] = 'Selected agent not found'
                        return render(request, 'inquiries/google_sheets_import.html', context)
                
                # Import leads
                selected_school = None
                if segment == 'schools' and school_id:
                    selected_school = School.objects.filter(id=school_id).first()

                result = sheets_service.import_leads_from_sheet(
                    spreadsheet_id=spreadsheet_id,
                    range_name=range_name,
                    admin_user=request.user,
                    selected_agent=selected_agent,
                    selected_school=selected_school
                )
                
                context['import_result'] = result
                
                if result['success']:
                    context['success_message'] = result['message']
                else:
                    context['error_message'] = result['message']
                    
            except FileNotFoundError as e:
                context['error_message'] = str(e)
            except Exception as e:
                context['error_message'] = f'Error connecting to Google Sheets: {str(e)}'
    
    return render(request, 'inquiries/google_sheets_import.html', context)


@login_required
@user_passes_test(is_admin)
def google_sheets_preview_view(request):
    """View for previewing Google Sheets data before import"""
    from .google_sheets_service import GoogleSheetsService
    
    context = {
        'title': 'Preview Google Sheets Data',
        'error_message': None,
        'sheet_data': None,
        'sheet_info': None,
        'available_agents': CustomUser.objects.filter(role='Agent').order_by('name')
    }
    
    if request.method == 'POST':
        spreadsheet_id = request.POST.get('spreadsheet_id', '').strip()
        range_name = request.POST.get('range_name', '').strip()
        
        if not spreadsheet_id:
            context['error_message'] = 'Please provide a valid Google Sheets ID'
        elif not range_name:
            context['error_message'] = 'Please provide a valid range (e.g., Sheet1!A1:Z1000)'
        else:
            try:
                # Initialize Google Sheets service
                sheets_service = GoogleSheetsService()
                
                # Get sheet info
                sheet_info = sheets_service.get_sheet_info(spreadsheet_id)
                if sheet_info:
                    context['sheet_info'] = sheet_info
                
                # Read sheet data
                sheet_data = sheets_service.read_sheet(spreadsheet_id, range_name)
                
                if sheet_data:
                    context['sheet_data'] = sheet_data
                    context['headers'] = sheet_data[0] if sheet_data else []
                    context['data_rows'] = sheet_data[1:6] if len(sheet_data) > 1 else []  # Show first 5 rows
                    context['total_rows'] = len(sheet_data) - 1 if len(sheet_data) > 1 else 0
                else:
                    context['error_message'] = 'No data found in the specified range'
                    
            except FileNotFoundError as e:
                context['error_message'] = str(e)
            except Exception as e:
                context['error_message'] = f'Error connecting to Google Sheets: {str(e)}'
    
    return render(request, 'inquiries/google_sheets_preview.html', context)


@login_required
@user_passes_test(is_admin)
def google_sheets_setup_view(request):
    """View for Google Sheets setup instructions"""
    context = {
        'title': 'Google Sheets Setup Instructions'
    }
    return render(request, 'inquiries/google_sheets_setup.html', context)

def agent_statistics_view(request):
    from .models import CustomUser, Lead, LeadLogs, CallRecording
    from django.db.models import Sum, Avg
    user = request.user
    agents = CustomUser.objects.filter(role='Agent')
    period = request.GET.get('period', 'day')
    today = now().date()
    if period == 'yesterday':
        from datetime import timedelta as dt_timedelta
        start_date = today - dt_timedelta(days=1)
        end_date = start_date
    else:
        start_date = today
        end_date = today
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif period == 'month':
            start_date = today.replace(day=1)

    # Admin can filter by agent, agent can only see their own stats
    if user.role == 'Admin':
        selected_agent_id = request.GET.get('agent_id')
        if selected_agent_id:
            agent = CustomUser.objects.get(id=selected_agent_id)
            leads = Lead.objects.filter(assigned_agent=agent, inquiry_date__gte=start_date)
            follow_ups = LeadLogs.objects.filter(changed_by=agent, changed_at__date__gte=start_date)
            calls = CallRecording.objects.filter(uploaded_by=agent, call_date__date__gte=start_date)
            admissions = leads.filter(status='Admission Confirmed')
        else:
            leads = Lead.objects.filter(inquiry_date__gte=start_date)
            follow_ups = LeadLogs.objects.filter(changed_at__date__gte=start_date)
            calls = CallRecording.objects.filter(call_date__date__gte=start_date)
            admissions = leads.filter(status='Admission Confirmed')
    else:
        selected_agent_id = str(user.id)
        leads = Lead.objects.filter(assigned_agent=user, inquiry_date__gte=start_date)
        follow_ups = LeadLogs.objects.filter(changed_by=user, changed_at__date__gte=start_date)
        calls = CallRecording.objects.filter(uploaded_by=user, call_date__date__gte=start_date)
        admissions = leads.filter(status='Admission Confirmed')

    # For 'yesterday', filter only that day
    if period == 'yesterday':
        leads = leads.filter(inquiry_date=start_date)
        follow_ups = follow_ups.filter(changed_at__date=start_date)
        calls = calls.filter(call_date__date=start_date)
        admissions = admissions.filter(inquiry_date=start_date)

    # Calculate call duration statistics
    calls_with_duration = calls.filter(duration__isnull=False)
    total_duration = calls_with_duration.aggregate(total=Sum('duration'))['total']
    avg_duration = calls_with_duration.aggregate(avg=Avg('duration'))['avg']
    
    def format_duration(duration):
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
        return "0m 0s"

    # Aggregate stats
    stats = {
        'leads_handled': leads.count(),
        'follow_ups': follow_ups.count(),
        'calls_made': calls.count(),
        'admissions': admissions.count(),
        'total_duration': format_duration(total_duration),
        'avg_duration': format_duration(avg_duration),
    }

    # Build activity log (grouped by date)
    from django.db.models.functions import TruncDate
    activity_log = []
    date_range = []
    if period == 'day':
        date_range = [today]
    elif period == 'yesterday':
        date_range = [start_date]
    elif period == 'week':
        date_range = [start_date + timedelta(days=i) for i in range(0, (today - start_date).days + 1)]
    elif period == 'month':
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        date_range = [start_date + timedelta(days=i) for i in range(0, today.day)]

    for date in date_range:
        leads_count = leads.filter(inquiry_date=date).count()
        follow_ups_count = follow_ups.filter(changed_at__date=date).count()
        calls_count = calls.filter(call_date__date=date).count()
        admissions_count = admissions.filter(inquiry_date=date).count()
        
        # Calculate duration for this date
        day_calls = calls.filter(call_date__date=date, duration__isnull=False)
        day_duration = day_calls.aggregate(total=Sum('duration'))['total']
        day_duration_formatted = format_duration(day_duration)
        
        activity_log.append({
            'date': date.strftime('%Y-%m-%d'),
            'leads_handled': leads_count,
            'follow_ups': follow_ups_count,
            'calls_made': calls_count,
            'admissions': admissions_count,
            'call_duration': day_duration_formatted,
        })

    context = {
        'agents': agents,
        'selected_agent_id': selected_agent_id or '',
        'period': period,
        'stats': stats,
        'activity_log': activity_log,
        'show_agent_filter': user.role == 'Admin',
    }
    return render(request, 'inquiries/agent/agent_statistics.html', context)

def active_agents_status_view(request):
    from .models import CustomUser
    agents = CustomUser.objects.filter(role='Agent')
    active_threshold = now() - timedelta(minutes=10)
    agent_data = []
    for agent in agents:
        is_active = agent.last_login and agent.last_login >= active_threshold
        agent_data.append({
            'name': agent.name,
            'last_login': agent.last_login.strftime('%Y-%m-%d %H:%M:%S') if agent.last_login else 'Never',
            'is_active': is_active,
        })
    return JsonResponse({'agents': agent_data})

@login_required
def agent_call_details_view(request):
    """View to get call details for a specific date and agent"""
    from .models import CallRecording
    from django.http import JsonResponse
    from datetime import datetime
    
    try:
        # Get parameters
        date_str = request.GET.get('date')
        agent_id = request.GET.get('agent_id')
        
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date parameter is required'})
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Determine which agent's calls to fetch
        if request.user.role == 'Admin':
            # Admin can view any agent's calls
            if agent_id:
                try:
                    agent = CustomUser.objects.get(id=agent_id, role='Agent')
                except CustomUser.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Agent not found'})
            else:
                # If no agent specified, return error
                return JsonResponse({'success': False, 'error': 'Agent ID is required for admin users'})
        else:
            # Agent can only view their own calls
            agent = request.user
        
        # Get calls for the specified date and agent
        calls = CallRecording.objects.filter(
            uploaded_by=agent,
            call_date__date=target_date
        ).select_related('lead').order_by('call_date')
        
        # Format call data
        calls_data = []
        for call in calls:
            # Format duration
            duration_str = call.get_duration_display() if call.duration else 'Unknown'
            
            # Format call time
            call_time = call.call_date.strftime('%H:%M:%S')
            
            calls_data.append({
                'lead_name': call.lead.student_name if call.lead else 'Unknown Lead',
                'lead_mobile': call.lead.mobile_number if call.lead else 'N/A',
                'lead_email': call.lead.email if call.lead else 'N/A',
                'lead_status': call.lead.status if call.lead else 'N/A',
                'call_time': call_time,
                'duration': duration_str,
                'notes': call.notes or '',
                'recording_url': call.recording_file.url if call.recording_file else None,
                'recording_filename': call.recording_file.name.split('/')[-1] if call.recording_file else None
            })
        
        return JsonResponse({
            'success': True,
            'calls': calls_data,
            'date': date_str,
            'agent_name': agent.name,
            'total_calls': len(calls_data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def send_proposal_view(request, inquiry_id):
    """Send proposal via email and WhatsApp with PDF attachment"""
    try:
        inquiry = Lead.objects.get(id=inquiry_id)
        
        if request.method == 'POST':
            proposal_type = request.POST.get('proposal_type')  # 'email', 'whatsapp', or 'both'
            custom_message = request.POST.get('custom_message', '')
            
            success_messages = []
            error_messages = []
            pdf_filepath = None
            pdf_filename = None
            
            # Generate PDF proposal
            try:
                # Get company information from settings
                company_settings = CompanySettings.get_settings()
                company_info = {
                    'name': company_settings.name,
                    'address': company_settings.address,
                    'phone': company_settings.phone,
                    'email': company_settings.email,
                    'website': company_settings.website
                }
                
                # Generate PDF
                proposal_generator = ProposalGenerator()
                pdf_filepath, pdf_filename = proposal_generator.generate_proposal_pdf(
                    inquiry, custom_message, company_info
                )
                
                success_messages.append("Professional PDF proposal generated successfully")
                
            except Exception as e:
                error_messages.append(f"Failed to generate PDF: {str(e)}")
                return redirect('inquiry_list')
            
            # Email proposal with PDF attachment
            if proposal_type in ['email', 'both'] and inquiry.email:
                try:
                    # Check email configuration first
                    if not settings.EMAIL_HOST_USER:
                        error_messages.append("Email configuration error: EMAIL_HOST_USER not set. Please contact admin.")
                        print("EMAIL CONFIGURATION ERROR: EMAIL_HOST_USER is not set in environment variables")
                    elif not settings.EMAIL_HOST_PASSWORD:
                        error_messages.append("Email configuration error: EMAIL_HOST_PASSWORD not set. Please contact admin.")
                        print("EMAIL CONFIGURATION ERROR: EMAIL_HOST_PASSWORD is not set in environment variables")
                    else:
                        subject = f"Educational Proposal for {inquiry.student_name} - {inquiry.student_class}"
                        print(f"Attempting to send email to: {inquiry.email}")
                        print(f"From email: {settings.EMAIL_HOST_USER}")
                        print(f"Subject: {subject}")
                        
                        # Create HTML message
                        html_message = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 10px;">
                                Educational Proposal
                            </h2>
                            
                            <p>Dear <strong>{inquiry.parent_name}</strong>,</p>
                            
                            <p>Thank you for your interest in our educational services for <strong>{inquiry.student_name}</strong>.</p>
                            
                            {f'<p style="background: #f8f9fa; padding: 15px; border-left: 4px solid #6366f1; margin: 20px 0;">{custom_message}</p>' if custom_message else ''}
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #6366f1; margin-top: 0;">Proposal Details</h3>
                                <p><strong>Student Name:</strong> {inquiry.student_name}</p>
                                <p><strong>Class:</strong> {inquiry.student_class}</p>
                                <p><strong>Inquiry Source:</strong> {inquiry.inquiry_source}</p>
                            </div>
                            
                            <p>Please find attached our detailed professional proposal for {inquiry.student_name} studying in {inquiry.student_class}.</p>
                            
                            <p>The proposal includes:</p>
                            <ul>
                                <li>Complete fee structure</li>
                                <li>Educational services offered</li>
                                <li>Terms and conditions</li>
                                <li>Contact information</li>
                            </ul>
                            
                            <p>Please review the proposal and contact us for any questions or to proceed with admission.</p>
                            
                            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                                <p style="margin: 0;"><strong>Best regards,</strong><br>
                                Your Education Team</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                        
                        # Plain text version
                        plain_message = f"""
Dear {inquiry.parent_name},

Thank you for your interest in our educational services for {inquiry.student_name}.

{custom_message if custom_message else ''}

Please find attached our detailed professional proposal for {inquiry.student_name} studying in {inquiry.student_class}.

The proposal includes:
- Complete fee structure
- Educational services offered
- Terms and conditions
- Contact information

Please review the proposal and contact us for any questions or to proceed with admission.

Best regards,
Your Education Team
                        """.strip()
                        
                        # Send email with PDF attachment
                        email = EmailMessage(
                            subject=subject,
                            body=plain_message,
                            from_email=settings.EMAIL_HOST_USER,
                            to=[inquiry.email]
                        )
                        email.content_subtype = "html"
                        email.attach_file(pdf_filepath)
                        email.send()
                        
                        success_messages.append(f"Email proposal with PDF sent to {inquiry.email}")
                        print(f"Email sent successfully to: {inquiry.email}")
                    
                except Exception as e:
                    error_message = f"Failed to send email: {str(e)}"
                    error_messages.append(error_message)
                    print(f"EMAIL SENDING ERROR: {error_message}")
                    print(f"Full error details: {repr(e)}")
            
            # WhatsApp proposal with PDF link
            if proposal_type in ['whatsapp', 'both'] and inquiry.mobile_number:
                try:
                    # Create WhatsApp message with PDF download link
                    whatsapp_message = f"""
*Educational Proposal for {inquiry.student_name}*

Dear {inquiry.parent_name},

Thank you for your interest in our educational services for {inquiry.student_name}.

{custom_message if custom_message else ''}

*Proposal Details:*
• Student: {inquiry.student_name}
• Class: {inquiry.student_class}
• Source: {inquiry.inquiry_source}

We have prepared a detailed professional proposal for {inquiry.student_name} studying in {inquiry.student_class}.

*The proposal includes:*
• Complete fee structure
• Educational services offered
• Terms and conditions
• Contact information

Please review the proposal and contact us for any questions or to proceed with admission.

Best regards,
Your Education Team
                    """.strip()
                    
                    # Generate WhatsApp link
                    whatsapp_link = f"https://wa.me/{inquiry.mobile_number}?text={whatsapp_message.replace(' ', '%20').replace(chr(10), '%0A')}"
                    
                    success_messages.append(f"WhatsApp proposal link generated for {inquiry.mobile_number}")
                    
                    # Store the WhatsApp link and PDF info in session
                    request.session['whatsapp_link'] = whatsapp_link
                    request.session['pdf_filename'] = pdf_filename
                    
                except Exception as e:
                    error_messages.append(f"Failed to generate WhatsApp link: {str(e)}")
            
            # Log the proposal sending activity
            if success_messages:
                # Update proposal tracking fields
                inquiry.proposal_sent_date = timezone.now()
                inquiry.proposal_sent_by = request.user
                inquiry.save()
                
                # Create a log entry for proposal sending
                proposal_data = {
                    'proposal_type': proposal_type,
                    'custom_message': custom_message,
                    'pdf_filename': pdf_filename,
                    'success_messages': success_messages,
                    'error_messages': error_messages,
                    'sent_at': timezone.now().isoformat()
                }
                
                LeadLogs.objects.create(
                    lead=inquiry,
                    changed_by=request.user,
                    changed_at=timezone.now(),
                    previous_data={},  # No previous data for new proposal
                    new_data=proposal_data
                )
            
            # Add success/error messages
            for msg in success_messages:
                messages.success(request, msg)
            for msg in error_messages:
                messages.error(request, msg)
            
            # Redirect back to inquiry list
            return redirect('inquiry_list')
        
        # GET request - show proposal form
        return render(request, 'inquiries/send_proposal.html', {
            'inquiry': inquiry,
            'whatsapp_link': request.session.get('whatsapp_link', ''),
            'pdf_filename': request.session.get('pdf_filename', '')
        })
        
    except Lead.DoesNotExist:
        messages.error(request, 'Lead not found.')
        return redirect('inquiry_list')

@login_required
def download_proposal_pdf(request, inquiry_id):
    """Download the generated PDF proposal"""
    try:
        inquiry = Lead.objects.get(id=inquiry_id)
        
        # Get the latest proposal log for this lead
        latest_proposal_log = LeadLogs.objects.filter(
            lead=inquiry,
            new_data__has_key='pdf_filename'
        ).order_by('-changed_at').first()
        
        if not latest_proposal_log:
            messages.error(request, 'No proposal PDF found for this lead.')
            return redirect('inquiry_list')
        
        pdf_filename = latest_proposal_log.new_data.get('pdf_filename')
        if not pdf_filename:
            messages.error(request, 'PDF filename not found.')
            return redirect('inquiry_list')
        
        # Construct file path
        pdf_filepath = os.path.join(settings.MEDIA_ROOT, 'proposals', pdf_filename)
        
        if not os.path.exists(pdf_filepath):
            messages.error(request, 'PDF file not found on server.')
            return redirect('inquiry_list')
        
        # Serve the file for download
        with open(pdf_filepath, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            return response
            
    except Lead.DoesNotExist:
        messages.error(request, 'Lead not found.')
        return redirect('inquiry_list')
    except Exception as e:
        messages.error(request, f'Error downloading PDF: {str(e)}')
        return redirect('inquiry_list')

@login_required
def preview_proposal_pdf(request, inquiry_id):
    """Preview the proposal PDF before sending"""
    try:
        inquiry = Lead.objects.get(id=inquiry_id)
        
        # Check if this is a PDF generation request (GET with custom_message parameter)
        custom_message = request.GET.get('custom_message', '')
        
        print(f"Preview request - inquiry_id: {inquiry_id}, custom_message: {custom_message}, method: {request.method}")
        
        if custom_message or request.method == 'POST':
            # Generate PDF for preview
            if request.method == 'POST':
                custom_message = request.POST.get('custom_message', '')
            
            try:
                # Get company information from settings
                try:
                    company_settings = CompanySettings.get_settings()
                    company_info = {
                        'name': company_settings.name,
                        'address': company_settings.address,
                        'phone': company_settings.phone,
                        'email': company_settings.email,
                        'website': company_settings.website
                    }
                except:
                    # Fallback to default company info if settings don't exist
                    company_info = {
                        'name': 'Your Educational Institution',
                        'address': 'Your Institution Address, City, State - PIN',
                        'phone': '+91-XXXXXXXXXX',
                        'email': 'info@yourinstitution.com',
                        'website': 'www.yourinstitution.com'
                    }
                
                # Generate PDF for preview
                proposal_generator = ProposalGenerator()
                pdf_filepath, pdf_filename = proposal_generator.generate_proposal_pdf(
                    inquiry, custom_message, company_info
                )
                
                # Check if this is a direct download request
                if request.GET.get('download') == 'true':
                    # Serve the PDF for download
                    with open(pdf_filepath, 'rb') as pdf_file:
                        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                        return response
                else:
                    # Serve the PDF for preview
                    with open(pdf_filepath, 'rb') as pdf_file:
                        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
                        return response
                    
            except Exception as pdf_error:
                # Return error message as HTML for iframe
                error_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                    <h3 style="color: #dc3545;">Error Generating Preview</h3>
                    <p style="color: #666;">{str(pdf_error)}</p>
                    <p style="color: #666;">Please check your company settings and try again.</p>
                    <br>
                    <a href="/inquiries/preview-proposal/{inquiry.id}/?custom_message={custom_message}&download=true" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download PDF Instead</a>
                </body>
                </html>
                """
                return HttpResponse(error_html, content_type='text/html')
        else:
            # Show preview form
            return render(request, 'inquiries/preview_proposal.html', {
                'inquiry': inquiry
            })
            
    except Lead.DoesNotExist:
        messages.error(request, 'Lead not found.')
        return redirect('inquiry_list')
    except Exception as e:
        messages.error(request, f'Error generating preview: {str(e)}')
        return redirect('inquiry_list')

@login_required
def test_email_config(request):
    """Test email configuration"""
    if request.method == 'POST':
        try:
            test_email = request.POST.get('test_email')
            if not test_email:
                messages.error(request, "Please provide a test email address")
                return redirect('inquiry_list')
            
            # Check email configuration
            if not settings.EMAIL_HOST_USER:
                messages.error(request, "Email configuration error: EMAIL_HOST_USER not set")
                return redirect('inquiry_list')
            if not settings.EMAIL_HOST_PASSWORD:
                messages.error(request, "Email configuration error: EMAIL_HOST_PASSWORD not set")
                return redirect('inquiry_list')
            
            # Send test email
            subject = "Test Email from CRM System"
            message = f"""
Hello,

This is a test email to verify that your email configuration is working correctly.

Email sent from: {settings.EMAIL_HOST_USER}
Test email sent to: {test_email}
Timestamp: {timezone.now()}

If you received this email, your email configuration is working properly!

Best regards,
CRM System
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[test_email],
                fail_silently=False
            )
            
            messages.success(request, f"Test email sent successfully to {test_email}")
            print(f"Test email sent successfully to {test_email}")
            
        except Exception as e:
            error_msg = f"Failed to send test email: {str(e)}"
            messages.error(request, error_msg)
            print(f"Test email error: {error_msg}")
            
        return redirect('inquiry_list')
    
    return redirect('inquiry_list')

@login_required
def realtime_preview_html(request, inquiry_id):
    """Generate real-time HTML preview of the proposal"""
    try:
        inquiry = Lead.objects.get(id=inquiry_id)
        custom_message = request.GET.get('custom_message', '')
        
        # Get company information from settings
        try:
            company_settings = CompanySettings.get_settings()
            company_info = {
                'name': company_settings.name,
                'address': company_settings.address,
                'phone': company_settings.phone,
                'email': company_settings.email,
                'website': company_settings.website
            }
        except:
            # Fallback to default company info if settings don't exist
            company_info = {
                'name': 'Your Educational Institution',
                'address': 'Your Institution Address, City, State - PIN',
                'phone': '+91-XXXXXXXXXX',
                'email': 'info@yourinstitution.com',
                'website': 'www.yourinstitution.com'
            }
        
        # Calculate fees based on class
        fee_structure = {
            'Play School': 3000, 'Nursery': 3500, 'LKG': 4000, 'UKG': 4500,
            'Grade 1': 5000, 'Grade 2': 5500, 'Grade 3': 6000, 'Grade 4': 6500,
            'Grade 5': 7000, 'Grade 6': 7500, 'Grade 7': 8000, 'Grade 8': 8500,
            'Grade 9': 9000, 'Grade 10': 9500, 'Grade 11': 10000, 'Grade 12': 10500,
        }
        base_fee = fee_structure.get(inquiry.student_class, 5000)
        
        # Generate HTML preview
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Proposal Preview</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .title {{ color: #6366f1; font-size: 24px; margin-bottom: 10px; }}
                .company-info {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 25px; }}
                .section-title {{ color: #4f46e5; font-size: 18px; margin-bottom: 15px; border-bottom: 2px solid #6366f1; padding-bottom: 5px; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .info-table td {{ padding: 8px; border: 1px solid #ddd; }}
                .info-table td:first-child {{ background: #f3f4f6; font-weight: bold; width: 30%; }}
                .services-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .services-table th, .services-table td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                .services-table th {{ background: #6366f1; color: white; }}
                .pricing-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .pricing-table th, .pricing-table td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                .pricing-table th {{ background: #059669; color: white; }}
                .total-row {{ background: #fef3c7; font-weight: bold; }}
                .custom-message {{ background: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 40px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">Educational Proposal for {inquiry.student_name}</div>
                <div>Date: {timezone.now().strftime('%B %d, %Y')}</div>
            </div>
            
            <div class="company-info">
                <strong>{company_info['name']}</strong><br>
                {company_info['address']}<br>
                Phone: {company_info['phone']} | Email: {company_info['email']}<br>
                Website: {company_info['website']}
            </div>
            
            <div class="section">
                <div class="section-title">Student Information</div>
                <table class="info-table">
                    <tr><td>Student Name</td><td>{inquiry.student_name}</td></tr>
                    <tr><td>Class</td><td>{inquiry.student_class}</td></tr>
                    <tr><td>Parent Name</td><td>{inquiry.parent_name}</td></tr>
                    <tr><td>Contact Number</td><td>{inquiry.mobile_number or 'Not provided'}</td></tr>
                    <tr><td>Email Address</td><td>{inquiry.email or 'Not provided'}</td></tr>
                    <tr><td>Address</td><td>{inquiry.address or 'Not provided'}</td></tr>
                    <tr><td>Inquiry Source</td><td>{inquiry.inquiry_source}</td></tr>
                </table>
            </div>
            
            {f'<div class="custom-message"><strong>Personal Message:</strong><br>{custom_message}</div>' if custom_message else ''}
            
            <div class="section">
                <div class="section-title">Our Educational Services</div>
                <table class="services-table">
                    <tr>
                        <th>Service</th>
                        <th>Description</th>
                        <th>Benefits</th>
                    </tr>
                    <tr>
                        <td>Academic Excellence</td>
                        <td>Comprehensive curriculum designed for holistic development</td>
                        <td>Strong foundation for future success</td>
                    </tr>
                    <tr>
                        <td>Experienced Faculty</td>
                        <td>Qualified and experienced teachers</td>
                        <td>Quality education and mentorship</td>
                    </tr>
                    <tr>
                        <td>Modern Infrastructure</td>
                        <td>State-of-the-art facilities and technology</td>
                        <td>Enhanced learning experience</td>
                    </tr>
                    <tr>
                        <td>Individual Attention</td>
                        <td>Personalized attention to each student</td>
                        <td>Better understanding and growth</td>
                    </tr>
                    <tr>
                        <td>Extracurricular Activities</td>
                        <td>Sports, arts, and cultural programs</td>
                        <td>Overall personality development</td>
                    </tr>
                    <tr>
                        <td>Career Guidance</td>
                        <td>Professional career counseling and guidance</td>
                        <td>Clear career path and goals</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <div class="section-title">Investment Details</div>
                <table class="pricing-table">
                    <tr>
                        <th>Fee Component</th>
                        <th>Amount (₹)</th>
                        <th>Description</th>
                    </tr>
                    <tr>
                        <td>Tuition Fee</td>
                        <td>₹{base_fee:,}</td>
                        <td>Monthly tuition fee</td>
                    </tr>
                    <tr>
                        <td>Admission Fee</td>
                        <td>₹5,000</td>
                        <td>One-time admission fee</td>
                    </tr>
                    <tr>
                        <td>Development Fee</td>
                        <td>₹2,000</td>
                        <td>Annual development fee</td>
                    </tr>
                    <tr>
                        <td>Transportation</td>
                        <td>₹1,500</td>
                        <td>Monthly transportation (optional)</td>
                    </tr>
                    <tr class="total-row">
                        <td>Total Monthly</td>
                        <td>₹{base_fee + 1500:,}</td>
                        <td>Including transportation</td>
                    </tr>
                    <tr class="total-row">
                        <td>Total Annual</td>
                        <td>₹{(base_fee + 1500) * 12 + 7000:,}</td>
                        <td>Including all fees</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <div class="section-title">Terms & Conditions</div>
                <ul>
                    <li>Fees are payable monthly in advance by the 5th of each month</li>
                    <li>Late payment may incur additional charges</li>
                    <li>30 days notice is required for withdrawal</li>
                    <li>The institution reserves the right to modify fee structure with prior notice</li>
                    <li>All disputes are subject to local jurisdiction</li>
                    <li>This proposal is valid for 30 days from the date of issue</li>
                </ul>
            </div>
            
            <div class="footer">
                Thank you for considering our educational services. We look forward to partnering in your child's educational journey.
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Lead.DoesNotExist:
        return HttpResponse("Lead not found", content_type='text/plain')
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", content_type='text/plain')

