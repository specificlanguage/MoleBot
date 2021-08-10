import requests, json
from typing import Optional
from RailTraverse import RailNode, euclid, taxi

class AuraNode(RailNode):
    def __init__(self, name: str, data: dict):
        super().__init__(name, data)
        self.badlinks = data.get("bad_links", []).append(data.get("unsafe_links", []))
        self.station = data.get("stop", False)
        self.switch = data.get("junction", False)
        self.stopjunction = data.get("stopjunction", False)
        self.junctionstop = data.get("junctionstop", False)
        self.crossing = data.get("crossing", False)
        self.line = data.get("line", False)
        self.dest = data.get("dest", "")


def get_aura_json():
    r = requests.get("https://raw.githubusercontent.com/auracc/aura-toml/main/computed.json")
    aura_json = r.json()
    with open("resources/aura.json", "w+") as fp:
        fp.truncate(0) # clear file to reload it
        json.dump(aura_json, fp)
    return aura_json

def line_routed_direction(cur, prev, nex):
    s, e = 0, 0
    for i in range(len(prev.links)):
        l = prev.links[i]
        if l == prev:
            s = i
        if l == nex:
            e = i
    return s, e


#TODO: fix AURA A* to comply with JSON
def find_aura_route(start: str, end: str):
    start_node = aura_node(start)
    end_node = aura_node(end)
    return astar(start_node, end_node)

def reconstruct_path(node, start):
    path = [node]

    tot_dist = 0
    while node != start:
        tot_dist += (euclid(node, node.parent) + taxi(node, node.parent)) / 2
        node = node.parent
        path.append(node)
    return path[::-1], tot_dist  # need to reverse path


def astar(start_node: AuraNode, end_node: AuraNode):

    # Unfortunately AURA requires a slightly modified A* from RailTraverse so although it's mostly the same
    # there are much different things that require a new function

    if start_node is None or end_node is None:
        return [], 0

    open_list = [start_node]
    closed_list = []

    def find_lowest_node(conns: iter):
        best_node = None
        best_f = 0

        for dest in conns:
            if dest.f == 0.0:
                dest.f = euclid(start_node, dest) + euclid(dest, end_node)
            if best_f == 0.0 or dest.f < best_f:
                best_node = dest
                best_f = dest.f
        return best_node

    while len(open_list) != 0:
        current_node = find_lowest_node(open_list)
        open_list.remove(current_node)  # remove current node from open list
        closed_list.append(current_node)  # add to closed list (to prevent backtracking)

        if current_node == end_node:
            return reconstruct_path(current_node, start_node)

        if current_node.station:
            continue  # can't leave the station since it doesn't route

        for node in current_node.links:
            node = aura_node(node)

def aura_node(s: str):
    try:
        return AuraNode(s, aura_json["nodes"][s])
    except KeyError:
        return None

aura_json = get_aura_json()
