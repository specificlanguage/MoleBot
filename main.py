import asyncio
import json
from discord import Intents, Embed, File
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext


class Bot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix="%", help_command=None, intents=intents)


def load_config():
    with open("config.json") as json_data_file:
        data = json.load(json_data_file)
    return data


CONFIG = load_config()
bot = Bot(intents=Intents.default())
slash = SlashCommand(bot, sync_commands=True)
for extension in CONFIG["enabled_cogs"]:
    bot.load_extension("cogs." + extension)


@bot.event
async def on_message(message):
    if "delusional" in message.content:
        await message.channel.send("**Edit CivWiki:** https://civwiki.org")
        await asyncio.sleep(3)


@slash.slash(name="mole", description="Mole guy", guild_ids=CONFIG["guild_ids"])
async def mole(ctx: SlashContext):
    await ctx.send(file=File('resources/montymole.gif'))



@bot.event
async def on_ready():
    print("Ready!")


bot.run(CONFIG["token"])
