from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.contrib import messages
from .models import Lead, CustomUser
from django.db.models import Count

@receiver(pre_save, sender=Lead)
def auto_assign_agent_on_lead_save(sender, instance, **kwargs):
    """
    Automatically assign an agent to a lead if no agent is assigned
    """
    # Only auto-assign if no agent is currently assigned
    if not instance.assigned_agent:
        instance.auto_assign_agent()
        # Note: We can't use messages here as signals don't have access to request
        # The view will handle showing appropriate messages

@receiver(post_delete, sender=CustomUser)
def redistribute_leads_on_agent_delete(sender, instance, **kwargs):
    """
    When an agent is deleted, reassign their leads to the agent with the least number of assigned leads.
    """
    if instance.role != 'Agent':
        return
    # Get all leads assigned to this agent
    leads = list(Lead.objects.filter(assigned_agent=instance))
    # Get all remaining agents (after deletion)
    remaining_agents = list(CustomUser.objects.filter(role='Agent'))
    if not remaining_agents:
        # No agents left, unassign leads
        for lead in leads:
            lead.assigned_agent = None
        Lead.objects.bulk_update(leads, ['assigned_agent'])
        return
    # Always assign to agent with least leads
    for lead in leads:
        agent_with_least_leads = min(
            remaining_agents,
            key=lambda agent: Lead.objects.filter(assigned_agent=agent).count()
        )
        lead.assigned_agent = agent_with_least_leads
    Lead.objects.bulk_update(leads, ['assigned_agent']) 