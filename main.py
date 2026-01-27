import discord
import requests
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

import os
TOKEN = os.getenv("DISCORD_TOKEN")
 
CHANNEL_ID = 1465732469436186751

intents = discord.Intents.all()
client = discord.Client(intents=intents)

timezone = pytz.timezone("Asia/Dhaka")

def get_random_ayah():
    ayah_number = random.randint(1, 6236)

    arabic = requests.get(f"https://api.alquran.cloud/v1/ayah/{ayah_number}").json()
    english = requests.get(f"https://api.alquran.cloud/v1/ayah/{ayah_number}/en.sahih").json()

    ar_text = arabic["data"]["text"]
    en_text = english["data"]["text"]
    surah = english["data"]["surah"]["englishName"]
    ayah_num = english["data"]["numberInSurah"]

    return ar_text, en_text, surah, ayah_num

async def send_daily_ayah():
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        ar, en, surah, num = get_random_ayah()
        message = f"📖 **Daily Ayah**\n\n{ar}\n\n**Translation:** {en}\n— Surah {surah}, Ayah {num}"
        await channel.send(message)
    else:
        print("Channel not found. Check CHANNEL_ID.")

@client.event
async def on_ready():
    print(f"{client.user} is online!")
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(send_daily_ayah, "cron", hour=6, minute=0)
    scheduler.start()
    await send_daily_ayah()

client.run(TOKEN)