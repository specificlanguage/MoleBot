import json
import requests
import logging
from discord.ext import tasks
from math import dist, atan2, pi
from operator import itemgetter


@tasks.loop(hours=3)
async def get_settlements():
    logging.info("Grabbing CivMap settlements file from GitHub at "
                 "https://raw.githubusercontent.com/ccmap/data/master/settlements.civmap.json")
    r = requests.get("https://raw.githubusercontent.com/ccmap/data/master/settlements.civmap.json")
    settlements_json = r.json()
    settlements_json = settlements_json.get("features")
    with open("resources/settlements.json", "w+") as fp:
        fp.truncate(0)  # clear file to reload it
        json.dump(settlements_json, fp)
    global settlements
    settlements = load_settlements()
    logging.info("Finished grabbing CivMap settlements!")


def load_settlements():
    with open("resources/settlements.json", "r") as fp:
        return json.load(fp)


settlements = load_settlements()


def find_closest(x: int, z: int):
    distances = {}
    for entry in settlements:
        name = entry.get("name")
        if '?' not in name and name[0] != '(':
            distance = dist([x, z], [entry["x"], entry["z"]])
            distances[name] = distance

    closest = list({k: v for k, v in sorted(distances.items(), key=lambda item: item[1])})[:10]
    closest_settlements = []

    for i in range(10):
        index = list(map(itemgetter('name'), settlements)).index(list(closest)[i])
        sett = settlements[index]

        distance = distances[sett.get('name')]

        angle = atan2(sett["z"] - z, sett["x"] - x) / pi * 180
        angle = angle if angle >= 0 else angle + 360
        x, z = sett["x"], sett["z"]

        directions = ["N", "NNW", "NW", "WNW", "W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE",
                      "E", "ENE", "NE", "NNE", "N"]

        direc = int(angle // 22.5)
        major = True if sett.get("Zoom Visibility") <= 2 else False
        info = {"name": sett.get('name'), "distance": distance,
                "direction": directions[direc], "major": major, "x": x, "z": z}
        closest_settlements.append(info)

    return closest_settlements

# TODO for next release: ensure there is at least one major settlement in the list
# TODO for next release: /civmap [name] to get a structure and basic info (if it exists)


