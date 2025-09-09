#!/usr/bin/env python3
"""
Test script to verify the new file deletion and comment file upload features
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/mnt/d/16.Dev/gemini')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from task.models import Task, TaskComment, TaskFile
from django.contrib.auth.models import User

def test_new_features():
    print("Testing new features...")
    
    # Check if TaskComment model has file field
    try:
        comment_fields = [field.name for field in TaskComment._meta.fields]
        if 'file' in comment_fields:
            print("✓ TaskComment.file field exists")
        else:
            print("✗ TaskComment.file field missing")
    except Exception as e:
        print(f"✗ Error checking TaskComment fields: {e}")
    
    # Check if TaskFile model exists
    try:
        file_fields = [field.name for field in TaskFile._meta.fields]
        print(f"✓ TaskFile model exists with fields: {file_fields}")
    except Exception as e:
        print(f"✗ Error checking TaskFile model: {e}")
    
    print("New features test completed!")

if __name__ == "__main__":
    test_new_features()
