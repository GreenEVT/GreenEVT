# This script plots the area of interest by joining the TAZs

import sqlite3
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

fig, axs = plt.subplots()
axs.set_aspect("equal", "datalim")

taz = []
for row in c.execute("SELECT GEOMETRY FROM taz WHERE tazce10 = 10100001 "):
    taz.append(shapely.wkb.loads(row[0]))

cu = shapely.ops.cascaded_union(taz)

for row in c.execute("SELECT GEOMETRY FROM parcels WHERE taz = 10100001  "):
    parcel = shapely.wkb.loads(row[0])
    plt.plot(parcel.x, parcel.y, marker="o", markersize=3, color="red")

plt.plot(*cu.exterior.xy)


plt.show()
conn.close()
