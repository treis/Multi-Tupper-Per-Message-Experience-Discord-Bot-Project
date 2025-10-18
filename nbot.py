import discord
from discord.ext import commands
import os
from secret import bot_token, guild_id
import aiosqlite
from create_db import test_delete_db, create_db
import asyncio
from db_management import Tupper

### Bot Setup
intents = discord.Intents.default()
intents.message_content = True
GUILD_ID = discord.Object(id=guild_id)

bot = commands.Bot(command_prefix="^", intents=intents)

# Create database if it doesn't exist
if os.path.exists("guild.db"):
    test_delete_db()  # delete database on re-run
create_db()

# Helper function for DB connection
async def return_db_connection():
    if not hasattr(bot, "db") or bot.db is None:
        bot.db = await aiosqlite.connect("guild.db", check_same_thread=False)
        await bot.db.execute("PRAGMA journal_mode=WAL;")
        await bot.db.commit()
    return bot.db

### Events
@bot.event
async def on_ready():
    if not hasattr(bot, "db") or bot.db is None:
        bot.db = await aiosqlite.connect("guild.db", check_same_thread=False)
        await bot.db.execute("PRAGMA journal_mode=WAL;")
        await bot.db.commit()
    if not hasattr(bot, "db_lock"):
        bot.db_lock = asyncio.Lock()
    print(f"Bot is ready! Logged in as {bot.user}")
    # Sync slash commands
    await bot.tree.sync(guild=GUILD_ID)
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    conn = await return_db_connection()
    word_count = len(message.content.split())
    tupper_try = message.content.split(":", 1)[0] + ":"
    try:
        await Tupper(message.author.id, conn).add_xp_by_bracket(word_count, tupper_try)
    except Exception as e:
        print(f"Error in on_message:\n{e}")
        await conn.rollback()
    await bot.process_commands(message)

### Load Cogs
async def load_cogs():
    await bot.load_extension("cogs.character_cog")
    await bot.load_extension("cogs.tupper_cog")
    await bot.load_extension("cogs.player_cog")
    await bot.load_extension("cogs.admin_cog")

### Main
async def main():
    await load_cogs()
    await bot.start(bot_token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:  # fallback for nested loop issues
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
