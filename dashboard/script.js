// ===== Configuration =====
const API_BASE = 'http://localhost:8000';

// ===== Demo Chat Messages =====
const demoResponses = {
    'hi': {
        messages: [
            { type: 'outgoing', text: 'hi' },
            { type: 'incoming', text: '👋 Hey there! Welcome to *FitZone Gym*!\n\nI\'m GymBuddy, your AI fitness assistant. I can help you with:\n\n💪 Workout Plans\n🥗 Diet Plans\n📅 Class Bookings\n📊 Progress Tracking\n\nWhat would you like to do today?' }
        ]
    },
    'hello': {
        messages: [
            { type: 'outgoing', text: 'hello' },
            { type: 'incoming', text: '👋 Hello! Great to see you at *FitZone Gym*!\n\nI\'m GymBuddy, ready to help with your fitness journey. Try these commands:\n\n• *workout* - Get today\'s plan\n• *diet* - View meal plan\n• *book* - Book a class\n• *progress* - See your stats\n\nHow can I assist you?' }
        ]
    },
    'workout': {
        messages: [
            { type: 'outgoing', text: 'workout' },
            { type: 'incoming', text: '💪 *Today\'s Workout - Upper Body*\n═══════════════════════\n\n🔥 *Warm-up* (5 mins)\n• Arm circles - 30 sec each\n• Jumping jacks - 1 min\n• Push-ups - 10 reps\n\n*Main Workout:*\n\n1️⃣ *Bench Press* - 4×12\n    Rest: 60 sec\n\n2️⃣ *Dumbbell Rows* - 3×15 each arm\n    Rest: 45 sec\n\n3️⃣ *Shoulder Press* - 3×12\n    Rest: 60 sec\n\n4️⃣ *Bicep Curls* - 3×15\n    Rest: 45 sec\n\n5️⃣ *Tricep Dips* - 3×12\n    Rest: 45 sec\n\n🧘 *Cool Down* - 5 min stretching\n\n📊 Expected: ~350 kcal burn\n\nReply *done* when finished!' }
        ]
    },
    'diet': {
        messages: [
            { type: 'outgoing', text: 'diet' },
            { type: 'incoming', text: '🍎 *Your Personalized Diet Plan*\n═══════════════════════\n\n📊 *Daily Targets:*\n  🔥 Calories: 2200 kcal\n  💪 Protein: 165g\n  🌾 Carbs: 220g\n  🥑 Fat: 73g\n\n📋 *Today\'s Meals:*\n\n*7:00 AM - Breakfast*\n  • 4 Egg whites + 1 whole egg\n  • 2 Multigrain rotis\n  • 1 glass milk with protein\n\n*10:30 AM - Snack*\n  • Greek yogurt with almonds\n  • 1 banana\n\n*1:00 PM - Lunch*\n  • 150g Grilled chicken\n  • Brown rice (1 cup)\n  • Mixed vegetable sabzi\n\n*5:00 PM - Pre-Workout*\n  • Peanut butter toast\n  • Black coffee\n\n*8:00 PM - Dinner*\n  • Paneer bhurji (150g)\n  • 2 Rotis\n  • Salad\n\n💧 *Hydration:* 3-4L water\n\n💡 *Tips:*\n  • Eat protein with every meal\n  • Avoid sugar after 4 PM' }
        ]
    },
    'book': {
        messages: [
            { type: 'outgoing', text: 'book class' },
            { type: 'incoming', text: '📅 *Available Classes Today*\n═══════════════════════\n\n1️⃣ *Morning Yoga* 🧘\n   ⏰ 6:00 AM | Trainer: Priya\n   👥 8/15 spots | Studio A\n   \n2️⃣ *HIIT Burn* 🔥\n   ⏰ 7:30 AM | Trainer: Arjun\n   👥 12/20 spots | Main Floor\n   \n3️⃣ *Spin Class* 🚴\n   ⏰ 6:00 PM | Trainer: Ravi\n   👥 5/15 spots | Spin Studio\n   \n4️⃣ *Boxing Basics* 🥊\n   ⏰ 7:00 PM | Trainer: Vikram\n   👥 10/12 spots | Boxing Ring\n\nReply with the *class number* to book!\n\nExample: *1* for Morning Yoga' }
        ]
    },
    'book class': {
        messages: [
            { type: 'outgoing', text: 'book class' },
            { type: 'incoming', text: '📅 *Available Classes Today*\n═══════════════════════\n\n1️⃣ *Morning Yoga* 🧘\n   ⏰ 6:00 AM | Trainer: Priya\n   👥 8/15 spots | Studio A\n   \n2️⃣ *HIIT Burn* 🔥\n   ⏰ 7:30 AM | Trainer: Arjun\n   👥 12/20 spots | Main Floor\n   \n3️⃣ *Spin Class* 🚴\n   ⏰ 6:00 PM | Trainer: Ravi\n   👥 5/15 spots | Spin Studio\n   \n4️⃣ *Boxing Basics* 🥊\n   ⏰ 7:00 PM | Trainer: Vikram\n   👥 10/12 spots | Boxing Ring\n\nReply with the *class number* to book!\n\nExample: *1* for Morning Yoga' }
        ]
    },
    'progress': {
        messages: [
            { type: 'outgoing', text: 'progress' },
            { type: 'incoming', text: '📊 *Your Progress Report*\n═══════════════════════\n\n🔥 *Streak:* 12 days! 🔥\n\n📈 *This Week:*\n  ✅ Workouts: 5/6\n  ✅ Diet adherence: 85%\n  ✅ Classes attended: 3\n\n⚖️ *Weight Journey:*\n  Start: 78 kg\n  Current: 74.5 kg\n  Goal: 72 kg\n  📉 Progress: 70% there!\n\n💪 *Strength Gains:*\n  Bench Press: +10 kg\n  Deadlift: +15 kg\n  Squat: +12 kg\n\n🏆 *Achievements:*\n  🥇 10-Day Streak Badge\n  🥈 Early Bird (5 AM workouts)\n  🥉 Class Champion\n\nKeep going! You\'re doing amazing! 💪' }
        ]
    },
    'help': {
        messages: [
            { type: 'outgoing', text: 'help' },
            { type: 'incoming', text: '❓ *GymBuddy Commands*\n═══════════════════════\n\n💬 *General:*\n  • hi/hello - Get started\n  • help - Show this menu\n\n💪 *Fitness:*\n  • workout - Today\'s plan\n  • done - Log workout\n  • streak - Check streak\n\n🥗 *Nutrition:*\n  • diet - View meal plan\n  • weight [kg] - Log weight\n  • breakfast/lunch/dinner\n\n📅 *Classes:*\n  • classes - See schedule\n  • book - Book a class\n  • my bookings - View bookings\n  • cancel - Cancel booking\n\n📊 *Progress:*\n  • progress - Weekly report\n  • stats - Overall stats\n\n🗣️ *Support:*\n  • talk to manager\n  • timings - Gym hours\n  • price - Membership info\n\nJust type any command!' }
        ]
    },
    'done': {
        messages: [
            { type: 'outgoing', text: 'done' },
            { type: 'incoming', text: '🎉 *Workout Complete!*\n═══════════════════════\n\n✅ Upper Body workout logged!\n⏱️ Duration: 45 mins\n🔥 Estimated burn: 350 kcal\n\n🔥 *Streak:* 13 days! NEW RECORD! 🎊\n\nYou\'re on fire! Keep it up!\n\nRemember to:\n💧 Stay hydrated\n🥗 Eat within 30 mins\n😴 Get 7-8 hours sleep\n\nSee you tomorrow! 💪' }
        ]
    },
    'streak': {
        messages: [
            { type: 'outgoing', text: 'streak' },
            { type: 'incoming', text: '🔥 *Your Streak Stats*\n═══════════════════════\n\n*Current Streak:* 12 days 🔥\n*Best Streak:* 18 days\n*Total Workouts:* 47\n\n📅 This Week:\nMon ✅ Tue ✅ Wed ✅ Thu ✅ Fri ✅ Sat ⬜ Sun ⬜\n\n🏆 *Streak Rewards:*\n✅ 7 days - Free protein shake\n✅ 14 days - 10% off supplements\n⬜ 30 days - Free personal training\n\nKeep going! 2 more days for 14-day reward! 🎯' }
        ]
    },
    'timings': {
        messages: [
            { type: 'outgoing', text: 'timings' },
            { type: 'incoming', text: '🕐 *FitZone Gym Hours*\n═══════════════════════\n\n*Monday - Saturday:*\n  🌅 Morning: 5:00 AM - 11:00 AM\n  🌆 Evening: 4:00 PM - 10:00 PM\n\n*Sunday:*\n  🌅 Morning: 6:00 AM - 12:00 PM\n  ❌ Evening: Closed\n\n*Public Holidays:*\n  🕐 7:00 AM - 1:00 PM\n\n📍 Location: 2nd Floor, Phoenix Mall\n📞 Contact: +91 98765 43210\n\nSee you at the gym! 💪' }
        ]
    },
    'price': {
        messages: [
            { type: 'outgoing', text: 'price' },
            { type: 'incoming', text: '💰 *Membership Plans*\n═══════════════════════\n\n*Monthly:* ₹2,499/month\n  • All gym equipment\n  • Group classes\n  • Locker facility\n\n*Quarterly:* ₹6,499 (₹2,166/mo)\n  • Everything in Monthly\n  • 1 Personal Training session\n  • Diet consultation\n\n*Annual:* ₹19,999 (₹1,666/mo) ⭐\n  • Everything in Quarterly\n  • 4 PT sessions/month\n  • Priority class booking\n  • Free supplements\n\n*Student Discount:* 15% off!\n\n🎁 *Current Offer:*\nJoin Annual & get 2 months FREE!\n\nInterested? Reply *join* or visit the front desk!' }
        ]
    }
};

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    checkApiStatus();
    initChat();

    // Check API status every 30 seconds
    setInterval(checkApiStatus, 30000);

    // Initialize keyboard support for command cards
    initCommandCards();
});

// ===== API Status Check =====
async function checkApiStatus() {
    const statusBtn = document.getElementById('statusBtn');
    const statusDot = statusBtn.querySelector('.status-dot');

    try {
        const response = await fetch(`${API_BASE}/health`, {
            mode: 'cors',
            timeout: 5000
        });

        if (response.ok) {
            const data = await response.json();
            statusDot.className = 'status-dot online';
            statusBtn.innerHTML = `<span class="status-dot online"></span>API Online`;
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        statusDot.className = 'status-dot offline';
        statusBtn.innerHTML = `<span class="status-dot offline"></span>API Offline`;
    }
}

// ===== Chat Initialization =====
function initChat() {
    const container = document.getElementById('chatContainer');

    // Initial welcome message
    addMessage('incoming', '👋 Welcome to *FitZone Gym*!\n\nI\'m GymBuddy, your AI assistant. Try typing:\n• hi\n• workout\n• diet\n• book\n• help');
}

// ===== Add Message to Chat =====
function addMessage(type, text) {
    const container = document.getElementById('chatContainer');
    const msg = document.createElement('div');
    msg.className = `message ${type}`;

    // Format WhatsApp-style text
    let formattedText = text
        .replace(/\*(.*?)\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    const time = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });

    msg.innerHTML = `${formattedText}<div class="message-time">${time}</div>`;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

// ===== Add Typing Indicator =====
function addTypingIndicator() {
    const container = document.getElementById('chatContainer');
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.id = 'typingIndicator';
    typing.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

// ===== Send Message - REAL AI API =====
// Current user context
let currentUserPhone = '+919876543210';
let currentUserName = 'Demo User';

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();

    if (!text) return;

    // Add outgoing message
    addMessage('outgoing', input.value);
    input.value = '';

    // Add typing indicator
    addTypingIndicator();

    try {
        // Call the REAL AI API
        const response = await fetch(`${API_BASE}/api/v1/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone: currentUserPhone,
                message: text,
                name: currentUserName
            })
        });

        if (response.ok) {
            const data = await response.json();
            removeTypingIndicator();

            // Add the REAL AI response
            addMessage('incoming', data.response);

            // Log for debugging
            console.log('🤖 AI Intent:', data.intent);
            console.log('👤 Member:', data.member_name);
            console.log('📊 Context:', data.member_context);
        } else {
            removeTypingIndicator();
            const errorData = await response.json().catch(() => ({}));
            console.error('API Error:', errorData);
            addMessage('incoming', '⚠️ Sorry, I could not process that. Please try again.');
        }
    } catch (error) {
        removeTypingIndicator();
        console.error('Network Error:', error);

        // Fallback to demo response if API is down
        const demoResponse = demoResponses[text.toLowerCase()];
        if (demoResponse) {
            addMessage('incoming', demoResponse.messages[1].text + '\n\n_(Offline mode - using cached response)_');
        } else {
            addMessage('incoming', `⚠️ Cannot connect to AI. Make sure the server is running at ${API_BASE}\n\nRun: uvicorn app.main:app --reload --port 8000`);
        }
    }
}

// ===== Onboard Demo User with Details =====
async function onboardDemoUser(name, goal, diet, weight, targetWeight) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/chat/onboard`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone: currentUserPhone,
                name: name || "Rahul",
                age: 28,
                gender: "male",
                height_cm: 175,
                current_weight_kg: weight || 82,
                target_weight_kg: targetWeight || 75,
                primary_goal: goal || "weight_loss",
                dietary_preference: diet || "veg"
            })
        });

        if (response.ok) {
            const data = await response.json();
            currentUserName = data.profile.name;
            console.log('✅ Onboarded:', data);
            return data;
        }
    } catch (error) {
        console.error('Onboard error:', error);
    }
    return null;
}

// ===== Handle Enter Key =====
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// ===== Simulate Command (from demo cards) =====
function simulateCommand(cmd) {
    const input = document.getElementById('chatInput');
    input.value = cmd;

    // Scroll to chat
    document.querySelector('.hero-visual').scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });

    // Send after scroll
    setTimeout(() => {
        sendMessage();
    }, 500);
}

// ===== Open Docs =====
function openDocs() {
    window.open(`${API_BASE}/docs`, '_blank');
}

// ===== Open Simulator Modal =====
function openSimulator() {
    document.getElementById('simulatorModal').classList.add('active');
}

function closeSimulator() {
    document.getElementById('simulatorModal').classList.remove('active');
}

// ===== Send Test Message via API =====
async function sendTestMessage() {
    const phone = document.getElementById('testPhone').value;
    const message = document.getElementById('testMessage').value;
    const responseDiv = document.getElementById('simulatorResponse');

    if (!phone || !message) {
        responseDiv.textContent = 'Please enter both phone and message';
        responseDiv.classList.add('active');
        return;
    }

    responseDiv.textContent = 'Sending...';
    responseDiv.classList.add('active');

    try {
        const response = await fetch(`${API_BASE}/api/v1/webhooks/test-send?phone=${encodeURIComponent(phone)}&message=${encodeURIComponent(message)}`, {
            method: 'POST'
        });

        const data = await response.json();
        responseDiv.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        responseDiv.textContent = `Error: ${error.message}\n\nMake sure the API is running at ${API_BASE}`;
    }
}

// ===== Smooth Scroll for Nav Links =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// ===== Close modal on outside click =====
document.getElementById('simulatorModal').addEventListener('click', function (e) {
    if (e.target === this) {
        closeSimulator();
    }
});

// ===== Keyboard Support for Command Cards =====
function initCommandCards() {
    const cards = document.querySelectorAll('.command-card');
    cards.forEach(card => {
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });
}

// ===== Keyboard navigation for modal =====
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeSimulator();
    }
});
