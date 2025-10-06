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
    
    # Django admin requires these fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
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
    
    def save(self, *args, **kwargs):
        # Auto-set is_staff based on role
        if self.role == 'Admin':
            self.is_staff = True
        super().save(*args, **kwargs)
    
    

# ======================== TRAVEL CRM MODELS ========================

class Hotel(models.Model):
    """Hotel management with room categories and pricing"""
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    star_rating = models.IntegerField(choices=[(i, f"{i} Star") for i in range(1, 6)], default=3)
    amenities = models.TextField(blank=True, null=True, help_text="List amenities separated by commas")
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

    class Meta:
        ordering = ['name']


class RoomCategory(models.Model):
    """Room categories for hotels with pricing"""
    ROOM_TYPE_CHOICES = [
        ('Standard', 'Standard'),
        ('Deluxe', 'Deluxe'),
        ('Suite', 'Suite'),
        ('Presidential', 'Presidential'),
        ('Economy', 'Economy'),
    ]
    
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='room_categories')
    room_type = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    extra_mattress_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_occupancy = models.IntegerField(default=2)
    description = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.hotel.name} - {self.room_type} (₹{self.price_per_night}/night)"

    class Meta:
        unique_together = ['hotel', 'room_type']
        ordering = ['hotel', 'price_per_night']


class Package(models.Model):
    """Master package templates with day-wise details"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    duration_days = models.IntegerField(help_text="Number of days")
    duration_nights = models.IntegerField(help_text="Number of nights")
    destination = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.duration_days}D/{self.duration_nights}N)"

    class Meta:
        ordering = ['-created_at']


class PackageDay(models.Model):
    """Day-wise breakdown of package with costs"""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='package_days')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200, help_text="e.g., 'Port Blair Arrival'")
    description = models.TextField()
    
    # Transportation costs
    cab_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ferry_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    speedboat_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Entry tickets
    entry_tickets = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total entry ticket cost")
    
    # Activities
    activities = models.TextField(blank=True, null=True, help_text="Comma-separated list of activities")
    
    def __str__(self):
        return f"{self.package.name} - Day {self.day_number}: {self.title}"

    class Meta:
        ordering = ['package', 'day_number']
        unique_together = ['package', 'day_number']


class Lead(models.Model):
    """Travel inquiry leads with itinerary builder"""
    
    TRAVEL_TYPE_CHOICES = [
        ('Honeymoon', 'Honeymoon'),
        ('Family', 'Family'),
        ('Solo', 'Solo'),
        ('Group', 'Group'),
        ('Corporate', 'Corporate'),
        ('Adventure', 'Adventure'),
        ('Pilgrimage', 'Pilgrimage'),
        ('Beach', 'Beach'),
        ('Hill Station', 'Hill Station'),
    ]

    INQUIRY_CHOICES = [
        ('Website', 'Website'),
        ('Walk-in', 'Walk-in'),
        ('Social Media', 'Social Media'),  
        ('Referral', 'Referral'),
        ('Advertisement', 'Advertisement'),
        ('Phone Call', 'Phone Call'),
    ]

    STATUS_CHOICES = [
        ('New Lead', 'New Lead'),
        ('DNP', 'DNP'),
        ('Not interested', 'Not interested'),
        ('Interested', 'Interested'),
        ('Follow Up', 'Follow Up'),
        ('Budget Discussion', 'Budget Discussion'),
        ('Itinerary Sent', 'Itinerary Sent'),
        ('Negotiation', 'Negotiation'),
        ('Booking Confirmed', 'Booking Confirmed'),
        ('Trip Completed', 'Trip Completed'),
    ]

    # Customer Information
    customer_name = models.CharField(max_length=100, default='Unknown')
    mobile_number = models.CharField(max_length=15, default='0000000000')
    email = models.EmailField(max_length=100, blank=True, null=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    
    # Travel Details
    destination = models.CharField(max_length=200, default='To Be Determined', help_text="Preferred destination")
    travel_type = models.CharField(choices=TRAVEL_TYPE_CHOICES, max_length=50, default='Family')
    number_of_travelers = models.IntegerField(default=1, help_text="Number of people traveling (Pax)")
    travel_start_date = models.DateField(null=True, blank=True, help_text="Preferred travel start date")
    travel_end_date = models.DateField(null=True, blank=True, help_text="Preferred travel end date")
    duration_days = models.IntegerField(null=True, blank=True, help_text="Trip duration in days")
    
    # Budget
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Customer's budget")
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price quoted to customer")
    
    # Lead Management
    inquiry_source = models.CharField(choices=INQUIRY_CHOICES, max_length=100)
    status = models.CharField(choices=STATUS_CHOICES, max_length=100, default='New Lead')
    remarks = models.TextField(blank=True, null=True)
    
    # Important Dates
    inquiry_date = models.DateField(null=True, blank=True)    
    follow_up_date = models.DateField(null=True, blank=True)
    booking_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    
    last_follow_up_updation = models.DateField(null=True, blank=True)
    last_inquiry_updation = models.DateField(null=True, blank=True)
    
    # Itinerary/Proposal tracking
    itinerary_sent_date = models.DateTimeField(null=True, blank=True, help_text='When the last itinerary was sent')
    itinerary_sent_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itineraries_sent',
        help_text='User who sent the last itinerary'
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
        return f"{self.customer_name} - {self.destination} ({self.travel_type}) - {self.status}"
    
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
        return f"Lead: {self.lead.customer_name} - Changed by: {self.changed_by.name if self.changed_by else 'Unknown'} at {self.changed_at}"

# ======================= ITINERARY BUILDER =======================

class ItineraryBuilder(models.Model):
    """Custom itinerary created for a specific lead"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='itineraries')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, help_text="Base package template")
    
    # Package inputs
    pax = models.IntegerField(help_text="Number of travelers")
    number_of_cabs = models.IntegerField(default=1)
    duration_days = models.IntegerField()
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Auto-calculated base price")
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Markup percentage on overall package")
    markup_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Markup amount")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Final price with markup")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_finalized = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Itinerary for {self.lead.customer_name} - {self.package.name if self.package else 'Custom'}"
    
    def calculate_total(self):
        """Calculate total price based on day-wise itineraries and markup"""
        base_total = sum(day.get_total_cost() for day in self.itinerary_days.all())
        self.base_price = base_total
        self.markup_amount = (base_total * self.markup_percentage) / 100
        self.total_price = base_total + self.markup_amount
        return self.total_price
    
    class Meta:
        ordering = ['-created_at']


class ItineraryDay(models.Model):
    """Day-wise customizable itinerary for a lead"""
    itinerary = models.ForeignKey(ItineraryBuilder, on_delete=models.CASCADE, related_name='itinerary_days')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Date and Time
    travel_date = models.DateField(null=True, blank=True, help_text="Actual travel date for this day")
    check_in_date = models.DateField(null=True, blank=True, help_text="Hotel check-in date")
    check_out_date = models.DateField(null=True, blank=True, help_text="Hotel check-out date")
    
    # Hotel Selection
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    room_category = models.ForeignKey(RoomCategory, on_delete=models.SET_NULL, null=True, blank=True)
    number_of_rooms = models.IntegerField(default=1)
    extra_mattress = models.IntegerField(default=0, help_text="Number of extra mattresses")
    is_hotel_booked = models.BooleanField(default=False, help_text="Mark as booked to block dates")
    
    # Transportation (inherited from PackageDay but customizable)
    cab_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ferry_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    speedboat_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entry_tickets = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional charges
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Any extra charges for this day")
    additional_charges_description = models.TextField(blank=True, null=True)
    
    # Activities
    activities = models.TextField(blank=True, null=True)
    
    def get_hotel_cost(self):
        """Calculate hotel cost for this day"""
        hotel_cost = 0
        if self.room_category:
            hotel_cost = (self.room_category.price_per_night * self.number_of_rooms)
            if self.extra_mattress > 0:
                hotel_cost += (self.room_category.extra_mattress_price * self.extra_mattress)
        return hotel_cost
    
    def get_transport_cost(self):
        """Calculate total transport cost"""
        return self.cab_price + self.ferry_price + self.speedboat_price
    
    def get_total_cost(self):
        """Calculate total cost for this day"""
        return (
            self.get_hotel_cost() + 
            self.get_transport_cost() + 
            self.entry_tickets + 
            self.additional_charges
        )
    
    def __str__(self):
        return f"Day {self.day_number} - {self.title}"
    
    class Meta:
        ordering = ['day_number']
        unique_together = ['itinerary', 'day_number']

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


class EventPlace(models.Model):
    """Event places and activities for itineraries"""
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100, help_text="e.g., Museum, Temple, Beach, Adventure Activity")
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Entry fee per person")
    description = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    operating_hours = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 9 AM - 6 PM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    class Meta:
        ordering = ['name']


class HotelBooking(models.Model):
    """Track hotel bookings and availability"""
    itinerary_day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name='bookings')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    room_category = models.ForeignKey(RoomCategory, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_rooms = models.IntegerField(default=1)
    extra_mattress = models.IntegerField(default=0)
    booking_status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ], default='Pending')
    booking_reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.hotel.name} - {self.check_in_date} to {self.check_out_date}"
    
    class Meta:
        ordering = ['check_in_date']
        unique_together = ['hotel', 'room_category', 'check_in_date', 'check_out_date']


class CompanySettings(models.Model):
    """Model to store travel company information for itineraries/proposals"""
    name = models.CharField(max_length=200, default='Your Travel Company')
    address = models.TextField(default='Your Company Address, City, State - PIN')
    phone = models.CharField(max_length=20, default='+91-XXXXXXXXXX')
    email = models.EmailField(default='info@yourtravelcompany.com')
    website = models.URLField(default='www.yourtravelcompany.com')
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    
    # Travel-specific settings
    gst_number = models.CharField(max_length=50, blank=True, null=True, help_text="GST Registration Number")
    pan_number = models.CharField(max_length=20, blank=True, null=True, help_text="PAN Number")
    tourism_license = models.CharField(max_length=100, blank=True, null=True, help_text="Tourism License Number")
    
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
                'name': 'Your Travel Company',
                'address': 'Your Company Address, City, State - PIN',
                'phone': '+91-XXXXXXXXXX',
                'email': 'info@yourtravelcompany.com',
                'website': 'www.yourtravelcompany.com'
            }
        )
        return settings