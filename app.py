import os
import time
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, render_template_string
import cloudscraper
from telegram import Bot
from twilio.rest import Client
import asyncio
# =========================
# CONFIGURATION (use environment variables for hosting)
# =========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Twilio number
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")          # Your phone number
MOVIE_URL = os.getenv(
    "MOVIE_URL",
    "https://in.bookmyshow.com/movies/chennai/jana-nayagan/ET00430817"
)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

# =========================
# INIT
# =========================
bot = Bot(token=BOT_TOKEN)
scraper = cloudscraper.create_scraper()
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = Flask(__name__)

# =========================
# LOG STORAGE
# =========================
LOGS = []
MAX_LOGS = 200  # prevent memory growth

IST = timezone(timedelta(hours=5, minutes=30))

def log(message):
    timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    entry = f"[{timestamp}] {message}"
    print(entry)

    LOGS.append(entry)
    if len(LOGS) > MAX_LOGS:
        LOGS.pop(0)

async def send_telegram_alert(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)
# =========================
# TWILIO CALL
# =========================
def make_call(message):
    try:
        call = twilio_client.calls.create(
            twiml=f"<Response><Say>{message}</Say></Response>",
            from_=TWILIO_PHONE_NUMBER,
            to=MY_PHONE_NUMBER
        )
        log(f"📞 Twilio call initiated (SID: {call.sid})")
    except Exception as e:
        log(f"⚠️ Twilio error: {e}")

# =========================
# MONITOR LOOP
# =========================
def monitor_tickets():
    log("🔍 Ticket monitoring started")

    while True:
        try:
            response = scraper.get(MOVIE_URL, timeout=15)

            if response.status_code == 200:
                page_text = response.text.lower()

                if "book tickets" in page_text or "select seats" in page_text:
                    log("🚨 POSSIBLE BOOKING OPEN!")

                    asyncio.run(
                        send_telegram_alert(
                        f"🚨 BOOKINGS MAY BE OPEN!\n{MOVIE_URL}"
                        )
                )


                    make_call(
                        "Jana Nayagan tickets may be live. Please check immediately."
                    )

                    log("✅ ALERT SENT — stopping monitor")
                    break
                else:
                    log("⏳ Not open yet...")
            else:
                log(f"❌ HTTP {response.status_code}")

        except Exception as e:
            log(f"⚠️ Error: {e}")

        time.sleep(CHECK_INTERVAL)

# =========================
# FRONTEND
# =========================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Ticket Monitor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {
            font-family: monospace;
            background: #0f172a;
            color: #e5e7eb;
            padding: 20px;
        }
        h1 { color: #38bdf8; }

        .log-box {
            background: #020617;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 13px;
        }

        .log-line {
            margin-bottom: 4px;
        }
    </style>
</head>
<body>
    <h1>🎬 Movie Ticket Alert Bot</h1>
    <p>Monitoring:</p>
    <code>{{ url }}</code>

    <hr>

    <div class="log-box" id="logBox">
        {% for line in logs %}
            <div class="log-line">{{ line }}</div>
        {% endfor %}
    </div>

    <script>
        // Auto-scroll to bottom
        const logBox = document.getElementById("logBox");
        logBox.scrollTop = logBox.scrollHeight;
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML_PAGE,
        logs=LOGS,
        url=MOVIE_URL
    )

@app.route("/logs")
def logs():
    return jsonify(LOGS)

# =========================
# START BACKGROUND THREAD
# =========================
threading.Thread(target=monitor_tickets, daemon=True).start()

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

