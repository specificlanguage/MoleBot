import discord
import os
import asyncpg as apg
from discord.ext import commands
from discord_slash import SlashContext, cog_ext


DB_URL = os.environ["DATABASE_URL"]


class Settings(commands.Cog, name="Settings"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="disablemole", description="Disable or reenables the mole guy :(")
    async def disablemole(self, ctx: SlashContext, **setting: bool):
        """Command handler for /disablemole, superceded task to 'modify_mole'"""
        await modify_mole(ctx)

    @cog_ext.cog_slash(name="config", description="Show/select settings")
    async def config(self, ctx: SlashContext):
        """Top-level command for config commands"""
        mole_setting = await get_mole(ctx.guild.id)
        wiki_setting = await get_wiki_setting(ctx.guild.id)
        embed = discord.Embed(title="Current settings:", description="`/mole`: {0}\n`/wiki` output: {1}"
                              .format(str(mole_setting), str(wiki_setting)))
        embed.set_footer(text="To change settings, do `/config mole` or `/config wiki`.")
        await ctx.send(embed=embed)


    @cog_ext.cog_subcommand(base="config", name="mole", description="Change /mole behavior")
    async def config_mole(self, ctx: SlashContext):
        """Command handler for mole subcommand of config, superceded task to 'modify_mole_'."""
        await modify_mole(ctx)

    @cog_ext.cog_subcommand(base="config", name="wiki", description="Change CivWiki query behavior")
    async def config_wiki(self, ctx: SlashContext):
        """Command handler for CivWiki subcommand of config, calls subroutines to set wiki value.
           Either disables or enables [[wiki querying]] in this subcommand, but does not disable /civwiki."""
        if ctx.guild is None:
            await ctx.send("This can only be run in a discord.")
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_messages:
            setting = not await get_wiki_setting(ctx.guild.id)
            new_setting = await set_wiki_setting(server_id=ctx.guild.id, setting=setting)
            if new_setting:
                await ctx.send("Enabled [[ wiki querying ]] on this server. Do `/config wiki {setting}` to change it \
                (`setting` is optional). You can also do `/civwiki` to query CivWiki anyway.")
            else:
                await ctx.send("Disabled [[ wiki querying ]] on this server. Do `/config wiki {setting}` to change it \
                (`setting` is optional). You can also do `/civwiki` to query CivWiki anyway.")
        else:  # Admins only
            await ctx.send("Only users with administrator or manage messages permissions can use this command.",
                           hidden=True)


async def modify_mole(ctx: SlashContext):
    """General handler for mole subcommand of config, calls subroutines to set mole value.
    Either disables or enables /mole in this subcommand."""
    if ctx.guild is None:
        await ctx.send("This can only be run in a discord.")
    if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_messages:
        setting = await change_mole(ctx.guild_id)
        if setting:
            await ctx.send("Enabled `/mole` on this server. Do `/disablemole` again to disable it."
                           .format(ctx.guild.name))
        else:  # Now set to false
            await ctx.send("Disabled `/mole` on this server. Do `/disablemole` again to enable it."
                           .format(ctx.guild.name))
    else:  # Admins only
        await ctx.send("Only users with administrator or manage messages permissions can use this command.",
                       hidden=True)

async def change_mole(server_id: int):
    """Tells PostgreSQL database to update the mole setting, or just return false if it's new."""
    set_mole_command = """INSERT INTO settings(discord_id, mole) VALUES($1, $2) ON CONFLICT (discord_id) DO
                            UPDATE SET mole = $3;"""
    old_setting = await get_mole(server_id)
    if old_setting == "New server":
        return False  # Just to notice that it's disabled as it's new.
        # Mostly for discords that used /disablemole prior to this update

    new_setting = not old_setting

    conn = await apg.connect(dsn=DB_URL)
    async with conn.transaction() as tr:
        await conn.execute(set_mole_command, server_id, new_setting, new_setting)
    return new_setting


async def get_mole(server_id: int):
    """Queries PostgreSQL database to get the mole setting, or return a special case if it's a new server."""
    get_setting = """SELECT mole FROM settings WHERE discord_id = ($1);"""

    conn = await apg.connect(dsn=DB_URL)
    async with conn.transaction() as tr:
        rows = await conn.fetchrow(get_setting, server_id)
        if len(rows) == 0:  # The discord doesn't exist in the db yet because it's disabled by default.
            set_mole_command = """INSERT INTO settings(discord_id, mole) VALUES($1, $2) ON CONFLICT (discord_id) DO
                            UPDATE SET wiki = $3;"""
            await conn.execute(set_mole_command, server_id, False, False)
            return "New server"
    return rows[0]  # Takes the first result, shows the first entry in the row


async def set_wiki_setting(server_id: int, setting: bool):
    """Requests PostgreSQL database to set `wiki` setting."""
    get_setting = """SELECT wiki FROM settings WHERE discord_id = $1;"""

    conn = await apg.connect(dsn=DB_URL)
    async with conn.transaction() as tr:
        rows = await conn.fetchall(get_setting, server_id)
        if len(rows) == 0:
            setting = not rows[0][0]
        set_mole_command = """INSERT INTO settings(discord_id, wiki) VALUES($1, $2) ON CONFLICT (discord_id) DO
                                UPDATE SET wiki = $3;"""
        await conn.execute(set_mole_command, server_id, setting, setting)
    return setting  # Takes the first result, shows the first entry in the row


async def get_wiki_setting(server_id: int):
    """Queries PostgreSQL database to get `wiki` setting."""
    get_setting = """SELECT wiki FROM settings WHERE discord_id = $1;"""

    conn = await apg.connect(dsn=DB_URL)
    async with conn.transaction() as tr:
        rows = await conn.fetchall(get_setting, server_id)
        if len(rows) == 0:  # The discord doesn't exist in the db yet because it's disabled by default.
            await set_wiki_setting(server_id, False)
            return False
    return rows[0][0]


async def init_settings(server_id: int):
    """Initializes settings upon a new server entering."""
    conn = await apg.connect(dsn=DB_URL)
    with conn.transaction() as tr:
        conn.execute("""INSERT INTO settings(discord_id) VALUES ($1);""", server_id)


async def left_discord(server_id: int):
    """Deletes entry upon a leaving a server by any means."""
    cmd = """DELETE FROM settings WHERE discord_id = $1;"""
    conn = await apg.connect(dsn=DB_URL)
    with conn.transaction() as tr:
        try:
            conn.execute(cmd, server_id)
        except:
            pass


def setup(bot):
    bot.add_cog(Settings(bot))
