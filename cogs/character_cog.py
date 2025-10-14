from db_management import Character
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
import sqlite3
from log_command import log_command

class CharacterCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name='add_character', description="Creates a character") 
    @app_commands.guilds(GUILD_ID) 
    async def add_character(self, interaction: discord.Interaction, name: str):
            name = name.lower()
            conn, cursor = return_db_connection()
            discord_id = interaction.user.id
            character = Character(discord_id, cursor)
            success_flag = 'failed'
            try: 
                message = character.register_character(discord_id, name)
                await interaction.response.send_message(message)
                success_flag = 'succeeded'
            except sqlite3.IntegrityError as e:
                conn.rollback()
                await interaction.response.send_message(f"Error, character name already in use:\n{e}")
            except Exception as e:
                conn.rollback()
                await interaction.response.send_message(f"Error adding character:\n{e}")
            finally: 
                # Call the helper to create a log
                log_command(
                    conn,
                    cursor,
                    discord_id,
                    'create_character',
                    f"{success_flag} to create character {name}."
                )

    @app_commands.command(name='rename_character', description="Renames a character")  
    @app_commands.guilds(GUILD_ID)
    async def rename_character(self, interaction: discord.Interaction, character_name: str, new_character_name: str):
        conn, cursor = return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, cursor)
        character_id = character.get_owned_character(character_name)
        success_flag = 'failed'
        if not character_id:
            await interaction.response.send_message("You do not own this character.")
            success_flag = 'failed'
            return
        try: 
            message = character.rename_character(character_name, new_character_name)
            await interaction.response.send_message(message)
            success_flag = 'succeeded'
        except Exception as e: 
            conn.rollback()
            await interaction.response.send_message(f"Character renaming failed:\n{e}")
        finally:
                # Call the helper to create a log
                log_command(
                    conn,
                    cursor,
                    discord_id,
                    'rename_character',
                    f"{success_flag} to rename {character_name} to {new_character_name}."
                )

    @app_commands.command(name='delete_character', description="Deletes a character") 
    @app_commands.guilds(GUILD_ID)
    async def delete_character(self, interaction: discord.Interaction, character_name: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = character.get_owned_character(character_name)
        success_flag = 'failed'
        if not character_id:
            await interaction.response.send_message("You do not own this character.")
            return
        try: 
            message = character.delete_character(character_name, discord_id)
            await interaction.response.send_message(message)
        except Exception as e: 
            conn.rollback()
            await interaction.response.send_message(f"Character deletion failed:\n{e}")
        finally:
            # Call the helper to create a log
                log_command(
                    conn,
                    cursor,
                    discord_id,
                    'delete_character',
                    f"{success_flag} to delete {character_name}."
                )

    @app_commands.command(name='set_level_of_character', description="Sets character level") 
    @app_commands.guilds(GUILD_ID)
    async def set_level_of_character(self, interaction: discord.Interaction, character_name: str, level: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = character.get_owned_character(character_name)
        success_flag = 'failed'
        if not character_id:
            await interaction.response.send_message("You do not own this character.")
            return
        try:
            level_int = int(level)
            if not 1 <= level_int <= 20:
                await interaction.response.send_message("Please input a number from 1-20.")
                return
        except ValueError as e:
            await interaction.response.send_message(f"Invalid input:\n{e}")
            return
        try:
            character.set_level(character_name, level_int, discord_id)
            conn.commit()
            await interaction.response.send_message(f"Character {character_name} level set to {level_int}.")
            success_flag = 'succeeded'
        except Exception as e: 
            conn.rollback()
            await interaction.response.send_message(f"Error setting level:\n{e}")
        finally:
            # Call the helper to create a log
                log_command(
                    conn,
                    cursor,
                    discord_id,
                    'set_level_of_character',
                    f"{success_flag} to set level of {character_name} to {level}."
                )

    @app_commands.command(name='remove_xp_from_character', description="Removes XP from a character")  
    @app_commands.guilds(GUILD_ID)
    async def remove_xp_from_character(self, interaction: discord.Interaction, character_name: str, xp: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = character.get_owned_character(character_name)
        success_flag = 'failed'
        if not character_id:
            await interaction.response.send_message("You do not own this character.")
            return
        try:
            xp_int = int(xp)
            if xp_int < 0:
                await interaction.response.send_message("XP must be positive.")
                return
        except ValueError as e:
            await interaction.response.send_message(f"Invalid XP input:\n{e}")
            return
        try:
            message = character.remove_xp(character_name, xp_int, discord_id)
            await interaction.response.send_message(message)
            success_flag = 'succeeded'
        except Exception as e: 
            conn.rollback()
            await interaction.response.send_message(f"Error removing XP:\n{e}")
        finally:
            # Call the helper to create a log
                log_command(
                    conn,
                    None,
                    discord_id,
                    'remove_xp',
                    f"{success_flag} to remove {xp} from {character_name}."
                )

async def setup(bot):
    await bot.add_cog(CharacterCommands(bot))  # Cog setup
