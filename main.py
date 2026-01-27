import discord
import requests
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import os
from flask import Flask
import threading
import asyncio
import time

# --- Discord Bot Setup ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.all()
client = discord.Client(intents=intents)

timezone = pytz.timezone("Asia/Dhaka")

# --- Function to get random ayah with retries ---
def get_random_ayah():
    for _ in range(3):  # Retry 3 times if API fails
        try:
            ayah_number = random.randint(1, 6236)
            arabic = requests.get(f"https://api.alquran.cloud/v1/ayah/{ayah_number}").json()
            english = requests.get(f"https://api.alquran.cloud/v1/ayah/{ayah_number}/en.sahih").json()

            ar_text = arabic["data"]["text"]
            en_text = english["data"]["text"]
            surah = english["data"]["surah"]["englishName"]
            ayah_num = english["data"]["numberInSurah"]

            return ar_text, en_text, surah, ayah_num
        except Exception as e:
            print("Error fetching ayah:", e)
            time.sleep(1)
    return "Error", "Error", "Error", 0

# --- Function to send ayah to Discord ---
async def send_daily_ayah():
    try:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            ar, en, surah, num = get_random_ayah()
            message = f"📖 **Daily Ayah**\n\n{ar}\n\n**Translation:** {en}\n— Surah {surah}, Ayah {num}"
            await channel.send(message)
        else:
            print("Channel not found. Check CHANNEL_ID.")
    except Exception as e:
        print("Error sending Daily Ayah:", e)

# --- Discord on_ready event ---
@client.event
async def on_ready():
    print(f"{client.user} is online!")
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(send_daily_ayah, "cron", hour=6, minute=0)  # 6 AM Dhaka time
    scheduler.start()
    await send_daily_ayah()  # Send immediately on startup

# --- Tiny Flask server to keep Render happy ---
app = Flask("")

@app.route("/")
def home():
    return "DailyAyah Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# --- Self-ping to prevent Render free tier from sleeping ---
def keep_alive():
    url = f"http://localhost:{os.environ.get('PORT', 8080)}/"
    while True:
        try:
            requests.get(url)
        except:
            pass
        time.sleep(300)  # every 5 minutes

threading.Thread(target=keep_alive).start()

# --- Run Discord bot ---
client.run(TOKEN)
