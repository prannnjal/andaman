# Travel CRM Transformation - Complete Guide

## Overview
This document outlines the transformation of the School CRM system into a comprehensive **Travel CRM** with advanced itinerary builder and package management capabilities.

---

## ✅ Completed Changes

### 1. **Database Models (100% Complete)**

#### New Models Created:
- **Hotel** - Complete hotel management with star ratings, amenities, contact info
- **RoomCategory** - Room types with pricing (Standard, Deluxe, Suite, etc.)
  - Price per night
  - Extra mattress pricing
  - Maximum occupancy
- **Package** - Master package templates
  - Duration (days/nights)
  - Destination
  - Active/inactive status
- **PackageDay** - Day-wise package breakdown
  - Cab prices
  - Ferry prices
  - Speedboat prices
  - Entry tickets
  - Activities
- **ItineraryBuilder** - Custom itineraries for leads
  - PAX (number of travelers)
  - Number of cabs
  - Duration
  - Markup percentage
  - Auto-calculated pricing
- **ItineraryDay** - Day-wise customizable itinerary
  - Hotel selection
  - Room category selection
  - Number of rooms
  - Extra mattress
  - Transportation costs
  - Additional charges

#### Updated Models:
- **Lead Model** transformed from School to Travel:
  - `student_name` → `customer_name`
  - `parent_name` → removed
  - Added: `destination`, `travel_type`, `number_of_travelers`
  - Added: `travel_start_date`, `travel_end_date`, `duration_days`
  - Added: `budget`, `quoted_price`
  - Added: `booking_date`, `payment_date`
  - Updated status choices for travel workflow
  
- **CompanySettings** updated:
  - Changed from Educational Institution to Travel Company
  - Added: `gst_number`, `pan_number`, `tourism_license`

### 2. **Admin Interface (100% Complete)**
All new models registered with comprehensive admin interfaces:
- Hotel management with inline room categories
- Package management with inline day-wise details
- Itinerary builder with inline day customization
- Enhanced list views with filters and search

### 3. **Forms (100% Complete)**
All forms updated for Travel CRM:
- `InquiryForm` - Travel inquiry creation
- `AgentUpdateLeadForm` - Agent lead management
- `EditLeadForm` - Lead editing
- All school-specific validations removed

### 4. **Database Migrations (100% Complete)**
✅ Migration created and applied: `0012_remove_lead_school_and_more.py`
- Removed all school-related fields
- Added all travel-related fields
- Created new Travel CRM models
- Database schema successfully updated

---

## 🚧 Remaining Work

### 1. **Hotel Management Module** (Priority: High)

#### Required Views:
```python
# inquiries/views.py

@login_required
@user_passes_test(is_admin)
def hotel_list(request):
    """List all hotels with filters"""
    pass

@login_required
@user_passes_test(is_admin)
def hotel_create(request):
    """Create new hotel with room categories"""
    pass

@login_required
@user_passes_test(is_admin)
def hotel_edit(request, hotel_id):
    """Edit hotel and room categories"""
    pass

@login_required
@user_passes_test(is_admin)
def hotel_delete(request, hotel_id):
    """Delete hotel"""
    pass
```

#### Required Templates:
- `templates/inquiries/hotel_list.html`
- `templates/inquiries/hotel_form.html`
- `templates/inquiries/hotel_detail.html`

#### Features Needed:
1. Upload/manage hotel details (name, address, city, contact)
2. Manage room categories with pricing
3. Set extra mattress prices
4. Bulk upload via Excel/CSV

---

### 2. **Package Management Module** (Priority: High)

#### Required Views:
```python
@login_required
@user_passes_test(is_admin)
def package_list(request):
    """List all packages"""
    pass

@login_required
@user_passes_test(is_admin)
def package_create(request):
    """Create package with day-wise breakdown"""
    pass

@login_required
@user_passes_test(is_admin)
def package_edit(request, package_id):
    """Edit package and days"""
    pass
```

#### Required Templates:
- `templates/inquiries/package_list.html`
- `templates/inquiries/package_form.html`
- `templates/inquiries/package_detail.html`

#### Features Needed:
1. Create day-wise packages
2. Add cab prices for each day
3. Add entry tickets, ferry, speedboat prices
4. Package activation/deactivation

---

### 3. **Itinerary Builder Interface** (Priority: CRITICAL)

This is the core feature that integrates with leads.

#### Required Views:
```python
@login_required
def itinerary_create(request, lead_id):
    """Create itinerary for a lead"""
    # Inputs: PAX, Package selection, Number of cabs, Days
    # Auto-generate itinerary from package template
    pass

@login_required
def itinerary_customize_day(request, itinerary_id, day_number):
    """Customize specific day of itinerary"""
    # Select hotel from database
    # Select room category
    # Number of rooms
    # Add extra charges
    pass

@login_required
def itinerary_calculate(request, itinerary_id):
    """Calculate total price with markup"""
    # Auto-calculate base price
    # Apply markup percentage
    # Generate final quotation
    pass

@login_required
def itinerary_send(request, itinerary_id):
    """Send itinerary to customer"""
    # Generate PDF/Email
    # Update lead status
    pass
```

#### Required Templates:
- `templates/inquiries/itinerary_builder.html` - Main builder interface
- `templates/inquiries/itinerary_day_customize.html` - Day customization
- `templates/inquiries/itinerary_preview.html` - Preview before sending
- `templates/inquiries/itinerary_pdf.html` - PDF template

#### Key Features:
1. **Auto-Generation**: When selecting package + PAX + cabs → auto-create all days
2. **Day-wise Customization**: 
   - Select hotel from dropdown
   - Select room category (shows available rooms with prices)
   - Input number of rooms
   - Add extra mattresses
   - Add additional charges with description
3. **Real-time Pricing**: Calculate costs as user makes selections
4. **Markup Application**: Overall package markup on final price
5. **Itinerary Preview**: Show complete itinerary before sending
6. **PDF Generation**: Professional itinerary PDF with company branding

---

### 4. **UI/UX Updates** (Priority: Medium)

#### Dashboard Updates:
Replace school-specific metrics with travel metrics:
```python
# Current metrics to change:
- Total Students → Total Travel Inquiries
- Admissions → Confirmed Bookings
- Student Class Distribution → Travel Type Distribution
- Block-wise distribution → Destination-wise distribution
```

#### Navigation Menu:
Update all navigation items:
```html
<!-- OLD -->
<a href="{% url 'school_list' %}">Schools</a>

<!-- NEW -->
<a href="{% url 'hotel_list' %}">Hotels</a>
<a href="{% url 'package_list' %}">Packages</a>
```

#### Templates to Update:
1. `dashboard.html` - Update metrics and charts
2. `lead_list.html` - Update column headers (Student Name → Customer Name, etc.)
3. `lead_detail.html` - Add itinerary builder button
4. `lead_form.html` - Already updated in forms
5. All navbar/sidebar templates

---

### 5. **URL Configuration** (Priority: High)

Add new URL patterns:

```python
# inquiries/urls.py

urlpatterns = [
    # ... existing patterns ...
    
    # Hotel Management
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/create/', views.hotel_create, name='hotel_create'),
    path('hotels/<int:hotel_id>/edit/', views.hotel_edit, name='hotel_edit'),
    path('hotels/<int:hotel_id>/delete/', views.hotel_delete, name='hotel_delete'),
    
    # Package Management
    path('packages/', views.package_list, name='package_list'),
    path('packages/create/', views.package_create, name='package_create'),
    path('packages/<int:package_id>/edit/', views.package_edit, name='package_edit'),
    path('packages/<int:package_id>/delete/', views.package_delete, name='package_delete'),
    
    # Itinerary Builder
    path('leads/<int:lead_id>/itinerary/create/', views.itinerary_create, name='itinerary_create'),
    path('itinerary/<int:itinerary_id>/', views.itinerary_detail, name='itinerary_detail'),
    path('itinerary/<int:itinerary_id>/day/<int:day_number>/customize/', views.itinerary_customize_day, name='itinerary_customize_day'),
    path('itinerary/<int:itinerary_id>/calculate/', views.itinerary_calculate, name='itinerary_calculate'),
    path('itinerary/<int:itinerary_id>/send/', views.itinerary_send, name='itinerary_send'),
    path('itinerary/<int:itinerary_id>/pdf/', views.itinerary_pdf, name='itinerary_pdf'),
]
```

---

## 📊 Model Relationships

```
Lead (Customer)
  └── ItineraryBuilder (1:Many)
       ├── Package (FK) - Base template
       ├── pax, cabs, days - Inputs
       ├── markup_percentage
       └── ItineraryDay (1:Many)
            ├── Hotel (FK)
            ├── RoomCategory (FK)
            ├── number_of_rooms
            ├── extra_mattress
            ├── cab_price, ferry_price, speedboat_price
            ├── entry_tickets
            └── additional_charges

Package
  └── PackageDay (1:Many)
       ├── day_number
       ├── title, description
       ├── cab_price, ferry_price, speedboat_price
       ├── entry_tickets
       └── activities

Hotel
  └── RoomCategory (1:Many)
       ├── room_type (Standard/Deluxe/Suite)
       ├── price_per_night
       ├── extra_mattress_price
       └── max_occupancy
```

---

## 🎯 Workflow: Creating an Itinerary for a Lead

### Step 1: Lead Inquiry Received
Agent/Admin creates lead with:
- Customer name, contact
- Destination preference
- Travel type (Honeymoon, Family, etc.)
- Number of travelers (PAX)
- Budget
- Preferred dates

### Step 2: Create Itinerary
1. From lead detail page, click "Create Itinerary"
2. Select base package (e.g., "Andaman 5D/4N Beach Package")
3. Input:
   - PAX: 4 people
   - Number of cabs: 1
   - Days: 5
4. Click "Generate Itinerary"
5. System auto-creates 5 ItineraryDay records based on PackageDay template

### Step 3: Customize Each Day
For each day:
1. Select hotel from dropdown (filtered by destination)
2. Select room category (shows price)
3. Input number of rooms (e.g., 2 rooms for 4 people)
4. Add extra mattress if needed
5. Adjust transportation costs if needed
6. Add additional charges with description

### Step 4: Apply Markup & Calculate
1. System calculates base price (sum of all days)
2. Apply markup percentage (e.g., 15%)
3. Calculate final price
4. Show breakdown:
   - Hotel costs: ₹X
   - Transportation: ₹Y
   - Activities: ₹Z
   - Markup: ₹A
   - **Total: ₹B**

### Step 5: Preview & Send
1. Preview complete itinerary
2. Generate professional PDF with:
   - Company logo
   - Day-wise breakdown
   - Hotel details
   - Pricing
   - Terms & conditions
3. Send via email or WhatsApp
4. Update lead status to "Itinerary Sent"

---

## 🔧 Technical Implementation Guide

### Itinerary Auto-Generation Logic

```python
def generate_itinerary_from_package(lead, package, pax, num_cabs):
    """Auto-generate itinerary from package template"""
    
    # Create ItineraryBuilder
    itinerary = ItineraryBuilder.objects.create(
        lead=lead,
        package=package,
        pax=pax,
        number_of_cabs=num_cabs,
        duration_days=package.duration_days,
        created_by=request.user
    )
    
    # Create ItineraryDay for each PackageDay
    for package_day in package.package_days.all():
        ItineraryDay.objects.create(
            itinerary=itinerary,
            day_number=package_day.day_number,
            title=package_day.title,
            description=package_day.description,
            cab_price=package_day.cab_price * num_cabs,  # Multiply by number of cabs
            ferry_price=package_day.ferry_price * pax,   # Multiply by PAX
            speedboat_price=package_day.speedboat_price * pax,
            entry_tickets=package_day.entry_tickets * pax,
            activities=package_day.activities
        )
    
    return itinerary
```

### Price Calculation Logic

```python
def calculate_itinerary_total(itinerary):
    """Calculate total price for itinerary"""
    
    base_total = 0
    
    for day in itinerary.itinerary_days.all():
        # Hotel cost
        if day.room_category:
            hotel_cost = day.room_category.price_per_night * day.number_of_rooms
            hotel_cost += day.room_category.extra_mattress_price * day.extra_mattress
        else:
            hotel_cost = 0
        
        # Transport cost
        transport_cost = day.cab_price + day.ferry_price + day.speedboat_price
        
        # Day total
        day_total = hotel_cost + transport_cost + day.entry_tickets + day.additional_charges
        base_total += day_total
    
    # Apply markup
    itinerary.base_price = base_total
    itinerary.markup_amount = (base_total * itinerary.markup_percentage) / 100
    itinerary.total_price = base_total + itinerary.markup_amount
    itinerary.save()
    
    return itinerary.total_price
```

---

## 📝 Next Steps (Priority Order)

1. **Immediate (Day 1-2)**:
   - ✅ Models created
   - ✅ Migrations applied
   - ✅ Admin interface configured
   - ✅ Forms updated
   - Update existing views to use new field names
   - Update URLs for hotel/package management

2. **High Priority (Day 3-5)**:
   - Create Hotel Management views & templates
   - Create Package Management views & templates
   - Update dashboard metrics and UI

3. **Critical (Day 6-10)**:
   - Build Itinerary Builder interface
   - Implement auto-generation logic
   - Create day-wise customization UI
   - Implement real-time pricing calculator

4. **Final (Day 11-12)**:
   - PDF generation for itineraries
   - Email/WhatsApp integration
   - Testing complete workflow
   - UI polish and bug fixes

---

## 🎨 UI Recommendations

### Color Scheme for Travel CRM:
- Primary: `#1E88E5` (Blue - represents sky/travel)
- Secondary: `#FFA726` (Orange - represents sun/vacation)
- Success: `#66BB6A` (Green - confirmed bookings)
- Accent: `#AB47BC` (Purple - premium packages)

### Icons to Use:
- Hotels: 🏨
- Packages: 📦
- Itinerary: 🗺️
- Destination: 🌍
- Flights/Transport: ✈️

---

## 📚 Resources & References

### Django Documentation:
- Model relationships: https://docs.djangoproject.com/en/stable/topics/db/models/
- Forms: https://docs.djangoproject.com/en/stable/topics/forms/
- Admin customization: https://docs.djangoproject.com/en/stable/ref/contrib/admin/

### PDF Generation:
- WeasyPrint: https://weasyprint.org/
- ReportLab: https://www.reportlab.com/

---

## ✅ Testing Checklist

Before going live:

- [ ] Create sample hotels with room categories
- [ ] Create sample packages with day-wise breakdown
- [ ] Create test lead and generate itinerary
- [ ] Customize each day (hotel selection, rooms, etc.)
- [ ] Verify pricing calculation is correct
- [ ] Test markup application
- [ ] Generate and verify PDF output
- [ ] Test email sending
- [ ] Verify lead status updates
- [ ] Test all CRUD operations (Create, Read, Update, Delete)
- [ ] Test with multiple user roles (Admin, Agent, Viewer)

---

## 🐛 Known Issues & Notes

1. **Data Migration**: Existing school data will have default values:
   - `customer_name` = "Unknown"
   - `destination` = "To Be Determined"
   - `travel_type` = "Family"
   
   These should be manually updated or cleaned up.

2. **Old Templates**: Many templates still reference school-specific fields. These need to be updated systematically.

3. **Existing Views**: Views.py contains many school-specific logic that needs updating.

---

## 🚀 Deployment Notes

When deploying:

1. **Backup Database**: Before running migrations on production
2. **Run Migrations**: `python manage.py migrate`
3. **Update Static Files**: `python manage.py collectstatic`
4. **Create Sample Data**: Populate hotels and packages
5. **Train Users**: Provide training on new itinerary builder workflow

---

## 📞 Support

For questions or issues during implementation, refer to:
- This documentation
- Django official docs
- Model docstrings (comprehensive help text added)

---

**Created**: October 2025
**Last Updated**: October 2025
**Version**: 1.0
**Status**: Phase 1 Complete (Models & Database) ✅

