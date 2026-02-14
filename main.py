import discord
from discord.ext import commands
import os
import asyncio
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
    print("✅ Simple role bot ready with 35s removal delay")
 
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
            print(f"✅ Added {role.name} to {member.name}")
        except discord.Forbidden:
            print(f"⚠️ Missing perms for {member.name} in {member.guild.name}")
 
    # Stop streaming OR disconnect: before True, (after False OR no channel), has role
    elif before.self_stream and (not after.self_stream or after.channel is None) and role in member.roles:
        print(f"⏳ {member.name} stopped streaming, waiting 35 seconds before removing role...")
        
        # Wait 35 seconds to allow LB bot to save time
        await asyncio.sleep(35)
        
        # Fetch fresh member data to check current state
        try:
            fresh_member = await member.guild.fetch_member(member.id)
        except discord.NotFound:
            print(f"⚠️ {member.name} left the server")
            return
        except discord.HTTPException as e:
            print(f"⚠️ Error fetching {member.name}: {e}")
            return
        
        # Check if they're still not streaming after the delay
        if fresh_member.voice and fresh_member.voice.self_stream:
            print(f"↩️ {member.name} started streaming again, keeping role")
            return
        
        # Still not streaming - remove role
        if role in fresh_member.roles:
            try:
                await fresh_member.remove_roles(role, reason="Stopped streaming (35s delay)")
                print(f"❌ Removed {role.name} from {member.name} after 35s delay")
            except discord.Forbidden:
                print(f"⚠️ Missing perms to remove {role.name} from {member.name}")
            except discord.HTTPException as e:
                print(f"⚠️ Error removing role from {member.name}: {e}")
 
bot.run(TOKEN)
