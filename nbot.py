import discord
from discord.ext import commands
import uuid
import os
from os import path
from secret import bot_token
from secret import guild_id
import sqlite3
from create_db import create_db, test_delete_db, Player, Character, Tupper
from embed import EmbedWrapper

### Database

# Create database if not exist, and set up connection
if os.path.exists('guild.db'):
    test_delete_db()  # delete database on re-run
    create_db()       # create db

conn = sqlite3.connect('guild.db', check_same_thread=False)
cursor = conn.cursor()  # create database connection

### Bot

# Set up the bot's intents, guild object, and make sure it can read messages
intents = discord.Intents.default()
intents.message_content = True
GUILD_ID = discord.Object(id=guild_id)

# Set up relevant events and settings
bot = commands.Bot(command_prefix='^', intents=intents)

@bot.event  # give message that says that discord bot is alive 
async def on_ready():
    print("The bot is alive, and the database is operational.")
    await bot.tree.sync(guild=GUILD_ID)
    conn.commit()

@bot.event  # return if user is the one sending a message
async def on_message(message):
    if message.author == bot.user:
        return
    word_count = len(message.content.split())
    tupper_try = message.content.split(":", 1)[0] + ":"
    try:
        tupper = Tupper(message.author.id, cursor)
        tupper.add_xp_by_bracket(word_count, tupper_try)
        conn.commit()
    except Exception as e:
        print(f"Error in on_message:\n{e}")

# User Commands

@bot.tree.command(name='register_me', description="Creates a character for use. Require the following arguments: name, level, starting tupper bracket.", guild=GUILD_ID)
async def RegisterPlayer(interaction: discord.Interaction):
    discord_id = interaction.user.id
    player = Player(discord_id, cursor)
    try: 
        success_message = player.register_player(interaction.user.name)
        conn.commit()
        await interaction.response.send_message(success_message)
    except Exception as e: 
        await interaction.response.send_message(f"You are already in the database, {interaction.user.name}\n{e}")
        return

@bot.tree.command(name='my_characters', description="Returns a list of your characters.", guild=GUILD_ID)
async def SeeMyCharacters(interaction: discord.Interaction):
    discord_id = interaction.user.id
    try:
        player = Player(discord_id, cursor)
        message = player.see_my_characters()
        command_embed_instance = EmbedWrapper().return_base_embed()
        command_embed_instance.add_field(name="Command Output for SeeMyCharacters", value=f"Success! \n\n {message}")
        await interaction.response.send_message(embed=command_embed_instance)
        conn.commit()
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving characters:\n{e}")

@bot.tree.command(name='return_players', description="Returns list of player discord_ids for debugging purposes.", guild=GUILD_ID)
async def ReturnPlayers(interaction: discord.Interaction):
    try:
        cursor.execute("SELECT * FROM players;")
        rows = cursor.fetchall()
        await interaction.response.send_message(rows)
        conn.commit()
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving players:\n{e}")

@bot.tree.command(name='add_character', description="Creates a character", guild=GUILD_ID)
async def AddCharacter(interaction: discord.Interaction, name: str):
    name = name.lower()
    discord_id = interaction.user.id
    character = Character(discord_id, cursor)
    try: 
        message = character.register_character(discord_id, name)
        conn.commit()
        await interaction.response.send_message(message)
    except sqlite3.IntegrityError as e:
        await interaction.response.send_message(f"Error, character name already in use:\n{e}")
    except Exception as e:
        await interaction.response.send_message(f"Error adding character:\n{e}")

@bot.tree.command(name='add_tupper', description="Adds a tupper.", guild=GUILD_ID)
async def AddTupper(interaction: discord.Interaction, bracket: str, character_name: str):
    bracket = bracket.lower()
    valid_brackets = bracket.endswith(':')  # tupper brackets must end with a colon 
    discord_id = interaction.user.id
    if not valid_brackets:
        await interaction.response.send_message(f"Make sure that your tupper brackets end with a colon.")
        return
    try: 
        cursor.execute('SELECT character_id FROM characters WHERE name = ?', (character_name,))
        row = cursor.fetchone()
        if not row:
            await interaction.response.send_message(f"Character info could not be found with the provided name. Please run /addcharacter, or run /my_characters to see the names of your characters.")
            return
        character_id = row[0]
        tupper = Tupper(discord_id, cursor)
        emb_tupper_bracket, emb_character_name = tupper.register_tupper(bracket, character_id)
        command_embed_instance = EmbedWrapper().return_base_embed()
        command_embed_instance.add_field(
            name="Command Output for AddTupper", 
            value=f"Success! \n\n **Player:** {interaction.user.name} \n\n **Tupper:** {emb_tupper_bracket} \n\n **Bound Character:** {emb_character_name}"
        )
        await interaction.response.send_message(embed=command_embed_instance)
        conn.commit()
    except Exception as e:
        await interaction.response.send_message(f"Error adding tupper:\n{e}")

@bot.tree.command(name='remove_tupper', description="Removes a tupper.", guild=GUILD_ID)
async def RemoveTupper(interaction: discord.Interaction, bracket: str):
    valid_brackets = bracket.endswith(':')  # tupper brackets must end with a colon 
    if not valid_brackets:
        await interaction.response.send_message(f"Make sure that your tupper brackets end with a colon.")
        return
    discord_id = interaction.user.id
    try: 
        tupper = Tupper(discord_id, cursor)
        message = tupper.delete_tupper(bracket)
        await interaction.response.send_message(message)
        conn.commit()
    except Exception as e: 
        await interaction.response.send_message(f"Error removing tupper:\n{e}")

@bot.tree.command(name='remove_xp_from_character', description="Command that removes xp by discord_id,", guild=GUILD_ID)
async def RemoveXPFromCharacter(interaction: discord.Interaction, character_name: str, xp: str):
    discord_id = interaction.user.id
    try:  # see if can turn string xp into int xp, if not, return helpful error message
        xp_int = int(xp)
    except ValueError as e: 
        await interaction.response.send_message(f"Please input a number, no decimal points.\n{e}")
        return
    try:
        character = Character(discord_id, cursor)
        message = character.remove_xp(character_name, xp_int, discord_id)
        await interaction.response.send_message(message)
        conn.commit()
    except Exception as e: 
        await interaction.response.send_message(f"Error removing XP:\n{e}")

@bot.tree.command(name='set_level_of_character', description="Command that removes xp by discord_id,", guild=GUILD_ID)
async def SetCharacterLevel(interaction: discord.Interaction, character_name: str, level: str):
    discord_id = interaction.user.id
    try:  # see if can turn string xp into int xp, if not, return helpful error message
        level_int = int(level)
        if not 1 <= level_int <= 20:
            await interaction.response.send_message("Please input a number from 1-20, no decimal points.")
            return
    except ValueError as e:
        await interaction.response.send_message(f"Invalid input:\n{e}")
        return
    try:
        character = Character(discord_id, cursor)
        character.set_level(character_name, level_int, discord_id)
        conn.commit()
        await interaction.response.send_message(f"Character {character_name} level set to {level_int}.")
    except Exception as e: 
        await interaction.response.send_message(f"Error setting level:\n{e}")

@bot.event  # close database connection if bot goes offline
async def shutdown():
    conn.close()

bot.run(bot_token)