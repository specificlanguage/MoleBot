import os
import psycopg2 as pg
from discord.ext import commands
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

DB_URL = os.environ["DATABASE_URL"]
conn = pg.connect(DB_URL, sslmode='require')


class Settings(commands.Cog, name="Settings"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="disablemole", description="Disable or reenables the mole guy :(",
                       options=[create_option(name="setting", description="Optional true/false",
                                              option_type=5, required=False)])
    async def disablemole(self, ctx: SlashContext, **setting: bool):
        """Command handler for /disablemole, superceded task to 'config_mole'"""
        await self.config_mole(ctx, setting)

    @cog_ext.cog_subcommand(base="config", name="mole", description="Change /mole behavior")
    async def config_mole(self, ctx: SlashContext):
        """Command handler for mole subcommand of config, calls subroutines to set mole value.
        Either disables or enables /mole in this subcommand."""
        if ctx.guild is None:
            await ctx.send("This can only be run in a discord.")
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_messages:
            setting = change_mole(ctx.guild_id)
            if setting:
                await ctx.send("Enabled `/mole` on this server. Do `/disablemole` again to disable it."
                               .format(ctx.guild.name))
            else:  # Now set to false
                await ctx.send("Disabled `/mole` on this server. Do `/disablemole` again to enable it."
                               .format(ctx.guild.name))
        else:  # Admins only
            await ctx.send("Only users with administrator or manage messages permissions can use this command.",
                           hidden=True)

    @cog_ext.cog_subcommand(base="config", name="wiki", description="Change CivWiki query behavior",
                            options=[create_option(name="setting", description="Optional true/false setting",
                                                   option_type=5, required=False)])
    async def config_wiki(self, ctx: SlashContext, **setting):
        """Command handler for CivWiki subcommand of config, calls subroutines to set wiki value.
           Either disables or enables [[wiki querying]] in this subcommand, but does not disable /civwiki."""
        if ctx.guild is None:
            await ctx.send("This can only be run in a discord.")
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_messages:
            try:
                setting = setting.get("setting")
            except KeyError:
                setting = not get_wiki_setting(ctx.guild.id)
            new_setting = set_wiki_setting(server_id=ctx.guild.id, setting=setting)
            if new_setting:
                await ctx.send("Enabled [[ wiki querying ]] on this server. Do `/config wiki {setting}` to change it \
                (`setting` is optional). You can also do `/civwiki` to query CivWiki anyway.")
            else:
                await ctx.send("Disabled [[ wiki querying ]] on this server. Do `/config wiki {setting}` to change it \
                (`setting` is optional). You can also do `/civwiki` to query CivWiki anyway.")
        else:  # Admins only
            await ctx.send("Only users with administrator or manage messages permissions can use this command.",
                           hidden=True)


def change_mole(server_id: int):
    """Tells PostgreSQL database to update the mole setting, or just return false if it's new."""
    set_mole_command = """INSERT INTO settings(discord_id, wiki) VALUES(%s, %s) ON CONFLICT DO
                            UPDATE SET wiki = %s WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        old_setting = get_mole(server_id)
        if old_setting == "New server":
            return False  # Just to notice that it's disabled as it's new.
            # Mostly for discords that used /disablemole prior to this update
        new_setting = not get_mole(server_id)
        curs.execute(set_mole_command, [server_id, new_setting, new_setting, server_id])
        conn.commit()
        return new_setting


def get_mole(server_id: int):
    """Queries PostgreSQL database to get the mole setting, or return a special case if it's a new server."""
    get_setting = """SELECT mole FROM settings WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        curs.execute(get_setting, [server_id])
        rows = curs.fetchall()
        if len(rows) == 0:  # The discord doesn't exist in the db yet because it's disabled by default.
            # This case only happens for discords that had /disablemole prior to this update.
            set_mole_command = """INSERT INTO settings(discord_id, mole) VALUES(%s, %s) ON CONFLICT DO
                            UPDATE SET wiki = %s WHERE discord_id = %s;"""
            curs.execute(set_mole_command, [server_id, False, False, server_id])
            conn.commit()
            return "New server"
    return rows[0][0]  # Takes the first result, shows the first entry in the row


def set_wiki_setting(server_id: int, setting: bool):
    """Requests PostgreSQL database to set `wiki` setting."""
    get_setting = """SELECT wiki FROM settings WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        curs.execute(get_setting, [server_id])
        if setting is None:
            rows = curs.fetchall()
            setting = not rows[0][0]
        set_mole_command = """INSERT INTO settings(discord_id, wiki) VALUES(%s, %s) ON CONFLICT DO
                                UPDATE SET wiki = %s WHERE discord_id = %s;"""
        curs.execute(set_mole_command, [server_id, setting, setting, server_id])
        conn.commit()
    return setting  # Takes the first result, shows the first entry in the row


def get_wiki_setting(server_id: int):
    """Queries PostgreSQL database to get `wiki` setting."""
    get_setting = """SELECT wiki FROM settings WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        curs.execute(get_setting, [server_id])
        rows = curs.fetchall()
        if len(rows) == 0:  # The discord doesn't exist in the db yet because it's disabled by default.
            set_wiki_setting(server_id, False)
            return False
    return rows[0][0]


def init_settings(server_id: int):
    """Initializes settings upon a new server entering."""
    with conn.cursor() as curs:
        curs.execute("""SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_schema='public');""")
        rows = curs.fetchall()
        if len(rows) == 0:
            curs.execute("""create table settings(discord_id bigint, mole boolean default false,
            wiki boolean default false);""")
        curs.execute("""INSERT INTO settings(discord_id) VALUES (%s);""", [server_id])


def left_discord(server_id: int):
    """Deletes entry upon a leaving a server by any means."""
    cmd = """DELETE FROM settings WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        try:
            curs.execute(cmd, [server_id])
            conn.commit()
        except:
            conn.rollback()


def setup(bot):
    bot.add_cog(Settings(bot))
