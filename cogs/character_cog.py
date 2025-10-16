from db_management import Character
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
import sqlite3
from log_command import audit_log
from secret import create_success_image, failure_image
from embed import EmbedWrapper

class CharacterCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name='add_character', description="Creates a character") 
    @app_commands.guilds(GUILD_ID) 
    @audit_log
    async def add_character(self, interaction: discord.Interaction, name: str):
            name = name.lower()
            conn = await return_db_connection()
            discord_id = interaction.user.id
            character = Character(discord_id, conn)
            success_flag = 'fail'
            embed = EmbedWrapper().return_base_embed()
            command_specific_audit_extension = f"create character named {name}."
            
            try: 
                message = await character.register_character(discord_id, name)
                embed.set_thumbnail(url=create_success_image)
                embed.add_field(name="Command Output for add_character", value=f"Success! \n\n {message}")
                await interaction.response.send_message(embed=embed)
                success_flag = 'succeeded'

            except sqlite3.IntegrityError as e:
                message = f"Error, character name already in use:\n{e}"
                embed.set_thumbnail(url=failure_image)
                embed.add_field(name="Command Output for add_character", value=f"Failure. \n\n {e}")
                await interaction.response.send_message(embed=embed)

            except Exception as e:
                message = f"Something unexpected went wrong.\n\n ```{e}```"
                embed.set_thumbnail(url=failure_image)
                embed.add_field(name="Command Output for add_character", value=f"Failure. \n\n {e}")
                await interaction.response.send_message(embed=embed)
            
            return command_specific_audit_extension, success_flag

    @app_commands.command(name='rename_character', description="Renames a character")  
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def rename_character(self, interaction: discord.Interaction, character_name: str, new_character_name: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = await character.get_owned_character(character_name)
        success_flag = 'fail'
        command_specific_audit_extension = f"rename character {character_name} to {new_character_name}"
    
        if not character_id:
            await interaction.response.send_message("You do not own this character.")
            return
        try: 
            message = character.rename_character(character_name, new_character_name)
            await interaction.response.send_message(message)
            success_flag = 'succeed'
        except Exception as e:
             await interaction.response.send_message(e)

        return command_specific_audit_extension, success_flag
        

    @app_commands.command(name='delete_character', description="Deletes a character") 
    @app_commands.guilds(GUILD_ID)
    @audit_log 
    async def delete_character(self, interaction: discord.Interaction, character_name: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = await character.get_owned_character(character_name)
        success_flag = 'fail'
        command_specific_audit_extension = f"delete character {character_name}."

        if not character_id:
            await interaction.response.send_message("You do not own this character.")
            return
        try: 
            message = await character.delete_character(character_name, discord_id)
            await interaction.response.send_message(message)
        except Exception as e: 
            await interaction.response.send_message(f"Character deletion failed:\n{e}")

        return command_specific_audit_extension, success_flag


    @app_commands.command(name='set_level_of_character', description="Sets character level") 
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def set_level_of_character(self, interaction: discord.Interaction, character_name: str, level: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = await character.get_owned_character(character_name)
        success_flag = 'fail'
        command_specific_audit_extension = f"set level of {character_name} to {level}."

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
            await character.set_level(character_name, level_int, discord_id)
            await interaction.response.send_message(f"Character {character_name} level set to {level_int}.")
            success_flag = 'succeed'
        except Exception as e: 
            await interaction.response.send_message(f"Error setting level:\n{e}")
            await conn.rollback()
            
            return command_specific_audit_extension, success_flag

    @app_commands.command(name='remove_xp_from_character', description="Removes XP from a character name.")  
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def remove_xp_from_character(self, interaction: discord.Interaction, character_name: str, xp: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = await character.get_owned_character(character_name)
        success_flag = 'fail'
        command_specific_audit_extension = f"remove {xp} from character {character_name}."

        if not character_id:
            await interaction.response.send_message("Please type a character name.  You can check the ones you own with /see_my_characters.")
            return
        try:
            xp_int = int(xp)
            if xp_int < 0:
                await interaction.response.send_message("XP must be positive.")
                return
        except ValueError as e:
            await interaction.response.send_message(f"Invalid XP input:\n{e}")
            await conn.rollback()

        try:
            message = await character.remove_xp(character_name, xp_int, discord_id)
            await interaction.response.send_message(message)
            success_flag = 'succeeded'
            
        except Exception as e: 
            await interaction.response.send_message(f"Error removing XP:\n{e}")
            await conn.rollback()

        return command_specific_audit_extension, success_flag

async def setup(bot):
    await bot.add_cog(CharacterCommands(bot))  # Cog setup
