import datetime
import discord
import logging
import requests
import re
from .CivMap import find_closest, get_settlements, find_containing_poly
from .Settings import get_wiki_setting
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from mcstatus import MinecraftServer
from string import whitespace


class ServerUtils(commands.Cog, name="ServerUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        get_settlements.start()

    @cog_ext.cog_slash(name="ping", description="Ping the default server or another server",
                       options=[create_option(name="server_ip", description="Enter a server IP (will default to CivClassic)",
                                              option_type=3, required=False)])
    async def ping(self, ctx: SlashContext, server_ip="mc.civclassic.com"):
        """Command handler to ping a Minecraft server from the discord server"""

        server = MinecraftServer.lookup(server_ip)
        try:
            status = server.status()
            embed = discord.Embed(title=server_ip, color=discord.Color.dark_orange(),
                                  description="Running {0}".format(status.version.name))
            embed.add_field(name="Players Online",
                            value="**{0}/{1}**".format(status.players.online, status.players.max))
            embed.add_field(name="Latency", value="**{0}** ms".format(status.latency))
            embed.add_field(name="Description", value=re.sub('§\S', '', status.description))
            embed.set_footer(text="Pinged at {0} UTC".format(datetime.datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")))
            # set image of icon (if there is one)
            await ctx.send(embed=embed)
        except:
            await ctx.send("Could not find **" + server_ip + "**, it's either offline or non-existent.")

    @cog_ext.cog_slash(name="whereis",description="Finds closest locations in CivClassic",
                       options=[create_option(name="x", description="CivClassic x-coordinate", option_type=4, required=True),
                                create_option(name="z", description="CivClassic z-coordinate", option_type=4, required=True)])
    async def whereis(self, ctx: SlashContext, x: int, z: int):
        """Command handler to look up a set of coordinates from CivClassic"""

        if abs(x) > 13000 or abs(z) > 13000:
            embed = discord.Embed(color=discord.Colour.red())
            embed.add_field(name="Error!",
                            value="Value of x or z-coordinate was more than 13000!")
            await ctx.send(embed=embed, hidden=True)
            return

        closest = find_closest(x, z)
        containing_nation = find_containing_poly(x, z)

        out = ""
        longest_len = max([len(dest["name"]) + len(dest["nation"]) + 2 for dest in closest])
        for item in closest:
            full_name = item.get("name") + ", " + item.get("nation")
            info = "{0} blocks {1} {2} ({3}, {4})".format(str(int(item.get("distance"))).rjust(4, " "),
                                                          item.get("direction").ljust(5, " "),
                                                          full_name.ljust(longest_len + 3, " "), item.get("x"),
                                                          item.get("z"))
            info = "#".ljust(2, " ") + info if item.get("major") else "".ljust(2, " ") + info
            out += info + "\n"

        civmapurl = "<https://ccmap.github.io/#c={0},{1},r800>".format(str(x), str(z))
        pretext = "**({0}, {1})** is in **".format(str(x), str(z)) + containing_nation + "**:" if containing_nation != "" \
            else "**Locations at ({0}, {1}):**".format(str(x), str(z))

        await ctx.send("{0}\nSee also: {1} ```md\n{2}```"
                       .format(pretext, civmapurl, out), embed=None, hidden=True)

    @cog_ext.cog_slash(name="whois", description="Find name history on a player",
                       options=[create_option(name="username", description="Username of user",
                                              option_type=3, required=True)])
    async def whois(self, ctx: SlashContext, username: str):
        """Command handler to look up a username (find their name history, skin, etc.)"""

        uuid = get_uuid(username)
        embed = discord.Embed(title="Name history of {0}:".format(username))
        if uuid == "":
            embed.add_field(name="Whoops!",
                            value="This username is currently unused right now; it could have been used in the past.\n"
                                  "Check **https://namemc.com/search?q={0}** for more information".format(username))
            await ctx.send(embed=embed)
            return
        history = get_name_history(uuid)
        out = ""
        for item in history[::-1]:  # reverse so the oldest name is last, typical for most minecraft name history sites
            name = item.get("name")
            changed_at = item.get("changedToAt", 0) // 1000
            # Mojang weirdly provides their timestamps with trailing millisecond zeroes which are never used
            if changed_at != 0:
                time = datetime.datetime.utcfromtimestamp(changed_at).strftime('%Y-%m-%d %H:%M:%S')
                out += "**{0}** - changed at **{1}**\n".format(name, time)
            else:
                out += "**{0}**\n".format(name)

        embed = discord.Embed(title="Name history of {0}:".format(username), description=out)

        embed.set_footer(text="See also: https://namemc.com/search?q={0}".format(username))
        embed.add_field(name="UUID: ", value=uuid, inline=True)
        civwiki_page = get_civwiki_page(username)
        if civwiki_page[1]:
            embed.add_field(name="CivWiki Page", value=civwiki_page[0], inline=False)
        embed.set_thumbnail(url="https://crafatar.com/avatars/{0}".format(uuid))

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="civwiki", description="Get a CivWiki page",
                       options=[create_option(name="page_name", description="The CivWiki page name.",
                                              option_type=3, required=False)])
    async def civwiki(self, ctx: SlashContext, page_name=""):
        """Command handler for CivWiki page."""
        if page_name == "":
            await ctx.send("**Edit CivWiki**: https://civwiki.org")
        url = "https://civwiki.org/wiki/" + page_name.replace(" ", "_")
        await ctx.send("{0}".format(url))

    @commands.Cog.listener("on_message")
    async def wikipage(self, ctx):
        """discord.py listener to check for messages"""

        if not await get_wiki_setting(ctx.guild.id) or \
                ctx.author.bot or ctx.author.id == self.bot.user.id:  # Ignore self
            return

        def url(s: str):
            return "https://civwiki.org/wiki/" + s.replace(" ", "_")

        wiki_pattern = "\[{2}([^\]\n]+) *\]{2}"
        pages = re.findall(wiki_pattern, ctx.content)
        pages = [page for page in pages if page not in whitespace]
        if len(pages) != 0:
            page_list = ""
            logging.info("Someone looked up {0} on CivWiki in {1} ({2})"
                         .format(", ".join([page for page in pages[:5]]), ctx.guild.name, ctx.guild.id))
            page_list += "\n".join([url(page) for page in pages[:5]])
            if len(pages) == 1:
                page_list = page_list.replace("<", "").replace(">", "")
            await ctx.reply(page_list, mention_author=False)

    # other commands that will become part of this cog (for next release)
    # civmap [x] [y] [z] or civmap[name] to give a link to civmap


def get_uuid(name: str):
    r = requests.get("https://api.mojang.com/users/profiles/minecraft/{0}".format(name))
    if r.status_code != 200:
        return ""
    return r.json().get("id")


def get_name_history(uuid: str):
    r = requests.get("https://api.mojang.com/user/profiles/{0}/names".format(uuid))
    return r.json()


def get_civwiki_page(page_name: str):
    url = "https://civwiki.org/wiki/" + page_name.replace(" ", "_")
    r = requests.head(url)
    if r.status_code == 200:
        return url, True
    else:
        return url, False


def setup(bot):
    bot.add_cog(ServerUtils(bot))
