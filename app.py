import time
import cloudscraper
from telegram import Bot
from twilio.rest import Client
import os

# =========================
# CONFIGURATION (use environment variables for hosting)
# =========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Twilio number
MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER")          # Your phone number

MOVIE_URL = "https://in.bookmyshow.com/movies/chennai/ikkis/ET00388415"
CHECK_INTERVAL = 30  # seconds between checks

# =========================
# INIT
# =========================
bot = Bot(token=BOT_TOKEN)
scraper = cloudscraper.create_scraper()
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# =========================
# Twilio Call Function
# =========================
def make_call(message):
    """Make a voice call via Twilio"""
    call = twilio_client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        from_=TWILIO_PHONE_NUMBER,
        to=MY_PHONE_NUMBER
    )
    print("📞 Call initiated, SID:", call.sid)

# =========================
# MONITOR LOOP
# =========================
while True:
    try:
        response = scraper.get(MOVIE_URL, timeout=15)
        if response.status_code == 200:
            page_text = response.text.lower()
            if "book tickets" in page_text or "select seats" in page_text:
                alert_msg = f"🚨 Possible booking open!\nCheck {MOVIE_URL}"

                # Telegram alert
                bot.send_message(chat_id=CHAT_ID, text=alert_msg)

                # Twilio phone call
                make_call("Jana Nayagan tickets may be live. Check your phone or computer immediately!")

                print("✅ ALERT SENT — Telegram + Twilio Call")
                break
            else:
                print("⏳ Not open yet...")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print("⚠️ Error:", e)

    time.sleep(CHECK_INTERVAL)
