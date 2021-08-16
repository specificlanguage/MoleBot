import asyncio
import os
import json
from cogs.RailTraverse import get_aura_json, get_kani_json
from discord import Intents, Embed, File
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
async def on_message(message):
    if "delusional" in message.content:
        await message.channel.send("**Edit CivWiki:** https://civwiki.org")
        await asyncio.sleep(3)


@slash.slash(name="mole", description="Mole guy")
async def mole(ctx: SlashContext):
    await ctx.send(file=File('resources/montymole.gif'))


@bot.event
async def on_ready():
    print("Ready!")


bot.run(os.environ.get("token"))
