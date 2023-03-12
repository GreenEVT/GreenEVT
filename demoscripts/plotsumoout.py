import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


input_file = "../output/small_demo_high_2040_2hours/sumo_generated/output/greensboro.log.xml"

#input_file = "output/citycenter_unoptimized.log.xml"
tree = ET.parse(input_file)

root = tree.getroot()

# Lists to sotore the output

time_steps = []
inserted = []
arrived = []
teleported = []


for item in root.findall('./step'):
    time_steps.append(int(float(item.attrib['time'])))
    inserted.append(int(item.attrib['inserted']))
    arrived.append(int(item.attrib['arrived']))
    teleported.append(int(item.attrib['teleports']))


plt.plot(time_steps, inserted)
plt.plot(time_steps, arrived)

#plt.show()


import tikzplotlib
tikzplotlib.clean_figure()

tikzplotlib.save("output.tikz")

