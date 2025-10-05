# Quick Start Guide - Travel CRM

## ✅ What's Been Done

### 1. Database Schema (100% Complete)
✅ All travel-specific models created and migrated:
- **Hotel** with room categories and pricing
- **Package** with day-wise breakdown
- **ItineraryBuilder** for custom itineraries
- **Lead** model completely transformed for travel business
- **CompanySettings** updated for travel agency

### 2. Admin Panel (100% Complete)
✅ All models registered and ready to use in Django Admin:
- Go to `http://localhost:8000/admin`
- You can immediately start adding:
  - Hotels
  - Room categories
  - Packages
  - Package days

### 3. Forms (100% Complete)
✅ All forms updated for travel CRM fields

---

## 🚀 How to Start Using It NOW

### Option 1: Use Django Admin (Recommended for Quick Start)

1. **Run the server:**
   ```bash
   python manage.py runserver
   ```

2. **Access admin panel:**
   - Go to: `http://localhost:8000/admin`
   - Login with your admin credentials

3. **Add Hotels:**
   - Click "Hotels" → "Add Hotel"
   - Fill in hotel details
   - Add room categories inline
   - Save

4. **Create Packages:**
   - Click "Packages" → "Add Package"
   - Fill in package details (name, destination, duration)
   - Add package days inline (day-wise breakdown with costs)
   - Save

5. **Create Itineraries:**
   - Click "Itinerary builders" → "Add Itinerary builder"
   - Select a lead
   - Select base package
   - Enter PAX and number of cabs
   - Save
   - Add day-wise customization with hotel selections

### Option 2: Build Custom Frontend (For Full Feature Set)

You need to create views and templates for:

#### Priority 1: Hotel Management
Create these views in `inquiries/views.py`:
```python
def hotel_list(request)  # List all hotels
def hotel_create(request)  # Add new hotel
def hotel_edit(request, hotel_id)  # Edit hotel
```

#### Priority 2: Package Management
```python
def package_list(request)  # List all packages
def package_create(request)  # Create package with days
def package_edit(request, package_id)  # Edit package
```

#### Priority 3: Itinerary Builder Interface
```python
def itinerary_create(request, lead_id)  # Create from lead
def itinerary_customize(request, itinerary_id)  # Customize days
def itinerary_send(request, itinerary_id)  # Send to customer
```

---

## 📦 Sample Data to Test With

### Sample Hotel:
```python
Hotel.objects.create(
    name="Beach Resort Paradise",
    address="123 Beach Road",
    city="Port Blair",
    state="Andaman & Nicobar",
    contact_number="+91-9876543210",
    star_rating=4,
    is_active=True
)
```

### Sample Room Category:
```python
RoomCategory.objects.create(
    hotel=hotel,
    room_type="Deluxe",
    price_per_night=3500,
    extra_mattress_price=500,
    max_occupancy=3
)
```

### Sample Package:
```python
package = Package.objects.create(
    name="Andaman Beach Getaway 5D/4N",
    description="Experience pristine beaches and water sports",
    duration_days=5,
    duration_nights=4,
    destination="Andaman Islands"
)
```

### Sample Package Day:
```python
PackageDay.objects.create(
    package=package,
    day_number=1,
    title="Arrival at Port Blair",
    description="Airport pickup, hotel check-in, city tour",
    cab_price=1500,
    ferry_price=0,
    speedboat_price=0,
    entry_tickets=200
)
```

---

## 🔄 Updated Workflow

### Old (School CRM):
1. Receive inquiry from parent
2. Assign to agent
3. Follow up for admission
4. Send proposal
5. Admission confirmed

### New (Travel CRM):
1. Receive travel inquiry from customer
2. Assign to agent
3. Create custom itinerary from package template
4. Customize day-wise (hotels, transport, activities)
5. Calculate price with markup
6. Send itinerary to customer
7. Booking confirmed
8. Trip completed

---

## 📊 Current State

```
✅ Database Models: COMPLETE
✅ Admin Interface: COMPLETE
✅ Forms: COMPLETE
✅ Migrations: COMPLETE

⚠️ Frontend Views: PENDING
⚠️ Templates: NEEDS UPDATE
⚠️ URLs: NEEDS UPDATE
⚠️ Dashboard UI: NEEDS UPDATE
```

---

## 🎯 To Get Full System Running

### Step 1: Update Existing Views
Many views in `inquiries/views.py` still reference `student_name`, `parent_name`, etc.

**Search and replace in views.py:**
- `student_name` → `customer_name`
- `parent_name` → remove or update logic
- `school` → `destination` or remove
- Add itinerary builder logic

### Step 2: Update Templates
Update all templates that display lead information:
- `lead_list.html` - Update column headers
- `lead_detail.html` - Update field labels, add itinerary button
- `lead_form.html` - Already handled by updated forms
- `dashboard.html` - Update metrics and charts

### Step 3: Add New URLs
Add URL patterns for:
- Hotel management
- Package management  
- Itinerary builder

---

## 💡 Quick Wins

### 1. Update Dashboard Immediately
In `dashboard.html`, change:
```html
<!-- OLD -->
<h3>Total Students: {{ total_students }}</h3>

<!-- NEW -->
<h3>Total Travel Inquiries: {{ total_leads }}</h3>
```

### 2. Update Lead List View
In `lead_list.html`, change column headers:
```html
<!-- OLD -->
<th>Student Name</th>
<th>Parent Name</th>
<th>Class</th>

<!-- NEW -->
<th>Customer Name</th>
<th>Destination</th>
<th>Travel Type</th>
<th>PAX</th>
```

### 3. Add Itinerary Button
In `lead_detail.html`:
```html
<a href="{% url 'itinerary_create' lead.id %}" class="btn btn-primary">
    Create Itinerary
</a>
```

---

## 🐛 Troubleshooting

### Error: "field 'student_name' does not exist"
**Solution**: This field was renamed to `customer_name`. Update your template/view to use `customer_name`.

### Error: "School matching query does not exist"
**Solution**: The School model was replaced with Hotel. Update any references from School to Hotel.

### Error: Forms not showing new fields
**Solution**: Forms have been updated. Make sure you're using the updated forms.py file.

---

## 📞 Quick Reference

### Model Field Mapping (Old → New)

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `student_name` | `customer_name` | Main contact |
| `parent_name` | - | Removed |
| `student_class` | `travel_type` | Enum changed |
| `school` | - | Use Hotel instead |
| `block` | `city` | Customer city |
| `location_panchayat` | `state` | Customer state |
| `proposal_sent_date` | `itinerary_sent_date` | Renamed |

### Status Choices Updated:
```python
OLD: ['DNP', 'Not interested', 'Interested', 'Follow Up', 'Low Budget', 'Meeting', 'Proposal']

NEW: ['New Lead', 'DNP', 'Not interested', 'Interested', 'Follow Up', 
      'Budget Discussion', 'Itinerary Sent', 'Negotiation', 
      'Booking Confirmed', 'Trip Completed']
```

---

## ✨ Features You Can Use RIGHT NOW

Even without custom views, you can use the admin panel to:
1. ✅ Add hotels and room categories
2. ✅ Create package templates with day-wise breakdown
3. ✅ Create travel leads with new fields
4. ✅ Build itineraries for leads
5. ✅ Customize each day with hotel selection
6. ✅ Calculate prices with markup
7. ✅ Track all changes with LeadLogs

---

## 🎉 You're Ready!

The foundation is complete. The system is fully functional through the Django admin panel. Custom frontend views will provide a better user experience, but you can start using the Travel CRM immediately!

**Next Steps:**
1. Add sample hotels via admin
2. Create a test package
3. Create a test lead
4. Build an itinerary for the lead
5. See the auto-calculation working!

Then gradually build the custom frontend as per the TRAVEL_CRM_TRANSFORMATION.md guide.

---

**Happy Traveling! 🌍✈️🏨**

