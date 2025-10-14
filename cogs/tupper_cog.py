from db_management import Tupper
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper
from decorators import log_command

class TupperCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='add_tupper', description="Adds a tupper.")
    @app_commands.guilds(GUILD_ID)
    async def add_tupper(self, interaction: discord.Interaction, bracket: str, character_name: str):
        bracket = bracket.lower()
        conn, cursor = return_db_connection()
        valid_brackets = bracket.endswith(':') 
        discord_id = interaction.user.id
        success_flag = 'failed'
        if not valid_brackets:
            await interaction.response.send_message(f"Make sure that your tupper brackets end with a colon.")
            return
        try: 
            cursor.execute('SELECT character_id FROM characters WHERE name = ?', (character_name,))
            row = cursor.fetchone()
            if not row:
                await interaction.response.send_message(f"Character info could not be found with the provided name. Please run /add_character, or run /my_characters to see the names of your characters.")
                return
            character_id = row[0]
            tupper = Tupper(discord_id, cursor)
            emb_tupper_bracket, emb_character_name = tupper.register_tupper(bracket, character_id)
            command_embed_instance = EmbedWrapper().return_base_embed()
            command_embed_instance.add_field(
                name="Command Output for AddTupper", 
                value=f"Success! \n\n **Player:** {interaction.user.name} \n\n **Tupper:** {emb_tupper_bracket} \n\n **Bound Character:** {emb_character_name}"
            )
            conn.commit()
            await interaction.response.send_message(embed=command_embed_instance)
            success_flag = 'succeeded'
        except Exception as e:
            conn.rollback()
            await interaction.response.send_message(f"Error adding tupper:\n{e}")
        finally:
            log_command(
                conn,
                cursor,
                discord_id,
                'add_tupper',
                f"{success_flag} to register tupper {bracket} for {character_name}."
            )
            conn.close()

    @app_commands.command(name='remove_tupper', description="Removes a tupper.")
    @app_commands.guilds(GUILD_ID)
    async def remove_tupper(self, interaction: discord.Interaction, bracket: str):
        conn, cursor = return_db_connection()
        discord_id = interaction.user.id
        tupper = Tupper(discord_id, cursor)
        success_flag = 'failed'
        if not tupper.tupper_belongs_to_player(bracket):
            await interaction.response.send_message("This tupper does not belong to you.")
            return
        valid_brackets = bracket.endswith(':') 
        if not valid_brackets:
            await interaction.response.send_message(f"Make sure that your tupper brackets end with a colon.")
            return
        try: 
            message = tupper.delete_tupper(bracket)
            conn.commit()
            await interaction.response.send_message(message)
            success_flag = 'succeeded'
        except Exception as e: 
            conn.rollback()
            await interaction.response.send_message(f"Error removing tupper:\n{e}")
        finally: 
            log_command(
                conn,
                cursor,
                discord_id,
                'add_tupper',
                f"{success_flag} to delete tupper {bracket} from their account."
            )
            conn.close()

async def setup(bot): 
    await bot.add_cog(TupperCommands(bot))
