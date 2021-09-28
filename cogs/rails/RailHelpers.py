from ..CivMap import find_containing_poly
from .RailTraverse import *
from math import dist, atan2, degrees


def find_closest_dests(x: int, z: int):
    """Finds the closest dest locations given a point. This is near a recreation from CivMap's closest dests
       algorithm, but is slightly modified to also check whether a claim contains that dest."""
    if abs(x) >= 13000 or abs(z) >= 13000:
        return []
    distances = {}
    for dest in KANI_JSON.keys():
        data = KANI_JSON.get(dest)
        if "j:" not in dest[:2]:
            distance = dist([x, z], [data["x"], data["z"]])
            distances[dest] = distance

    closest = list({k: v for k, v in sorted(distances.items(), key=lambda item: item[1])})[:10]
    closest_dests = []

    for dest in closest:
        data = KANI_JSON.get(dest)
        to_dist = distances[dest]
        angle = degrees(atan2(data["z"] - z, data["x"] - x)) + 90
        angle = angle if angle >= 0 else angle + 360
        links = len(data["links"])

        directions = ["N", "NNW", "NW", "WNW", "W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE",
                      "E", "ENE", "NE", "NNE", "N"]
        direction = directions[int(angle // 22.5)]

        containing_nation = find_containing_poly(data["x"], data["z"])

        closest_dests.append({"name": dest, "distance": to_dist, "x": data["x"], "z": data["z"],
                              "angle": angle, "links": links, "direction": direction, "nation": containing_nation})

    return closest_dests


def handle_not_found(orig: set, dest: set):
    """Handling helper command to return strings when an origin/destination is not found!"""
    out = ""
    if len(orig) == 0:
        out += "**Error**: Origin station not found!\n"
    else:
        out += "**Error**: Did you mean *{0}* for your origin?\n".format("*, *".join([d for d in orig]))
    if len(dest) == 0:
        out += "**Error**: Destination station not found!\n"
    else:
        out += "**Error**: Did you mean *{0}* for your destination?\n".format("*, *".join([d for d in dest]))
    return out

