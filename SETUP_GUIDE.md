# GymBuddy - Complete Setup & Maintenance Guide

This guide will walk you through setting up GymBuddy from scratch, even if you have no technical background.

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Quick Start (Local Testing)](#2-quick-start-local-testing)
3. [WhatsApp Business API Setup](#3-whatsapp-business-api-setup)
4. [Get Gemini API Key](#4-get-gemini-api-key)
5. [Connect Everything](#5-connect-everything)
6. [Running the System](#6-running-the-system)
7. [Adding Gym Classes](#7-adding-gym-classes)
8. [Daily Maintenance](#8-daily-maintenance)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

### What You Need

| Item | How to Get | Time |
|------|------------|------|
| **Docker Desktop** | [docker.com/download](https://docker.com/products/docker-desktop/) | 5 min |
| **Python 3.11+** | Pre-installed on Mac or [python.org](https://python.org) | 5 min |
| **WhatsApp Business Account** | [business.facebook.com](https://business.facebook.com) | 1-3 days |
| **Gemini API Key** | [aistudio.google.com](https://aistudio.google.com) | 2 min |
| **ngrok (free)** | [ngrok.com](https://ngrok.com) | 2 min |

### Check if Docker is installed
```bash
docker --version
```
If it shows a version, you're good! If not, install Docker Desktop.

---

## 2. Quick Start (Local Testing)

### Step 1: Navigate to Project
```bash
cd /Users/raghav/Desktop/systems/gymbuddy
```

### Step 2: Create Environment File
```bash
cp .env.example .env
```

### Step 3: Start Database (PostgreSQL + Redis)
```bash
docker-compose up -d
```
Wait about 30 seconds. Check status:
```bash
docker-compose ps
```
Both services should show "Up".

### Step 4: Install Python Dependencies
```bash
# Create virtual environment (one time)
python3 -m venv venv

# Activate it (every time)
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 5: Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Step 6: Verify it's working
Open in browser: http://localhost:8000

You should see:
```json
{"service": "GymBuddy API", "status": "running"}
```

🎉 **The backend is running!** But WhatsApp isn't connected yet.

---

## 3. WhatsApp Business API Setup

This is the longest step (~1-3 days for approval).

### Step 1: Create Meta Business Account

1. Go to [business.facebook.com](https://business.facebook.com)
2. Click "Create Account"
3. Enter your gym's business name
4. Verify your email
5. Complete business verification (may take 1-3 days)

### Step 2: Create Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Name it "GymBuddy" or your gym name
5. Select your Business Account

### Step 3: Add WhatsApp Product

1. In your app dashboard, click "Add Products"
2. Find "WhatsApp" and click "Set Up"
3. Choose "API Setup" (not Business Solution)

### Step 4: Get Your Credentials

In the WhatsApp API Setup page, you'll see:

| Credential | Where to Find | What to Copy |
|------------|---------------|--------------|
| **Phone Number ID** | API Setup → Phone number ID | Numbers like `1234567890123456` |
| **WhatsApp Business Account ID** | API Setup → WhatsApp Business Account ID | Numbers like `9876543210123` |
| **Access Token** | API Setup → Temporary access token | Long string starting with `EAAG...` |

⚠️ **Important:** The temporary token expires in 24 hours. For production, create a permanent token:
1. Go to Business Settings → Users → System Users
2. Create a system user
3. Generate a permanent token with `whatsapp_business_messaging` permission

### Step 5: Add Test Phone Number

1. In API Setup, click "Add phone number"
2. You can use your personal WhatsApp number for testing
3. Verify the number via OTP

### Step 6: Set Up Webhook

First, expose your local server to the internet:

```bash
# Install ngrok (one time)
brew install ngrok

# Start ngrok tunnel
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok.io`

In Meta Developer Dashboard:
1. Go to WhatsApp → Configuration
2. Click "Edit" next to Webhook
3. **Callback URL:** `https://YOUR-NGROK-URL/api/v1/webhooks/whatsapp`
4. **Verify Token:** `gymbuddy_verify_token_2026`
5. Click "Verify and Save"

Subscribe to these webhook fields:
- ✅ `messages`
- ✅ `message_template_status_update` (optional)

---

## 4. Get Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google account
3. Click "Get API Key" → "Create API key"
4. Copy the key (looks like `AIzaSy...`)

**Free Tier Limits:**
- 15 requests per minute
- 1,500 requests per day
- More than enough for testing!

---

## 5. Connect Everything

Edit your `.env` file:

```bash
nano .env
```

Update these values:
```env
# Database (already set up)
DATABASE_URL=postgresql://gymbuddy:gymbuddy123@localhost:5432/gymbuddy

# WhatsApp (from Step 3)
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id_here
WHATSAPP_ACCESS_TOKEN=your_access_token_here

# Gemini (from Step 4)
GEMINI_API_KEY=your_gemini_api_key_here

# Your Gym Info
GYM_NAME=Your Gym Name Here
```

Save and restart the server:
```bash
# Press Ctrl+C to stop
# Then restart:
uvicorn app.main:app --reload --port 8000
```

---

## 6. Running the System

### Daily Startup Sequence

1. **Start Docker (databases)**
```bash
cd /Users/raghav/Desktop/systems/gymbuddy
docker-compose up -d
```

2. **Activate Python environment**
```bash
source venv/bin/activate
```

3. **Start the API server**
```bash
uvicorn app.main:app --reload --port 8000
```

4. **Start ngrok (if testing locally)**
```bash
ngrok http 8000
```

⚠️ **Note:** If ngrok URL changes, update it in Meta Developer Dashboard!

### Test Your Setup

1. Send "Hi" from your WhatsApp to your test number
2. You should receive a welcome message with goal selection buttons!

If it works, GymBuddy is live! 🎉

---

## 7. Adding Gym Classes

Use the API to add classes. Here's how:

### Using the API Docs

1. Open http://localhost:8000/docs
2. Find `POST /api/v1/classes/`
3. Click "Try it out"
4. Enter class details:

```json
{
  "name": "Morning Yoga",
  "class_type": "yoga",
  "trainer_name": "Priya",
  "scheduled_at": "2026-01-12T06:00:00",
  "duration_mins": 60,
  "capacity": 15,
  "room": "Studio A",
  "intensity": "low",
  "goal_tags": ["flexibility", "stress_relief"]
}
```

### Common Class Types
- `yoga` (low intensity)
- `hiit` (high intensity)
- `spin` (high intensity)
- `strength` (medium intensity)
- `dance` (medium intensity)
- `boxing` (high intensity)

### Bulk Add Classes (Advanced)

Create a script `add_classes.py`:
```python
import httpx
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# Your weekly schedule
classes = [
    # Monday
    {"name": "Morning Yoga", "class_type": "yoga", "trainer_name": "Priya", "duration_mins": 60, "capacity": 15, "room": "Studio A", "intensity": "low"},
    {"name": "HIIT Burn", "class_type": "hiit", "trainer_name": "Arjun", "duration_mins": 45, "capacity": 20, "room": "Main Floor", "intensity": "high"},
    # Add more...
]

# Schedule for next 7 days
for day_offset in range(7):
    date = datetime.now() + timedelta(days=day_offset)
    if date.weekday() < 6:  # Monday-Saturday
        for cls in classes:
            # Morning class at 6 AM
            cls["scheduled_at"] = date.replace(hour=6).isoformat()
            response = httpx.post(f"{BASE_URL}/classes/", json=cls)
            print(f"Added: {cls['name']} on {date.date()}")
```

Run it:
```bash
python add_classes.py
```

---

## 8. Daily Maintenance

### Morning Checklist (5 minutes)

1. **Check services are running:**
```bash
docker-compose ps  # Should show 2 services "Up"
```

2. **Check API health:**
```bash
curl http://localhost:8000/health
```

3. **Check ngrok (if using):**
Make sure the tunnel is active and URL matches Meta webhook config.

### Weekly Tasks

1. **Check member stats:**
```bash
curl http://localhost:8000/api/v1/members/stats/overview
```

2. **Add classes for next week**

3. **Review at-risk members:**
```bash
curl "http://localhost:8000/api/v1/members?state=at_risk"
```

### Database Backup (Weekly)

```bash
# Create backup
docker exec gymbuddy_postgres pg_dump -U gymbuddy gymbuddy > backup_$(date +%Y%m%d).sql

# Restore from backup (if needed)
docker exec -i gymbuddy_postgres psql -U gymbuddy gymbuddy < backup_20260111.sql
```

---

## 9. Troubleshooting

### Problem: WhatsApp messages not being received

**Check ngrok:**
```bash
# Is ngrok running?
curl https://your-ngrok-url.ngrok.io/health
```

**Check webhook:**
1. Go to Meta Developer Dashboard → WhatsApp → Configuration
2. Verify the callback URL matches your ngrok URL
3. Click "Verify and Save" again

### Problem: "Unauthorized" error in WhatsApp

Your access token has expired!

1. Go to Meta Developer Dashboard
2. Get a new temporary token OR create a permanent system user token

### Problem: AI plans not generating

Check your Gemini API key:
```bash
grep GEMINI_API_KEY .env
```

Make sure it's set. Test it:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY"
```

### Problem: Database connection error

Restart Docker:
```bash
docker-compose down
docker-compose up -d
```

### Problem: Server won't start

Check if port 8000 is in use:
```bash
lsof -i :8000
```

Kill the process or use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

---

## Quick Reference

### Important URLs
| URL | Purpose |
|-----|---------|
| http://localhost:8000 | API Health Check |
| http://localhost:8000/docs | API Documentation |
| https://developers.facebook.com | Meta Dashboard |
| https://aistudio.google.com | Gemini API |

### Key Commands
```bash
# Start everything
cd /Users/raghav/Desktop/systems/gymbuddy
docker-compose up -d
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Stop everything
# Ctrl+C to stop server
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Getting Help

If something doesn't work:
1. Check the server logs in your terminal
2. Check docker logs: `docker-compose logs`
3. Try restarting everything

---

## Next Steps

Once basic setup is working:

1. **Create Message Templates:** Submit templates to Meta for approval (required for proactive messages)
2. **Set Up Reminders:** Add scheduled jobs for class reminders
3. **Add Admin Dashboard:** React dashboard for managing members
4. **Deploy to Production:** Move from ngrok to a proper server

---

*GymBuddy v1.0.0 - Built with ❤️ for Indian Gyms*
