import discord
from discord.ext import commands
import os
from os import path
from secret import bot_token
from secret import guild_id
import sqlite3
from create_db import test_delete_db, create_db
import asyncio
from db_management import Tupper

### Database

# Create database if not exist, and set up connection
if os.path.exists('guild.db'):
    test_delete_db()  # delete database on re-rune
    create_db()       # create db

def return_db_connection(): 
    conn = sqlite3.connect('guild.db', check_same_thread=False)
    cursor = conn.cursor()  # create database connections
    return conn, cursor

### Bot

# Set up the bot's intents, guild object, and make sure it can read messages
intents = discord.Intents.default()
intents.message_content = True
GUILD_ID = discord.Object(id=guild_id)

# Set up relevant events and settings
bot = commands.Bot(command_prefix='^', intents=intents)

# Events

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    await bot.tree.sync(guild=GUILD_ID)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    conn, cursor = return_db_connection()
    word_count = len(message.content.split())
    tupper_try = message.content.split(":", 1)[0] + ":"

    try:
        tupper = Tupper(message.author.id, cursor)
        tupper.add_xp_by_bracket(word_count, tupper_try)
        conn.commit()
    except Exception as e:
        print(f"Error in on_message:\n{e}")
        conn.rollback()
    finally:
        conn.close()

    await bot.process_commands(message)

# Load Cogs
async def load_cogs():
    await bot.load_extension("cogs.character_cog")
    await bot.load_extension("cogs.tupper_cog")
    await bot.load_extension("cogs.player_cog")
    await bot.load_extension("cogs.admin_cog")

# Start the bot
async def main():
    await load_cogs()
    await bot.start(bot_token)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError: 
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()