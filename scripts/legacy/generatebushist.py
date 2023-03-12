import sqlite3


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

hist = [0] * 200

for count in c.execute(
    "SELECT count(*) FROM parcels WHERE taz > 0 AND bus_id > 0 GROUP BY bus_id "
):
    hist[count[0]] = hist[count[0]] + 1

conn.close()
print(hist)
