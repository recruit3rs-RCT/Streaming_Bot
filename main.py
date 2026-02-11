import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv('DISCORD_TOKEN')  # Secure env var
STREAM_ROLE_NAME = "Streaming stat"

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask('')

@app.route('/')
def home():
    return "Bot alive!"

def run_flask():
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    Thread(target=run_flask, daemon=True).start()  # Start web server

@bot.event
async def on_voice_state_update(member, before, after):
    role = discord.utils.get(member.guild.roles, name=STREAM_ROLE_NAME)
    if role is None:
        return

    # Started streaming
    if not before.self_stream and after.self_stream:
        if role not in member.roles:
            await member.add_roles(role, reason="User started streaming")

    # Stopped streaming
    elif before.self_stream and not after.self_stream:
        if role in member.roles:
            await member.remove_roles(role, reason="User stopped streaming")

bot.run(TOKEN)
