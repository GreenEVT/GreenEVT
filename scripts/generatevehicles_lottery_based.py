"""
This script generates vehicles and their possibility threshold of becoming an EV. 

How it works:
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


def create_vehicles(db_conn: sqlite3.Connection, random_seed: int):
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

    # clean up old data and recreate tables
    c.execute("DROP TABLE IF EXISTS vehicles")
    c.execute(
        """CREATE TABLE vehicles (
        vehicle_id BIGINT PRIMARY KEY,
        sumo_edge STRING,
        taz INTEGER,
        bus_name STRING,
        ev_threshold INTEGER,
        charging_start INTEGER,
        charging_end INTEGER,
        departure INTEGER
        )"""
    )

    # create a cache for vehicles to be inserted to be used in batch insertion
    # in the form of 4-tuples (vehicle_id, sumo_edge, taz, ev_threshold)
    vehicles_to_be_inserted = []

    # ev id
    i = 0
    number_of_intervals = 100

    # find the total number of vehicles in residential areas (filtered through active_load being between 0 to 10mW)
    total_residentail_vehicles = [
        r
        for r in c.execute(
            """
        SELECT SUM(b.vehicles)
        FROM (SELECT sumo_edge, active_load FROM buses WHERE active_load > 0 AND active_load < 10) a
        JOIN (SELECT SUM(vehicles) as vehicles, sumo_edge FROM simple_parcels GROUP BY sumo_edge) b
        ON a.sumo_edge = b.sumo_edge
    """
        )
    ][0][0]

    # create a composite query where we correspond the number of vehicles in a bus and the active loads on the bus
    load_and_vehicles_by_bus = np.array(
        [
            r
            for r in c.execute(
                """
                    SELECT a.sumo_edge, a.active_load, b.vehicles, b.taz, a.bus
                    FROM (SELECT active_load, sumo_edge, bus FROM buses WHERE active_load > 0 AND active_load < 10) a
                    JOIN (SELECT sumo_edge, SUM(vehicles) as vehicles, taz FROM simple_parcels WHERE vehicles > 0 GROUP BY sumo_edge) b
                    ON a.sumo_edge = b.sumo_edge
                """
            )
        ]
    )

    # use the active load at each sumo_edge, compute the weighted probability to assign new EVs.
    # Note that because the number of EVs assigned to the edge will not exceed the vehicle count of the area,
    # we're assigning low thresholds (meaning they're more likely to be EV's in all scenarios) to high active load
    # The rationale is for residential areas with high consumption the residents are more likely to be more wealthy,
    # and hence a higher probability of EV penetration. Low thresholds fill in the high probability areas first, hence
    # creating an overall distribution where low thresholds tend to reside in higher power areas.

    # Here we're squaring the powers to make distribution more distinguishable
    load_and_vehicles_by_bus[:, 1] = np.power(
        load_and_vehicles_by_bus[:, 1].astype("float"), 2
    )
    # normalize
    load_and_vehicles_by_bus[:, 1] = load_and_vehicles_by_bus[:, 1].astype(
        "float"
    ) / np.sum(load_and_vehicles_by_bus[:, 1].astype("float"))

    EV_id = 0
    # Threshold (0-100) is used to decide whether each individual vehicle is EV or not in any scenario in a deterministic,
    # incremental manner. To filter EVs at 20% penetration rate, simply filter EVs with thresholds less than 20.
    threshold = 0
    vehicles_to_be_inserted = []

    while EV_id < total_residentail_vehicles:

        # Equally divide the 100 thresholds.
        if EV_id > (threshold / number_of_intervals) * total_residentail_vehicles:
            threshold += 1

        # Based on the distribution, pick a lottery
        bus_ndx = np.random.choice(
            load_and_vehicles_by_bus.shape[0],
            p=load_and_vehicles_by_bus[:, 1].astype("float"),
        )

        # Create this vehicle
        bus_to_assign_next_EV = load_and_vehicles_by_bus[bus_ndx]
        (
            sumo_edge,
            _prob,
            remaining_EVs_to_assign,
            taz,
            bus_name,
        ) = bus_to_assign_next_EV
        # the last values are: default start_charging time, default end_charging time, and departure time.
        vehicles_to_be_inserted.append(
            (EV_id, sumo_edge, taz, bus_name, threshold, -480, 0, 0)
        )

        # Decrement the number of vehicles remaining at the edge
        load_and_vehicles_by_bus[bus_ndx][2] = (
            load_and_vehicles_by_bus[bus_ndx][2].astype("int") - 1
        )

        # Batch update to boost performance.
        if len(vehicles_to_be_inserted) > 1000:
            l.info(f"progress: {EV_id} / {total_residentail_vehicles}")
            c_insert.executemany(
                ("INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?, ?)"),
                vehicles_to_be_inserted,
            )
            vehicles_to_be_inserted.clear()

        # If all vehicles at an edge are assigned a threshold, take this edge out.
        # Note: there's probably more optimal ways to do this...
        if int(remaining_EVs_to_assign) <= 0:
            load_and_vehicles_by_bus = np.delete(load_and_vehicles_by_bus, bus_ndx, 0)
            # recompute the distribution function.
            load_and_vehicles_by_bus[:, 1] = load_and_vehicles_by_bus[:, 1].astype(
                "float"
            ) / np.sum(load_and_vehicles_by_bus[:, 1].astype("float"))
        EV_id += 1

    # Commit the remaining batch
    c_insert.executemany(
        ("INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?, ?)"),
        vehicles_to_be_inserted,
    )
    conn.commit()

    l.info("Done.")


if __name__ == "__main__":
    random_seed = 2022
    conn = sqlite3.connect("../data/UDS.db")
    create_vehicles(random_seed=random_seed, db_conn=conn)
