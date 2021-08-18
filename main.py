import asyncio
import os
import log
import logging
from discord import Intents, File
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext


class Bot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix="%", help_command=None, intents=intents)


bot = Bot(intents=Intents.default())
slash = SlashCommand(bot, sync_commands=True)
cogs = ["RailUtils", "ServerUtils"]
for extension in cogs:
    bot.load_extension("cogs." + extension)


@bot.event
async def on_slash_command(message):
    guild_name = bot.get_guild(message.guild_id)
    kwargs = message.kwargs
    args = [key + ":" + str(kwargs[key]) for key in kwargs.keys()]
    command = "/" + message.name + " " + " ".join(args)

    if message.guild is not None:
        logging.info("{0} sent '{1}' in guild {2} ({3})".format(message.author, command,
                                                              guild_name, message.guild_id))
    else:
        logging.info("{0} sent '{1}' (via a DM)".format(message.author, command))


@bot.event
async def on_message(message):
    if message.author == bot:
        return
    if "delusional" in message.content:
        await message.channel.send("**Edit CivWiki:** https://civwiki.org")
        await asyncio.sleep(3)


@slash.slash(name="mole", description="Mole guy")
async def mole(ctx: SlashContext):
    await ctx.send(file=File('resources/montymole.gif'))


@bot.event
async def on_ready():
    logging.info("MoleBot is ready!")

log.init_logger()
bot.run(os.environ.get("token"))
