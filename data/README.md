# Data Directory

This directory contains the documents and files used for the RAG (Retrieval-Augmented Generation) system.

# Data Format Documentation

This document describes the structure and format of data files used by the Analytics UI Generator.

## User Activity Data Structure

### JSON Data Format (`activity_data.json`)

The main user activity data is stored in a structured JSON format containing analytics information for different applications:

```json
{
  "whatsapp": {
    "daily_usage": [
      {
        "date": "2025-10-14",
        "active_time_minutes": 85,
        "messages_sent": 124,
        "messages_received": 156,
        "media_shared": 12,
        "most_active_chat": "Family Group",
        "peak_hours": ["12:00", "20:00"],
        "chat_categories": {
          "group_chats": 65,
          "personal_chats": 35
        }
      }
    ],
    "weekly_summary": {
      "total_active_time": 595,
      "average_daily_time": 85,
      "total_messages_sent": 868,
      "total_messages_received": 1092,
      "most_active_day": "Saturday"
    }
  },
  "youtube": {
    "daily_usage": [
      {
        "date": "2025-10-14",
        "watch_time_minutes": 120,
        "videos_watched": 8,
        "most_watched_category": "Technology",
        "peak_usage_hour": "20:00",
        "categories": {
          "Technology": 45,
          "Education": 35,
          "Entertainment": 40
        }
      }
    ],
    "weekly_summary": {
      "total_watch_time": 840,
      "average_daily_time": 120,
      "favorite_category": "Technology",
      "total_videos": 42
    }
  },
  "battery": {
    "daily_usage": [
      {
        "date": "2025-10-14",
        "battery_level_start": 100,
        "battery_level_end": 25,
        "charging_sessions": 1,
        "screen_on_time_minutes": 420,
        "top_consuming_apps": {
          "YouTube": 25,
          "WhatsApp": 15,
          "Camera": 12
        }
      }
    ],
    "performance_metrics": {
      "average_battery_life": 18,
      "charging_efficiency": 95,
      "battery_health": "Good"
    }
  }
}
```

### Vector Database Text Format (`user_data_for_vectordb.txt`)

This file contains formatted text data optimized for vector search and semantic retrieval:

```text
WhatsApp Usage Analytics:
Daily activity shows user sent 124 messages and received 156 messages on 2025-10-14.
Active time was 85 minutes with peak hours at 12:00 and 20:00.
Most active chat was Family Group.
Chat categories breakdown: 65% group chats, 35% personal chats.
Weekly summary shows total active time of 595 minutes with average daily time of 85 minutes.
Total messages sent this week: 868, received: 1092.

YouTube Usage Analytics:
Daily viewing on 2025-10-14 included 120 minutes watch time across 8 videos.
Most watched category was Technology with 45 minutes.
Peak usage hour was 20:00.
Category breakdown: Technology 45 minutes, Education 35 minutes, Entertainment 40 minutes.
Weekly summary shows total watch time of 840 minutes with average daily time of 120 minutes.
Favorite category this week: Technology.
Total videos watched: 42.

Battery Performance Analytics:
Daily battery usage on 2025-10-14 started at 100% and ended at 25%.
One charging session occurred during the day.
Screen on time was 420 minutes (7 hours).
Top consuming apps: YouTube 25%, WhatsApp 15%, Camera 12%.
Performance metrics show average battery life of 18 hours.
Charging efficiency is 95% with battery health rated as Good.
```

## Data Schema Definitions

### WhatsApp Data Schema

```typescript
interface WhatsAppDailyUsage {
  date: string;                    // ISO date format (YYYY-MM-DD)
  active_time_minutes: number;     // Total active time in minutes
  messages_sent: number;           // Number of messages sent
  messages_received: number;       // Number of messages received
  media_shared: number;            // Number of media files shared
  most_active_chat: string;        // Name of most active chat/group
  peak_hours: string[];            // Array of peak usage hours (HH:MM format)
  chat_categories: {
    group_chats: number;           // Percentage of time in group chats
    personal_chats: number;        // Percentage of time in personal chats
  };
}

interface WhatsAppWeeklySummary {
  total_active_time: number;       // Total minutes for the week
  average_daily_time: number;      // Average daily minutes
  total_messages_sent: number;     // Total messages sent this week
  total_messages_received: number; // Total messages received this week
  most_active_day: string;         // Day with highest activity
}
```

### YouTube Data Schema

```typescript
interface YouTubeDailyUsage {
  date: string;                    // ISO date format (YYYY-MM-DD)
  watch_time_minutes: number;      // Total watch time in minutes
  videos_watched: number;          // Number of videos watched
  most_watched_category: string;   // Category with most watch time
  peak_usage_hour: string;         // Hour with peak usage (HH:MM format)
  categories: {
    [category: string]: number;    // Minutes watched per category
  };
}

interface YouTubeWeeklySummary {
  total_watch_time: number;        // Total minutes for the week
  average_daily_time: number;      // Average daily minutes
  favorite_category: string;       // Most watched category
  total_videos: number;            // Total videos watched this week
}
```

### Battery Data Schema

```typescript
interface BatteryDailyUsage {
  date: string;                    // ISO date format (YYYY-MM-DD)
  battery_level_start: number;     // Starting battery percentage (0-100)
  battery_level_end: number;       // Ending battery percentage (0-100)
  charging_sessions: number;       // Number of charging sessions
  screen_on_time_minutes: number;  // Screen on time in minutes
  top_consuming_apps: {
    [app_name: string]: number;    // Percentage of battery consumed
  };
}

interface BatteryPerformanceMetrics {
  average_battery_life: number;    // Average battery life in hours
  charging_efficiency: number;     // Charging efficiency percentage
  battery_health: string;          // Battery health status
}
```

## Data Validation Rules

### Required Fields

All data entries must include:
- `date`: Valid ISO date string
- Numeric fields: Non-negative numbers
- Percentage fields: Values between 0-100
- Time fields: Valid HH:MM format

### Data Consistency

- Daily usage arrays should be sorted by date (newest first)
- Weekly summaries should aggregate from daily usage data
- Percentage fields in categories should sum to approximately 100%
- Battery levels should be between 0-100

### File Formats

#### JSON Files
- UTF-8 encoding
- Valid JSON syntax
- Consistent indentation (2 spaces)
- No trailing commas

#### Text Files
- UTF-8 encoding
- Unix line endings (LF)
- No binary characters
- Optimized for semantic chunking

## Adding New Data

### Adding New Apps

To add support for a new app, follow these steps:

1. **Extend JSON Structure**:
   ```json
   {
     "new_app": {
       "daily_usage": [
         {
           "date": "2025-10-14",
           "app_specific_metric": 123,
           "another_metric": "value"
         }
       ],
       "weekly_summary": {
         "summary_metric": 456
       }
     }
   }
   ```

2. **Update Vector Text**:
   ```text
   New App Usage Analytics:
   Daily activity shows app-specific metrics and usage patterns.
   Weekly summary provides aggregated insights.
   ```

3. **Update Agent Recognition**:
   ```python
   # In analytics_agent.py
   app_keywords = {
       'new_app': ['new_app', 'keyword1', 'keyword2'],
       # ... existing apps
   }
   ```

### Data Quality Guidelines

#### Completeness
- All required fields must be present
- No null or undefined values for essential metrics
- Consistent date ranges across all apps

#### Accuracy
- Realistic values for all metrics
- Consistent units across similar measurements
- Proper time zone handling for dates

#### Freshness
- Regular updates to daily usage arrays
- Weekly summaries computed from recent daily data
- Removal of outdated entries beyond retention period

## Sample Data Generator

For testing purposes, you can generate sample data:

```python
from datetime import datetime, timedelta
import json
import random

def generate_sample_data(days=7):
    """Generate sample user activity data for testing."""
    data = {
        "whatsapp": {"daily_usage": [], "weekly_summary": {}},
        "youtube": {"daily_usage": [], "weekly_summary": {}},
        "battery": {"daily_usage": [], "performance_metrics": {}}
    }
    
    base_date = datetime.now() - timedelta(days=days-1)
    
    for i in range(days):
        current_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # WhatsApp data
        data["whatsapp"]["daily_usage"].append({
            "date": current_date,
            "active_time_minutes": random.randint(60, 120),
            "messages_sent": random.randint(50, 200),
            "messages_received": random.randint(60, 250),
            "media_shared": random.randint(5, 20),
            "most_active_chat": random.choice(["Family Group", "Work Team", "Friends"]),
            "peak_hours": random.sample(["09:00", "12:00", "18:00", "20:00"], 2),
            "chat_categories": {
                "group_chats": random.randint(50, 80),
                "personal_chats": random.randint(20, 50)
            }
        })
        
        # Similar for YouTube and battery...
    
    return data
```

This data format documentation ensures consistent data structure and enables reliable UI generation across all supported applications.

## Adding New Documents

1. Place your document files in the appropriate subdirectory
2. Files should be in plain text format with clear, structured content
3. Restart the application to reindex new documents

## Example Document Structure

```text
# Login Screen Pattern

Pattern: Login Form
Description: A standard login form with email/username and password fields.
Components:
- TextField for email/username
- TextField for password (secured)
- "Remember me" checkbox
- Login button
- "Forgot password" link

Best Practices:
- Place login form in center of screen
- Use clear validation messages
- Provide password visibility toggle
- Support keyboard navigation
```