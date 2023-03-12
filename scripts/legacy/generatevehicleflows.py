"""
This script generate the flow files that speicifies the starting and end positions of individual vehicles and put them
in an xml file, which is needed for routers (like duarouter program) to route vehicles to their destinations.

Depends on:
- database
    - vehicles table

Parameters:
- Passed in:
    - WIP
- Hardcoded:
    - WIP

Generates:
- Flows files (required for routing, e.g. duarouter)
"""

import os
import sys

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import sumolib
import sqlite3
from xml.etree import ElementTree as ET

# BEGIN PARAMETERS
# Node that everyone should evacuate to.
evac_edge = "120108286#1"

# Size of the evacuation window in seconds

window_sizes = [0, 1, 2, 4, 8]  # 6*(60*60) Specify as a vector

# TAZs to evacuate, empty list means no tazs (taz = []), e.g. taz = ['11101001', '12707001']. This example coveres the urban area of Greensboro, NC.
tazs = [
    "10100001",
    "10200001",
    "10300001",
    "10401001",
    "10404001",
    "10500001",
    "10602001",
    "10701001",
    "10702001",
    "10800001",
    "10900001",
    "11000001",
    "11200001",
    "11300001",
    "11400001",
    "11500001",
]


# This should be one for the main project, must be an integer
vehicle_multipliers = [1, 2, 4, 8]  # Specfy as a vector
# END PARAMETERS


output_file_prefix = "../sumo/flows/citycenter"
conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

updates = []


# generate taz filter string for sqlite query
if limit > 0:
    limit_str = " LIMIT " + str(limit)
else:
    limit_str = ""

if len(tazs) == 0:
    taz_str = "WHERE taz > 0"
else:
    taz_str = "WHERE taz IN ("
    for taz in tazs:
        taz_str = taz_str + " '" + taz + "',"
    taz_str = taz_str[:-1] + ") "


for window_size in window_sizes:
    for vehicle_multiplier in vehicle_multipliers:
        print(
            f"generating flow for scenario: window_size: {window_size} | vehicle_multiplier: {vehicle_multiplier}"
        )
        routes = ET.Element("routes")

        i = 0
        for row in c.execute(
            "SELECT sumo_edge, vehicles_count FROM simplified_parcels "
            + taz_str
            + limit_str
        ):

            for j in range(0, vehicle_multiplier * int(row[1])):
                flow = ET.SubElement(routes, "flow")
                starttime = randint(0, window_size * 60 * 60)
                flow.set("begin", str(starttime))
                flow.set("number", "1")
                flow.set("id", str(i))
                flow.set("color", "0,0,1")
                flow.set("to", evac_edge)
                flow.set("from", str(row[0]))
                flow.set("end", str(starttime + 1))
                i = i + 1

        tree = ET.ElementTree(routes)
        tree.write(
            output_file_prefix
            + "_w"
            + str(window_size)
            + "_m"
            + str(vehicle_multiplier)
            + ".flows.xml"
        )

conn.close()


#  run afterwards
#  duarouter --unsorted-input=true --route-files=demands.flows.xml --net=../sumo/greensboro.net.xml --output-file=greensboro.rou.xml

#  List of all TAZs ['10100001', '10200001', '10300001', '10401001', '10403001', '10404001', '10500001', '10601001', '10602001', '10701001', '10702001', '10800001', '10900001', '11000001', '11101001', '11102001', '11200001', '11300001', '11400001', '11500001', '11601001', '11602001', '11904001', '11905001', '12503001', '12504001', '12505001', '12505002', '12508001', '12509001', '12510001', '12511001', '12511002', '12601001', '12601002', '12604001', '12607001', '12608001', '12609001', '12609002', '12610001', '12611001', '12612001', '12617001', '12703001', '12704001', '12705001', '12706001', '12707001', '12803001', '12803002', '12803003', '12803004', '12804001', '12805001', '15100001', '15300002', '15300004', '15300006', '15401001', '15402005', '15500001', '15600006', '15703001', '15704001', '15705001', '15705002', '15706001', '15707001', '15800004', '16003002', '16005001', '16006001', '16006002', '16007001', '16007002', '16009001', '16009002', '16010001', '16011001', '16101001', '16101002', '16102001', '16103001', '16306001', '16405001', '16405002', '16405003', '16406001', '16407001', '16408001', '16409001', '16409002', '16502001', '16503001', '16503002', '16505001', '16506001', '16506002', '16702006', '16800001', '17100003', '17100004', '17200003', '17200004', '98010001']
