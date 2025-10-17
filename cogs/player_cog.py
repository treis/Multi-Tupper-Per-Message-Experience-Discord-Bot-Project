from db_management import Player
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper
from log_command import audit_log
from embed import EmbedWrapper
from secret import failure_image, see_characters_image, tupper_image

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name='my_characters', description="Returns a list of your characters.")
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def see_my_characters(self, interaction: discord.Interaction):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        player = Player(discord_id, conn)
        success_flag = 'fail'
        command_specific_audit_extension = ""
        command_name = 'see_my_characters'

        try:
            message = await player.see_my_characters()
            embed = await EmbedWrapper().return_base_embed()
            embed.set_thumbnail(url=see_characters_image)
            embed.add_field(name=f"Command Output {command_name}", value=f"{message}")
            # overriding EmbedWrapper() in only this instance to make sure code block appears correctly.
            await interaction.response.send_message(embed=embed)
            success_flag = 'succeeded'

        except Exception as e: 
            message = f"Either you are already in the database, or something else went wrong: \n {e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()

        await conn.close()
        return command_specific_audit_extension, success_flag
    

    @app_commands.command(name='register_me', description="Adds you to the database so you can use other functions of the bot.")
    @app_commands.guilds(GUILD_ID)
    @audit_log
    async def register_player(self, interaction: discord.Interaction):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        player = Player(discord_id, conn)
        success_flag = 'fail'
        command_specific_audit_extension = ""
        command_name = 'register_me'

        try: 
            message = await player.register_player(interaction.user.name)
            embed = await EmbedWrapper().return_embed(tupper_image, command_name, message)
            success_flag = 'succeed'
            await interaction.response.send_message(embed=embed)
    
        except Exception as e: 
            message = f"Either you are already in the database, or something else went wrong: \n {e}"
            embed = await EmbedWrapper().return_embed(failure_image, command_name, message)
            await interaction.response.send_message(embed=embed)
            await conn.rollback()
    
        await conn.close()
        return command_specific_audit_extension, success_flag

async def setup(bot): 
    await bot.add_cog(PlayerCommands(bot))
