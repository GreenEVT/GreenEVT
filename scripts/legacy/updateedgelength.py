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


net = sumolib.net.readNet("../sumo/greensboro.net.xml")
print("Network loaded....puh")


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


updates = []
for row in c.execute("SELECT sumoedge FROM sumoedgetaz WHERE length = 0 LIMIT 30000"):
    updates.append((net.getEdge(str(row[0])).getLength(), row[0]))


c.executemany("UPDATE sumoedgetaz SET length = ? WHERE sumoedge = ?", updates)


conn.commit()

conn.close()
