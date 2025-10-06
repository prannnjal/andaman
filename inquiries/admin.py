from django.contrib import admin
from .models import (
    Lead, CustomUser, CompanySettings, Hotel, RoomCategory, 
    Package, PackageDay, ItineraryBuilder, ItineraryDay, 
    LeadLogs, CallRecording, EventPlace, HotelBooking
)


class RoomCategoryInline(admin.TabularInline):
    model = RoomCategory
    extra = 1
    fields = ['room_type', 'price_per_night', 'extra_mattress_price', 'max_occupancy', 'is_available']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'star_rating', 'contact_number', 'is_active', 'created_at']
    list_filter = ['star_rating', 'city', 'state', 'is_active']
    search_fields = ['name', 'city', 'contact_number']
    inlines = [RoomCategoryInline]
    readonly_fields = ['created_at', 'created_by']


@admin.register(RoomCategory)
class RoomCategoryAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'room_type', 'price_per_night', 'extra_mattress_price', 'max_occupancy', 'is_available']
    list_filter = ['room_type', 'is_available', 'hotel']
    search_fields = ['hotel__name', 'room_type']


class PackageDayInline(admin.TabularInline):
    model = PackageDay
    extra = 1
    fields = ['day_number', 'title', 'description', 'cab_price', 'ferry_price', 'speedboat_price', 'entry_tickets', 'activities']


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'destination', 'duration_days', 'duration_nights', 'is_active', 'created_at']
    list_filter = ['destination', 'is_active', 'duration_days']
    search_fields = ['name', 'destination']
    inlines = [PackageDayInline]
    readonly_fields = ['created_at', 'created_by']


@admin.register(PackageDay)
class PackageDayAdmin(admin.ModelAdmin):
    list_display = ['package', 'day_number', 'title', 'cab_price', 'ferry_price', 'speedboat_price', 'entry_tickets']
    list_filter = ['package']
    search_fields = ['package__name', 'title']


class ItineraryDayInline(admin.TabularInline):
    model = ItineraryDay
    extra = 0
    fields = ['day_number', 'title', 'hotel', 'room_category', 'number_of_rooms', 'extra_mattress']


@admin.register(ItineraryBuilder)
class ItineraryBuilderAdmin(admin.ModelAdmin):
    list_display = ['lead', 'package', 'pax', 'duration_days', 'total_price', 'is_finalized', 'created_at']
    list_filter = ['is_finalized', 'created_at']
    search_fields = ['lead__customer_name', 'package__name']
    inlines = [ItineraryDayInline]
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'base_price', 'markup_amount', 'total_price']


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    list_display = ['itinerary', 'day_number', 'title', 'hotel', 'room_category', 'number_of_rooms']
    list_filter = ['hotel', 'room_category']
    search_fields = ['itinerary__lead__customer_name', 'title']


class ItineraryBuilderInline(admin.TabularInline):
    model = ItineraryBuilder
    extra = 0
    fields = ['package', 'pax', 'duration_days', 'total_price', 'is_finalized']
    readonly_fields = ['total_price']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'mobile_number', 'destination', 'travel_type', 'status', 'assigned_agent', 'inquiry_date']
    list_filter = ['status', 'travel_type', 'inquiry_source', 'assigned_agent']
    search_fields = ['customer_name', 'mobile_number', 'email', 'destination']
    date_hierarchy = 'inquiry_date'
    inlines = [ItineraryBuilderInline]
    
    # Simplified fields for add/edit forms
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'mobile_number', 'email', 'city', 'address')
        }),
        ('Travel Details', {
            'fields': ('destination', 'travel_type', 'number_of_travelers', 'travel_start_date', 'travel_end_date', 'duration_days'),
            'classes': ('collapse',)
        }),
        ('Budget & Pricing', {
            'fields': ('budget', 'quoted_price'),
            'classes': ('collapse',)
        }),
        ('Lead Management', {
            'fields': ('inquiry_source', 'status', 'remarks', 'inquiry_date', 'follow_up_date'),
            'classes': ('collapse',)
        }),
        ('Assignment', {
            'fields': ('assigned_agent', 'admin_assigned'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form for add vs edit"""
        if obj is None:  # Adding a new lead
            # Show only customer information fields for new leads
            self.fields = ('customer_name', 'mobile_number', 'email', 'city', 'address')
            # Hide fieldsets during add
            self.fieldsets = None
        else:  # Editing existing lead
            # Show all fields in fieldsets for editing
            self.fields = None
            # Restore fieldsets for editing
            self.fieldsets = (
                ('Customer Information', {
                    'fields': ('customer_name', 'mobile_number', 'email', 'city', 'address')
                }),
                ('Travel Details', {
                    'fields': ('destination', 'travel_type', 'number_of_travelers', 'travel_start_date', 'travel_end_date', 'duration_days'),
                    'classes': ('collapse',)
                }),
                ('Budget & Pricing', {
                    'fields': ('budget', 'quoted_price'),
                    'classes': ('collapse',)
                }),
                ('Lead Management', {
                    'fields': ('inquiry_source', 'status', 'remarks', 'inquiry_date', 'follow_up_date'),
                    'classes': ('collapse',)
                }),
                ('Assignment', {
                    'fields': ('assigned_agent', 'admin_assigned'),
                    'classes': ('collapse',)
                }),
            )
        return super().get_form(request, obj, **kwargs)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile_number', 'email', 'role', 'date_joined']
    list_filter = ['role', 'date_joined']
    search_fields = ['name', 'mobile_number', 'email']


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'website']


@admin.register(LeadLogs)
class LeadLogsAdmin(admin.ModelAdmin):
    list_display = ['lead', 'changed_by', 'changed_at']
    list_filter = ['changed_at', 'changed_by']
    search_fields = ['lead__customer_name']
    readonly_fields = ['lead', 'changed_by', 'changed_at', 'previous_data', 'new_data']


@admin.register(CallRecording)
class CallRecordingAdmin(admin.ModelAdmin):
    list_display = ['lead', 'call_date', 'duration', 'uploaded_by']
    list_filter = ['call_date', 'uploaded_by']
    search_fields = ['lead__customer_name']
    readonly_fields = ['call_date', 'duration']


@admin.register(EventPlace)
class EventPlaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'event_type', 'entry_fee', 'is_active', 'created_at']
    list_filter = ['event_type', 'city', 'is_active']
    search_fields = ['name', 'city', 'location']
    readonly_fields = ['created_at', 'created_by']


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'room_category', 'check_in_date', 'check_out_date', 'booking_status', 'number_of_rooms']
    list_filter = ['booking_status', 'check_in_date', 'hotel']
    search_fields = ['hotel__name', 'booking_reference']
    readonly_fields = ['created_at', 'updated_at']