#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os  # Importing os module to interact with the operating system
import sys  # Importing sys module for system-specific functions

def main():
    """Run administrative tasks."""
    
    # Setting the default Django settings module for the project.
    # This tells Django which settings file to use.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_inquiry_system.settings')
    
    try:
        # Importing Django's command-line execution function
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # If Django is not installed or not available, raise an error with a helpful message
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Execute the command-line utility with the arguments provided
    execute_from_command_line(sys.argv)

# This ensures that the main() runs only if the script is executed directly (not imported as a module)
if __name__ == '__main__':
    main()