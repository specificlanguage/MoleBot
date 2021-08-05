import json
from discord import Client, Intents, Embed, File
from discord_slash import SlashCommand, SlashContext


def load_config():
    with open("config-example.json") as json_data_file:
        data = json.load(json_data_file)
    return data


config = load_config()
client = Client(intents=Intents.default())
slash = SlashCommand(client, sync_commands=True)


@slash.slash(name="mole", description="Mole guy", guild_ids=[803472116061569065])
async def mole(ctx: SlashContext):
    await ctx.send(file=File('resources/montymole.gif'))


@client.event
async def on_ready():
    print("Ready!")


client.run(config["token"])