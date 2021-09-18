import os
import psycopg2 as pg

DB_URL = os.environ["DATABASE_URL"]
conn = pg.connect(DB_URL, sslmode='require')


def change_mole(server_id: int):
    set_mole_command = """UPDATE settings SET mole = %s WHERE discord_id = %s"""
    with conn.cursor() as curs:
        old_setting = get_mole(server_id)
        if old_setting == "New server":
            return False  # Just to notice that it's disabled as it's new.
                          # Mostly for discords that used /disablemole prior to this update
        new_setting = not get_mole(server_id)
        curs.execute(set_mole_command, [new_setting, server_id])
        conn.commit()
        return new_setting


def get_mole(server_id: int):
    get_setting = """SELECT mole FROM settings WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        curs.execute(get_setting, [server_id])
        rows = curs.fetchall()
        if len(rows) == 0:
            set_mole_command = """INSERT INTO settings(discord_id, mole) VALUES(%s, %s)"""
            curs.execute(set_mole_command, [server_id, False])
            conn.commit()
            return "New server"
    return rows[0][0]  # Takes the first result, shows the first entry in the row


def left_discord(server_id: int):
    cmd = """DELETE FROM settings WHERE discord_id = %s;"""
    with conn.cursor() as curs:
        try:
            curs.execute(cmd, [server_id])
            conn.commit()
        except:
            conn.rollback()
