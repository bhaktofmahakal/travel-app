#!/usr/bin/env python
"""
Quick script to create migrations for ImageField to CharField conversion
For Render deployment without Pillow
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_booking.settings')
django.setup()

if __name__ == '__main__':
    # Create migrations
    print("Creating migrations for ImageField to CharField conversion...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    print("Migration files created successfully!")
    print("These will be applied automatically during Render deployment.")