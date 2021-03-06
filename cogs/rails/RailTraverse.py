from discord.ext import tasks
from typing import List
from math import dist
from queue import PriorityQueue
from .RailHelpers import *
import difflib
import json
import logging
import requests


class RailNode:
    """KANI object node that loads all information from file.
    Used for pathfinding, reconstruction, and everything in between."""
    def __init__(self, name: str, data: dict):
        self.name = name
        self.x = data.get("x", 0)
        self.z = data.get("z", 0)
        self.links = data.get("links", [])
        self.f = 0
        self.g = 0
        self.parent = None  # must be type RailNode
        self.station = data.get("station", False)
        self.switch = data.get("switch", False)
        self.badlinks = data.get("BadLinks", {})
        self.stop = not (self.station or self.switch)

    def __eq__(self, other):
        """Overrides equal to check whether the name is the same;
        should be the only criteria as KANI nodes are unique in name."""
        return self.name == other.name

    def __str__(self):
        """Returns a string for easy readability. Also adds parent support."""
        try:
            return self.name + "\n Parent: " + self.parent
        except TypeError:
            return self.name

    def __repr__(self):
        """Returns a string for easy readability. Also adds parent support."""
        try:
            return self.name + "\n Parent: " + self.parent
        except TypeError:
            return self.name


# adaptation for AURA system
class AuraNode(RailNode):
    """AURA object node that extends support from KANI node.
    Loads all necessary information from JSON that will or may get used later."""
    def __init__(self, name: str, data: dict):
        super().__init__(name, data)
        self.badlinks = data.get("bad_links", {})
        self.unsafelinks = data.get("unsafe_links", [])
        self.type = data.get("type", "")
        self.stop = self.type == "stop"
        self.dest_stop = data.get("dest_stop", "")
        self.dest = data.get("dest", "")
        self.dest_a = data.get("dest_a", "")  # Accounts for AURA line nodes
        self.dest_b = data.get("dest_b", "")
        self.dest_junction = data.get("dest_junction", "")
        self.link_dests = data.get("link_dests", {})


def euclid(start, end):
    """Helper function that calculates distance."""
    return dist([start.x, start.z], [end.x, end.z])


def taxi(start, end):
    """Helper function that calculates distance VIA manhattan method, ie. absolute value."""
    return sum([abs(start.x - end.x), abs(start.z - end.z)])


def load_kani_json():
    """Helper function to load KANI_JSON from the file (may not be needed)"""
    with open("resources/kani.json", "r") as fp:
        return json.load(fp)


def load_aura_json():
    """Helper function to load AURA_JSON from the file (may not be needed)"""
    with open("resources/aura.json", "r") as fp:
        return json.load(fp)


@tasks.loop(hours=3.0)
async def get_kani_json():
    """Coroutine that is automatically scheduled every 3 hours to grab the KANI JSON."""
    logging.info("Grabbing KANI JSON file from GitHub at "
                 "https://raw.githubusercontent.com/Ameliorate/KANI/master/docs/export.json")

    r = requests.get("https://raw.githubusercontent.com/Ameliorate/KANI/master/docs/export.json")
    k = r.json()
    with open("resources/kani.json", "w+") as fp:
        fp.truncate(0)  # clear file to reload it
        json.dump(k, fp)
    global KANI_JSON, KANI_ALIASES
    KANI_JSON = load_kani_json()
    KANI_ALIASES = get_aliases()


@tasks.loop(hours=3.0)
async def get_aura_json():
    """Coroutine that is automatically scheduled every 3 hours to grab the AURA JSON."""
    logging.info("Grabbing AURA JSON file from Github at "
                 "https://raw.githubusercontent.com/auracc/aura-toml/main/computed.json")

    r = requests.get("https://raw.githubusercontent.com/auracc/aura-toml/main/computed.json")
    a = r.json()
    with open("resources/aura.json", "w+") as fp:
        fp.truncate(0)  # clear file to reload it
        json.dump(a, fp)
    global AURA_JSON
    AURA_JSON = load_aura_json()


def reconstruct_path(node: RailNode):
    """Reconstructs the KANI pathway from the destinations given, after A* algorithm is called.
     Only calculates KANI pathways."""
    path = []
    if node.station:
        path.append(node.name + ":exit")
    path.append(node.name)
    tot_dist = 0

    while node.parent is not None:
        tot_dist += (euclid(node, node.parent) + taxi(node, node.parent)) / 2
        if node.name in node.parent.badlinks.keys():
            path.append(node.parent.badlinks.get(node.name))
        else:
            path.append(node.name)
        node = node.parent

    path.append(node.name)

    new_path = []
    for i in path:
        a = i.split(" ")
        for j in reversed(a):
            new_path.append(j)
    path = new_path

    lookup = set()
    path = [x for x in path if x not in lookup and lookup.add(x) is None]

    return path[::-1], tot_dist  # need to reverse path


def reconstruct_aura_path(node: AuraNode):
    """Reconstructs the AURA pathway from the destinations given, after A* algorithm is called.
    Only calculates AURA pathways, as more things are involved."""
    path = []
    tot_dist = 0

    if node.type == "junctionstop":
        path.append(node.dest_stop)
    if node.dest == "":
        path.append(node.name)
    else:
        path.append(node.dest)

    print(path)

    last_node = None
    first_node = node

    while node.parent is not None:
        print(node, node.parent)
        tot_dist += (euclid(node, node.parent) + taxi(node, node.parent)) / 2

        if node.type == "line":
            start_index = node.links.index(node.parent.name)
            end_index = node.links.index(last_node.name)

            # Reverse for path
            if start_index < end_index:
                path.append(node.dest_b)
            else:
                path.append(node.dest_a)

        # Skip if node didn't use the junction
        elif node.type == "stopjunction" and first_node != node:
            path.append(node.dest_junction)
            path.append(node.dest)
        elif node.type == "crossing":
            pass  # no additional dests added
        elif node.name in node.parent.badlinks.keys():
            path.append(node.parent.badlinks[node.name])
        else:
            path.append(node.dest)

        last_node = node  # in case for lines
        node = node.parent

    # Special case when the first stop needs to access a line to get on the system
    if last_node.type == "line":
        path.append(node.link_dests.get(last_node.name, ""))

    lookup = set()
    path = [x for x in path if x not in lookup and lookup.add(x) is None]
    return path[::-1], tot_dist


def find_kani_route(start: str, end: str):
    """Entry point for KANI pathfinding, given a start and end will return the path."""
    start_node = kani_node(start)
    end_node = kani_node(end)
    if start_node is None or end_node is None:
        start_alias = find_alias(start)
        if len(start_alias) != 1:
            return [], 0
        start_node = kani_node(start_alias.pop())

    if end_node is None:
        end_alias = find_alias(end)
        if len(end_alias) != 1:
            return [], 0
        end_node = kani_node(end_alias.pop())

    print(start_node, end_node)
    return astar(start_node, end_node)


def find_aura_route(start: str, end: str):
    """Entry point for AURA pathfinding, given a start and end string it will return the path."""
    start_node = aura_node(start)
    end_node = aura_node(end)

    if start_node is None or end_node is None:
        return [], 0

    incorrect_types = ["switch", "crossing", "junction", "line"]
    if start_node.type in incorrect_types or end_node.type in incorrect_types:
        return [], -1  # not a valid pair

    return astar(start_node, end_node, aura_routing=True)


# Adapted from pseudocode at https://en.wikipedia.org/wiki/A*_search_algorithm#Pseudocode
def astar(start_node: RailNode, end_node: RailNode, aura_routing=False):
    """Implementation of A* pathfinding algorithm to pathfind routes between two nodes.
       This has the added benefit of being able to calculate destinations for AURA and KANI when necessary."""
    if start_node == end_node:
        return [], -2

    # TODO: Is there are need for node objects anymore?
    # Priority queue implemented as the heapdict package; this particular package allows us to change priorities.

    # This stores f & g scores for us so it's not in the nodes.
    open_list = {start_node.name: {"node": start_node, "f": euclid(start_node, end_node), "g": 0}}
    closed_list = {}

    def edgeLen(start: RailNode, end: RailNode):
        return (taxi(start, end) + euclid(start, end)) / 2

    def find_next_node():
        return min(open_list, key=lambda k: open_list[k]["f"])

    def get_node(name, current_node):
        if aura_routing:
            a = aura_node(name)
            if a.type == "line":
                a.x, a.z = current_node.x, current_node.z
            return a
        return kani_node(name)

    while not len(open_list) == 0:
        current_name = find_next_node()
        current = open_list.pop(current_name)
        closed_list.update({current_name: current})
        current_node, f, g = current["node"], current["f"], current["g"]

        # If we've reached our destination no need to continue
        if current_node == end_node:
            if type(current_node) == AuraNode:
                return reconstruct_aura_path(current_node)
            return reconstruct_path(current_node)

        # Can't leave node, only applicable as destination
        if current_node.stop and current_node != start_node:
            continue

        for link in current_node.links:
            if link in closed_list:  # This is a literal copout so AURA can work correctly
                continue
            if link in open_list:
                link_node = open_list[link]["node"]
                link_g = open_list[link]["g"]
            else:
                link_node = get_node(link, current_node)
                link_g = -1

            tentative_gscore = g + edgeLen(current_node, link_node)
            if link_g == -1 or tentative_gscore < link_g:
                link_node.parent = current_node
                new_dict = {"node": link_node,
                 "f": tentative_gscore + euclid(link_node, end_node),
                 "g": tentative_gscore}
                open_list.update({link: new_dict})

    return [], 0


def get_aliases():
    """Gets aliases for all KANI destinations. Run as a coroutine in get_kani_json, saves to KANI_ALIASES"""
    alias_dict = {}
    for key in KANI_JSON.keys():
        alias_dict[key] = key
        for alias in KANI_JSON[key].get("aliases", []):
            alias_dict[alias] = key
    return alias_dict


def kani_node(s: str):
    """Helper function to return a KANI type node from a string, if the string matches."""
    try:
        return RailNode(s, KANI_JSON[s])
    except KeyError:
        return None


def aura_node(s: str):
    """Helper function to return an AURA type node from a string, if the string matches."""
    nodes = AURA_JSON.get("nodes")
    find_node = nodes.get(s)
    if find_node is not None:
        return AuraNode(s, AURA_JSON["nodes"][s])
    valid_keys = []
    for d in nodes.keys():
        if s.lower() in [name.lower() for name in nodes.get(d).get("name", [])]:
            valid_keys.append(d)
            break

    if len(valid_keys) != 0:
        return AuraNode(valid_keys[0], AURA_JSON["nodes"][valid_keys[0]])
    return None


def find_alias(dest: str):
    """Finds dest names close to a string. Checks for substring matching, and uses aliases."""
    dest_list = set()
    for key in KANI_ALIASES:
        d = KANI_ALIASES[key]
        if dest in key and d not in dest_list:
            dest_list.add(d)

    return dest_list


def names_close_to(dest: str):
    """Finds names close to a string based on difflib."""
    close_matches = difflib.get_close_matches(dest, KANI_ALIASES.keys())
    return set([KANI_ALIASES[key] for key in close_matches])


def get_advisories(dest_list: List[str]):
    """Given a dest_list, return a list of advisories from the KANI JSON."""
    advisories = []
    for s in dest_list:
        try:
            advisories.append(KANI_JSON[s]["advisory"])
        except KeyError:
            continue
    return advisories


def kani_formatting(path, dist):
    """Formats KANI paths into readable format, succeeds RailUtils.dest functionality for KANI."""

    kani_notices = get_advisories(path)
    last = path[-1]
    if "exit" in last:
        last = path[-2]

    if kani_node(path[0]).switch:
        kani_notices.append("You are routing from a switch.")
    if kani_node(last).switch:
        kani_notices.append("You are routing to a switch. You may need to disembark manually by entering /dest.")

    notices = "".join([f"\n> -{i}" for i in kani_notices])
    route = "/dest " + " ".join(path)
    time = int(dist) // 8
    min, sec = int(time // 60), int(time % 60)
    if notices != "":
        notices = "**KANI Notice(s)**: " + notices
    return "{0} \n\n Travel Time: about {1}min {2}sec \n Distance: {3}m \n\n {4}"\
        .format(route, min, sec, int(dist), notices)


def aura_formatting(path, dist):
    """""Formats KANI paths into readable format, succeeds RailUtils.dest functionality for KANI."""

    # Junction routing
    if len(path) < 0:
        return "*No route found. You are routing to/from a switch/destination/line in AURA.*"

    elif len(path) > 0:
        aura_notices = []
        orig = aura_node(path[0])
        dest = aura_node(path[-1])
        valid_stops = ["stop", "junctionstop", "stopjunction"]

        # Surface check
        if orig.name + "-surface" in AURA_JSON["nodes"]:
            aura_notices += "AURA Notice: Your origin has a surface station that you may want to check for better " \
                            "routes. Add '(surface)' to your origin input."
        if dest.name + "-surface" in AURA_JSON["nodes"]:
            aura_notices += "AURA Notice: Your destination has a surface station that you may want to check for " \
                            "better routes. Add '(surface)' to your destination input."

        # Non-valid stop
        if dest.type not in valid_stops:
            aura_notices += "AURA Notice: You are not routing to a stop."

        notices = "".join([f"\n> -{i}" for i in aura_notices])
        route = "/dest " + " ".join(path)
        time = int(dist) // 8
        min, sec = int(time // 60), int(time % 60)

        if notices != "":
            notices = "**AURA Notice(s)**: " + notices
        return "{0} \n\n Travel Time: about {1}min {2}sec \n Distance: {3}m \n\n {4}" \
            .format(route, min, sec, int(dist), notices)

AURA_JSON = load_aura_json()
KANI_JSON = load_kani_json()
KANI_ALIASES = get_aliases()
