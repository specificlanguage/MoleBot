import asyncio
import log
import logging
import os
import random
import requests
from discord import Intents, File, Embed
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


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
    if message.author.bot:
        return
    if message.author.id == bot.user.id:  # Ignore self
        return
    if "delusional" in message.content and "[[" not in message.content:
        await message.channel.send("**Edit CivWiki:** https://civwiki.org")
        await asyncio.sleep(3)


@slash.slash(name="mole", description="Mole guy")
async def mole(ctx: SlashContext):
    chance = random.randint(1, 100)
    if chance > 5:
        await ctx.send(file=File('resources/montymole.gif'))
    else:
        mole_gifs = ["https://tenor.com/view/taupe-hide-gif-5585646",
                     "https://media.giphy.com/media/MuACBobEZorb6Xyc1S/giphy.gif",
                     "https://media.giphy.com/media/LFnXTvOR49SZa/giphy.gif",
                     "https://tenor.com/view/mole-deal-withit-naked-mole-rat-gif-12749507",
                     "https://c.tenor.com/iK1zcO0bcUQAAAAC/mole-monty-mole.gif"]
        await ctx.send(random.choice(mole_gifs))


@slash.slash(name="helps", description="Help!",
             options=[create_option(name="command",
                                    description="command",
                                    option_type=3,
                                    required=False)])
async def helps(ctx: SlashContext, command=""):
    url = "https://discord.com/api/v8/applications/{0}/commands".format(os.environ.get("app_id"))
    header = {"Authorization": "Bot " + os.environ.get("token")}
    r = requests.get(url, headers=header)
    cmds, out = r.json(), ""

    commands = [cmd.get("name") for cmd in cmds]
    if command in commands:
        cmd = cmds[commands.index(command)]
        name = cmd.get("name")
        desc = cmd.get("description")
        options = cmd.get("options", [])
        embed = Embed(title="/" + name, description=desc)
        out = ""
        for option in options:
            out += "`" + option.get("name") + "` - " + option.get("description")
        if out != "":
            embed.add_field(name="Options", value=out)
        await ctx.send(embed=embed)

    elif command == "":
        embed = Embed(title="Hi, I'm MoleBot!",
                      description="I'm a bot created by specificlanguage created to do simple Civ tasks, "
                                  "like finding rail /dest commands or finding the closest place to a point; "
                                  "but of course I also create moles as well. Use `/` for all commands!",
                      url="https://c.tenor.com/z8JgskMjeuAAAAAC/yes-monty-mole.gif")
        cds = sorted(commands)
        out = []
        for cmd in cds:
            c = cmds[commands.index(cmd)]
            out.append("`" + c.get("name") + "` - " + c.get("description"))

        embed.add_field(name="Commands:", value="\n".join(out), inline=True)
        embed.add_field(name="Issues?", value="For any bugs, please make an issue at the GitHub at "
                                              "https://github.com/specificlanguage/MoleBot", inline=False)
        await ctx.reply(embed=embed)

    else:
        await ctx.reply("Command not found. Try `/help`?")


@bot.event
async def on_ready():
    logging.info("MoleBot is ready!")


logger = log.init_logger()
bot.run(os.environ.get("token"))
