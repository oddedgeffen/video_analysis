#!/usr/bin/env python
"""
Trial Link Management Script

This script provides various commands to manage trial links:
- Create new trial links
- List existing trial links
- Check trial link status
- Deactivate trial links
- View usage statistics
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video_analyze.settings')
django.setup()

from video_analyzer.models import TrialLink
from django.utils import timezone

def create_trial_link(max_videos, days_valid=30):
    """Create a new trial link"""
    link = TrialLink.objects.create(
        max_videos=max_videos,
        expires_at=timezone.now() + timedelta(days=days_valid)
    )
    return link

def list_trial_links():
    """List all trial links with their status"""
    links = TrialLink.objects.all().order_by('-created_at')
    
    if not links:
        print("No trial links found.")
        return
    
    print(f"{'Code':<36} {'Max':<4} {'Used':<4} {'Remaining':<9} {'Expires':<20} {'Status':<8}")
    print("-" * 85)
    
    for link in links:
        remaining = max(0, link.max_videos - link.videos_used)
        expires_str = link.expires_at.strftime('%Y-%m-%d %H:%M') if link.expires_at else 'Never'
        status = "Active" if link.can_use() else "Expired/Used"
        
        print(f"{link.code:<36} {link.max_videos:<4} {link.videos_used:<4} {remaining:<9} {expires_str:<20} {status:<8}")

def check_trial_link(code):
    """Check the status of a specific trial link"""
    try:
        link = TrialLink.objects.get(code=code)
        
        print(f"Trial Link: {link.code}")
        print(f"Max Videos: {link.max_videos}")
        print(f"Videos Used: {link.videos_used}")
        print(f"Videos Remaining: {max(0, link.max_videos - link.videos_used)}")
        print(f"Expires At: {link.expires_at}")
        print(f"Created At: {link.created_at}")
        print(f"Active: {link.is_active}")
        print(f"Can Use: {link.can_use()}")
        print(f"Full URL: http://localhost:3000/trial/{link.code}")
        
    except TrialLink.DoesNotExist:
        print(f"Trial link with code '{code}' not found.")

def deactivate_trial_link(code):
    """Deactivate a trial link"""
    try:
        link = TrialLink.objects.get(code=code)
        link.is_active = False
        link.save()
        print(f"Trial link {code} has been deactivated.")
    except TrialLink.DoesNotExist:
        print(f"Trial link with code '{code}' not found.")

def delete_trial_link(code):
    """Permanently delete a trial link"""
    try:
        link = TrialLink.objects.get(code=code)
        print(f"Trial link details:")
        print(f"  Code: {link.code}")
        print(f"  Max Videos: {link.max_videos}")
        print(f"  Videos Used: {link.videos_used}")
        print(f"  Created: {link.created_at}")
        print(f"  Expires: {link.expires_at}")
        
        # Ask for confirmation
        confirm = input(f"\nAre you sure you want to DELETE trial link {code}? (yes/no): ").lower().strip()
        
        if confirm in ['yes', 'y']:
            link.delete()
            print(f"Trial link {code} has been permanently deleted.")
        else:
            print("Deletion cancelled.")
            
    except TrialLink.DoesNotExist:
        print(f"Trial link with code '{code}' not found.")

def delete_expired_links():
    """Delete all expired trial links"""
    from django.utils import timezone
    
    expired_links = TrialLink.objects.filter(expires_at__lt=timezone.now())
    count = expired_links.count()
    
    if count == 0:
        print("No expired trial links found.")
        return
    
    print(f"Found {count} expired trial link(s):")
    for link in expired_links:
        print(f"  - {link.code} (expired: {link.expires_at})")
    
    confirm = input(f"\nAre you sure you want to DELETE {count} expired trial link(s)? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        deleted_count = expired_links.delete()[0]
        print(f"Successfully deleted {deleted_count} expired trial link(s).")
    else:
        print("Deletion cancelled.")

def delete_unused_links():
    """Delete trial links that have never been used"""
    unused_links = TrialLink.objects.filter(videos_used=0)
    count = unused_links.count()
    
    if count == 0:
        print("No unused trial links found.")
        return
    
    print(f"Found {count} unused trial link(s):")
    for link in unused_links:
        print(f"  - {link.code} (created: {link.created_at})")
    
    confirm = input(f"\nAre you sure you want to DELETE {count} unused trial link(s)? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        deleted_count = unused_links.delete()[0]
        print(f"Successfully deleted {deleted_count} unused trial link(s).")
    else:
        print("Deletion cancelled.")

def delete_all_links():
    """Delete ALL trial links"""
    all_links = TrialLink.objects.all()
    count = all_links.count()
    
    if count == 0:
        print("No trial links found.")
        return
    
    print(f"Found {count} trial link(s):")
    for link in all_links:
        print(f"  - {link.code} (max: {link.max_videos}, used: {link.videos_used}, created: {link.created_at})")
    
    print(f"\nWARNING: This will permanently delete ALL {count} trial link(s)!")
    confirm = input("Are you absolutely sure you want to DELETE ALL trial links? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        deleted_count = all_links.delete()[0]
        print(f"Successfully deleted {deleted_count} trial link(s).")
    else:
        print("Deletion cancelled.")

def usage_stats():
    """Show usage statistics"""
    total_links = TrialLink.objects.count()
    active_links = TrialLink.objects.filter(is_active=True).count()
    expired_links = total_links - active_links
    
    total_videos_allowed = sum(link.max_videos for link in TrialLink.objects.all())
    total_videos_used = sum(link.videos_used for link in TrialLink.objects.all())
    
    print("Trial Link Statistics:")
    print(f"Total Links: {total_links}")
    print(f"Active Links: {active_links}")
    print(f"Expired/Deactivated Links: {expired_links}")
    print(f"Total Videos Allowed: {total_videos_allowed}")
    print(f"Total Videos Used: {total_videos_used}")
    print(f"Total Videos Remaining: {total_videos_allowed - total_videos_used}")

def show_help():
    """Show help message"""
    print("Trial Link Management Script")
    print("Usage: python manage_trial_links.py <command> [arguments]")
    print()
    print("Commands:")
    print("  create <max_videos> [days_valid]  - Create a new trial link")
    print("  list                              - List all trial links")
    print("  check <code>                      - Check status of a specific trial link")
    print("  deactivate <code>                 - Deactivate a trial link")
    print("  delete <code>                     - Permanently delete a trial link")
    print("  delete-expired                    - Delete all expired trial links")
    print("  delete-unused                     - Delete all unused trial links")
    print("  delete-all                        - Delete ALL trial links")
    print("  stats                             - Show usage statistics")
    print("  help                              - Show this help message")
    print()
    print("Examples:")
    print("  python manage_trial_links.py create 10")
    print("  python manage_trial_links.py create 5 7")
    print("  python manage_trial_links.py list")
    print("  python manage_trial_links.py check abc123-def456-ghi789")
    print("  python manage_trial_links.py deactivate abc123-def456-ghi789")
    print("  python manage_trial_links.py delete abc123-def456-ghi789")
    print("  python manage_trial_links.py delete-expired")
    print("  python manage_trial_links.py delete-unused")
    print("  python manage_trial_links.py delete-all")
    print("  python manage_trial_links.py stats")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Error: Please provide the number of videos")
            print("Usage: python manage_trial_links.py create <max_videos> [days_valid]")
            sys.exit(1)
        
        try:
            max_videos = int(sys.argv[2])
            days_valid = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            
            if max_videos <= 0:
                print("Error: Number of videos must be positive")
                sys.exit(1)
            
            link = create_trial_link(max_videos, days_valid)
            print(f"Created trial link:")
            print(f"Code: {link.code}")
            print(f"Max Videos: {link.max_videos}")
            print(f"Expires: {link.expires_at}")
            print(f"URL: http://localhost:3000/trial/{link.code}")
            
        except ValueError:
            print("Error: Please provide valid numbers")
            sys.exit(1)
    
    elif command == "list":
        list_trial_links()
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Error: Please provide the trial link code")
            print("Usage: python manage_trial_links.py check <code>")
            sys.exit(1)
        
        code = sys.argv[2]
        check_trial_link(code)
    
    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("Error: Please provide the trial link code")
            print("Usage: python manage_trial_links.py deactivate <code>")
            sys.exit(1)
        
        code = sys.argv[2]
        deactivate_trial_link(code)
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Error: Please provide the trial link code")
            print("Usage: python manage_trial_links.py delete <code>")
            sys.exit(1)
        
        code = sys.argv[2]
        delete_trial_link(code)
    
    elif command == "delete-expired":
        delete_expired_links()
    
    elif command == "delete-unused":
        delete_unused_links()
    
    elif command == "delete-all":
        delete_all_links()
    
    elif command == "stats":
        usage_stats()
    
    elif command == "help":
        show_help()
    
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)
