from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib import messages
from .models import Lead
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