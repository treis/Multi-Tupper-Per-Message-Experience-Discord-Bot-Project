class Connection:
    """Class that represents a connection to the database, for use in character and player database manipulation."""
    def __init__(self, discord_id : int, cursor):
        self.discord_id = discord_id
        self.cursor = cursor

# dictionary that stores multiplication based on level 

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

# variables used in calculating a base value before multiplication with the above dictionary. See Tupper.add_xp_bracket() for formula used for calculating XP.

xppw = 1
falloff = 1

class AuditLogging(Connection):
    def __init__(self, discord_id: int, cursor):
        super().__init__(discord_id, cursor)

    def create_log(self, discord_id, command_type, command_message):
        """Creates a log for a command given discord_id, command_type, and command_message."""
        self.cursor.execute(
            "INSERT INTO logs (discord_id, command_type, command_message) VALUES (?, ?, ?)",
            (discord_id, command_type, command_message)
        )
        self.conn.commit()

    async def get_logs(self, discord_id=None, command_type=None, start_date=None, end_date=None): # reference admin_cog.py query_logs command
        query = "SELECT discord_id, command_type, command_message, date FROM logs WHERE 1=1"
        params = []

        if discord_id:
            query += " AND discord_id = ?"
            params.append(discord_id)
        if command_type:
            query += " AND command_type = ?"
            params.append(command_type)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        self.cursor.execute(query, tuple(params))
        rows = self.cursor.fetchall()

        logs = [f"<@{r[0]}> {r[2]} - Date **{r[3]}**" for r in rows]
        return logs

class Player(Connection):
    def get_owned_character(self, character_name): # function that is occasionally used to make sure that a player owns a character, usually to stop other players from deleting others' tuppers and characters
        """Checks if a discord_id owns a character."""
        self.cursor.execute(
            "SELECT character_id FROM characters WHERE name = ? AND discord_id = ?",
            (character_name, self.discord_id)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def register_player(self, discord_username): # reference player_cog.py /register_me command 
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
    def get_owned_character(self, name: str):
        """Checks if a discord_id owns a character. Functionally similar to Player.get_owned_character()"""
        self.cursor.execute(
            "SELECT character_id FROM characters WHERE name = ? AND discord_id = ?",
            (name, self.discord_id)
        )
        row = self.cursor.fetchone()
        if not row:
            return None
        return row[0]

    def register_character(self, discord_id, character_name) -> str:
        """Registers a character."""
        self.cursor.execute('INSERT INTO characters (discord_id, name) VALUES (?, ?)', (discord_id, character_name))
        return f"Character named {character_name} has been added to the database."
    
    def remove_xp(self, character_name: str, xp: int, discord_id: int) -> str: 
        """Removes xp from a character by name and discord_id. Not allowed to put xp below 0."""
        self.cursor.execute('''UPDATE characters
                            SET xp = MAX(xp - ?, 0) 
                            WHERE name = ? AND discord_id = ?''', (xp, character_name, discord_id))

        if self.cursor.rowcount == 0: 
            return f"No character named {character_name} found." # no result for name and discord_id

        return f"Character named {character_name} has had {xp} removed from their total. Can check new total with my_characters."
    
    def set_level(self, character_name: str, level: int, discord_id: int) -> str:
        """Set level of character given name, desired level (max 20 - reinforced in database schema), and discord_id."""
        self.cursor.execute('''UPDATE characters
                            SET level = ?
                            WHERE name = ? AND discord_id = ?''', (level, character_name, discord_id))
        
        if self.cursor.rowcount == 0:
            return f"No character named {character_name} found." # no result for name and discord_id

        return f"Character named {character_name} has had their level set to {level}."
    
    def delete_character(self, character_name: str, discord_id: int): 
        """Delete character given character_name and discord_id."""
        self.cursor.execute('''
        DELETE FROM characters
        WHERE name = ? AND discord_id = ?
        ''', (character_name, discord_id))

        if self.cursor.rowcount == 0:
            return f"No character named {character_name} found." # no result for name and discord_id
        
        return f"Character named {character_name} has been deleted."
    
    def rename_character (self, character_name, new_character_name): 
        """Rename character given character name and new character name."""
        self.cursor.execute('''
            UPDATE characters
            SET name = ?
            WHERE name = ?
        ''', (new_character_name, character_name))

        return f"{character_name} has been renamed to {new_character_name}."

class Tupper(Connection):
    def tupper_belongs_to_player(self, tupper_bracket):
        """Verify if tupper belongs to player."""
        self.cursor.execute('''
        SELECT t.bracket
        FROM tupper_brackets t
        JOIN characters c ON t.character_id = c.character_id
        WHERE t.bracket = ? AND c.discord_id = ?
        ''', (tupper_bracket, self.discord_id))
        return self.cursor.fetchone() is not None  # True if tupper belongs to player
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

    def add_xp_by_bracket(self, word_len: int, bracket):
        """Fetch character level from database given word length and tupper bracket."""
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
        rpxp_raw = (word_len * xppw * level_mults[level - 1] / 6) * ((100 - falloff * (level - 3)) / 100) # formula used to calculate XP

        # Add XP to the character
        self.cursor.execute('''
            UPDATE characters
            SET xp = xp + ?
            WHERE character_id = ?
        ''', (round(rpxp_raw, 1), character_id))

        return f"{round(rpxp_raw,1)} XP added to character with tupper {bracket}."