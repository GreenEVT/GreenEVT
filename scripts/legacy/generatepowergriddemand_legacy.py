"""
This script generates power grid simulator that will be parsed and used in openDSS

Depends on:
- database

Parameters:
- Passed in:
    - WIP
- Hardcoded:
    - WIP

Generates:
- WIP
"""


import sqlite3
import csv
import numpy as np

# Output file
output_file = "output.csv"

# Scenario ["static", "base", "medium", "high"]
scenario = "high"

# Static only: The probability that a random vehicle is electric
prob_ev = 0.4

# Non-static: base in [2020, 2028]; medium, high in [2020, 2050]
year = 2050


# End of parameters


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


probs = {}
if scenario != "static":
    for row in c.execute(
        "SELECT taz, fractionevs FROM scenarios WHERE prediction =? AND year=?",
        (scenario, year),
    ):
        probs[row[0]] = float(row[1])


output_data = [
    [
        "id",
        "joint_count",
        "target_fid",
        "bus",
        "long",
        "lat",
        "feeder",
        "substation",
        "active_load",
        "reactive_load",
        "taz",
        "sumo_edge",
        "type",
        "numevs",
    ]
]


sum_evs = 0

for row in c.execute(
    "SELECT * FROM  buses a LEFT JOIN (SELECT bus_id, sum(vehicles_count) AS tot_veh FROM simplified_parcels WHERE bus_id > 0 GROUP BY bus_id) b ON b.bus_id = a.id "
):
    # All the bus data
    temp_data = list(row[:-2])

    # Check if we have vehicles at the bus
    if row[-1]:
        num_of_vehicles = row[-1]
    else:
        num_of_vehicles = 0

    # Decide the number of vehicles that should be EVs
    if scenario == "static":
        num_of_evs = np.random.binomial(num_of_vehicles, prob_ev)
    else:
        taz = row[10]
        if taz in probs:
            num_of_evs = np.random.binomial(num_of_vehicles, probs[taz])
        else:
            num_of_evs = np.random.binomial(num_of_vehicles, 0)

    sum_evs += num_of_evs
    temp_data.append(num_of_evs)
    output_data.append(temp_data)

# Save the CSV file
with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(output_data)

conn.close()

print("Total number of EVs: ", sum_evs)
