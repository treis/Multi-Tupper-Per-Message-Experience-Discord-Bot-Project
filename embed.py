import discord
from datetime import datetime
from secret import *
from secret import footer_text

class EmbedWrapper():
    def __init__(self):

        embed = discord.Embed(
            title='',
            description='',
            url='',
            color=discord.Color.random(),
            timestamp=datetime.now()
        )   

        self.embed = embed

    def return_base_embed(self): 
        # self.embed.add_field(name="Field name", value="Bottom Text")
        # self.embed.add_field(name="Non-inline field name", value="The number of inline fields that can shown on the same row is limited to 3", inline=False)
        self.embed.set_author(name=bot_author, url='', icon_url=modron_token)
        # self.embed.set_image(url=modron_full)
        self.embed.set_thumbnail(url=modron_full)
        self.embed.set_footer(text=footer_text, icon_url=modron_token)
        return self.embed

