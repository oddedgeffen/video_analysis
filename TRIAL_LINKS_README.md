# Trial Link Management Guide

This guide explains how to create and manage trial links for the Video Analysis SaaS application.

## Overview

Trial links allow users to access the video analysis service with limited usage. Each trial link has:
- A unique code (UUID)
- Maximum number of videos allowed
- Expiration date (default: 30 days)
- Usage tracking
- Active/inactive status

## Methods to Create Trial Links

### 1. Simple Script (`create_trial_link.py`)

**Usage:**
```bash
python create_trial_link.py <number_of_videos>
```

**Examples:**
```bash
# Create a trial link with 5 videos
python create_trial_link.py 5

# Create a trial link with 10 videos
python create_trial_link.py 10
```

**Output:**
```
http://localhost:3000/trial/3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
```

### 2. Advanced Management Script (`manage_trial_links.py`)

**Usage:**
```bash
python manage_trial_links.py <command> [arguments]
```

**Commands:**

#### Create Trial Links
```bash
# Create with default 30-day expiration
python manage_trial_links.py create 10

# Create with custom expiration (7 days)
python manage_trial_links.py create 5 7
```

#### List All Trial Links
```bash
python manage_trial_links.py list
```

**Output:**
```
Code                                 Max  Used Remaining Expires              Status
-------------------------------------------------------------------------------------
3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0 5    0    5         2025-11-08 20:14     Active
8f0ca7fe-b63e-4ac6-82fd-30f9f88afb49 5    0    5         2025-11-08 20:05     Active
```

#### Check Specific Trial Link
```bash
python manage_trial_links.py check 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
```

**Output:**
```
Trial Link: 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
Max Videos: 5
Videos Used: 0
Videos Remaining: 5
Expires At: 2025-11-08 20:14:41.099849+00:00
Created At: 2025-10-09 20:14:41.099849+00:00
Active: True
Can Use: True
Full URL: http://localhost:3000/trial/3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
```

#### Deactivate Trial Link
```bash
python manage_trial_links.py deactivate 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
```

#### Delete Trial Link
```bash
python manage_trial_links.py delete 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
```

**Output:**
```
Trial link details:
  Code: 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0
  Max Videos: 5
  Videos Used: 0
  Created: 2025-10-09 20:14:41.099849+00:00
  Expires: 2025-11-08 20:14:41.099849+00:00

Are you sure you want to DELETE trial link 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0? (yes/no): yes
Trial link 3bcfac13-9ad6-4a7a-8e7c-fc42a6f24bc0 has been permanently deleted.
```

#### Delete Expired Trial Links
```bash
python manage_trial_links.py delete-expired
```

**Output:**
```
Found 3 expired trial link(s):
  - abc123-def456-ghi789 (expired: 2025-10-01 12:00:00+00:00)
  - def456-ghi789-jkl012 (expired: 2025-10-02 15:30:00+00:00)
  - ghi789-jkl012-mno345 (expired: 2025-10-03 09:15:00+00:00)

Are you sure you want to DELETE 3 expired trial link(s)? (yes/no): yes
Successfully deleted 3 expired trial link(s).
```

#### Delete Unused Trial Links
```bash
python manage_trial_links.py delete-unused
```

**Output:**
```
Found 5 unused trial link(s):
  - abc123-def456-ghi789 (created: 2025-10-01 12:00:00+00:00)
  - def456-ghi789-jkl012 (created: 2025-10-02 15:30:00+00:00)
  - ghi789-jkl012-mno345 (created: 2025-10-03 09:15:00+00:00)
  - jkl012-mno345-pqr678 (created: 2025-10-04 18:45:00+00:00)
  - mno345-pqr678-stu901 (created: 2025-10-05 11:20:00+00:00)

Are you sure you want to DELETE 5 unused trial link(s)? (yes/no): yes
Successfully deleted 5 unused trial link(s).
```

#### View Usage Statistics
```bash
python manage_trial_links.py stats
```

**Output:**
```
Trial Link Statistics:
Total Links: 18
Active Links: 18
Expired/Deactivated Links: 0
Total Videos Allowed: 74
Total Videos Used: 11
Total Videos Remaining: 63
```

#### Show Help
```bash
python manage_trial_links.py help
```

### 3. Django Admin Interface

Access the Django admin interface at `http://localhost:8000/admin/` (after running migrations):

1. **Navigate to Trial Links section**
2. **Click "Add Trial Link"**
3. **Fill in the form:**
   - Max Videos: Number of videos allowed
   - Expires At: Expiration date/time
   - Is Active: Check to activate the link
4. **Save**

**Admin Features:**
- View all trial links in a table
- Filter by active status, creation date, expiration date
- Search by trial link code
- Edit trial link properties
- View usage statistics
- Deactivate/activate trial links
- Delete individual trial links
- Bulk actions: delete selected, deactivate selected, activate selected

### 4. Programmatic Creation (Python/Django Shell)

```python
# In Django shell: python manage.py shell
from video_analyzer.models import TrialLink
from django.utils import timezone
from datetime import timedelta

# Create a trial link
link = TrialLink.objects.create(
    max_videos=10,
    expires_at=timezone.now() + timedelta(days=30)
)

print(f"Created trial link: {link.code}")
print(f"URL: http://localhost:3000/trial/{link.code}")
```

## Trial Link Model Fields

- **`code`**: Unique UUID identifier (auto-generated)
- **`max_videos`**: Maximum number of videos allowed
- **`videos_used`**: Number of videos already used
- **`expires_at`**: Expiration date and time
- **`created_at`**: Creation timestamp (auto-generated)
- **`is_active`**: Whether the link is active

## Trial Link Methods

- **`can_use()`**: Returns True if the link can still be used
- **`increment_usage()`**: Increments the videos_used counter

## API Endpoints

### Check Trial Link Status
```
GET /api/trial/check/<code>/
```

**Response:**
```json
{
    "valid": true,
    "videos_remaining": 5,
    "max_videos": 10,
    "expires_at": "2025-11-08T20:14:41.099849Z"
}
```

## Frontend Integration

Trial links are used in the React frontend:

1. **Landing Page**: `/trial/<code>` - Validates trial and shows remaining usage
2. **Recording Page**: `/trial/<code>/record` - Allows video recording if trial is valid
3. **Admin Bypass**: Admins can bypass trial validation entirely

## Best Practices

1. **Set Reasonable Limits**: 5-10 videos for most trials
2. **Monitor Usage**: Regularly check statistics to understand usage patterns
3. **Clean Up**: Deactivate expired or unused trial links
4. **Security**: Trial codes are UUIDs, making them hard to guess
5. **Expiration**: Set appropriate expiration dates (7-30 days)

## Troubleshooting

### Common Issues

1. **"Trial link not found"**: Check if the code is correct and the link exists
2. **"Trial expired"**: Check the expiration date and create a new link if needed
3. **"No videos remaining"**: The trial has reached its usage limit
4. **Database errors**: Ensure Django migrations are up to date

### Migration Issues

If you encounter migration errors:
```bash
# Create migration for TrialLink model
python manage.py makemigrations video_analyzer

# Apply migrations
python manage.py migrate
```

## Examples

### Create Trial Links for Different Scenarios

```bash
# Quick 5-video trial (7 days)
python manage_trial_links.py create 5 7

# Extended 20-video trial (30 days)
python manage_trial_links.py create 20 30

# Single video test (1 day)
python manage_trial_links.py create 1 1
```

### Monitor Trial Usage

```bash
# Check all trial links
python manage_trial_links.py list

# Get overall statistics
python manage_trial_links.py stats

# Check specific trial
python manage_trial_links.py check <code>
```

### Delete and Clean Up Trials

```bash
# Delete a specific trial link
python manage_trial_links.py delete <code>

# Delete all expired trial links
python manage_trial_links.py delete-expired

# Delete all unused trial links
python manage_trial_links.py delete-unused

# Deactivate a specific trial (keeps the record)
python manage_trial_links.py deactivate <code>
```

This comprehensive system provides multiple ways to create and manage trial links, from simple command-line tools to a full Django admin interface.
