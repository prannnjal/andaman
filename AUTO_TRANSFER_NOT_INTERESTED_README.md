# Automatic Transfer of "Not Interested" Leads to Viewers

## Overview
This feature automatically transfers leads with "Not interested" status to users with "Viewer" role. This helps in organizing leads and ensuring that uninterested leads are managed by appropriate personnel.

## How It Works

### 1. Automatic Transfer on Status Change
When a lead's status is changed to "Not interested", the system automatically:
- Finds a user with "Viewer" role
- Transfers the lead to that viewer
- Updates transfer tracking fields:
  - `transferred_from`: Previous agent
  - `transferred_to`: Viewer user
  - `transfer_date`: Current timestamp
  - `transfer_reason`: "Automatic transfer due to 'Not interested' status"

### 2. Signal-Based Implementation
The automatic transfer is implemented using Django signals (`pre_save`) in `inquiries/signals.py`:
- Triggers when a lead is saved
- Compares old and new status values
- Only transfers if status changes TO "Not interested"
- Handles both new leads and existing lead updates

### 3. User Notifications
When a lead is automatically transferred, users receive notifications:
- Success message: "Lead updated successfully!"
- Info message: "Lead automatically transferred to viewer: [Viewer Name] due to 'Not interested' status."

## Management Command

### Transfer Existing Leads
To transfer existing leads that already have "Not interested" status:

```bash
# Dry run to see what would be transferred
python manage.py transfer_not_interested_leads --dry-run

# Actually transfer the leads
python manage.py transfer_not_interested_leads
```

### Command Features
- `--dry-run`: Shows what would be transferred without making changes
- Finds all leads with "Not interested" status not assigned to viewers
- Transfers them to the first available viewer user
- Provides detailed output of the transfer process

## Requirements

### Viewer Users
- At least one user with role "Viewer" must exist in the system
- If no viewer users exist, automatic transfer will be skipped
- The system will log a message: "No viewer users found for automatic transfer"

### Lead Model Fields
The following fields are used for transfer tracking:
- `transferred_from`: ForeignKey to CustomUser (Agent who transferred)
- `transferred_to`: ForeignKey to CustomUser (Viewer who received)
- `transfer_date`: DateTimeField (When transfer occurred)
- `transfer_reason`: TextField (Reason for transfer)

## Error Handling

### Signal Errors
- If an error occurs during automatic transfer, it's logged but doesn't prevent the lead from being saved
- Errors are printed to console for debugging

### Missing Viewers
- If no viewer users exist, the transfer is skipped
- A message is logged: "No viewer users found for automatic transfer"

## Testing

### Manual Testing
1. Create a lead with any status other than "Not interested"
2. Change the status to "Not interested"
3. Save the lead
4. Verify that the lead is automatically transferred to a viewer
5. Check that transfer tracking fields are populated

### Automated Testing
Run the management command with `--dry-run` to verify existing leads:
```bash
python manage.py transfer_not_interested_leads --dry-run
```

## Logging
The system logs transfer activities:
- Successful transfers: "Lead [Name] automatically transferred to viewer: [Viewer Name]"
- Missing viewers: "No viewer users found for automatic transfer"
- Errors: "Error in auto_transfer_not_interested_leads: [Error Message]"

## Future Enhancements
- Multiple viewer assignment strategies (round-robin, workload-based)
- Email notifications to viewers when leads are transferred
- Dashboard statistics for transferred leads
- Bulk transfer operations for historical data
