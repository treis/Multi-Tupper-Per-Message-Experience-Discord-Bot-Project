from db_management import AuditLogging

def log_command(conn, cursor, discord_id, command_type, command_message):
    try:
        audit = AuditLogging(discord_id, cursor)
        audit.conn = conn  # Ensure AuditLogging can commit
        audit.create_log(discord_id, command_type, command_message)
    except Exception as e:
        print(f"Failed to create log: {e}")
