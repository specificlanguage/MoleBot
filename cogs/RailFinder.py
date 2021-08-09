from typing import Optional

import requests, json
from math import dist

class RailNode:
    def __init__(self, name: str, data: dict,
                 rail_type: Optional[str] = "KANI",
                 station: Optional[bool] = False,
                 switch: Optional[bool] = False):
        self.name = name
        self.x = data["x"]
        self.z = data["z"]
        self.links = data["links"]
        self.f = 0
        self.g = 0
        self.parent = None  # must be type RailNode
        self.rail_type = rail_type
        self.station = data["station"] if not KeyError else False
        self.switch = data["switch"] if not KeyError else False
        self.badlinks = data["badlinks"] if not KeyError else []

    def __eq__(self, other):
        if self.name == other.name:
            return True
        if self.x == other.x and self.z == other.z:  # just in case
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


def taxi(start, end):
    return sum(abs(start.x - end.x), abs(start.z - end.z))


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
    tot_dist = 0
    while node != start:
        tot_dist += (euclid(node, node.parent) + taxi(node, node.parent)) / 2
        node = node.parent
        path.append(node)
    return path, tot_dist


def find_kani_route(start: str, end: str):
    start_node = kani_node(start)
    end_node = kani_node(end)
    return astar(start_node, end_node)

#TODO: fix AURA A* to comply with JSON
def find_aura_route(start: str, end: str):
    start_node = aura_node(start)
    end_node = aura_node(end)
    return astar(start_node, end_node)

def astar(start_node: RailNode, end_node: RailNode):
    if start_node is None or end_node is None:
        return [], 0

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

        if current_node == end_node:
            return reconstruct_path(current_node, start_node)[::-1]

        print(current_node)
        for node in current_node.links:
            if current_node.rail_type == "AURA":
                node = aura_node(node)
            else:
                node = kani_node(node)

            if node in closed_list or node in open_list:
                continue
            if node.name in current_node.badlinks:
                continue
            if not(node.station or node.switch) and current_node != start_node:
                continue  # can't leave node

            node.parent = current_node
            node.g = current_node.g + euclid(current_node, node)
            node.f = node.g + euclid(node, end_node)
            open_list.append(node)

    return [], 0


def kani_node(s: str):
    try:
        return RailNode(s, kani_json[s])
    except KeyError:
        return None

def aura_node(s: str):
    try:
        return RailNode(s, aura_json["nodes"][s], rail_type="AURA")
    except KeyError:
        return None


kani_json = get_kani_json()
aura_json = get_aura_json()
