from db_management import AuditLogging

# This file houses the log_command function that is re-used across cog commands in order to create logs for each command

def log_command(conn, cursor, discord_id, command_type, command_message):

    # Ex) conn | cursor | 131313123213 | create_character | successfully created a character named bobby

    try:
        audit = AuditLogging(discord_id, cursor) # generate AuditLogging object given discord_id and sql-lite cursor, refer to db_management to see AuditLogging.create_log()
        audit.conn = conn  # Ensure AuditLogging has a connection
        audit.create_log(discord_id, command_type, command_message) # create a log 

    except Exception as e:
        print(f"Failed to create log: {e}") # print error to console in case log is not created

