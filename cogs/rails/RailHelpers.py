from cogs.rails.RailTraverse import KANI_JSON
from math import dist, pi, atan2
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
    closest = [{"name": dest, "distance": distances[dest],
                "x": KANI_JSON.get(dest)["x"],
                "z": KANI_JSON.get(dest)["z"],
                "angle": atan2(KANI_JSON.get(dest)["z"] - z, KANI_JSON.get(dest)["x"] - x) / pi * 180,
                "links": len(KANI_JSON.get(dest).get("links"))} for dest in closest]
    # Note calculation comes later!

    return closest


def names_close_to(dest: str):
    return difflib.get_close_matches(dest, KANI_JSON.keys())
