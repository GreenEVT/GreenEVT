import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import sqlite3

import matplotlib.pyplot as plt


input_file = "../sumo/netstateTAZ15705002.log.xml"

tree = ET.parse(input_file)

root = tree.getroot()

groupby = 30  # Average window


taz = "15705002"

# Find edges

conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

edges = []

for row in c.execute("SELECT sumoedge  FROM sumoedgetaz WHERE taz = " + taz):
    edges.append(row[0])


conn.close()


time = 0
vehicles = []
speed = 0.0
speed_samples = 0

plot_data = []
for timestep in root.findall("./timestep"):

    if time % groupby == 0:
        if speed_samples > 0:
            plot_data.append((len(vehicles), speed / speed_samples * len(vehicles)))
        else:
            plot_data.append((len(vehicles), 0))
        vehicles = []
        speed = 0.0
        speed_samples = 0

    for edge in timestep:
        if edge.attrib["id"] in edges:
            for lane in edge:
                for vehicle in lane:
                    vehicle_id = int(float(vehicle.attrib["id"]))
                    if vehicle_id not in vehicles:
                        vehicles.append(vehicle_id)
                    speed += float(vehicle.attrib["speed"])
                    speed_samples += 1

    time += 1

plt.scatter(*zip(*plot_data))
plt.title("MFD for TAZ" + taz)
plt.xlabel("Number of vehicles in TAZ")
plt.ylabel("Avarge vehicle flow [veh*m/s]")
plt.show()
