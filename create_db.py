import sqlite3
import os

def test_delete_db(): 
    if os.path.exists('guild.db'):
        os.remove('guild.db')

def create_db(): # create database upon initializing nbot.py
    conn = sqlite3.connect('guild.db', check_same_thread=False)
    cursor = conn.cursor()
    conn.execute('PRAGMA foreign_keys = ON')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            discord_id TEXT PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            character_id INTEGER PRIMARY KEY AUTOINCREMENT,
            xp REAL DEFAULT 0.0 CHECK (xp >= 0),
            discord_id TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            level INTEGER CHECK (level >= 1 AND level <= 20) DEFAULT 1,
            FOREIGN KEY (discord_id) REFERENCES players(discord_id)
                ON DELETE RESTRICT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tupper_brackets (
            bracket TEXT NOT NULL,
            character_id INTEGER NOT NULL,
            discord_id TEXT NOT NULL,
            FOREIGN KEY (character_id) REFERENCES characters(character_id)
                ON DELETE CASCADE,
            FOREIGN KEY (discord_id) REFERENCES players(discord_id)
                ON DELETE RESTRICT,
            UNIQUE (discord_id, bracket)
        )
    ''')

    conn.commit() # commit created database
    conn.close() # close connection


# dictionary to help calculate xp value

level_mults = {
            0: 1.0,
            1: 1.0,           # Level 1 → 2
            2: 2.0,           # Level 2 → 3
            3: 6.0,           # Level 3 → 4
            4: 12.66,         # Level 4 → 5
            5: 24.922,        # Level 5 → 6
            6: 29.9064,       # Level 6 → 7
            7: 36.4938,       # Level 7 → 8
            8: 46.3031,       # Level 8 → 9
            9: 52.7855,       # Level 9 → 10
            10: 69.148,        # Level 10 → 11
            11: 49.0941,       # Level 11 → 12
            12: 65.2891,       # Level 12 → 13
            13: 65.2891,       # Level 13 → 14
            14: 81.6114,       # Level 14 → 15
            15: 97.9337,       # Level 15 → 16
            16: 97.9337,       # Level 16 → 17
            17: 130.2558,      # Level 17 → 18
            18: 130.2558,      # Level 18 → 19
            19: 162.8197       # Level 19 → 20
}

# xppw = xppw per word, faloff = 1
xppw = 1
falloff = 1

class Connection:
    """Class that represents a connection to the database, for use in character and player database manipulation."""
    def __init__(self, discord_id : int, cursor):
        self.discord_id = discord_id
        self.cursor = cursor

class Player(Connection):
    def register_player(self, discord_username):
        """Registers a player."""
        self.cursor.execute('INSERT INTO players (discord_id) VALUES (?)', (self.discord_id,))
        return f"Player {self.discord_id} ({discord_username}) has been added to the database."

    def see_my_characters(self) -> str:
        """Displays character list with level, XP, and tupper brackets by discord_id."""

        # Get all characters for this player along with their level and XP
        self.cursor.execute('SELECT name, character_id, level, xp FROM characters WHERE discord_id = ?', (self.discord_id,))
        all_characters = self.cursor.fetchall()  # list of tuples (name, character_id, level, xp)

        # Get all tupper brackets for this player
        self.cursor.execute('''
            SELECT characters.name, tupper_brackets.bracket
            FROM characters
            JOIN tupper_brackets ON tupper_brackets.character_id = characters.character_id
            WHERE characters.discord_id = ?
        ''', (self.discord_id,))
        results = self.cursor.fetchall()  # list of tuples (name, bracket)

        # Build dictionary of character -> brackets
        characters_with_tuppers = {}
        character_info = {}  # store level and xp for each character
        for name, _id, level, xp in all_characters:
            characters_with_tuppers[name] = []  # Initialize empty list for brackets
            character_info[name] = {"level": level, "xp": xp}  # store level and xp

        for name, bracket in results:
            characters_with_tuppers.setdefault(name, []).append(bracket)

        # Build return message
        return_message = ''
        for character_name, brackets in characters_with_tuppers.items():
            level = character_info[character_name]["level"]
            xp = character_info[character_name]["xp"]
            if brackets:
                return_message += f'**{character_name} (Level {level}, XP {xp})** :\n ```{", ".join(brackets)}```\n'
            else:
                return_message += f'**{character_name} (Level {level}, XP {xp})** :\n ```no tuppers``` \n'

        return return_message

class Character(Connection):
    def register_character(self, discord_id, character_name) -> str:
        """Registers a character."""
        self.cursor.execute('INSERT INTO characters (discord_id, name) VALUES (?, ?)', (discord_id, character_name))
        return f"Character named {character_name} has been added to the database."
    
    def remove_xp(self, character_name: str, xp: int, discord_id: int) -> str: 
        self.cursor.execute('''UPDATE characters
                            SET xp = MAX(xp - ?, 0)
                            WHERE name = ? AND discord_id = ?''', (xp, character_name, discord_id))

        if self.cursor.rowcount == 0:
            return f"No character named {character_name} found." # no result for name and discord_id

        return f"Character named {character_name} has had {xp} removed from their total. Can check new total with my_characters."
    
    def set_level(self, character_name: str, level: int, discord_id: int) -> str:
        self.cursor.execute('''UPDATE characters
                            SET level = ?
                            WHERE name = ? AND discord_id = ?''', (level, character_name, discord_id))
        
        if self.cursor.rowcount == 0:
            return f"No character named {character_name} found." # no result for name and discord_id

        return f"Character named {character_name} has had their level set to {level}."
    
class Tupper(Connection):
    def register_tupper(self, bracket, character_id):
        """Register a tupper bracket. Brackets may not be re-used across a player."""
        self.cursor.execute('INSERT INTO tupper_brackets (bracket, character_id, discord_id) VALUES (?, ?, ?)', (bracket, character_id, self.discord_id))
        self.cursor.execute('SELECT name FROM characters WHERE character_id = ?', (character_id,))
        character_name = self.cursor.fetchall()[0][0]
        return bracket, character_name

    def delete_tupper(self, bracket):
        """Delete a tupper bracket."""
        self.cursor.execute('''
            DELETE FROM tupper_brackets
            WHERE discord_id = ? AND bracket = ?
        ''', (self.discord_id, bracket))

        return f"Tupper {bracket} deleted."

    def add_xp_by_bracket(self, word_len, bracket):
        # Fetch character level from database
        self.cursor.execute('''
            SELECT c.level, c.character_id
            FROM characters c
            JOIN tupper_brackets t ON c.character_id = t.character_id
            WHERE t.bracket = ? AND t.discord_id = ?
        ''', (bracket, self.discord_id))

        result = self.cursor.fetchone()
        if not result:
            return f"No character found for tupper {bracket}."

        level, character_id = result

        # Calculate XP
        rpxp_raw = (word_len * xppw * level_mults[level - 1] / 6) * ((100 - falloff * (level - 3)) / 100)

        # Add XP to the character
        self.cursor.execute('''
            UPDATE characters
            SET xp = xp + ?
            WHERE character_id = ?
        ''', (round(rpxp_raw, 1), character_id))

        return f"{round(rpxp_raw,1)} XP added to character with tupper {bracket}."
