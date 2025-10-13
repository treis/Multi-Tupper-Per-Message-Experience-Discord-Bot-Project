from db_management import AuditLogging
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from secret import admin_role_command_text

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

from db_management import AuditLogging
import discord
from discord import app_commands
from discord.ext import commands
from nbot import return_db_connection, GUILD_ID
from secret import admin_role_command_text

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='logs_by_date',
        description="Returns logs by optional parameters, only usable by admins."
    )
    @app_commands.guilds(GUILD_ID)
    async def query_logs(
        self,
        interaction: discord.Interaction,
        user_mention: discord.Member | None = None,
        command_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None
    ):
        # Admin check
        if admin_role_command_text not in [role.name for role in interaction.user.roles]:
            return await interaction.response.send_message(
                "You do not have permission to use this command."
            )
        
        await interaction.response.defer()
        discord_id = interaction.user.id

        conn, cursor = return_db_connection()
        try:
            audit = AuditLogging(discord_id, cursor)
            target_id = user_mention.id if user_mention else None
            logs = await audit.get_logs(
                discord_id=target_id,
                command_type=command_type,
                start_date=start_date,
                end_date=end_date
            )

            if logs:
                await interaction.followup.send("\n".join(logs))
            else:
                await interaction.followup.send("No logs found.")
        finally:
            conn.close()

async def setup(bot):
   await bot.add_cog(AdminCommands(bot))


async def setup(bot):
   await bot.add_cog(AdminCommands(bot))



