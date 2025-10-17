from db_management import Character
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
import sqlite3
from log_command import audit_log
from secret import tupper_image, create_success_image, failure_image, delete_image
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
            command_name = 'add_character'
            command_specific_audit_extension = f"create character named {name}."
            
            try: 
                message = await character.register_character(discord_id, name)
                embed = await EmbedWrapper().return_embed(create_success_image, command_name, message)
                await interaction.response.send_message(embed=embed)
                success_flag = 'succeeded'

            except sqlite3.IntegrityError as e:
                message = f"Error, character name already in use."
                embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
                await interaction.response.send_message(embed=embed)

            except Exception as e:
                message = f"Something unexpected went wrong.\n\n {e}"
                embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
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
        command_name = 'rename_character'
        command_specific_audit_extension = f"rename character {character_name} to {new_character_name}"
    
        if not character_id:
            message = "You do not own this character."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            return
        
        try: 
            message = await character.rename_character(character_name, new_character_name)
            embed = await EmbedWrapper().return_embed(tupper_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            success_flag = 'succeed'
    
        except Exception as e:
            message = f"Unexpected error executing {command_name}:\n\n{e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()


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
        command_name = 'delete_character'
        command_specific_audit_extension = f"delete character {character_name}."

        if not character_id:
            message = f"Character **{character_name}** was not found."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            return
            
        try: 
            message = await character.delete_character(character_name, discord_id)
            embed = await EmbedWrapper().return_embed(delete_image, command_name, message)
            await interaction.response.send_message(message)
            success_flag = 'succeed'

        except Exception as e:
            message = f"Unexpected error executing {command_name}:\n\n{e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()

        await conn.close()
        return command_specific_audit_extension, success_flag


    @app_commands.command(name='set_level_of_character', description="Sets character level") 
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def set_level_of_character(self, interaction: discord.Interaction, character_name: str, level: int):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = await character.get_owned_character(character_name)
        success_flag = 'fail'
        command_name = 'set_level_of_character'
        command_specific_audit_extension = f"set level of {character_name} to {level}."

        if not character_id:
            message = f"Character **{character_name}** was not found."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            return

        if not 1 <= level <= 20:
            message = f"**{level}** is not between 1 and 20."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            return
        
        try:
            message = await character.set_level(character_name, level, discord_id)
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            success_flag = 'succeed'

        except Exception as e:
            message = f"Unexpected error executing {command_name}:\n\n{e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()

        await conn.close()    
        return command_specific_audit_extension, success_flag

    @app_commands.command(name='remove_xp_from_character', description="Removes XP from a character name.")  
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def remove_xp_from_character(self, interaction: discord.Interaction, character_name: str, xp: int):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        character = Character(discord_id, conn)
        character_id = await character.get_owned_character(character_name)
        success_flag = 'fail'
        command_name = 'remove_xp_from_character'
        command_specific_audit_extension = f"remove {xp} from character {character_name}."

        if not character_id:
            message = f"Character **{character_name}** was not found."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            return

        if xp < 0:
            message = f"**{xp}** is not greater than 0. Nice try, though."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            return

        try:
            message = await character.remove_xp(character_name, xp, discord_id)
            embed = await EmbedWrapper().return_embed(delete_image, command_name, message)
            await interaction.response.send_message(message)
            success_flag = 'succeed'
            
        except Exception as e:
            message = f"Unexpected error executing {command_name}:\n\n{e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()

        await conn.close()
        return command_specific_audit_extension, success_flag

async def setup(bot):
    await bot.add_cog(CharacterCommands(bot))  # Cog setup
