from db_management import AuditLogging
from functools import wraps
from nbot import return_db_connection

# This file houses the log_command function that is re-used across cog commands in order to create logs for each command

async def log_command(conn, cursor, discord_id, command_type, command_message):

    # Ex) conn | cursor | 131313123213 | create_character | successfully created a character named bobby
    try:
        audit = AuditLogging(discord_id, cursor) # generate AuditLogging object given discord_id and sql-lite cursor, refer to db_management to see AuditLogging.create_log()
        audit.conn = conn  # Ensure AuditLogging has a connection
        await audit.create_log(discord_id, command_type, command_message) # create a log 
    except Exception as e:
        print(f"Failed to create log: {e}") # print error to console in case log is not created

def audit_log(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        command_specific_audit_extension, audit_success = await func(*args, **kwargs) # run audit command first, return string saying whether or not it succeed | fail
        interaction = args[1]
        discord_id = interaction.user.id
        command_type = interaction.command.name
        conn = await return_db_connection()

        try:
            audit = AuditLogging(discord_id, conn) # generate AuditLogging object given discord_id and sql-lite cursor, refer to db_management to see AuditLogging.create_log()
            audit_log = f"{audit_success}ed to run {command_type}" + command_specific_audit_extension
            await audit.create_log(discord_id, command_type, audit_log) # create a log 

        except Exception as e:
            print(f"Failed to create log: {e}") # print error to console in case log is not created
            await conn.rollback()
            
    return wrapper

