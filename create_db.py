import sqlite3
import os

# This file exists to create the database 

def test_delete_db(db_name="guild.db"):
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"Database '{db_name}' deleted successfully.")
    else:
        print(f"Database '{db_name}' does not exist.")


def create_db():
    """Creates the database and tables if they do not exist."""
    conn = sqlite3.connect('guild.db', check_same_thread=False)
    cursor = conn.cursor()

    # Important: enable foreign key support
    conn.execute('PRAGMA foreign_keys = ON')

    # Players table (root reference)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            discord_id TEXT PRIMARY KEY
        )
    ''')

    # Logs table (kept even if player is deleted)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT,
            command_type TEXT NOT NULL,
            command_message TEXT NOT NULL,
            date TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (discord_id) REFERENCES players(discord_id)
        )
    ''')

    # Characters table (deletes when player is deleted)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            character_id INTEGER PRIMARY KEY AUTOINCREMENT,
            xp REAL DEFAULT 0.0 CHECK (xp >= 0),
            discord_id TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            level INTEGER CHECK (level >= 1 AND level <= 20) DEFAULT 1,
            FOREIGN KEY (discord_id) REFERENCES players(discord_id)
                ON DELETE CASCADE
        )
    ''')

    # Admins table (untouched by deletes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            role_name TEXT NOT NULL DEFAULT 'bot master'
        )
    ''')

    # Tupper brackets (delete when character is deleted)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tupper_brackets (
            bracket TEXT NOT NULL,
            character_id INTEGER NOT NULL,
            discord_id TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters(character_id)
                ON DELETE CASCADE,
            FOREIGN KEY (discord_id) REFERENCES players(discord_id),
            UNIQUE (discord_id, bracket)
        )
    ''')

    conn.commit()
    conn.close()
