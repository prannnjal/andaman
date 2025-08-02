from django.core.management.base import BaseCommand
from django.db.models import Count
from inquiries.models import Lead, CustomUser


class Command(BaseCommand):
    help = 'Auto-assign unassigned leads to agents with least workload'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be assigned without actually assigning',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all unassigned leads
        unassigned_leads = Lead.objects.filter(assigned_agent__isnull=True)
        
        if not unassigned_leads.exists():
            self.stdout.write(
                self.style.SUCCESS('No unassigned leads found.')
            )
            return
        
        self.stdout.write(f'Found {unassigned_leads.count()} unassigned leads')
        
        # Get all agents with their lead counts
        agents = CustomUser.objects.filter(role='Agent').annotate(
            lead_count=Count('assigned_agent')
        ).order_by('lead_count')
        
        if not agents.exists():
            self.stdout.write(
                self.style.ERROR('No agents found in the system.')
            )
            return
        
        self.stdout.write('\nAgent workload:')
        for agent in agents:
            self.stdout.write(f'  {agent.name}: {agent.lead_count} leads')
        
        if dry_run:
            self.stdout.write('\nDRY RUN - Would assign leads as follows:')
            for lead in unassigned_leads:
                # Get agent with least leads
                agent_with_least = agents.first()
                self.stdout.write(f'  Lead {lead.id} ({lead.student_name}) -> {agent_with_least.name}')
        else:
            assigned_count = 0
            for lead in unassigned_leads:
                # Get agent with least leads
                agent_with_least = agents.first()
                lead.assigned_agent = agent_with_least
                lead.save()
                assigned_count += 1
                
                # Update the agents queryset to reflect the new assignment
                agents = CustomUser.objects.filter(role='Agent').annotate(
                    lead_count=Count('assigned_agent')
                ).order_by('lead_count')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully assigned {assigned_count} leads to agents.')
            ) 