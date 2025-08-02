# Auto-Assignment Feature for Lead Management

## Overview
This feature automatically assigns leads to agents based on workload distribution. When a new lead is created or updated without an assigned agent, the system automatically assigns it to the agent with the least number of leads.

## How It Works

### 1. Automatic Assignment Logic
- The system counts the number of leads assigned to each agent
- When a new lead is created or updated without an agent, it's automatically assigned to the agent with the lowest lead count
- This ensures even distribution of workload among agents

### 2. Implementation Points

#### Model Level (Lead Model)
- `Lead.get_agent_with_least_leads()`: Class method that returns the agent with the least number of leads
- `Lead.auto_assign_agent()`: Instance method that assigns the current lead to the agent with least workload

#### View Level
- **`add_inquiry`**: Automatically assigns agent when creating new leads (no assigned_agent field in form)
- **`manage_lead_status`**: Uses EditLeadForm with assigned_agent field for manual assignment when editing
- **`auto_assign_unassigned_leads_view`**: Bulk assignment for existing unassigned leads

#### Signal Level
- **`auto_assign_agent_on_lead_save`**: Django signal that triggers auto-assignment on lead save

### 3. User Interface

#### Form Changes
- **Add New Inquiry**: No longer shows "Assigned Agent" field - agents are assigned automatically
- **Edit Existing Lead**: Still shows "Assigned Agent" field for manual assignment/override
- **Auto-Assign Button**: Available in the inquiry list for admins
- **Bulk Assignment**: Can assign all unassigned leads at once
- **Manual Override**: Admins can still manually assign leads to specific agents when editing

#### User Feedback
- Success messages when auto-assignment occurs
- Warning messages when no agents are available
- Information messages showing which agent was assigned

### 4. Management Commands

#### `auto_assign_leads`
```bash
# Test the assignment without making changes
python manage.py auto_assign_leads --dry-run

# Actually assign unassigned leads
python manage.py auto_assign_leads
```

### 5. Configuration

#### Requirements
- Agents must have role='Agent' in the CustomUser model
- Leads must have assigned_agent field as null/blank for auto-assignment to trigger

#### Signals Registration
- Signals are automatically registered in `inquiries/apps.py`
- No additional configuration required

## Usage Examples

### Creating a New Lead
```python
# When creating a new lead without specifying an agent
lead = Lead.objects.create(
    student_name="John Doe",
    parent_name="Jane Doe",
    # ... other fields
    # assigned_agent is not specified
)
# The lead will be automatically assigned to the agent with least leads
```

### Bulk Assignment
```python
# Assign all unassigned leads
unassigned_leads = Lead.objects.filter(assigned_agent__isnull=True)
for lead in unassigned_leads:
    lead.auto_assign_agent()
    lead.save()
```

### Manual Override
```python
# Manually assign to specific agent (overrides auto-assignment)
lead.assigned_agent = specific_agent
lead.save()
```

## Benefits

1. **Workload Balance**: Ensures even distribution of leads among agents
2. **Automation**: Reduces manual work for administrators
3. **Efficiency**: Leads are assigned immediately upon creation
4. **Flexibility**: Admins can still manually override assignments
5. **Transparency**: Clear feedback on assignment decisions

## Troubleshooting

### Common Issues

1. **No agents available**: Ensure there are users with role='Agent'
2. **Assignment not working**: Check if signals are properly registered
3. **Performance issues**: For large datasets, consider using bulk operations

### Debugging

1. Use the management command with `--dry-run` to see what would be assigned
2. Check agent lead counts using Django shell:
   ```python
   from inquiries.models import CustomUser
   from django.db.models import Count
   
   agents = CustomUser.objects.filter(role='Agent').annotate(
       lead_count=Count('assigned_agent')
   ).order_by('lead_count')
   
   for agent in agents:
       print(f"{agent.name}: {agent.lead_count} leads")
   ```

## Future Enhancements

1. **Geographic Assignment**: Assign based on agent location and lead location
2. **Performance-based Assignment**: Consider agent conversion rates
3. **Time-based Assignment**: Consider agent availability and working hours
4. **Priority-based Assignment**: Handle high-priority leads differently

## User Management

### Agent Creation with Custom Passwords

Admins can now create agents with custom passwords instead of auto-generated ones:

1. **Admin Access**: Only admins can create new users/agents
2. **Custom Password**: Admin sets the password during user creation
3. **Password Validation**: 
   - Minimum 8 characters
   - Password confirmation required
   - Passwords must match
4. **Email Notification**: Agent receives welcome email with login credentials
5. **Login Options**: Agent can login using either email or phone number

### Agent Password Management

Admins can update agent passwords through the user update functionality:

1. **Optional Password Changes**: Admins can change agent passwords when updating user details
2. **Password Validation**: Same validation rules apply (8+ characters, confirmation required)
3. **Immediate Effect**: Password changes take effect immediately
4. **Security**: Only admins can change passwords
5. **User Experience**: Agents can login with new password right away

### User Creation Process

1. Admin navigates to "Add User" page
2. Fills in user details (name, email, phone, role, expiration)
3. Sets custom password and confirms it
4. System validates password requirements
5. User is created with the custom password
6. Welcome email is sent to the new user
7. User can immediately login with the provided credentials

### User Update Process

1. Admin navigates to user list and clicks "Edit" on a user
2. Admin can update user details (name, email, phone, role, expiration)
3. **Optional Password Change**: Admin can optionally set a new password
   - Leave password fields blank to keep current password
   - Fill both password fields to change the password
4. System validates password requirements (if provided)
5. User is updated with new details and/or password
6. Success message confirms the update
7. User can immediately login with the new password (if changed)

## Agent Lead Access Control

### Lead Visibility Rules

**Agents can only see leads assigned to them:**
- **Inquiry List**: Only shows leads assigned to the logged-in agent
- **Dashboard**: Statistics based only on agent's assigned leads
- **Detailed Stats**: Performance metrics for agent's leads only
- **Follow-up Management**: Only shows follow-ups for assigned leads
- **Export Function**: Only exports agent's assigned leads
- **Filter Options**: Filter dropdowns only show data from assigned leads

**Admins can see all leads:**
- Full access to all leads in the system
- Can view, edit, and manage all leads
- Can assign leads to agents
- Can see system-wide statistics

### Implementation Details

The filtering is implemented in multiple views:
- `Filter_Inquiries()`: Core filtering function used by most views
- `dashboard()`: Dashboard statistics filtering
- `detailed_stats()`: Detailed statistics filtering
- `export_inquiries_excel()`: Export filtering
- `Prepare_Context_For_Filter_Leads_Component()`: Filter dropdown data

### Security Benefits

1. **Data Isolation**: Agents cannot access leads assigned to other agents
2. **Privacy Protection**: Sensitive lead information is restricted
3. **Performance**: Reduced data load for agents
4. **Compliance**: Better control over data access

## Phone Call Functionality

### Agent Call Features

Agents can now make phone calls directly from the leads list:

1. **Clickable Phone Numbers**: Phone numbers in the leads list are clickable
2. **Visual Indicators**: Green phone icons next to phone numbers
3. **Hover Effects**: Visual feedback when hovering over phone numbers
4. **Tooltips**: Clear indication that numbers are clickable
5. **Call Logging**: All calls are logged for tracking purposes
6. **User Notifications**: Success notifications when calls are initiated

### How It Works

**For Agents:**
1. Navigate to the leads list
2. Find the lead you want to call
3. Click on the phone number (or the phone icon)
4. Your device's phone app will open with the number pre-filled
5. A notification confirms the call was initiated
6. The call is automatically logged in the system

**Technical Implementation:**
- Uses HTML5 `tel:` protocol for phone links
- Font Awesome icons for visual appeal
- JavaScript for call logging and notifications
- Backend API endpoint for call tracking
- Responsive design for mobile compatibility

### Call Logging

The system automatically logs:
- **Agent Name**: Who made the call
- **Student Name**: Who was called
- **Phone Number**: The number dialed
- **Timestamp**: When the call was initiated
- **Status**: Call attempt logged

### Benefits

1. **Convenience**: One-click calling from the leads list
2. **Efficiency**: No need to manually dial numbers
3. **Tracking**: All call attempts are logged
4. **User Experience**: Intuitive and responsive interface
5. **Mobile Friendly**: Works on both desktop and mobile devices

## Lead Transfer Functionality

### Agent Lead Transfer Features

Agents can now transfer leads to other agents with full tracking and history:

1. **Transfer Button**: Available in leads list for agents and admins
2. **Transfer Form**: Professional form with agent selection and reason
3. **Transfer History**: Complete tracking of all transfers
4. **Permission Control**: Agents can only transfer their assigned leads
5. **Audit Trail**: All transfers are logged and tracked
6. **Transfer Display**: Transfer history visible in leads table

### How It Works

**For Agents:**
1. Navigate to leads list
2. Find a lead assigned to you
3. Click the "Transfer" button
4. Select target agent from dropdown
5. Provide transfer reason
6. Confirm transfer
7. Lead is transferred with full history tracking

**For Admins:**
1. Can transfer any lead to any agent
2. Full access to transfer functionality
3. Can view all transfer history
4. Can override agent permissions

### Transfer Tracking

The system automatically tracks:
- **Transferred From**: Original agent
- **Transferred To**: New agent
- **Transfer Date**: When transfer occurred
- **Transfer Reason**: Why the transfer was made
- **Transfer History**: Complete audit trail

### Database Schema

**New Fields Added to Lead Model:**
- `transferred_from`: Agent who transferred the lead
- `transferred_to`: Agent who received the lead
- `transfer_date`: When the transfer occurred
- `transfer_reason`: Reason for the transfer

### User Interface

**Transfer Form Features:**
- Professional, clean design
- Agent selection dropdown (excludes current agent)
- Required reason field
- Confirmation dialog
- Success/error messages
- Transfer history display

**Leads Table Enhancements:**
- New "Transfer History" column
- Shows transfer details (from, to, date, reason)
- Transfer button for eligible leads
- Visual indicators for transferred leads

### Security & Permissions

1. **Agent Restrictions**: Agents can only transfer their assigned leads
2. **Admin Override**: Admins can transfer any lead
3. **Validation**: Form validation for required fields
4. **Audit Trail**: All transfers logged in LeadLogs
5. **Confirmation**: User confirmation before transfer

### Benefits

1. **Workload Management**: Distribute leads efficiently
2. **Specialization**: Transfer leads to specialized agents
3. **Tracking**: Complete audit trail of all transfers
4. **Transparency**: Clear visibility of transfer history
5. **Control**: Proper permission management
6. **Efficiency**: Streamlined transfer process

## Agent Lead Update Restrictions

### Field Access Control

Agents have restricted access when updating lead status:

**Agents CAN modify:**
- Student Name, Parent Name, Mobile Number, Email, Address
- Block, Location/Panchayat, Student Class
- Status, Remarks
- All date fields (Inquiry Date, Follow-up Date, Registration Date, etc.)

**Agents CAN see but CANNOT modify:**
- **Inquiry Source**: Can see but cannot change how the lead was acquired
- **Admin Assigned**: Can see but cannot change admin assignment
- **Assigned Agent**: Can see but cannot change agent assignment

### Implementation Details

**Form-Based Restrictions:**
- **AgentUpdateLeadForm**: Restricted form for agents with read-only fields
- **EditLeadForm**: Full form for admins
- **Dynamic Form Selection**: View chooses form based on user role
- **Read-only Fields**: Visual indicators and disabled inputs for restricted fields

**Permission Checks:**
- Agents can only edit leads assigned to them
- Admins can edit any lead
- Proper error messages for unauthorized access

### User Experience

**For Agents:**
1. Navigate to leads list
2. Click "Update" on assigned lead
3. See form with all fields visible
4. **Read-only fields**: inquiry source, admin assignment, agent assignment (grayed out)
5. Can update all other lead information
6. Visual indicators show which fields cannot be modified

**For Admins:**
1. Full access to all lead fields
2. Can modify inquiry source, admin assignment, and agent assignment
3. No restrictions on lead editing

### Security Benefits

1. **Data Integrity**: Prevents unauthorized changes to critical fields
2. **Role Separation**: Clear distinction between agent and admin capabilities
3. **Audit Trail**: All changes logged regardless of restrictions
4. **Permission Control**: Proper access control based on user role
5. **Form Validation**: Server-side validation ensures restrictions are enforced
6. **Transparency**: Agents can see all data but cannot modify restricted fields
7. **Visual Feedback**: Clear indicators show which fields are read-only 