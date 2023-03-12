# Helper function to find TAZ from coordinate


import sqlite3
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt
from shapely.geometry import Point



conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

tazs = []
for row in c.execute("SELECT GEOMETRY, tazce10 FROM taz"):
    tazs.append((str(row[1]), shapely.wkb.loads(row[0])))


def findtaz(lon, lat):
	p = Point(lon, lat)
	for (id, shape) in tazs:
		if p.within(shape):
			return id



pts_lon = [-79.77083684,
-79.83026013,
-79.79953108,
-79.78807697,
-79.79314022,
-79.85874715,
-79.85041458,
-79.81973503,
-79.89013835,
-79.89699215,
-79.75735862,
-79.76626436,
-79.80162964,
-79.8104378,
-79.82773325,
-79.8946082,
-79.79506945,
-79.83551356,
-79.86308776,
-79.78179079,
-79.86655322,
-79.82643191]

pts_lat = [36.06080749,
36.02822722,
36.10015888,
36.08151595,
36.0717329,
36.03263776,
36.09656135,
36.05084464,
36.10467541,
36.07808588,
36.07971801,
36.10260437,
36.01806969,
36.08650311,
36.07023955,
36.0536334,
36.0535097,
36.11148617,
36.07138671,
36.030756,
36.12656791,
36.13769678]
for i in range(0, len(pts_lon)):
	print(findtaz(pts_lon[i],pts_lat[i]))



conn.close()