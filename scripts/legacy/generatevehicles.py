"""
This script generates vehicles and their possibility threshold of becoming an EV. 

How it works:
    When the script is run, the table "simpliefied_parcels" from the database is pulled 
    and the information of how many vehicles is in each parcel is collected. Then
    vehicles are generated and assigned to each parcel according to the number specified.
    Then a number from 0 - 100 is assigned to the vehicle to threshold whether it's
    an EV or not. This is later used in generatepowergriddemand.py. For example, if
    the generation script specifies 60% of vehicles should be EV, then all vehicles 
    with a threshold <60 will be marked as EV.

Depends on:
- database
    - simplified_parcel table that contains parcels and vehicles per parcel data.

Parameters:
- Passed in:
    - WIP
- Hardcoded:
    - WIP

Generates:
- Vehicles table in database.
"""

import sqlite3
import random

# BEGIN PARAMETERS

# To ensure that the scenarios are reproducable, use seeded random
random.seed(2022)

# END PARAMETERS


conn = sqlite3.connect("../data/UDS.db")

# create a cursor for querying
c = conn.cursor()
# create a separate cursor for insertion.
c_insert = conn.cursor()

# clean up old data and recreate tables
c.execute("DROP TABLE IF EXISTS vehicles")
c.execute(
    """CREATE TABLE vehicles (
    vehicle_id BIGINT PRIMARY KEY,
    sumo_edge STRING,
    taz INTEGER,
    ev_threshold INTEGER
    )"""
)

# create a cache for vehicles to be inserted to be used in batch insertion
# in the form of 4-tuples (vehicle_id, sumo_edge, taz, ev_threshold)
vehicles_to_be_inserted = []

i = 0

# for display purpose only.
vehicles_grand_total = [
    r[0]
    for r in c.execute(
        "SELECT SUM(vehicles_count) FROM simplified_parcels WHERE taz > 0"
    )
][0]


print("Generating vehicles in the database...")

for parcel in c.execute(
    f"SELECT sumo_edge, vehicles_count, taz FROM simplified_parcels WHERE vehicles_count > 0 AND taz > 0"
):
    # extract the vehicle count in this parcel
    sumo_edge, vehicle_count, taz = parcel
    for vehicle in range(vehicle_count):
        # create a uniform distributed random as EV threshold
        EV_threshold = random.randint(0, 100)
        vehicles_to_be_inserted.append((i, sumo_edge, taz, EV_threshold))
        i += 1

    # update by the batch of size 5000 to boost performance and reduce memory load
    if len(vehicles_to_be_inserted) > 5000:
        print(f"progress: {i} / {vehicles_grand_total}")
        c_insert.executemany(
            ("INSERT INTO vehicles VALUES (?, ?, ?, ?)"), vehicles_to_be_inserted
        )
        vehicles_to_be_inserted.clear()

c_insert.executemany(
    ("INSERT INTO vehicles VALUES (?, ?, ?, ?)"), vehicles_to_be_inserted
)
vehicles_to_be_inserted.clear()
print(f"progress: {i} / {vehicles_grand_total}")


conn.commit()
conn.close()
