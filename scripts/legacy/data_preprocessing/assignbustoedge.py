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
from xml.etree import ElementTree as ET

net = sumolib.net.readNet("../sumo/greensboro.net.xml")
print("Network loaded....puh")
radius = 10

conn = sqlite3.connect("../data/UDS.db")

c = conn.cursor()

updates = []


for row in c.execute("SELECT id, long, lat FROM buses WHERE sumo_edge =0 LIMIT 1000"):
    print(row)
    x, y = net.convertLonLat2XY(row[1], row[2])
    edges = net.getNeighboringEdges(x, y, radius)
    if len(edges) > 0:
        # This sort key function is needed, since sometims two edges are exactly on the same distance
        distancesAndEdges = sorted(
            [(dist, edge) for edge, dist in edges], key=lambda item: item[0]
        )
        dist, closestEdge = distancesAndEdges[0]
        updates.append((closestEdge.getID(), row[0]))
    else:
        print("No edge found")


c.executemany("UPDATE buses SET sumo_edge=? WHERE id=?", updates)
conn.commit()

conn.close()
