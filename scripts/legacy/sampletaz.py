import os
import sys
import sqlite3

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci


# Configuration
sumoBinary = (
    "/storage/home/hcoda1/9/nnilsson3/sumo-1.7.0/bin/sumo"  # Path to sumo simulator
)
configFile = sys.argv[1]  # "greensboroTAZ15705002.sumocfg"  # The configuration
# Maximum simulation time (NB: the max time in the configuration file does not matter anymore)
maxTime = 48 * 60 * 60
taz = sys.argv[2]  # The taz of interest
cleanInterval = 60  # How often vehicles outside the TAZ should be removed


# End configuration
sumoCmd = [sumoBinary, "-c", configFile]

# Get the edges in the TAZ
conn = sqlite3.connect("../../../data/UDS.db")
c = conn.cursor()

edges = []

for row in c.execute(
    "SELECT sumoedge, length  FROM sumoedgetaz WHERE taz = "
    + str(taz)
    + " OR from_taz = "
    + str(taz)
):
    edges.append(row[0])


conn.close()

# Start the simulation

traci.start(sumoCmd)

step = 0
while step < maxTime and traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    step += 1

    if step % cleanInterval == 0:
        # Remove vehicles outside the TAZ
        for vehicle in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(vehicle)
            if edge not in edges:
                traci.vehicle.remove(vehicle)


traci.close()
