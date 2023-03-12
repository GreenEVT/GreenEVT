"""
This script interfaces Jorge Huerta's evacuation schedule by tazs csv file (generated from his algorithms) and updates the vehicles database, updating the charging start, end time as well as departure time.

In this setup, because evacuation is done taz-by-taz, all vehicles in the same taz will share the same departure time.

We're assuming all vehicles start to charge 8 hours (480 minute) prior to their departure

As of 2/15/2022, the field names are: ('TAZ_ID', 'Evacuation_node', 'Vehicles', 'Evacuated', 'Nonevacuated', 'Evacuated_percentage', 'Distance', 'Elementary', 'Nonpreemptive', 'Departure_rate', 'First_departure_time_hmm', 'Last_departure_time_hmm', 'Traversing_time_mins', 'First_arrival_time_hmm', 'Last_arrival_time_hmm', 'Path')

"""

import logging
import numpy as np
import sqlite3


logger = logging.getLogger("Vehicle Charging Time Assignment")


def assign_by_taz(dst_path: str, scenario_id: int, db_conn: sqlite3.Connection):
    """
    Function reads the evacuation schedule by taz file from the data directory, and
    assign EV's their charging times and departure times based on the taz they belong.
    """
    # load the data.
    data = np.genfromtxt(
        f"{dst_path}/evacuation_schedule_by_taz.csv",
        delimiter=",",
        skip_header=4,
        dtype="str",
        usecols=[0, 10],  # [0] is TAZ id, [10] is departure time in minutes.
    )

    # header
    col_names = data[0]

    conn = db_conn
    c = conn.cursor()

    updates = []
    for row in data[1:]:
        # if departure time data is not valid format (H:MM), skip.
        if ":" not in row[1]:
            continue

        taz = row[0]
        [hours, minutes] = row[1].split(":")
        mins = int(hours) * 60 + int(minutes)
        charging_start = mins - 8 * 60  # assuming 8 hours straight charging time
        charging_end = mins
        updates.append(
            (charging_start, charging_end, charging_end, taz, scenario_id)
        )  # assume departure time is imeediately after charging ends.

    c.executemany(
        "UPDATE vehicles SET charging_start = ?, charging_end = ?, departure = ? WHERE taz = ? AND scenario_id = ?",
        updates,
    )

    conn.commit()


def assign_randomly(db_conn: sqlite3.Connection, scenario_id: int, window: int, charging_time: int):
    # Assigns the departure time randomly within the time window (in seconds) and the charing time in minutes

    c = db_conn.cursor()

    updates = []
    for row in c.execute("SELECT vehicle_id FROM vehicles WHERE scenario_id = ?", (scenario_id,)):
        vehicle_id_int = row[0]
        departure_time = int(window*np.random.random())
        charging_end = int((departure_time*1.0)/60)
        charging_start = charging_end - charging_time
        updates.append((charging_start, charging_end, departure_time, vehicle_id_int))

    logger.debug("Updating the departure_time.")
    c.executemany("UPDATE vehicles SET charging_start = ?, charging_end = ?, departure = ? WHERE vehicle_id = ?", updates)
    db_conn.commit()



def assign_evenly_by_taz(dst_path: str, db_conn: sqlite3.Connection):
    # this is an alternative assignment method where:
    # - taz's release their vehicles one by one, by a 30-minute interval. Sequence is randomly assigned.
    # - all vehicles within the same taz will all be released in the taz's designated time window,
    interval = 30
    cur = db_conn.cursor()

    tazs = [r[0] for r in cur.execute("SELECT DISTINCT taz FROM vehicles")]
    sequence = [i for i in range(len(tazs))]
    np.random.shuffle(sequence)
    logger.debug("Obtaining vehicle profile by taz's...")
    updates = []
    for (ndx, taz) in enumerate(tazs):
        seq_for_this_taz = sequence[ndx]
        vehicles_in_this_taz = [r for r in cur.execute("SELECT vehicle_id FROM vehicles WHERE taz = ?", (taz, ))]
        for vehicle_id in vehicles_in_this_taz:
            vehicle_id_int = vehicle_id[0]
            departure_time = charging_end = int(interval * (seq_for_this_taz + np.random.random()))
            charging_start = int(charging_end - 8 * 60)
            updates.append((charging_start, charging_end, departure_time, vehicle_id_int))


    logger.debug("Done. Now making assignments.")
    cur.executemany("UPDATE vehicles SET charging_start = ?, charging_end = ?, departure = ? WHERE vehicle_id = ?", updates)

    db_conn.commit()
    logger.debug("Done.")



if __name__ == "__main__":
    conn = sqlite3.connect("../data/UDS.db")
    assign_evenly_by_taz("../data", conn)
    # assign_by_taz("../data", conn)
