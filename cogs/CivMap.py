import json
import requests
import logging
import re
from shapely.geometry import Point, Polygon
from discord.ext import tasks
from math import dist, atan2, degrees
from operator import itemgetter


@tasks.loop(hours=3)
async def get_settlements():
    """Task function, which runs ~3hrs to get CivMap settlement/claims jsons from the CCMap repository"""
    logging.info("Grabbing CivMap data files from GitHub at "
                 "https://raw.githubusercontent.com/ccmap/data/master/")
    r = requests.get("https://raw.githubusercontent.com/ccmap/data/master/settlements.civmap.json")
    s = requests.get("https://raw.githubusercontent.com/ccmap/data/master/land_claims.civmap.json")
    settlements_json = r.json().get("features")
    claims_json = s.json().get("features")
    with open("resources/claims.json", "w+") as fp:
        fp.truncate(0)
        json.dump(claims_json, fp)
    with open("resources/settlements.json", "w+") as fp:
        fp.truncate(0)  # clear file to reload it
        json.dump(settlements_json, fp)
    global settlements, claims
    settlements = load_settlements()
    claims = load_claims()


def load_settlements():
    """Helper function to load settlements from the json (after loading it)"""
    with open("resources/settlements.json", "r") as fp:
        return json.load(fp)


# Unlike all the other load functions, this transforms the list of features into a json with all polygons.
def load_claims():
    """Helper function to load claims from the json (and also load the polygons correctly)"""
    claims = []
    with open("resources/claims.json", "r") as fp:
        claims_json = json.load(fp)
    for claim in claims_json:
        polygons = claim.get("polygon")
        p = [Polygon(poly) for poly in polygons]
        claims.append({"name": claim.get("name"), "claim": p})
    return claims


settlements = load_settlements()
claims = load_claims()  # structure: [{name: str, claim: polygon}]


def find_closest(x: int, z: int):
    """Finds the closest ten settlements from a given location."""
    # TODO: Ensure there is at least one major settlement in the return statement!
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

        nation = sett.get("nation", "")
        nation = re.sub(pattern="\,.*$", repl="", string=nation)
        distance = distances[sett.get('name')]

        angle = degrees(atan2(sett["z"] - z, sett["x"] - x)) + 90
        angle = angle if angle >= 0 else angle + 360
        x, z = sett["x"], sett["z"]

        directions = ["N", "NNW", "NW", "WNW", "W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE",
                      "E", "ENE", "NE", "NNE", "N"]

        direc = int(angle // 22.5)
        major = True if sett.get("Zoom Visibility") <= 2 else False
        info = {"name": sett.get('name'), "distance": distance,
                "direction": directions[direc], "major": major, "x": x, "z": z, "nation": nation}
        closest_settlements.append(info)

    return closest_settlements


# CivMap, while not completely susceptible to overlapping claims,
# is generally pretty good about maintaining claims polygons.
def find_containing_poly(x: int, z: int):
    """This function finds whether the polygon contains a point given in here."""
    global claims
    for c in claims:
        polys = c.get("claim")
        point = Point(x, z)
        for poly in polys:
            if poly.contains(point):
                return c.get("name")
    return ""


# TODO for next release: /civmap [name] to get a structure and basic info (if it exists)


