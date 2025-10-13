from db_management import Player
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='my_characters', description="Returns a list of your characters.")
    @app_commands.guilds(GUILD_ID)
    async def see_my_characters(self, interaction: discord.Interaction):
        conn, cursor = return_db_connection()
        discord_id = interaction.user.id
        try:
            player = Player(discord_id, cursor)
            message = player.see_my_characters()
            command_embed_instance = EmbedWrapper().return_base_embed()
            command_embed_instance.add_field(name="Command Output for SeeMyCharacters", value=f"Success! \n\n {message}")
            conn.commit()
            await interaction.response.send_message(embed=command_embed_instance)
        except Exception as e:
            await interaction.response.send_message(f"Error retrieving characters:\n{e}")
        finally: 
            conn.close()

    @app_commands.command(name='register_me', description="Adds you to the database so you can use other functions of the bot.")
    @app_commands.guilds(GUILD_ID)
    async def register_player(self, interaction: discord.Interaction):
        conn, cursor = return_db_connection()
        discord_id = interaction.user.id
        player = Player(discord_id, cursor)
        try: 
            success_message = player.register_player(interaction.user.name)
            conn.commit()
            await interaction.response.send_message(success_message)
        except Exception as e: 
            await interaction.response.send_message(f"You are already in the database, {interaction.user.name}\n{e}")
            conn.rollback()
        finally: 
            conn.close()

async def setup(bot): 
    await bot.add_cog(PlayerCommands(bot))
