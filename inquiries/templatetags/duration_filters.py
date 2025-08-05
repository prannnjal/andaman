from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def duration_format(duration):
    """
    Format a duration (timedelta) object into a readable string
    """
    if duration is None:
        return "N/A"
    
    if isinstance(duration, timedelta):
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"
    
    return str(duration) 