import requests, json
from math import dist
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


class RailNode:
    def __init__(self, name: str, x: int, y: int, z: int, aura_edge: list[str], kani_edge:list[str]):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.aura_conns = aura_edge
        self.kani_conns = kani_edge

    def __eq__(self, other):
        if self.name == other.name and self.x == other.x and self.y == other.y and self.z == other.z:
            return True
        return False

    def get_links_kani(self):
        pass # TODO get links or possibly not create a class for each rail node -- may not be ncessary


def get_kani_rail_node(str):
    with open("resources/kani.json") as kf:
        kani_json = json.load(kf)
        try:
            node = kani_json[str]
            # railnode = RailNode(name=str,x=node["x"],y=node["y"],z=node["z"], aura_edge=)
            # TODO: get all links for each system
        except KeyError:
            print("Could not find {0}".format(str))
            return None



def euclid(start: RailNode, end: RailNode):
    return dist(start.x - end.x) + dist(start.z - end.z)


def get_kani_json():
    r = requests.get("https://raw.githubusercontent.com/Ameliorate/KANI/master/docs/export.json")
    kani_json = r.json()
    with open("resources/kani.json", "w") as fp:
        fp.close() # clear file before writing again
        json.dump(kani_json, fp)


def get_aura_json():
    r = requests.get("https://raw.githubusercontent.com/auracc/aura-toml/main/computed.json")
    aura_json = r.json()
    with open("resources/aura.json", "w") as fp:
        fp.close() # clear file before writing again
        json.dump(aura_json, fp)


def astar(start: RailNode, end: RailNode):
    open_list = {start}
    closed_list = set[RailNode]()
    path = []
    gscore = 0
    fscore = euclid(start, end)  # although we're measuring in blocks, this will give us a better result

    def find_lowest_node(conns: set[RailNode]):
        cn = None
        for i in conns:
            if cn is None or euclid(i, end) < euclid(cn, end):
                cn = i
        return cn

    # somewhat pseudocode below
    while len(open_list) != 0:
        current_node = find_lowest_node(open_list)
        open_list.remove(current_node)
        closed_list.add(current_node)

        if current_node == end:
            return path

        for link in current_node.get_links_kani():
            pass
            # TODO: finish the A* algorithm, after finishing data types earlier












def setup(bot):
    bot.add_cog(RailUtils(bot))

