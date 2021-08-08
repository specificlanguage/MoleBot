import requests, json
from math import dist
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

class RailNode:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.x = data["x"]
        self.z = data["z"]
        self.links = data["links"]

    def __eq__(self, other):
        if self.name == other.name:
            return True
        if self.x == other.x and self.z == other.z: # just in case
            return True
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


def euclid(start, end):
    return dist([start.x, start.z], [end.x, end.z])


def get_kani_json():
    r = requests.get("https://raw.githubusercontent.com/Ameliorate/KANI/master/docs/export.json")
    kani_json = r.json()
    with open("resources/kani.json", "w+") as fp:
        fp.truncate(0) # clear file to reload it
        json.dump(kani_json, fp)
    return kani_json


def get_aura_json():
    r = requests.get("https://raw.githubusercontent.com/auracc/aura-toml/main/computed.json")
    aura_json = r.json()
    with open("resources/aura.json", "w+") as fp:
        fp.truncate(0) # clear file to reload it
        json.dump(aura_json, fp)
    return aura_json

def kani_astar(start: str, end: str):
    start_node = kani_item(start)
    end_node = kani_item(end)

    if start_node is None or end_node is None:
        return ""

    open_list = [start_node]
    closed_list = []
    path = []
    tot_dist = 0

    print(start_node, end_node)

    def find_lowest_node(conns: iter):
        best_node = None
        best_f = 0

        for dest in conns:
            temp_f_score = euclid(start_node, dest) + euclid(dest, end_node)
            if best_f == 0 or temp_f_score < best_f:
                best_f = temp_f_score
                best_node = dest
        return best_node

    # somewhat pseudocode below
    while len(open_list) != 0:
        current_node = find_lowest_node(open_list)
        open_list.remove(current_node)
        closed_list.append(current_node)
        path.append(current_node)

        g = euclid(start_node, current_node)
        tot_dist += g

        h = euclid(current_node, end_node)

        if current_node == end_node:
            return path

        for node in current_node.links:
            node = kani_item(node)
            if node in closed_list: # if in closed list, skip
                continue
            elif node in open_list:
                if g + euclid(current_node, node) < euclid(start_node, current_node):
                    closed_list.append(node)
            else:
                open_list.append(node)

    return ""


def kani_item(s: str):
    try:
        return RailNode(s, kani_json[s])
    except KeyError:
        return None


kani_json = get_kani_json()
aura_json = get_aura_json()

def setup(bot):
    bot.add_cog(RailUtils(bot))

