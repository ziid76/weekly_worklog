#!/usr/bin/env python3
"""
Test script for profile edit functionality
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/mnt/d/16.Dev/gemini')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.forms import UserProfileForm, UserUpdateForm
from accounts.models import UserProfile
from django.contrib.auth.models import User

def test_forms():
    print("Testing profile edit forms...")
    
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        print(f"User {'created' if created else 'found'}: {user.username}")
        
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        print(f"Profile {'created' if created else 'found'} for user: {user.username}")
        
        # Test forms
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        
        print("✓ Forms created successfully")
        print(f"User form fields: {list(user_form.fields.keys())}")
        print(f"Profile form fields: {list(profile_form.fields.keys())}")
        
        # Test form validation with sample data
        test_data = {
            'last_name_ko': '홍',
            'first_name_ko': '길동',
            'position': '대리',
            'phone': '010-1234-5678'
        }
        
        profile_form = UserProfileForm(test_data, instance=profile)
        if profile_form.is_valid():
            print("✓ Profile form validation passed")
        else:
            print(f"✗ Profile form validation failed: {profile_form.errors}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_forms()
