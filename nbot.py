import discord
from discord.ext import commands
import os
from secret import bot_token
from secret import guild_id
import aiosqlite
from create_db import test_delete_db, create_db
import asyncio
from db_management import Tupper

# Create databas guild.db if it does not already exist, and set up connection
if os.path.exists('guild.db'):
    test_delete_db()  # delete database on re-run. Uncomment this and invite catastrophe.
    create_db()       # create db

async def return_db_connection():
    # Creates and returns an aiosqlite connection for use elsewhere
    conn = await aiosqlite.connect('guild.db', check_same_thread=False)
    return conn

### Bot

# Set up the bot's intents, guild object, and make sure it can read messages
intents = discord.Intents.default() 
intents.message_content = True
GUILD_ID = discord.Object(id=guild_id)

# Set up relevant events and settings
bot = commands.Bot(command_prefix='^', intents=intents)

# Events

@bot.event 
async def on_ready(): # executes when the bot comes online
    print(f"Bot is ready! Logged in as {bot.user}")
    await bot.tree.sync(guild=GUILD_ID) # sync commands to discord server

@bot.event
async def on_message(message): # executes every message
    if message.author == bot.user: # if bot sends a command, don't do anything
        return
    conn = await return_db_connection() 
    word_count = len(message.content.split())
    tupper_try = message.content.split(":", 1)[0] + ":" # takes the tupper at the beginning of the string 

    try:
        await Tupper(message.author.id, conn).add_xp_by_bracket(word_count, tupper_try) 
        # make a Tupper object, which subclasses from a Connection (requires discord id and cursor) to the sq-lite server that can run specific commands, querying by discord id

    except Exception as e: # if anything goes wrong, print the error to consoles
        print(f"Error in on_message:\n{e}")
        await conn.rollback() # un-type sql code that may have been written by the cursor in Tupper.add_xp_by_bracket() method

    await bot.process_commands(message) # without this line, none of the other commands that require user input in the cogs will be registered

# Load Cogs (see cogs folder)
async def load_cogs():
    await bot.load_extension("cogs.character_cog") # character_cog.py in cogs
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