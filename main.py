import asyncio
import log
import logging
import os
import random
import requests
from cogs import Settings
from discord import Intents, Embed
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


class Bot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix="%", help_command=None, intents=intents)


bot = Bot(intents=Intents.default())
slash = SlashCommand(bot, sync_commands=True)
cogs = ["RailUtils", "ServerUtils", "Settings"]
for extension in cogs:
    bot.load_extension("cogs." + extension)


@bot.event
async def on_slash_command(message):
    guild_name = bot.get_guild(message.guild_id)
    kwargs = message.kwargs
    args = [key + ":" + str(kwargs[key]) for key in kwargs.keys()]
    command = "/" + message.name + " " + " ".join(args)

    if message.guild is not None:
        logging.info("'{0}' was sent in guild {1} ({2})".format(command, guild_name, message.guild_id))
    else:
        logging.info("'{0}' was sent via a DM".format(command))


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
    if ctx.guild is not None:
        mole_settings = Settings.get_mole(ctx.guild.id)
        if mole_settings == "New server" or mole_settings is False:
            await ctx.send("The administrator has disabled moles on this server. *Sorry!*", hidden=True)
            return
    chance = random.randint(1, 100)
    if chance <= 5:
        mole_gifs = ["https://tenor.com/view/taupe-hide-gif-5585646",
                     "https://media.giphy.com/media/MuACBobEZorb6Xyc1S/giphy.gif",
                     "https://media.giphy.com/media/LFnXTvOR49SZa/giphy.gif",
                     "https://tenor.com/view/mole-deal-withit-naked-mole-rat-gif-12749507",
                     "https://c.tenor.com/iK1zcO0bcUQAAAAC/mole-monty-mole.gif",
                     "https://media.giphy.com/media/n3sCOv1J7AKknd0zVX/giphy.gif",
                     "https://c.tenor.com/KOoh92LGypQAAAAM/monty-mole-monty_mole.gif",
                     "https://c.tenor.com/AZPQZggbt_YAAAAM/monty-mole-monty.gif",
                     "https://c.tenor.com/MO81qAF59TYAAAAM/monty-mole-the-winner.gif"]
        await ctx.send(random.choice(mole_gifs))
    else:
        await ctx.send("https://c.tenor.com/z8JgskMjeuAAAAAC/yes-monty-mole.gif")


@slash.slash(name="help", description="Help!",
             options=[create_option(name="command",
                                    description="command",
                                    option_type=3,
                                    required=False)])
async def help(ctx: SlashContext, command=""):
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
        await ctx.send(embed=embed, hidden=True)

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
        await ctx.reply(embed=embed, hidden=True)

    else:
        await ctx.reply("Command not found. Try `/help`?", hidden=True)


@slash.slash(name="invite", description="Spread the mole to another server")
async def invite(ctx: SlashContext):
    embed = Embed(title="Help spread the word of the mole!",
                  description="Invite me to another server so they can generate dest commands,"
                              "find where they are on CivClassic, and other features too!")
    embed.set_thumbnail(url="https://c.tenor.com/AZPQZggbt_YAAAAd/monty-mole-monty.gif")
    embed.add_field(name="Invite:",
                    value="https://discord.com/api/oauth2/authorize?client_id={0}&permissions"
                          "=0&scope=bot%20applications.commands".format(os.environ.get("app_id")))
    embed.set_footer(text="Made by specificlanguage#2891. Contact him for more information!")
    await ctx.send(embed=embed)


@bot.event
async def on_guild_join(guild):
    logging.info("MoleBot has joined {0}! (id = {1})".format(guild.name, guild.id))
    Settings.init_settings(server_id=guild.id)

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send("Hi, I'm MoleBot! Type /help to see what I do. "
                               "(and don't worry. I've disabled /mole on this server by default.)")
            break


@bot.event
async def on_guild_remove(guild):
    logging.info("MoleBot has left {0}. (id = {1})".format(guild.name, guild.id))
    Settings.left_discord(guild.id)


@bot.event
async def on_ready():
    logging.info("MoleBot is ready!")

logger = log.init_logger()
bot.run(os.environ.get("token"))
