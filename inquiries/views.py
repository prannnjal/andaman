from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Lead, Agent, CustomUser
from cities_light.models import City
from .forms import InquiryForm, ManageLeadStatusForm, AgentForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
# Django's authenticate() function doesn't itself contain the authentication logic—it simply loops through all the backends listed in your AUTHENTICATION_BACKENDS setting and calls their authenticate() methods. 
from datetime import date, timedelta
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.timezone import now
from django.contrib import messages
from openpyxl import Workbook
from django.db.models import Count, Q, DateField, F
from django.db.models.functions import TruncDate
from django.conf import settings
from django.http import JsonResponse
import pandas as pd

# ====================================================================================

# Function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_staff  # Only allow staff users (admins)

# ====================================================================================

def agent_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Django's authenticate() function doesn't itself contain the authentication logic—it simply loops through all the backends listed in your AUTHENTICATION_BACKENDS setting and calls their authenticate() methods. Authenticate user based on email and password. The authenticate is our custom def authenticate() function which we have created in our auth_backends.py file. 
        
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_staff:  # Check if user is admin (staff user)
                print("===============> Admin logged in\n")
                login(request, user)
                # The function sets a session cookie on the user's browser, and Django uses that cookie to identify the user in future requests. After this call, request.user will return the logged-in user on subsequent requests.
                
                return redirect('dashboard')  # Redirect to the admin dashboard

            try:
                print("===============> Agent logged in\n")
                # Check if the authenticated user is an Agent
                agent = user.agent  # This will work only for users who are agents
                login(request, user)
                return redirect('dashboard')  # Redirect to the agent's dashboard
            except Agent.DoesNotExist:
                messages.error(request, 'This account is not an agent.')
                return redirect('agent_login')  # Stay on the login page

        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'inquiries/agent_login.html')

# ====================================================================================

@login_required
def inquiry_list(request):
    user = request.user     # request.user returns the currently logged-in user, which is an instance of your CustomUser model (or User if you haven't switched to a custom model).

    # Filter inquiries based on user type (staff or agent)
    if user.is_staff:
        inquiries = Lead.objects.all()
    elif getattr(user, "agent", None):  # Check if the user is linked to an Agent. Since Agent has a OneToOneField to CustomUser, we check if the user has an agent attribute before accessing user.agent.
        inquiries = Lead.objects.filter(assigned_agent=user.agent)  # Agent has a OneToOneField linked to CustomUser. So you can simply access agent model instance of a user via user.agent.
    else:
        inquiries = Lead.objects.none()     # return an empty queryset if the user is neither an admin nor an agent
    
    # Handle filters from the GET request
    student_name = request.GET.get('student_name')
    if student_name:
        inquiries = inquiries.filter(student_name__icontains=student_name)  # icontains = Partial match (case insensitive)

    mobile_number = request.GET.get('mobile_number')
    if mobile_number:
        inquiries = inquiries.filter(mobile_number__icontains=mobile_number)

    student_class = request.GET.get('student_class')
    if student_class:
        inquiries = inquiries.filter(student_class=student_class)

    inquiry_source = request.GET.get('inquiry_source')
    if inquiry_source:
        inquiries = inquiries.filter(inquiry_source__icontains=inquiry_source)

    status = request.GET.get('status')
    if status:
        inquiries = inquiries.filter(status=status)

    agent = request.GET.get('agent')
    if agent:
        inquiries = inquiries.filter(assigned_agent_id=agent)

    agent_email = request.GET.get('agent_email')
    if agent_email:
        inquiries = inquiries.filter(assigned_agent__user__email__icontains=agent_email)    # we use double underscore(__) to access sub-attribute of a field. Like here we are accessing assigned_agent.user.email
        
    location_panchayat = request.GET.get('location_panchayat')
    if location_panchayat:
        inquiries = inquiries.filter(location_panchayat__icontains=location_panchayat)
        
    block = request.GET.get('block')
    if block:
        inquiries = inquiries.filter(block__icontains=block)

    admin_name = request.GET.get('admin_name')
    if admin_name:
        inquiries = inquiries.filter(admin_assigned__isnull=False, admin_assigned__username__icontains=admin_name)

    admin_email = request.GET.get('admin_email')
    if admin_email:
        inquiries = inquiries.filter(admin_assigned__isnull=False,admin_assigned__email__icontains=admin_email)
        
    follow_up_date = request.GET.get('follow_up_date')
    if follow_up_date:
        inquiries = inquiries.filter(follow_up_date=follow_up_date)

    inquiry_date = request.GET.get('inquiry_date')
    if inquiry_date:
        inquiries = inquiries.filter(inquiry_date=inquiry_date)

    registration_date = request.GET.get('registration_date')
    if registration_date:
        inquiries = inquiries.filter(registration_date=registration_date)

    admission_test_date = request.GET.get('admission_test_date')
    if admission_test_date:
        inquiries = inquiries.filter(admission_test_date=admission_test_date)

    admission_offered_date = request.GET.get('admission_offered_date')
    if admission_offered_date:
        inquiries = inquiries.filter(admission_offered_date=admission_offered_date)

    admission_confirmed_date = request.GET.get('admission_confirmed_date')
    if admission_confirmed_date:
        inquiries = inquiries.filter(admission_confirmed_date=admission_confirmed_date)

    '''
    Populate options for dropdowns. "Populate" here means retrieving data from the database and making it available for dropdown options in a form.
    The flat=True argument is used when calling .values_list() on a Django QuerySet. It flattens the results into a single list instead of returning a list of tuples.
    '''
    agents = Agent.objects.all()
    # locations = City.objects.all()        
    locations_panchayat = Lead.objects.values_list('location_panchayat', flat=True).distinct()
    block = Lead.objects.values_list('block', flat=True).distinct()
    inquiry_sources = Lead.objects.values_list('inquiry_source', flat=True).distinct()
    statuses = Lead.objects.values_list('status', flat=True).distinct()
    student_classes = Lead.objects.values_list('student_class', flat=True).distinct()
    admins = CustomUser.objects.filter(is_staff=True)

    '''
    The below is Passing context dictionary to the template. 
    
    How This is Used in the Template (inquiry_list.html)? 
    
    {% for inquiry in inquiries %}
        <tr>
            <td>{{ inquiry.student_name }}</td>
            <td>{{ inquiry.inquiry_source }}</td>
            <td>{{ inquiry.status }}</td>
        </tr>
    {% endfor %}
    '''
    
    return render(request, 'inquiries/inquiry_list.html', {
        'inquiries': inquiries,
        'agents': agents,
        'location_panchayat': locations_panchayat,
        'block': block,
        'inquiry_sources': inquiry_sources,
        'statuses': statuses,
        'student_classes': student_classes,
        'admins': admins,
    })


# ====================================================================================

@login_required  
def add_inquiry(request):
    if request.method == 'POST':
        form = InquiryForm(request.POST, user=request.user)

        if form.is_valid():
            inquiry = form.save(commit=False)
                        
            if request.POST.get('block') == "Other":
                print("=================> yeh waaala case hit for block")
                inquiry.block = request.POST.get('manual_block')

            if request.POST.get('location_panchayat') == "Other":
                print("=================> yeh waaala case hit for panchayta")
                inquiry.location_panchayat = request.POST.get('manual_location_panchayat')

            
            inquiry.save()
            
            # print("=================> Form was valid")
            # # Print all submitted data
            # print("=============> Submitted Form Data:")
            # for field, value in request.POST.items():
            #     print(f"{field}: {value}")            

            # Get the assigned agent
            assigned_agent = inquiry.assigned_agent

            # Email recipient list
            recipient_list = []  # Default recipient email(s)
            if assigned_agent and assigned_agent.user.email:
                recipient_list.append(assigned_agent.user.email)
                send_mail(
                    subject='New Inquiry Arrived',
                    message=f'A new inquiry has arrived.\n\nDetails:\n{inquiry}',
                    from_email='uncertain30@gmail.com',  # Sender email
                    recipient_list=recipient_list,  # Recipient email(s)
                    fail_silently=False,
                )                        
            
            return redirect('inquiry_list')
        # else:
        #     print("==================> form was not valid and form.location_panchayat = ")
            
        #     # Print all submitted data
        #     print("Submitted Form Data:")
        #     for field, value in request.POST.items():
        #         print(f"{field}: {value}")
    else:
        form = InquiryForm(user=request.user)
        
    return render(request, 'inquiries/add_inquiry.html', {'form': form})

# ====================================================================================

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
def manage_lead_status(request, inquiry_id):
    # Fetch the Lead instance for the given inquiry_id
    inquiry = get_object_or_404(Lead, id=inquiry_id)    # fetches that instance from Lead model whose id is=inquiry_id 

    if request.method == 'POST':
        # Bind the form with POST data and the current inquiry instance. This ensures that the form updates the correct Lead object instead of creating a new one.
        form = ManageLeadStatusForm(request.POST, instance=inquiry)
        
        if form.is_valid(): # Ensures all required fields are correctly filled.
            form.save()  # Save the form with updated values
            
            # Optionally, add logic for email notifications or additional actions here
            
            return redirect('inquiry_list')  # Redirect back to the inquiry list after saving
    else:
        # Prefill form with the inquiry's current details
        form = ManageLeadStatusForm(initial={
            'assigned_agent': inquiry.assigned_agent,
            'status': inquiry.status,
            'remarks': inquiry.remarks,
            'inquiry_date': inquiry.inquiry_date,
            'follow_up_date': inquiry.follow_up_date,            
            'registration_date': inquiry.registration_date,
            'admission_test_date': inquiry.admission_test_date,
            'admission_offered_date': inquiry.admission_offered_date,
            'admission_confirmed_date': inquiry.admission_confirmed_date,
            'rejected_date': inquiry.rejected_date,            
            'admin_assigned': inquiry.admin_assigned,
        }, instance=inquiry)  # Ensure form is tied to the existing instance

    return render(request, 'inquiries/update_status.html', {'form': form, 'inquiry': inquiry})

# ====================================================================================


@login_required
@user_passes_test(is_admin)  # Restrict access to admins
def remove_agent_view(request):
    if request.method == 'POST':
        # print("===============> request.POST = ",request.POST)
        lead_id = request.POST.get('lead_id')  # Get the lead ID
        
        print("===============> lead_id = ",lead_id)
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
        agents = Agent.objects.prefetch_related('lead_set').all()
        '''
        This query retrieves all agents and their respective leads. Below is way to access it: 
        
        for agent in agents:
            print(agent.lead_set.all())
        '''
        return render(request, 'inquiries/remove_lead.html', {'agents': agents})

# ====================================================================================

@login_required
def dashboard(request):
    user = request.user  # Get the logged-in user

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.is_staff:  
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.filter(assigned_agent__user=user)  # Agent sees only their assigned inquiries

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

    return render(request, 'inquiries/dashboard.html', context)

# ====================================================================================

@login_required
def agent_performance(request):
    user = request.user  # Get the logged-in user

    # If the user is an admin, get all agents; otherwise, get only the logged-in agent
    if user.is_staff:
        agents = Agent.objects.all()  # Admins see all agents
    else:
        agents = Agent.objects.filter(user=user)  # Agents see only their own data

    # Initialize list to store agent performance data
    agent_data = []

    for agent in agents:
        # Total Leads Assigned
        total_leads = Lead.objects.filter(assigned_agent=agent).count()

        # Leads Converted to Registration
        leads_to_registration = Lead.objects.filter(assigned_agent=agent, status='Registration').count()

        # Leads Converted to Admission Offered
        leads_to_admission_offered = Lead.objects.filter(assigned_agent=agent, status='Admission Offered').count()

        # Leads Converted to Admission Confirmed
        leads_to_admission_confirmed = Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed').count()

        # Leads Rejected
        leads_rejected = Lead.objects.filter(assigned_agent=agent, status='Rejected').count()

        # Conversion Rates (Admission Offered and Confirmed)
        conversion_rate = (leads_to_admission_offered + leads_to_admission_confirmed) / total_leads * 100 if total_leads > 0 else 0

        # Follow-Up Efficiency (leads with follow-up date set)
        leads_with_follow_up = Lead.objects.filter(assigned_agent=agent, follow_up_date__isnull=False).count()
        follow_up_efficiency = (leads_with_follow_up / total_leads * 100) if total_leads > 0 else 0

        # Average Time to Conversion (from Inquiry to Admission Confirmed)
        total_days_to_conversion = sum(
            (lead.admission_confirmed_date - lead.inquiry_date).days
            for lead in Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed')
            if lead.inquiry_date and lead.admission_confirmed_date
        )
        conversions_count = Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed').count()
        average_days_to_conversion = total_days_to_conversion / conversions_count if conversions_count else 0

        # Leads Remaining in Pending Status (still in Inquiry or Follow-up)
        leads_in_pending = Lead.objects.filter(assigned_agent=agent, status__in=['Inquiry', 'Follow-up']).count()

        # Collect data for each agent
        agent_data.append({
            'agent': agent,
            'total_leads': total_leads,
            'leads_to_registration': leads_to_registration,
            'leads_to_admission_offered': leads_to_admission_offered,
            'leads_to_admission_confirmed': leads_to_admission_confirmed,
            'leads_rejected': leads_rejected,
            'conversion_rate': conversion_rate,
            'follow_up_efficiency': follow_up_efficiency,
            'average_days_to_conversion': average_days_to_conversion,
            'leads_in_pending': leads_in_pending
        })

    # Sort agents by performance (conversion rate as example)
    agent_data = sorted(agent_data, key=lambda x: x['conversion_rate'], reverse=True)

    # Render the performance template
    return render(request, 'inquiries/agent_performance.html', {'agent_data': agent_data})


# ====================================================================================

@login_required
def export_inquiries_excel(request):
    user = request.user  # Get the logged-in user

    # If the user is an admin, get all inquiries; otherwise, get only the logged-in agent's inquiries
    if user.is_staff:
        inquiries = Lead.objects.all()
    else:
        inquiries = Lead.objects.filter(assigned_agent__user=user)  # Filter only assigned inquiries for the agent

    # Create a workbook and select the active worksheet
    workbook = Workbook()   # Create a new Excel workbook
    worksheet = workbook.active  # Gets the default (active) sheet in the workbook.
    worksheet.title = "Inquiries"   # Rename the sheet to "Inquiries"

    # Add the header row
    headers = [
        'Student Name', 'Parent Name', 'Mobile Number', 'Email', 'Address', 'Block',
        'Location/Panchayat', 'Inquiry Source', 'Student Class', 'Status',
        'Remarks', 'Inquiry Date', 'Follow-up Date', 'Registration Date',
        'Admission Test Date', 'Admission Offered Date', 'Admission Confirmed Date',
        'Rejected Date', 'Assigned Agent', 'Admin Assigned'
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
            inquiry.follow_up_date if inquiry.follow_up_date else "N/A",
            inquiry.registration_date if inquiry.registration_date else "N/A",
            inquiry.admission_test_date if inquiry.admission_test_date else "N/A",
            inquiry.admission_offered_date if inquiry.admission_offered_date else "N/A",
            inquiry.admission_confirmed_date if inquiry.admission_confirmed_date else "N/A",
            inquiry.rejected_date if inquiry.rejected_date else "N/A",
            inquiry.assigned_agent.name if inquiry.assigned_agent else "N/A",
            inquiry.admin_assigned.username if inquiry.admin_assigned else "N/A"
        ])

    # Set the response content type and save the workbook to the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')   # This tells Django that the response contains an Excel file (.xlsx format).
    
    response['Content-Disposition'] = 'attachment; filename="inquiries.xlsx"'   # This forces a file download instead of displaying raw data in the browser. The file will be named inquiries.xlsx when downloaded.

    workbook.save(response)     # saving the Excel file directly into the HTTP response
    return response     # Sends the Excel file as a downloadable response to the user

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def assign_lead(request):
    inquiries = Lead.objects.filter(assigned_agent__isnull=True)  # Fetch unassigned inquiries
    agents = Agent.objects.all()  # Fetch all agents

    if request.method == 'POST':
        inquiry_id = request.POST.get('inquiry_id')  # Get selected inquiry ID
        agent_id = request.POST.get('agent_id')  # Get selected agent ID

        # Validate input
        if not inquiry_id or not agent_id:
            messages.error(request, "Please select both an inquiry and an agent.")
            return redirect('assign_lead')

        try:
            # Get the inquiry and agent objects
            inquiry = get_object_or_404(Lead, id=inquiry_id)
            agent = get_object_or_404(Agent, id=agent_id)

            # Assign the agent to the inquiry
            inquiry.assigned_agent = agent
            inquiry.save()

            # Provide success feedback to the user
            messages.success(request, f"Inquiry for '{inquiry.student_name}' has been successfully assigned to Agent '{agent.name}'.")
        except Exception as e:
            # Handle unexpected errors gracefully
            messages.error(request, f"An error occurred while assigning the lead: {str(e)}")

        return redirect('assign_lead')  # Redirect to the same page after assignment

    # If request is GET    
    return render(request, 'inquiries/assign_lead.html', {
        'inquiries': inquiries,
        'agents': agents
    })
    
# ====================================================================================

@login_required
@user_passes_test(is_admin)
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
def send_agent_welcome_email(agent, default_password):
    subject = "Welcome to the Team!"
    message = f"Hello {agent.name},\n\n" \
              f"Your agent account has been created successfully.\n\n" \
              f"Here are your login credentials:\n" \
              f"Email: {agent.user.email}\n" \
              f"Password: {default_password}\n\n" \
              f"Please login and change your password after the first login.\n\n" \
              f"Best regards,\nThe Team"
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,  # Default email set in settings.py
        recipient_list=[agent.user.email],
        fail_silently=False,
    )

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
            #default_password = CustomUser.objects.make_random_password()  # Generates a secure random password

            
            user = CustomUser.objects.create_user(username=email, email=email, password=default_password)

            # Create the agent object and associate with the user
            agent = form.save(commit=False)  # Don't save yet; we need to associate it with the user. We just need to create the instance of the Agent as of now.
            agent.user = user  # Associate the user
            agent.save()

            # Send the email with the default password
            send_agent_welcome_email(agent, default_password)

            # Show success message
            messages.success(request, f"Agent '{agent.name}' added successfully! The default password has been sent to their email.")
            return redirect('add_agent')  # Redirect to the same page after success
        else:
            messages.error(request, "Error adding agent. Please correct the errors below.")
    else:
        form = AgentForm()

    return render(request, 'inquiries/add_agent.html', {'form': form})

# ====================================================================================

@login_required
@user_passes_test(is_admin)
def agent_list(request):
    # Get filter query parameters
    name_filter = request.GET.get('name', '')
    email_filter = request.GET.get('email', '')
    min_score_filter = request.GET.get('min_score', '')
    max_score_filter = request.GET.get('max_score', '')

    # Filter agents based on the query parameters
    agents = Agent.objects.all()

    if name_filter:
        agents = agents.filter(name__icontains=name_filter)
    if email_filter:
        agents = agents.filter(user__email__icontains=email_filter)
    if min_score_filter:
        agents = agents.filter(performance_score__gte=int(min_score_filter))
    if max_score_filter:
        agents = agents.filter(performance_score__lte=int(max_score_filter))

    # Handle deletion of agents
    if request.method == 'POST':  # Handle agent deletion
        agent_id = request.POST.get('agent_id')  # Get the agent ID from the form
        agent = get_object_or_404(Agent, id=agent_id)
        user = agent.user  # Get the associated user
        agent.delete()
        if user:  
            user.delete()  # Delete the associated user
        messages.success(request, f"Agent '{agent.name}' has been deleted successfully.")
        return redirect('agent_list')  # Refresh the agent list after deletion

    return render(request, 'inquiries/agent_list.html', {
        'agents': agents,
        'name_filter': name_filter,
        'email_filter': email_filter,
        'min_score_filter': min_score_filter,
        'max_score_filter': max_score_filter,
    })
    
# ====================================================================================