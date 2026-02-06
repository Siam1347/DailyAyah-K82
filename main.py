import discord
from discord import app_commands
import requests
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import os
from flask import Flask
import threading
import time

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

timezone = pytz.timezone("Asia/Dhaka")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---------------- Ayah Helpers ----------------

def get_ayah(surah, ayah):
    data = requests.get(
        f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.sahih"
    ).json()
    ar = requests.get(
        f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}"
    ).json()

    return (
        ar["data"]["text"],
        data["data"]["text"],
        data["data"]["surah"]["englishName"],
        ayah,
        data["data"]["surah"]["numberOfAyahs"]
    )

def get_random_ayah():
    surah = random.randint(1, 114)
    ayah = random.randint(1, 7)
    return get_ayah(surah, ayah)

# ---------------- Button View ----------------

class AyahView(discord.ui.View):
    def __init__(self, surah, ayah, max_ayah):
        super().__init__(timeout=120)
        self.surah = surah
        self.ayah = ayah
        self.max_ayah = max_ayah

    @discord.ui.button(label="Next Ayah ▶", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ayah + 1 > self.max_ayah:
            await interaction.response.send_message(
                "End of this Surah.", ephemeral=True
            )
            return

        self.ayah += 1
        ar, en, surah_name, num, max_ayah = get_ayah(self.surah, self.ayah)

        await interaction.response.edit_message(
            content=(
                f"📖 **Surah {surah_name} – Ayah {num}**\n\n"
                f"{ar}\n\n**Translation:** {en}"
            ),
            view=self
        )

# ---------------- Slash Commands ----------------

@tree.command(name="ayah", description="Get a random Quran ayah")
async def ayah(interaction: discord.Interaction):
    ar, en, surah, num, max_ayah = get_random_ayah()
    await interaction.response.send_message(
        f"📖 **Surah {surah} – Ayah {num}**\n\n{ar}\n\n**Translation:** {en}",
        view=AyahView(random.randint(1,114), num, max_ayah)
    )

@tree.command(name="surah", description="Get ayahs from a specific surah")
@app_commands.describe(number="Surah number (1–114)")
async def surah(interaction: discord.Interaction, number: int):
    if not 1 <= number <= 114:
        await interaction.response.send_message("Invalid surah number.", ephemeral=True)
        return

    ar, en, surah_name, num, max_ayah = get_ayah(number, 1)
    await interaction.response.send_message(
        f"📖 **Surah {surah_name} – Ayah 1**\n\n{ar}\n\n**Translation:** {en}",
        view=AyahView(number, 1, max_ayah)
    )

# ---------------- Daily Ayah ----------------

async def send_daily_ayah():
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        ar, en, surah, num, _ = get_random_ayah()
        await channel.send(
            f"📖 **Daily Ayah**\n\n{ar}\n\n**Translation:** {en}"
        )

# ---------------- Ready Event ----------------

@client.event
async def on_ready():
    await tree.sync()
    print("Commands synced.")
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(send_daily_ayah, "cron", hour=6, minute=0)
    scheduler.start()

# ---------------- Flask (Render keepalive) ----------------

app = Flask("")

@app.route("/")
def home():
    return "Bot running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- Start Bot ----------------

client.run(TOKEN)
