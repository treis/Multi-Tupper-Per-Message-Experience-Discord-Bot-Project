from db_management import Player
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper
from log_command import log_command
from embed import EmbedWrapper
from secret import create_success_image, failure_image, see_characters_image

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='my_characters', description="Returns a list of your characters.")
    @app_commands.guilds(GUILD_ID)
    async def see_my_characters(self, interaction: discord.Interaction):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        player = Player(discord_id, conn)
        success_flag = 'failed'
        embed = EmbedWrapper().return_base_embed()
        try:
            message = await player.see_my_characters()
            embed.set_image(url=see_characters_image)
            embed.add_field(name="Command Output for my_characters", value=f"Success! \n\n {message}")
            await interaction.response.send_message(embed=embed)
            success_flag = 'succeeded'

        except Exception as e:
            message = f"Error retrieving characters:\n{e}"
            embed.set_thumbnail(url=failure_image)
            embed.add_field(name="Command Output for my_characters", value=f"Failure. \n\n {message}")
            await interaction.response.send_message(embed=embed)

        finally:
            await log_command(
                conn,
                None,
                discord_id,
                'see_my_characters',
                f"{success_flag} to see characters of {discord_id}."
            )
    
    @app_commands.command(name='register_me', description="Adds you to the database so you can use other functions of the bot.")
    @app_commands.guilds(GUILD_ID)
    async def register_player(self, interaction: discord.Interaction):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        player = Player(discord_id, conn)
        success_flag = 'failed'
        embed = EmbedWrapper().return_base_embed()
        try: 
            message = await player.register_player(interaction.user.name)
            embed.set_image(url=create_success_image)
            embed.add_field(name="Command Output for register_player", value=f"Success! \n\n {message}")
            await interaction.response.send_message(embed=embed)
            success_flag = 'succeeded'

        except Exception as e: 
            message = f"Either you are already in the database, or something else went wrong: \n\n ```{e}```"
            embed.set_thumbnail(url=failure_image)
            embed.add_field(name="Command Output for register_player", value=f"Failure. \n\n {message}")
            await interaction.response.send_message(embed=embed)
            success_flag = 'failed'
            await conn.rollback()
    
        finally:
            await log_command(
                conn,
                NotImplemented,
                discord_id,
                'register_player',
                f"{success_flag} to register themselves as a player."
            )

async def setup(bot): 
    await bot.add_cog(PlayerCommands(bot))
