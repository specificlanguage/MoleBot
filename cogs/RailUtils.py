import discord
import logging
import re
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from cogs.rails.RailTraverse import find_kani_route, find_aura_route, \
    kani_node, aura_node, AURA_JSON, get_aura_json, get_kani_json, get_advisories
from cogs.rails.RailHelpers import find_closest_dests, names_close_to


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        get_aura_json.start()
        get_kani_json.start()

    @cog_ext.cog_slash(name="dest",
                       description="Finds /dest commands",
                       options=[create_option(name="origin",
                                              description="Enter an origin station",
                                              option_type=3,
                                              required=True),
                                create_option(name="destination",
                                              description="Enter an destination station",
                                              option_type=3,
                                              required=True)])
    async def dest(self, ctx: SlashContext, origin: str, destination: str):
        origin, destination = origin.lower(), destination.lower()
        kani_route, kani_dist = find_kani_route(origin, destination)
        aura_route, aura_dist = find_aura_route(origin, destination)

        kani_notices = get_advisories(kani_route)

        embed = discord.Embed(title="Route from {0} to {1}:".format(origin, destination),
                              color=discord.Color.red())

        if origin == destination:
            embed.add_field(name="No route found!", value="You're at your destination already!")

        notices = ""  # FYI for later

        # ------------------------------------
        # KANI Routing
        # Destination not found -- try to search for names close to it
        if len(kani_route) == 0:
            out = ""
            origin_names = names_close_to(origin)
            destination_names = names_close_to(destination)
            if len(origin_names) > 0 and kani_node(origin) is None:
                out += "*Error*:\n Did you mean **{0}** for your origin?\n" \
                    .format("** or **".join([dest for dest in names_close_to(origin)]))
            if len(destination_names) > 0 and kani_node(destination) is None:
                out += "*Error*:\n Did you mean **{0}** for your destination?\n" \
                    .format("** or **".join([dest for dest in names_close_to(origin)]))
            if out != "":
                embed.add_field(name="KANI system:", value=out)

        # Route found
        elif len(kani_route) > 0:
            notices = "".join([f"> -{i}\n" for i in kani_notices])

            if kani_node(origin).switch:
                notices += "You are routing from a switch.\n"
            if kani_node(destination).switch:
                notices += "You are routing to a switch. You will need to disembark manually.\n"

            kani_route = " ".join(kani_route)
            time = int(kani_dist) // 8
            time_min, time_sec = int(time // 60), int(time % 60)
            if notices != "":
                notices = "**KANI Notice(s)**: " + notices
            embed.add_field(name="KANI system:",
                            value="/dest {0} \n\n Travel Time: About {1}m{2}s \n Distance: {3}m \n\n {4}".
                            format(kani_route, time_min, time_sec, int(kani_dist), notices))

        # ------------------------------------------------------------------------
        # AURA routing

        # Special notice that you're routing from a junction instead
        if len(aura_route) < 0:
            embed.add_field(name="AURA system:",
                            value="*No route found. You are routing to/from a switch/destination/line in AURA.*")

        # Valid route
        elif len(aura_route) > 0:
            aura_origin = aura_node(origin)
            aura_dest = aura_node(destination)
            valid_stops = ["stop", "junctionstop", "stopjunction"]

            # Surface check
            if aura_origin.name + "-surface" in AURA_JSON["nodes"]:
                notices += "AURA Notice: Your origin has a surface station that you may want to check for better " \
                           "routes. Add '(surface)' to your origin input.\n "
            if aura_dest.name + "-surface" in AURA_JSON["nodes"]:
                notices += "AURA Notice: Your destination has a surface station that you may want to check for " \
                           "better routes. Add '(surface)' to your destination input.\n"

            # Routing to a non-valid stop
            if aura_dest.type not in valid_stops:
                notices += "AURA Notice: You are not routing to a stop.\n"

            aura_route = " ".join(aura_route)
            time = int(aura_dist) // 8
            time_min, time_sec = int(time // 60), int(time % 60)
            embed.add_field(name="AURA system:",
                            value="/dest {0} \n\n Travel Time: About {1}m{2}s \n Distance: {3}m \n\n {4}".
                            format(aura_route, time_min, time_sec, int(aura_dist), notices))

        embed.set_footer(text="See amel.pw/kani or auracc.github.io for more information!")

        # No routes found
        if len(embed.fields) == 0:
            embed.add_field(name="No routes found!",
                            value="No routes found! Check that you spelled your origin/destination correctly.")
            logging.info("No route found between {0} and {1}".format(origin, destination))
        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_slash(name="finddests",
                       description="Finds closest /dest locations to use",
                       options=[create_option(name="x",
                                              description="Civclassic x-coordinate to search",
                                              option_type=4,
                                              required=True),
                                create_option(name="z",
                                              description="CivClassic z-coordinate to search",
                                              option_type=4,
                                              required=True)])
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
