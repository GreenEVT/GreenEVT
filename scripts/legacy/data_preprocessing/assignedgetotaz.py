# This script assign each edge to a TAZ

import os, sys

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import sumolib
import pyproj
import sqlite3
import shapely.geometry
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt


net = sumolib.net.readNet("../sumo/greensboro.net.xml")
print("Network loaded....puh")


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


taz = []
tazid = []
for row in c.execute("SELECT GEOMETRY, tazce10 FROM taz "):
    taz.append(shapely.wkb.loads(row[0]))
    tazid.append((row[1], shapely.wkb.loads(row[0])))

cu = shapely.ops.cascaded_union(taz)

updates = []
count = 0
for edge in net.getEdges():
    edgeid = edge.getID()
    x, y = edge.getFromNode().getCoord()
    # 	x,y = edge.getToNode().getCoord()
    lon, lat = net.convertXY2LonLat(x, y)

    # Find the corresponding edge
    point = shapely.geometry.Point(lon, lat)
    tid = 0
    if point.within(cu):
        for (id, t) in tazid:
            if point.within(t):
                tid = int(id)
                count = +1
                break
    updates.append((tid, edgeid))


c.executemany("UPDATE sumoedgetaz SET from_taz = ? WHERE sumoedge =?", updates)


print(count)
conn.commit()

conn.close()
