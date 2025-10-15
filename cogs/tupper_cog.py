from db_management import Tupper
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from embed import EmbedWrapper
from log_command import log_command
from secret import minor_write_image, failure_image

class TupperCommands(commands.Cog): # create a class for TupperCommand cog with methods that will become commands to be registered in main bot file at the end of this file
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='add_tupper', description="Adds a tupper.")
    @app_commands.guilds(GUILD_ID)
    async def add_tupper(self, interaction: discord.Interaction, bracket: str, character_name: str):
        conn = await return_db_connection() # get conn and cursor from function that exists in main bot file
        valid_brackets = bracket.endswith(':') # check if brackets end with a colon (rule for valid tupperbox brackets)
        discord_id = interaction.user.id # get discord id of the user who invoked the command
        success_flag = 'failed' # create a flag that will presume the command failed unless explicitly changed as a result of a successful commmand
        embed = EmbedWrapper().return_base_embed() # return embed for purposes of sending a message to the user later on

        if not valid_brackets: # return if tupper brackets are malformed
            await interaction.response.send_message(f"Make sure that your tupper brackets end with a colon.") # one-liner error message to be sent in the same channel that invoked the command 
                    
        try: 
            async with conn.execute('SELECT character_id FROM characters WHERE name = ?', (character_name,)) as cursor: # check if character is in the database, return if otherwise, tell user character not in database
                row = await cursor.fetchone()

            if not row:
                await interaction.response.send_message(f"Character info could not be found with the provided name. Please run /add_character, or run /my_characters to see the names of your characters.")
                return
            
            character_id = row[0] # sql-lite returns a tuple that represents a row from characters table , the 0th position will be character_id (an integer)
            tupper = Tupper(discord_id, conn)
            emb_tupper_bracket, emb_character_name = await tupper.register_tupper(bracket, character_id)
            embed.set_image(minor_write_image)
            embed.add_field(
                name="Command Output for AddTupper", 
                value=f"Success! \n\n **Player:** {interaction.user.name} \n\n **Tupper:** {emb_tupper_bracket} \n\n **Bound Character:** {emb_character_name}"
            )
            await interaction.response.send_message(embed=embed) # send built embed
            success_flag = 'succeeded' # all checks succeeded and the database is updated, so edit success_flag from failed to succeeded
            
        except Exception as e:
            embed.set_image(failure_image)
            await conn.rollback() # undo the attempted change 
            await interaction.response.send_message(f"Error adding tupper:\n{e}") # one-liner error message to be sent in the same channel that invoked the command 
            
        finally:
            # build log_coommand to make sure this attempt, 
            await log_command(
                conn,
                None,
                discord_id,
                'add_tupper',
                f"{success_flag} to register tupper {bracket} for {character_name}."
            )

    @app_commands.command(name='remove_tupper', description="Removes a tupper.")
    @app_commands.guilds(GUILD_ID)
    async def remove_tupper(self, interaction: discord.Interaction, bracket: str):
        conn = await return_db_connection()
        discord_id = interaction.user.id
        tupper = Tupper(discord_id, conn)
        success_flag = 'failed'
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
            conn.rollback()
            await interaction.response.send_message(f"Error removing tupper:\n{e}")
        finally: 
            await log_command(
                conn,
                None,
                discord_id,
                'add_tupper',
                f"{success_flag} to delete tupper {bracket} from their account."
            ) 

async def setup(bot): # this asynchronous function must exist in order for the main bot file to be able to register it 
    await bot.add_cog(TupperCommands(bot))
