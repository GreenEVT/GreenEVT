import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


input_file = "../sumo/my_output.xml"

tree = ET.parse(input_file)

root = tree.getroot()

# Lists to sotore the output

time_steps = []
inserted = []
arrived = []
teleported = []


for item in root.findall("./step"):
    time_steps.append(int(float(item.attrib["time"])))
    inserted.append(int(item.attrib["inserted"]))
    arrived.append(int(item.attrib["arrived"]))
    teleported.append(int(item.attrib["teleports"]))


plt.plot(time_steps, inserted)
plt.plot(time_steps, arrived)
plt.plot(time_steps, teleported)

plt.ylabel("Vehicles")
plt.xlabel("Time")
plt.legend(["Inserted", "Arrived", "Teleported"])
plt.show()
