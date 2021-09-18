from ..CivMap import find_containing_poly
from .RailTraverse import get_advisories, KANI_JSON, KANI_ALIASES, kani_node, AURA_JSON, aura_node
from math import dist, atan2, degrees
import difflib


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


def find_alias(dest: str):
    """Finds dest names close to a string. Checks for substring matching and difflib close to matching."""
    dest_list = set()
    for key in KANI_ALIASES:
        d = KANI_ALIASES[key]
        if dest in key and d not in dest_list:
            dest_list.add(d)

    return dest_list


def names_close_to(dest: str):
    close_matches = difflib.get_close_matches(dest, KANI_ALIASES.keys())
    return set([KANI_ALIASES[key] for key in close_matches])


def handle_not_found(orig: set, dest: set):
    out = ""
    if len(orig) == 0:
        out += "**Error**: We couldn't find an origin station with that name!\n"
    else:
        out += "**Error**: Did you mean *{0}* for your origin?\n".format("*, *".join([d for d in orig]))
    if len(dest) == 0:
        out += "**Error**: We couldn't find a destination station with that name!\n"
    else:
        out += "**Error**: Did you mean *{0}* for your destination?\n".format("*, *".join([d for d in dest]))
    return out


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
