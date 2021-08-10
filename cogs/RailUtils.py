import main, discord, difflib
from cogs.RailTraverse import find_kani_route, kani_json, kani_node
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
        route, dist = find_kani_route(origin.lower(), destination.lower())

        embed = discord.Embed(title="Route from {0} to {1}:".format(origin, destination),
                              color=discord.Color.red())
        # Only supports KANI for right now

        if len(route) == 0:
            embed.add_field(name="KANI system:",
                            value="*No route found. Make sure you typed your destination correctly, use /find [dest]"
                                  "to find your origin route*")
        else:
            route = " ".join([dest.name for dest in route])
            time = int(dist) / 8
            time_min, time_sec = int(time // 60), int(time % 60)
            embed.add_field(name="KANI system:",
                            value="/dest {0} \n\n Travel Time: About {1}m{2}s".format(route, time_min, time_sec))

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(RailUtils(bot))