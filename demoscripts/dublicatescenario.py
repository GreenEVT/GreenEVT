# Helper function to find TAZ from coordinate


import sqlite3
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt
from shapely.geometry import Point



conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


input_scenario_name = "small_demo_medium_2040_allatonce"

output_scenarion_name = "small_demo_medium_2040_2hours"

c.execute("SELECT id, year, level, fixed_penetration_rate FROM scenarios WHERE name = ?" ,(input_scenario_name,))

row = c.fetchone()

old_id = row[0]

c.execute("INSERT INTO scenarios(name, year, level, fixed_penetration_rate) VALUES (?,?,?,?)", (output_scenarion_name, row[1], row[2], row[3]))

new_id = c.lastrowid 


print(old_id)
c_insert = conn.cursor()
for row in c.execute("SELECT sumo_edge, taz, bus_name, ev, charging_start, charging_end, departure FROM vehicles WHERE scenario_id =? ", (old_id,)):
	c_insert.execute("INSERT INTO vehicles(sumo_edge, taz, bus_name, ev, charging_start, charging_end, departure, scenario_id) VALUES(?,?,?,?,?,?,?,?)", (row[0], row[1], row[2], row[3], row[4], row[5], row[6], new_id))


conn.commit()
conn.close()