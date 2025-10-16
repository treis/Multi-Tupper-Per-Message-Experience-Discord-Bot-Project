from db_management import Tupper
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper
from log_command import audit_log
from secret import minor_write_image, failure_image

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
        embed = EmbedWrapper().return_base_embed()
        command_specific_audit_extension = f"added tupper bracket {bracket} to character {character_name}."

        try:
            message = await tupper.register_tupper(bracket, character_name)
            await interaction.response.send_message(f"{message}")

        except Exception as e: 
             await interaction.response.send_message(f"{e}")

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

        if not await tupper.tupper_belongs_to_player(bracket):
            await interaction.response.send_message("This tupper does not belong to you, or, maybe you forgot the colon.")
            return
        valid_brackets = bracket.endswith(':') 
        if not valid_brackets:
            await interaction.response.send_message(f"Make sure that your tupper brackets end with a colon.")
            return
        try: 
            message = await tupper.delete_tupper(bracket)
            await interaction.response.send_message(message)
            success_flag = 'succeeded'
        except Exception as e: 
            await interaction.response.send_message(f"Error removing tupper:\n{e}")
            await conn.rollback()

        return command_specific_audit_extension, success_flag

async def setup(bot): # this asynchronous function must exist in order for the main bot file to be able to register it 
    await bot.add_cog(TupperCommands(bot))