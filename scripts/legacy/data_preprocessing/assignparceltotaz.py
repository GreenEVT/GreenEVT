# This script plots the area of interest by joining the TAZs

import sqlite3
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


taz = []
tazid = []
for row in c.execute("SELECT GEOMETRY, tazce10 FROM taz "):
    taz.append(shapely.wkb.loads(row[0]))
    tazid.append((row[1], shapely.wkb.loads(row[0])))

cu = shapely.ops.cascaded_union(taz)

updates = []
for row in c.execute("SELECT ogc_fid, GEOMETRY FROM parcels WHERE taz =-1 LIMIT 100"):
    point = shapely.wkb.loads(row[1])
    tid = 0
    if point.within(cu):
        for (id, t) in tazid:
            if point.within(t):
                tid = int(id)
                break
    updates.append((tid, row[0]))

c.executemany("UPDATE parcels SET taz=? WHERE ogc_fid=?", updates)
conn.commit()

conn.close()
