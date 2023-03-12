import sqlite3


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

res = c.execute("SELECT name from sqlite_master where type='table'")
print([name for name in res])

res = c.execute(
    "SELECT sumo_edge, COUNT(vehicle_id) FROM vehicles GROUP BY sumo_edge LIMIT 5"
)

print([r for r in res])


conn.close()
