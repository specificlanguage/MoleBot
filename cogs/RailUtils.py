import requests, json
from math import dist
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option


class RailUtils(commands.Cog, name="RailUtils"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def euclid(start, end):
    return dist(start["x"] - end["x"]) + dist(start["z"] - end["z"])


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
        return None

    open_list = {start}
    closed_list = set()
    path = []
    dist = 0
    g = 0
    h = euclid(start_node, end_node)  # although we're measuring in blocks, this will give us a better result

    def find_lowest_node(conns: set):
        best_node = None
        best_f = 0

        for dest in conns:
            node = aura_json[dest]
            temp_f_score = abs(euclid(node, start)) + abs(euclid(node, end))
            if best_f == 0 or temp_f_score < best_f:
                best_f = temp_f_score
                best_node = node
        return best_node

    # somewhat pseudocode below
    while len(open_list) != 0:
        current_node = find_lowest_node(open_list)
        open_list.remove(current_node)
        closed_list.add(current_node)
        path.append(current_node)

        g = euclid(start, current_node)
        h = euclid(current_node, end)

        if current_node == end:
            return path

        for node in current_node["links"]:
            if node not in closed_list:
                open_list.add(node)
            if node in open_list:
                temp_g = euclid(start, node)
                g_parent = euclid(start, current_node) + euclid(current_node, node)
                if temp_g < g_parent:
                    path.remove(current_node)
                    path.append(node)

    return None

def kani_item(s: str):
    try:
        return kani_json[s]
    except KeyError:
        return None


kani_json = get_kani_json()
aura_json = get_aura_json()

def setup(bot):
    bot.add_cog(RailUtils(bot))

