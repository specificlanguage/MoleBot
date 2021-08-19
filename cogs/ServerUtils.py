import datetime
import discord
import logging
import requests
import re
from cogs.CivMap import find_closest, get_settlements
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from mcstatus import MinecraftServer
from string import whitespace


class ServerUtils(commands.Cog, name="ServerUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        get_settlements.start()

    @cog_ext.cog_slash(name="ping",
                       description="Ping the default server or another server",
                       options=[create_option(name="server_ip",
                                              description="Enter a server IP (will default to CivClassic)",
                                              option_type=3,
                                              required=False)])
    async def ping(self, ctx: SlashContext, server_ip="mc.civclassic.com"):
        # This feels very tacky, may want to change this later
        server = MinecraftServer.lookup(server_ip)
        try:
            status = server.status()
            embed = discord.Embed(title=server_ip, color=discord.Color.dark_orange(),
                                  description="Running {0}".format(status.version.name))
            embed.add_field(name="Players Online",
                            value="**{0}/{1}**".format(status.players.online, status.players.max))
            embed.add_field(name="Latency", value="**{0}** ms".format(status.latency))
            embed.add_field(name="MOTD", value=status.description)
            embed.set_footer(text="Pinged at {0} UTC".format(datetime.datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")))
            # set image of icon (if there is one)
            await ctx.send(embed=embed)
        except:
            await ctx.send("Could not find **" + server_ip + "**, it's either offline or non-existent.")

    @cog_ext.cog_slash(name="whereis",
                       description="Finds closest locations in CivClassic",
                       options=[create_option(name="x",
                                              description="CivClassic x-coordinate",
                                              option_type=4,
                                              required=True),
                                create_option(name="z",
                                              description="CivClassic z-coordinate",
                                              option_type=4,
                                              required=True)])
    async def whereis(self, ctx: SlashContext, x: int, z: int):
        if abs(x) > 13000 or abs(z) > 13000:
            embed = discord.Embed(color=discord.Colour.red())
            embed.add_field(name="Error!",
                            value="Value of x or z-coordinate was more than 13000!")
            await ctx.send(embed=embed)
            return

        closest = find_closest(x, z)
        out = ""
        longest_len = max([len(dest["name"]) for dest in closest])
        for item in closest:
            info = "{0} blocks {1} {2} ({3}, {4})".format(str(int(item.get("distance"))).rjust(4, " "),
                                                          item.get("direction").ljust(5, " "),
                                                          item.get("name").ljust(longest_len, " "), item.get("x"),
                                                          item.get("z"))
            info = "#".ljust(2, " ") + info if item.get("major") else "".ljust(2, " ") + info
            out += info + "\n"

        civmapurl = "<https://ccmap.github.io/#c={0},{1},r800>".format(str(x), str(z))

        await ctx.send("**Locations at ({0}, {1}):**\nSee also: {2} ```md\n{3}```"
                       .format(str(x), str(z), civmapurl, out), embed=None)

    @cog_ext.cog_slash(name="civwiki",
                       description="Get a CivWiki page",
                       options=[create_option(name="page_name",
                                              description="The CivWiki page name.",
                                              option_type=3,
                                              required=False)])
    async def civwiki(self, ctx: SlashContext, page_name=""):
        if page_name == "":
            await ctx.send("**Edit CivWiki**: https://civwiki.org")
            return
        page_name = page_name.lower().capitalize()
        url, success = get_civwiki_page(page_name)
        if not success:
            await ctx.send("{0}\n*This page might not exist yet!*".format(url))
        else:
            await ctx.send("{0}".format(url))

    @commands.Cog.listener("on_message")
    async def wikipage(self, ctx):
        wiki_pattern = "\[{2}([^\]\n]+) *\]{2}"
        pages = re.findall(wiki_pattern, ctx.content)
        pages = [page for page in pages if page not in whitespace]
        if len(pages) != 0:
            page_list = ""
            for page in pages[:5]:
                logging.info(ctx.author.name + " looked up " + page + " on CivWiki")
                url, success = get_civwiki_page(page)
                if not success:
                    page_list += "*<{0}>*\n".format(url)
                else:
                    page_list += "<{0}>\n".format(url)
            if "*" in page_list:
                page_list += "*Links in italics may not exist yet!*"
            if len(pages) == 1:
                page_list = page_list.replace("<", "").replace(">", "")
            await ctx.reply(page_list, mention_author=False)

    # other commands that will become part of this cog (for next release)
    # civmap [x] [y] [z] or civmap[name] to give a link to civmap
    # whois [player] to get a player's info from namemc or other playtime sources


def get_civwiki_page(page_name: str):
    url = "https://civwiki.org/wiki/" + page_name.replace(" ", "_")
    r = requests.head(url)
    if r.status_code == 200:
        return url, True
    else:
        return url, False


def setup(bot):
    bot.add_cog(ServerUtils(bot))
