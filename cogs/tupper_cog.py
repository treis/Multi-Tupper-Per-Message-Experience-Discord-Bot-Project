from db_management import Tupper
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper
from log_command import audit_log
from secret import tupper_image, failure_image

class TupperCommands(commands.Cog): # create a class for TupperCommand cog with methods that will become commands to be registered in main bot file at the end of this file
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='add_tupper', description="Adds a tupper.")
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def add_tupper(self, interaction: discord.Interaction, bracket: str, character_name: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id 
        tupper = Tupper(discord_id, conn)
        success_flag = 'fail'
        command_specific_audit_extension = f"tupper bracket {bracket} to character {character_name}."
        command_name = 'add_tupper'
    
        try:
            message = await tupper.register_tupper(bracket, character_name)
            embed = await EmbedWrapper().return_embed(tupper_image, command_name, message)
            await interaction.response.send_message(embed=embed)

        except Exception as e: 
            message = f"Something unexpected went wrong when adding your tupper:\n\n{e}."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)

        await conn.close()
        return command_specific_audit_extension, success_flag


    @app_commands.command(name='remove_tupper', description="Removes a tupper.")
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def remove_tupper(self, interaction: discord.Interaction, bracket: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        tupper = Tupper(discord_id, conn)
        success_flag = 'fail'
        command_specific_audit_extension = f"removed tupper bracket {bracket}."
        command_name = 'remove_tupper'

        if not await tupper.tupper_belongs_to_player(bracket):
            message = f"You do not own tupper **{bracket}**. Check which ones you own with /my_characters."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
    
        if not bracket.endswith(':'):
            message = f"Your tupper brackets did not end with a colon."
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)

        try: 
            message = await tupper.delete_tupper(bracket)
            embed = await EmbedWrapper().return_embed(tupper_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            success_flag = 'succeed'
    
        except Exception as e:
            message = f"Unexpected error executing {command_name}:\n\n{e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()

        await conn.close()
        return command_specific_audit_extension, success_flag

async def setup(bot): # this asynchronous function must exist in order for the main bot file to be able to register it 
    await bot.add_cog(TupperCommands(bot))