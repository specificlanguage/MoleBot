import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from cogs.RailTraverse import find_kani_route, find_aura_route, kani_node, aura_node, aura_json


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="dest",
                       description="Finds /dest command for KANI system",
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

        if len(kani_route) <= 0:
            embed.add_field(name="KANI system:",
                            value="*No route found. Make sure you typed your destinations correctly.*")
        else:
            notices = ""
            if kani_node(origin).switch:
                notices += "*KANI Notice: You are routing from a switch.*\n"
            if kani_node(destination).switch:
                notices += "*KANI Notice: You are routing to a switch. You will need to disembark manually.*\n"

            kani_route = " ".join(kani_route)
            time = int(kani_dist) // 8
            time_min, time_sec = int(time // 60), int(time % 60)
            embed.add_field(name="KANI system:",
                            value="/dest {0} \n\n{1}\n Travel Time: About {2}m{3}s \n Distance: {4}m".
                            format(kani_route, notices, time_min, time_sec, int(kani_dist)))

        if len(aura_route) <= 0:
            embed.add_field(name="AURA system:",
                            value="*No route found. Make sure you typed your destinations correctly.\n"
                                  "You may also be routing from a switch/destination/line in AURA.*")

        else:
            notices = ""  # FYI for later

            aura_origin = aura_node(origin)
            aura_dest = aura_node(destination)
            valid_stops = ["stop", "junctionstop", "stopjunction"]

            if aura_origin.name + "-surface" in aura_json["nodes"]:
                notices += "*AURA Notice: Your origin has a surface station that you may want to check for better " \
                           "routes. Add '(surface)' to your origin input.*\n "
            if aura_dest.name + "-surface" in aura_json["nodes"]:
                notices += "*AURA Notice: Your destination has a surface station that you may want to check for " \
                           "better routes. Add '(surface)' to your destination input.*\n"
            if aura_dest.type not in valid_stops:
                notices += "*AURA Notice: You are not routing to a stop.*\n"

            aura_route = " ".join(aura_route)
            time = int(aura_dist) // 8
            time_min, time_sec = int(time // 60), int(time % 60)
            embed.add_field(name="AURA system:",
                            value="/dest {0} \n\n{1}\n Travel Time: About {2}m{3}s \n Distance: {4}m".
                            format(aura_route, notices, time_min, time_sec, int(aura_dist)))

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(RailUtils(bot))
