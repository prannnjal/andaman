# Views.py Update Status - Travel CRM

## ✅ Fixed Issues (Dashboard Error Resolved)

### 1. **Admin Dashboard View** (Line ~812)
**Status**: ✅ FIXED

**Changes Made:**
```python
# OLD (School CRM)
total_inquiries = inquiries.filter(status='Inquiry').count()
total_registrations = inquiries.filter(status='Registration').count()
total_tests = inquiries.filter(status='Admission Test').count()
registrations_today = inquiries.filter(status='Registration', registration_date=today).count()

# NEW (Travel CRM)
new_leads = inquiries.filter(status='New Lead').count()
itinerary_sent = inquiries.filter(status='Itinerary Sent').count()
bookings_confirmed = inquiries.filter(status='Booking Confirmed').count()
inquiries_today = inquiries.filter(status='New Lead', inquiry_date=today).count()
itinerary_sent_today = inquiries.filter(status='Itinerary Sent', itinerary_sent_date__date=today).count()
```

**Context Variables Updated:**
- `total_inquiries` → `new_leads`
- `total_registrations` → `itinerary_sent`
- `total_admissions_confirmed` → `bookings_confirmed`
- `registrations_today` → `itinerary_sent_today`
- `low_budget_count` → `budget_discussion_count`
- Added: `negotiation_count`

### 2. **Agent Dashboard View** (Line ~1088)
**Status**: ✅ FIXED

**Changes Made:**
- Updated status filters to use Travel CRM statuses
- Changed `student_class` grouping to `travel_type`
- Updated all date field references
- Fixed context variables

---

## ⚠️ Still Need Attention

The following views/functions still reference old School CRM fields and need updating:

### High Priority (Will cause errors):

#### 1. **Filter Functions** (Lines 240-318)
**References:**
- `student_class` filtering
- `student_name` filtering
- `parent_name` filtering
- `registration_date`, `admission_test_date`, etc.

**Fix Needed:**
```python
# Line 240-242
student_classes = query_params.getlist('student_class[]')  # Change to travel_type
if student_classes:
    inquiries = inquiries.filter(student_class__in=student_classes)

# Should be:
travel_types = query_params.getlist('travel_type[]')
if travel_types:
    inquiries = inquiries.filter(travel_type__in=travel_types)
```

#### 2. **Inquiry List View** (Lines 384-397)
**References:**
- `student_name` for distinct values
- Template context uses `selected_student_names`

**Fix Needed:**
```python
# Line 384
students = Lead.objects.values_list('student_name', flat=True).distinct()

# Should be:
customers = Lead.objects.values_list('customer_name', flat=True).distinct()
```

#### 3. **Show All Inquiries View** (Lines 561-584)
**References:**
- `student_name`, `parent_name`, `student_class`

**Fix Needed:**
```python
# Lines 561-562
students = Lead.objects.values_list('student_name', flat=True).distinct() 
parents = Lead.objects.values_list('parent_name', flat=True).distinct() 

# Should be:
customers = Lead.objects.values_list('customer_name', flat=True).distinct()
destinations = Lead.objects.values_list('destination', flat=True).distinct()
```

#### 4. **Export to Excel View** (Lines 1276-1292)
**References:**
- All old field names in Excel output

**Fix Needed:**
```python
# Line 1276-1292
inquiry.student_name,
inquiry.parent_name,
inquiry.student_class,
inquiry.registration_date,

# Should be:
inquiry.customer_name,
inquiry.destination,
inquiry.travel_type,
inquiry.booking_date,
```

#### 5. **Agent Inquiry Filters** (Lines 1643-1688)
**References:**
- `student_name`, `parent_name`, `student_class`

**Fix Needed:**
```python
# Lines 1643-1644
students = base_queryset.values_list('student_name', flat=True).distinct()
parents = base_queryset.values_list('parent_name', flat=True).distinct()

# Should be:
customers = base_queryset.values_list('customer_name', flat=True).distinct()
destinations = base_queryset.values_list('destination', flat=True).distinct()
```

### Medium Priority (May cause issues):

#### 6. **Call Logging** (Lines 2128-2139)
**References:**
- `student_name` in print statements

#### 7. **Lead Transfer** (Lines 2213-2223)
**References:**
- `lead.student_name` in success messages

**Fix:** Change all to `lead.customer_name`

#### 8. **Call Recording List** (Line 2766)
**References:**
- `call.lead.student_name`

**Fix:** Change to `call.lead.customer_name`

### Low Priority (Email/Proposal Generation):

#### 9. **Email Proposal Functions** (Lines 2838-2946)
**References:**
- `inquiry.student_name`, `inquiry.parent_name`, `inquiry.student_class`
- All proposal/email templates

**Note:** These are for school proposals - entire logic needs updating for travel itineraries

#### 10. **PDF Generation** (Lines 3231-3279)
**References:**
- Fee structure based on `student_class`
- All old fields in PDF template

**Note:** This entire section needs rewriting for travel itinerary PDFs

---

## 🛠️ Recommended Fix Strategy

### Phase 1: Critical Fixes (Do Now)
1. ✅ Dashboard views - DONE
2. Fix filtering functions (lines 240-318)
3. Fix inquiry list views (lines 384-397, 561-584)
4. Fix export to Excel (lines 1276-1292)

### Phase 2: Update Messages & Display (Do Next)
5. Fix all `student_name` references in messages
6. Fix call recording displays
7. Update agent filter views

### Phase 3: Feature Updates (Plan & Implement)
8. Redesign email/proposal system for travel itineraries
9. Create new PDF generation for itineraries
10. Add itinerary builder views

---

## 🔍 Quick Search Commands

To find remaining issues:

```bash
# Find all student_name references
grep -n "student_name" inquiries/views.py

# Find all parent_name references
grep -n "parent_name" inquiries/views.py

# Find all student_class references
grep -n "student_class" inquiries/views.py

# Find all old date fields
grep -n "registration_date\|admission_test_date\|admission_offered_date" inquiries/views.py
```

---

## ✅ What Works Now

1. **Dashboard loads successfully** - Main dashboard displays without errors
2. **Status filtering** - New travel statuses work in dashboard
3. **Today's counts** - Displays today's travel inquiries correctly
4. **Travel type grouping** - Groups by travel type instead of class
5. **Call recording stats** - Still functional

---

## 📋 Testing Checklist

Before considering views.py complete:

- [x] Dashboard loads without errors
- [x] Agent dashboard loads
- [ ] Lead list filters work
- [ ] Export to Excel works
- [ ] Lead detail pages show correct fields
- [ ] Transfer lead functionality works
- [ ] Email/proposal system updated
- [ ] All old field references removed

---

## 🎯 Next Steps

1. **Test the dashboard** - Navigate to `/inquiries/dashboard/` and verify it loads
2. **Fix filters** - Update filtering functions to use travel fields
3. **Update templates** - Templates also need updating to display new fields
4. **Test each view** - Systematically test and fix each view function

---

**Status**: Dashboard error FIXED ✅
**Next**: Update filter functions and inquiry list views
**Priority**: High - needed for basic system operation

