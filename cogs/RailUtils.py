from cogs.RailFinder import find_kani_route
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    

def setup(bot):
    bot.add_cog(RailUtils(bot))