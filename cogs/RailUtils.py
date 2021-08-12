import main, discord, difflib
from cogs.RailTraverse import find_kani_route, find_aura_route
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="dest",
                       description="Finds /dest command for KANI system",
                       guild_ids=main.CONFIG["guild_ids"],
                       options=[create_option(name="origin",
                                              description="Enter an origin station",
                                              option_type=3,
                                              required=True),
                                create_option(name="destination",
                                              description="Enter an destination station",
                                              option_type=3,
                                              required=True)
                                ]
                       )
    async def dest(self, ctx: SlashContext, origin: str, destination: str):
        kani_route, kani_dist = find_kani_route(origin.lower(), destination.lower())
        aura_route, aura_dist = find_aura_route(origin.lower(), destination.lower())

        embed = discord.Embed(title="Route from {0} to {1}:".format(origin, destination),
                              color=discord.Color.red())
        if len(kani_route) == 0:
            embed.add_field(name="KANI system:",
                            value="*No route found. Make sure you typed your destinations correctly.*")
        else:
            kani_route = " ".join(kani_route)
            time = int(kani_dist) // 8
            time_min, time_sec = int(time // 60), int(time % 60)
            embed.add_field(name="KANI system:",
                            value="/dest {0} \n\n Travel Time: About {1}m{2}s".format(kani_route, time_min, time_sec))

        if len(aura_route) == 0:
            embed.add_field(name="AURA system:",
                            value="*No route found. Make sure you typed your destinations correctly.*")
        else:
            aura_route = " ".join(aura_route)
            time = int(aura_dist) // 8
            time_min, time_sec = int(time // 60), int(time % 60)
            embed.add_field(name="AURA system:",
                            value="/dest {0} \n\n Travel Time: About {1}m{2}s".format(aura_route, time_min, time_sec))

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(RailUtils(bot))