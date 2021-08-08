from typing import Optional

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
        self.f = 0
        self.g = 0
        self.parent = None # RailNode

    def __eq__(self, other):
        if self.name == other.name:
            return True
        if self.x == other.x and self.z == other.z: # just in case
            return True
        return False

    def __str__(self):
        try:
            return self.name + "\n Parent: " + self.parent
        except TypeError:
            return self.name

    def __repr__(self):
        try:
            return self.name + "\n Parent: " + self.parent
        except TypeError:
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


def reconstruct_path(node, start):
    path = [node]
    while node != start:
        print(node.parent)
        node = node.parent
        path.append(node)
    return path


def kani_astar(start: str, end: str):
    start_node = kani_item(start)
    end_node = kani_item(end)

    if start_node is None or end_node is None:
        return []

    open_list = [start_node]
    closed_list = []
    tot_dist = 0

    def find_lowest_node(conns: iter):
        best_node = None
        best_f = 0

        for dest in conns:
            if dest.f == 0.0:
                dest.g = euclid(start_node, dest)
                dest.f = euclid(start_node, dest) + euclid(dest, end_node)
            if best_f == 0.0 or dest.f < best_f:
                best_node = dest
                best_f = dest.f

        return best_node

    while len(open_list) != 0:
        current_node = find_lowest_node(open_list)
        open_list.remove(current_node)
        closed_list.append(current_node)
        current_node.g = euclid(start_node, current_node)
        tot_dist += current_node.g
        if current_node == end_node:
            print(start_node, end_node, current_node)
            return reconstruct_path(current_node, start_node)[::-1], tot_dist

        for node in current_node.links:
            node = kani_item(node)
            if node in closed_list or node in open_list:
                continue

            node.parent = current_node
            node.g = current_node.g + euclid(current_node, node)
            node.f = node.g + euclid(node, end_node)
            open_list.append(node)

    return []


def kani_item(s: str):
    try:
        return RailNode(s, kani_json[s])
    except KeyError:
        return None


kani_json = get_kani_json()
aura_json = get_aura_json()

def setup(bot):
    bot.add_cog(RailUtils(bot))

