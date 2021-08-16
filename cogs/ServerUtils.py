import datetime
import discord
from cogs.CivMap import find_closest
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from mcstatus import MinecraftServer


class ServerUtils(commands.Cog, name="ServerUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="ping",
                       description="Ping the default server or another server (note this cannot ping Bedrock servers)",
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
                       description="Ping the default server or another server (note this cannot ping Bedrock servers)",
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
        else:
            closest = find_closest(x, z)
            out = ""
            for item in closest:
                info = "{0} blocks {1} {2}".format(str(int(item.get("distance"))).rjust(4, " "),
                                                   item.get("direction").ljust(7),
                                                   item.get("name"))
                if item.get("major"):
                    info = "**" + info + "**"
                out += info + "\n"

            embed = discord.Embed(color=discord.Colour.gold())
            embed.add_field(name="Closest features to {0}, {1}:".format(x, z), value=out)
            embed.add_field(name="CivMap link:",
                            value="<https://ccmap.github.io/#c=" + str(int(x)) + "," + str(int(z)) + "," + "r400>")

        await ctx.send(embed=embed)


    # other commands that will become part of this cog:
    # whereis [x] [y] [z] to find a location in the world
    # civmap [x] [y] [z] or civmap[name] to give a link to civmap
    # civwiki to give a link to civwiki




def setup(bot):
    bot.add_cog(ServerUtils(bot))