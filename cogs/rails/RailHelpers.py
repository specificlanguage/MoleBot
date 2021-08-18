from cogs.rails.RailTraverse import KANI_JSON
from math import dist, atan2, degrees
import difflib


def find_closest_dests(x: int, z: int):
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

        closest_dests.append({"name": dest, "distance": to_dist, "x": data["x"], "z": data["z"],
                              "angle": angle, "links": links, "direction": direction})

    return closest_dests


def names_close_to(dest: str):
    return [match for match in difflib.get_close_matches(dest, KANI_JSON.keys()) if "j:" not in match[:2]]
