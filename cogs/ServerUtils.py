import discord, datetime
import main
from mcstatus import MinecraftServer
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

config = main.CONFIG["ServerUtils"]


class ServerUtils(commands.Cog, name="ServerUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="ping",
                       description="Ping the default server or another server (note this cannot ping Bedrock servers)",
                       guild_ids=main.CONFIG["guild_ids"],
                       options=[create_option(name="server_ip",
                                              description="Enter a server IP (will default to CivClassic)",
                                              option_type=3,
                                              required=False)])
    async def ping(self, ctx: SlashContext, server_ip=config["default_server"]):
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

    # other commands that will become part of this cog:
    # whereis [x] [y] [z] to find a location in the world
    # civmap [x] [y] [z] or civmap[name] to give a link to civmap
    # civwiki to give a link to civwiki


def setup(bot):
    bot.add_cog(ServerUtils(bot))