# This script plots the area of interest by joining the TAZs

import sqlite3
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


taz = []
tazid = []
for row in c.execute("SELECT GEOMETRY, tractce FROM censustracts"):
    taz.append(shapely.wkb.loads(row[0]))
    tazid.append((str(row[1]), shapely.wkb.loads(row[0])))

cu = shapely.ops.cascaded_union(taz)

updates = []
for row in c.execute(
    "SELECT ogc_fid, GEOMETRY FROM parcels WHERE censustract = -1 LIMIT 50000"
):
    point = shapely.wkb.loads(row[1])
    tid = "0"
    if point.within(cu):
        for (id, t) in tazid:
            if point.within(t):
                tid = str(id)
                break
    updates.append((tid, row[0]))


c.executemany("UPDATE parcels SET censustract=? WHERE ogc_fid=?", updates)
conn.commit()

conn.close()
