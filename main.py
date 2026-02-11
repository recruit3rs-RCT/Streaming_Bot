import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv('DISCORD_TOKEN')
STREAM_ROLE_NAME = "Streaming stat"  # Exact role name

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
    Thread(target=run_flask, daemon=True).start()

@bot.event
async def on_voice_state_update(member, before, after):
    if not member.guild:  # Ignore DMs
        return
        
    role = discord.utils.get(member.guild.roles, name=STREAM_ROLE_NAME)
    if role is None:
        return

    # Start streaming: after True, before False, no role yet
    if after.self_stream and not before.self_stream and role not in member.roles:
        try:
            await member.add_roles(role, reason="Started streaming")
            print(f"Added {role.name} to {member}")
        except discord.Forbidden:
            print(f"Missing perms for {member} in {member.guild}")

    # Stop streaming OR disconnect: before True, (after False OR no channel), has role
    elif before.self_stream and (not after.self_stream or after.channel is None) and role in member.roles:
        try:
            await member.remove_roles(role, reason="Stopped streaming/disconnected")
            print(f"Removed {role.name} from {member}")
        except discord.Forbidden:
            print(f"Missing perms to remove {role.name} from {member}")

bot.run(TOKEN)
