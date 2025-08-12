from django.core.management.base import BaseCommand
from django.utils import timezone
from inquiries.models import Lead, CustomUser


class Command(BaseCommand):
    help = 'Transfer existing leads with "Not interested" status to users with "Viewer" role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be transferred without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all leads with "Not interested" status that are not assigned to viewers
        not_interested_leads = Lead.objects.filter(
            status='Not interested'
        ).exclude(
            assigned_agent__role='Viewer'
        )
        
        # Get a viewer user
        viewer_user = CustomUser.objects.filter(role='Viewer').first()
        
        if not viewer_user:
            self.stdout.write(
                self.style.ERROR('No user with "Viewer" role found. Please create a viewer user first.')
            )
            return
        
        if not not_interested_leads.exists():
            self.stdout.write(
                self.style.SUCCESS('No leads with "Not interested" status found that need transfer.')
            )
            return
        
        self.stdout.write(f'Found {not_interested_leads.count()} leads with "Not interested" status to transfer.')
        self.stdout.write(f'Will transfer to viewer: {viewer_user.name} ({viewer_user.email})')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            for lead in not_interested_leads:
                self.stdout.write(
                    f'Would transfer: {lead.student_name} (currently assigned to: {lead.assigned_agent.name if lead.assigned_agent else "None"})'
                )
        else:
            transferred_count = 0
            for lead in not_interested_leads:
                # Update transfer tracking fields
                lead.transferred_from = lead.assigned_agent
                lead.transferred_to = viewer_user
                lead.transfer_date = timezone.now()
                lead.transfer_reason = "Bulk transfer of existing 'Not interested' leads to viewer"
                
                # Assign to viewer
                lead.assigned_agent = viewer_user
                lead.save()
                
                transferred_count += 1
                self.stdout.write(
                    f'Transferred: {lead.student_name} to {viewer_user.name}'
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully transferred {transferred_count} leads to viewer.')
            )
