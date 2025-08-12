# When Filter Implementation for Inquiry Lead List

## Overview
This document describes the implementation of a new "when" filter for the inquiry lead list that allows users to filter inquiries by relative time periods.

## Features Implemented

### 1. Status Filter (Already Existed)
The following status filters are already available and working:
- **DNP** - Do Not Pursue
- **Not interested** - Lead not interested
- **Interested** - Lead interested
- **Follow Up** - Requires follow up
- **Low Budget** - Budget constraints
- **Meeting** - Meeting scheduled
- **Proposal** - Proposal sent

### 2. New "When" Filter
A new time-based filter has been added that allows filtering inquiries by relative time periods:

#### Time Period Options:
- **Today** - Inquiries from today
- **Yesterday** - Inquiries from yesterday
- **This Week** - Inquiries from the current week (Monday to today)
- **Last Week** - Inquiries from the previous week (Monday to Sunday)
- **This Month** - Inquiries from the current month (1st to today)
- **Last Month** - Inquiries from the previous month
- **This Year** - Inquiries from the current year (Jan 1st to today)
- **Last Year** - Inquiries from the previous year
- **Last 7 Days** - Inquiries from the last 7 days including today
- **Last 30 Days** - Inquiries from the last 30 days including today
- **Last 90 Days** - Inquiries from the last 90 days including today

## Technical Implementation

### 1. Backend Changes

#### New Function Added: `Filter_By_When()`
Location: `inquiries/views.py` (lines ~137-200)

This function handles the time-based filtering logic:
- Uses Django's `timezone.now().date()` for accurate date calculations
- Implements various date range calculations for different time periods
- Filters inquiries based on the `inquiry_date` field

#### Updated Function: `Filter_Inquiries()`
Location: `inquiries/views.py` (lines ~200-250)

Added support for the "when" filter:
```python
# Handle "when" filter for relative time periods
when_filter = query_params.get('when_filter')
if when_filter:
    inquiries = Filter_By_When(inquiries, when_filter)
```

#### Updated Function: `Prepare_Context_For_Filter_Leads_Component()`
Location: `inquiries/views.py` (lines ~1400-1450)

Added context for the "when" filter:
```python
selected_when_filter = query_params.get('when_filter')
# ... in return statement
"selected_when_filter": selected_when_filter,
```

### 2. Frontend Changes

#### Template Updates: `Filter_Inquiries_Component.html`
Location: `inquiries/templates/inquiries/Filter_Inquiries_Component.html`

Added a new filter section with:
- Label: "Filter by Time Period"
- Select dropdown with all time period options
- Proper styling consistent with other filters
- Select2 integration for enhanced UX

#### Form Integration
The "when" filter is integrated into the existing filter form and works alongside:
- Status filters
- Date range filters
- Agent/Admin filters
- Other existing filters

## Usage

### 1. Accessing the Filter
1. Navigate to the Inquiry List page
2. Click on "Open Filters" button
3. The "when" filter appears below the status filter

### 2. Using the Filter
1. Select a time period from the dropdown
2. Click "Filter" to apply the filter
3. The inquiry list will show only inquiries matching the selected time period
4. Use "Reset" to clear all filters

### 3. Combining Filters
The "when" filter can be combined with other filters:
- Filter by status (e.g., "Interested") + time period (e.g., "This Month")
- Filter by agent + time period
- Filter by inquiry source + time period

## Benefits

1. **Quick Access**: Users can quickly filter inquiries by common time periods
2. **Improved UX**: No need to manually set date ranges for common scenarios
3. **Consistent Interface**: Follows the same design pattern as other filters
4. **Flexible Filtering**: Can be combined with existing filters
5. **Performance**: Efficient database queries using date ranges

## Technical Notes

- The filter is based on the `inquiry_date` field in the Lead model
- Uses Django's timezone-aware date handling
- Integrates with existing Select2 JavaScript library for enhanced UI
- Maintains consistency with existing filter styling and behavior
- No database schema changes required

## Future Enhancements

Potential improvements that could be added:
1. Custom date range input alongside relative time periods
2. Additional time periods (e.g., "Last Quarter", "This Quarter")
3. Filter by other date fields (e.g., follow-up date, registration date)
4. Saved filter presets for common combinations
5. Export filtered results to Excel/PDF

## Testing

The implementation has been tested for:
- ✅ Syntax validation (`python manage.py check`)
- ✅ Template rendering
- ✅ Filter logic implementation
- ✅ Integration with existing filter system
- ✅ Responsive design compatibility
