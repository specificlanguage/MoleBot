import discord
import re
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from cogs.rails.RailTraverse import *
from cogs.rails.RailHelpers import *


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        get_aura_json.start()
        get_kani_json.start()

    @cog_ext.cog_slash(name="dest", description="Finds /dest commands",
                       options=[create_option(name="origin", description="Enter an origin station",
                                              option_type=3, required=True),
                                create_option(name="destination", description="Enter an destination station",
                                              option_type=3, required=True)])
    async def dest(self, ctx: SlashContext, origin: str, destination: str):
        """Discord slash ommand handler for /dest [origin] [destination]. Calls many functions to determine optimal
        route, then sends an embed to the sender showing best routes."""

        # Get info, return error if same
        origin, destination = origin.lower(), destination.lower()
        embed = discord.Embed(title="Route from {0} to {1}:".format(origin, destination), color=discord.Color.red())
        if origin == destination:
            embed.add_field(name="No route found!", value="You can't have the same origin and destination!")

        kani_route, kani_dist = find_kani_route(origin, destination)
        aura_route, aura_dist = find_aura_route(origin, destination)

        # No routes found!
        if len(kani_route) == 0:
            orig_aliases, dest_aliases = find_alias(origin), find_alias(destination)
            orig_aliases.update(names_close_to(origin))
            dest_aliases.update(names_close_to(destination))
            embed.add_field(name="No KANI route found!", value=handle_not_found(orig_aliases, dest_aliases))
                
        # Routing formatting
        elif len(kani_route) > 0:
            embed.add_field(name="KANI system:", value=kani_formatting(kani_route, kani_dist))
        if len(aura_route) > 0:
            embed.add_field(name="AURA system:", value=aura_formatting(aura_route, aura_dist))

        # Footer, No Routes Found
        embed.set_footer(text="See amel.pw/kani or auracc.github.io for more information!")

        if len(embed.fields) == 0:
            embed.add_field(name="No routes found!",
                            value="No routes found! Check that you spelled your origin/destination correctly.")
            logging.info("No route found between {0} and {1}".format(origin, destination))

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_slash(name="finddests",
                       description="Finds closest /dest locations to use",
                       options=[create_option(name="x", description="Civclassic x-coordinate to search",
                                              option_type=4, required=True),
                                create_option(name="z", description="CivClassic z-coordinate to search",
                                              option_type=4, required=True)])
    async def finddests(self, ctx: SlashContext, x: int, z: int):
        dests = find_closest_dests(x, z)
        if len(dests) == 0:
            await ctx.send("You're searching for nodes outside of the map!", hidden=True)
            return
        out = ""

        longest_len = max([len(item.get("name")) for item in dests])

        for item in dests:
            nations = re.sub("\\n.*$", repl="", string=item.get("nation"))
            info = "{0} blocks {1} {2} {3} ({4}, {5})".format(str(int(item.get("distance"))).rjust(4, " "),
                                                              item.get("direction").ljust(5, " "),
                                                              item.get("name").ljust(longest_len + 2, " "),
                                                              "".join(nations).ljust(22, " "),
                                                              item.get("x"), item.get("z"))
            info = "@".ljust(2, " ") + info if item.get("links") >= 3 else "".ljust(2, " ") + info
            out += info + "\n"
        await ctx.send("**Dests near ({0}, {1}):**\nSee also: <https://amel.pw/kani> ```py\n{2}```"
                       .format(str(x), str(z), out), embed=None, hidden=True)


def setup(bot):
    bot.add_cog(RailUtils(bot))
