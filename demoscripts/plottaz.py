# This script plots the TAZ from the database

import sqlite3
import shapely.wkb
import matplotlib.pyplot as plt


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

fig, axs = plt.subplots()
axs.set_aspect("equal", "datalim")

for row in c.execute("SELECT GEOMETRY FROM taz "):
    taz = shapely.wkb.loads(row[0])
    for geom in taz.geoms:
        xs, ys = geom.exterior.xy
        axs.fill(xs, ys, alpha=0.5, fc="r", ec="none")
        axs.plot(xs, ys)

plt.show()
conn.close()
