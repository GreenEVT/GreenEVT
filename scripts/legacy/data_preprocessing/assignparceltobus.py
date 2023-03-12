import sqlite3
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt
import math


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


buses = []


# For simplicity, let's read in all the buses
for row in c.execute("SELECT id, long, lat FROM buses WHERE active_load > 0"):
    buses.append((row[0], (row[1], row[2])))


# Only run the following part of the script if you want to recompute the avarge minum distance between the buses

# dist = 0.0
# for i in range(0, len(buses)-1):
# 	(ida, (loa, lata)) = buses[i]
# 	shortdist = 10000.0
# 	for j in range(i+1, len(buses)):
# 		(idb, (lob, latb)) = buses[j]
# 		tdist = math.sqrt((loa-lob)**2 + (lata -latb)**2)
# 		if tdist < shortdist:
# 			shortdist = tdist
# 	dist = dist + shortdist
# 	print(i)
# print(dist/(len(buses)-1))


# Result from above: Averge distance 0.0002214569908230549 degrees (Approximetely 80 feet = 24 meter)
# Result from aboce with only active load: Aveage distance 0.0004327132767485107 degress

max_busdistance = 2 * 0.0004327132767485107
updates = []

for parcel in c.execute(
    "SELECT ogc_fid, GEOMETRY FROM parcels WHERE taz > 0 AND bus_id == -2 LIMIT 10000"
):
    coord = shapely.wkb.loads(parcel[1])
    (plong, plat) = (coord.x, coord.y)
    min_dist = max_busdistance
    min_busid = -2

    for (busid, (buslong, buslat)) in buses:
        dist = math.sqrt((plong - buslong) ** 2 + (plat - buslat) ** 2)
        if dist < min_dist:
            min_dist = dist
            min_busid = busid

    updates.append((min_busid, parcel[0]))


c.executemany("UPDATE parcels SET bus_id=? WHERE ogc_fid=?", updates)
conn.commit()

conn.close()
