# GymBuddy - Demo Guide for Clients

This guide helps you demonstrate GymBuddy to clients in an impressive way.

## 🚀 Quick Start (Demo Setup)

### Step 1: Start the Backend API

```bash
cd /Users/raghav/Desktop/systems/gymbuddy
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### Step 2: Start the Demo Dashboard

```bash
cd /Users/raghav/Desktop/systems/gymbuddy/dashboard
python3 -m http.server 8001
```

### Step 3: Open in Browser

- **Demo Dashboard**: http://localhost:8001
- **API Documentation**: http://localhost:8000/docs

---

## 🎯 Demo Script (15-20 minutes)

### Part 1: Introduction (2 mins)

1. Open the **Demo Dashboard** (http://localhost:8001)
2. Explain the problem:
   - "Gym member retention is a massive issue in India"
   - "Most gyms lose 50%+ members in first 3 months"
   - "Staff can't personally engage with 500+ members"

3. Show the solution:
   - "GymBuddy is an AI WhatsApp assistant for gyms"
   - "Members interact via India's #1 messaging app"
   - "24/7 automated engagement, personalized plans"

### Part 2: Live Chat Demo (5 mins)

Use the **interactive WhatsApp simulator** on the landing page:

| Command | What to Show |
|---------|--------------|
| `hi` | Welcome message with options |
| `workout` | AI-generated personalized workout |
| `diet` | Indian cuisine-friendly meal plan |
| `book class` | Interactive class booking |
| `progress` | Member stats, streaks, achievements |
| `help` | Full command list |

**Pro Tips:**
- Emphasize the *instant responses*
- Point out *Indian food options* in diet plan
- Highlight *gamification* (streaks, badges)

### Part 3: API Demo (3 mins)

1. Open http://localhost:8000/docs
2. Show key endpoints:
   - `POST /api/v1/members` - Create member
   - `GET /api/v1/classes` - List classes
   - `POST /api/v1/webhooks/whatsapp` - WhatsApp integration

3. Try a live API call:
   - Expand `GET /` endpoint
   - Click "Try it out" → "Execute"
   - Show the JSON response

### Part 4: Technical Highlights (3 mins)

Show these impressive features:

✅ **AI-Powered** - Google Gemini generates personalized plans
✅ **WhatsApp Native** - Most popular platform in India
✅ **Class Booking** - Waitlists, reminders, capacity management
✅ **Member Retention** - State machine identifies at-risk members
✅ **Analytics Ready** - Track engagement, churn prediction

### Part 5: Business Value (2 mins)

Present the ROI:

| Problem | GymBuddy Solution |
|---------|-------------------|
| High churn rate | Proactive engagement before members leave |
| Staff overload | Automate 90% of routine queries |
| No personalization | AI creates custom workout + diet plans |
| Missed bookings | Automated reminders reduce no-shows |
| Limited hours | 24/7 availability via WhatsApp |

### Part 6: Pricing & Next Steps (2 mins)

Scroll to pricing section on demo page:

- **Starter**: ₹4,999/mo (up to 200 members)
- **Growth**: ₹9,999/mo (up to 500 members) 
- **Enterprise**: ₹24,999/mo (unlimited)

Close with: "Would you like to start a 14-day free trial?"

---

## 🛠️ Troubleshooting

### API won't start?

```bash
# Check if port is in use
lsof -i :8000

# Use different port
python -m uvicorn app.main:app --reload --port 8001
```

### Database issues?

```bash
# Delete and recreate SQLite database
rm gymbuddy.db
python -m uvicorn app.main:app --reload --port 8000
```

### WhatsApp not working?

This demo uses a simulator. For real WhatsApp:
1. Get Meta Business API access
2. Configure `.env` with your credentials
3. Use ngrok for webhook URL

---

## 📱 Real WhatsApp Demo (Advanced)

For a live WhatsApp demo:

1. **Start ngrok**: `ngrok http 8000`
2. **Update webhook**: Go to Meta Developer Dashboard
3. **Send test message**: Use the API test endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/test-send?phone=+919876543210&message=hello"
```

---

## 📁 Project Files

```
gymbuddy/
├── app/                    # Backend API
│   ├── main.py            # FastAPI entry
│   ├── services/          # Business logic
│   ├── flows/             # WhatsApp flows
│   └── routers/           # API routes
├── dashboard/              # Demo frontend
│   ├── index.html         # Landing page
│   ├── styles.css         # Styling
│   └── script.js          # Interactivity
├── .env                    # Configuration
└── requirements.txt        # Dependencies
```

---

## 🎁 Bonus Demo Ideas

1. **Show API docs interactivity** - Let client try API calls
2. **Explain the AI** - "Powered by Google Gemini, same AI as Google"
3. **Mobile demo** - Dashboard is responsive, show on phone
4. **Competitor comparison** - "No one else offers WhatsApp + AI in India"

---

*GymBuddy v1.0.0 - Built with ❤️ for Indian Gyms*
