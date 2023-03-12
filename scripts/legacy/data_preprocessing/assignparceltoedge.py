# This script assign each bus in the database to a corresponding edge in the SUMO network


# Import the sumolib
import os, sys

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import sumolib
import sqlite3
import pyproj
import shapely.wkb
import shapely.ops
from xml.etree import ElementTree as ET

# import rtree

net = sumolib.net.readNet("../sumo/greensboro.net.xml")
print("Network loaded....puh")
radius = 2000

conn = sqlite3.connect("../data/UDS.db")

c = conn.cursor()

updates = []

for i in range(1, 2):
    for parcel in c.execute(
        'SELECT ogc_fid, GEOMETRY FROM parcels WHERE taz > 0 AND sumo_edge = "-2" '
    ):
        coord = shapely.wkb.loads(parcel[1])
        x, y = net.convertLonLat2XY(coord.x, coord.y)
        edges = net.getNeighboringEdges(x, y, radius)
        if len(edges) > 0:
            # This sort key function is needed, since sometims two edges are exactly on the same distance
            distancesAndEdges = sorted(
                [(dist, edge) for edge, dist in edges], key=lambda item: item[0]
            )

            ce = None
            for dist, closestEdge in distancesAndEdges:
                t = closestEdge.getType()
                if ("highway" in t) and ("motorway" not in t):
                    ce = closestEdge
                    break
            if ce is not None:
                updates.append((ce.getID(), parcel[0]))
            else:
                print("Only highway edges found")
                updates.append((-2, parcel[0]))

        else:
            print("No edge found")
            updates.append((-2, parcel[0]))

    c.executemany("UPDATE parcels SET sumo_edge=? WHERE ogc_fid=?", updates)
    conn.commit()

conn.close()
