"""
This script generates vehicles and their possibility threshold of becoming an EV. 

How it works:

    UPDATE
    When the script is run, the view "simplified_parcels" from the database is pulled 
    and the information of how many vehicles is in each parcel is collected. Then
    vehicles are generated and assigned to each parcel according to the number specified.
    Then a number from 0 - 100 is assigned to the vehicle to threshold whether it's
    an EV or not. This is later used in generatepowergriddemand.py. For example, if
    the generation script specifies 60% of vehicles should be EV, then all vehicles 
    with a threshold <60 will be marked as EV.

Depends on:
- database
    - simplified_parcel view that contains parcels and vehicles per parcel data.

Generates:
- Vehicles table in database.
"""

import sqlite3
import logging
import numpy as np


l = logging.getLogger("Vehicle Generator")


def create_vehicles(db_conn: sqlite3.Connection, scenario_name: str, year_prediction: int, level_predition: str, ev_penetration_rate: int, random_seed: int, tazs: list):
    """
    Function creates the Vehicles table in the database with properly assigned
    buses, tazs, sumo_edge and properly allocated EV_threshold based on lottery.

    It also gives vehicles default charging start and end times, as well as a
    departure time. If non-default behavior is expected, use other scripts to
    modify these fields after the vehicles are generated. (For example, run
    "assign_charging_times_to_vehicles" after running this script.)

    :param random_seed: the random seed to guarantee reproducability under same params.
    """

    l.info("Generating vehicles in the database...")

    # use the given seed for reproduce-ability
    np.random.seed(random_seed)

    # create db connection and cursors
    conn = db_conn
    # create a cursor for querying
    c = conn.cursor()
    # create a separate cursor for insertion.
    c_insert = conn.cursor()

    c.execute("SELECT id FROM scenarios WHERE name = ?", (scenario_name,))
    data=c.fetchone()

    scenario_id = 0

    if data is None:
        # We have to add a new scenario
        c.execute("INSERT INTO scenarios(name, year, level, fixed_penetration_rate) VALUES (?,?,?,?)", (scenario_name, year_prediction, level_predition, ev_penetration_rate))
        scenario_id = c.lastrowid
    else:
        # The scenario already is there
        scenario_id = data[0]

    # clean up old generate vehicle data if there is any
    c.execute("DELETE FROM vehicles WHERE scenario_id = ?", (scenario_id, ))



    if len(tazs) > 0:
        # Get all the vehicles in the specificed TAZs
        c.execute("SELECT * FROM simple_parcels WHERE vehicles > 0 AND taz IN (" + ",".join(tazs) + ") ORDER BY taz")
    else:
         # Get all the vehicles 
        c.execute("SELECT * FROM simple_parcels WHERE vehicles > 0 ORDER BY taz") 


    vehicles = c.fetchall()

    last_taz = -1

    ev_prob = ev_penetration_rate
    for vehicle in vehicles:
        if ev_penetration_rate == -1:
            # Check if the TAZ has changed 
            if vehicle[3] != last_taz:
                last_taz = vehicle[2]
                c.execute("SELECT fractionevs FROM ev_estimates WHERE taz = ? AND prediction = ? AND year = ?", (last_taz, level_predition, year_prediction)    )
                ev_prob = c.fetchone()[0]

        bus_id = vehicle[1]
        taz = vehicle[2]
        sumo_edge = vehicle[3]
        num_vehicles = vehicle[4]
        for i in range(num_vehicles):
            ev = 0
            if ev_prob > np.random.rand():
                ev = 1
            c_insert.execute("INSERT INTO vehicles(sumo_edge, taz, bus_name, ev, charging_start, charging_end, departure, scenario_id) VALUES (?,?,?,?,?,?,?,?)", (sumo_edge, taz, bus_id, ev, -480, 0, 0, scenario_id))

    conn.commit()

    l.info("Done.")


if __name__ == "__main__":
    random_seed = 2022
    conn = sqlite3.connect("../data/UDS.db")
    create_vehicles(random_seed=random_seed, scenario_name="medium_2028", year_prediction=2028, level_predition="medium", ev_penetration_rate=-1, db_conn=conn)
