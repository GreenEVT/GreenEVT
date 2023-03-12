"""
This module provides utility to run opendss simulation on the given vehicles profile in the sqlite database
over the entire span of simulation time. 

Depends on:
- Database:
    - Table "Vehicles"
- OpenDSS:
    - Network files with a Master.dss

Generates:
- overloads reports at different timestamps
"""

from typing import Dict
import sqlite3
import os
import shutil
import re
import logging
import sys

import opendssdirect as dss


l = logging.getLogger("OpenDSS Solver")


def query_charging_evs_per_bus_by_time(
    timestamp: int, scenario_id: int, c: sqlite3.Cursor
) -> Dict[str, int]:
    """
    Function queries the database, and construct a dictionary where the key is the name of the bus,
    and the value is the number of EV charging at this particular bus at the specified time (in minutes),
    given the scenario (EV penetration)

    :param timestamp: time, in minutes
    :param scenario_id: the id of the scenario

    :return: a dictionary in form {"bus_name": num_ev}. Example: {"p1ilv1007": 2}
    """
    res = c.execute(
        """
        SELECT COUNT(vehicle_id), bus_name FROM vehicles 
        WHERE charging_start <= ? AND charging_end >= ?
        AND ev == 1
        AND scenario_id=?
        GROUP BY bus_name
        """,
        (timestamp, timestamp,scenario_id),
    )

    return {r[1]: r[0] for r in res}


def iteratively_solve_opendss(
    dst_path: str,
    db_conn: sqlite3.Connection,
    step_size: int,
    scenario_id: int,
    load_per_charging_ev: float,
    export_option='Overloads'
):
    """
    Function pulls the database for EV information in order to update the opendss network loads.
    It then solves the circuit and compile reports iteratively with a specified time step size,
    and putting the results as files under the opendss directory.

    :param dst_path: working directory path.
    :param db_conn: database connection.
    :param step_size: how big the time step size should be.
    :param penetration_constant: penetration rate (0-100).
    :param load_per_charging_ev: load in kW per charging EV.
    """

    l.info("Running OpenDSS simulations...")
    conn = db_conn
    c = conn.cursor()

    work_dir = f"{dst_path}/open_dss"

    if len([r for r in os.walk(work_dir)]) == 0:
        raise FileNotFoundError(f"Directory [{work_dir}] is empty or doesn't exist")

    r = dss.run_command(f"Set Datapath = {work_dir}")

    res = c.execute(
        """SELECT MIN(charging_start), MAX(charging_end) FROM vehicles
                    WHERE scenario_id = ?
                    """,
        (scenario_id,),
    )

    times = [r for r in res][0]

    if len(times) <= 0 or None in times:
        l.warn("no electric vehicle is found in this scenario.")
        return
    (start_time, end_time) = times

    timestamp = start_time
    interval_max = int((end_time - start_time) / step_size)

    last_evs_by_bus = {}
    for interval_ndx in range(interval_max):
        evs_by_bus = query_charging_evs_per_bus_by_time(
            timestamp, scenario_id=scenario_id, c=c
        )

        l.info(
            f"timestamp: {timestamp} | iteration {interval_ndx + 1} out of {interval_max}"
        )
        # if the charging profile hasn't changed, move on.
        if evs_by_bus == last_evs_by_bus:
            l.debug(
                "profile is identical to last timestamp. exporting cached results..."
            )
        else:
            # Modify Electricity load in DSS load files to reflect EV charging.
            # We do this by iterating through load files, and for each bus we will
            # use our dictionary that we constructed, and add appropriate load to the kW field,
            # and create a new copy of the load file on the fly. (The original load file is untouched)
            for dirpath, dirs, files in os.walk(f"{work_dir}"):
                if "Loads_original.dss" in files:

                    # src is the original no-ev file. We read from this file and write
                    # to dst file where the EV load is added.
                    src_path = f"{dirpath}/Loads_original.dss"
                    working_copy_path = f"{dirpath}/Loads.dss"
                    with open(src_path, "r") as src:
                        with open(working_copy_path, "w") as dst:
                            for line in src.readlines():
                                # Use Regex to find the bus pattern
                                bus_name_pattern = re.compile("bus1=[\w]+.")
                                match = bus_name_pattern.findall(line)
                                if len(match) > 0:
                                    # Extract the bus name by getting rid of the things
                                    # before (including) "=" as well as the trailing "."
                                    bus_name = match[0].split("=")[1][:-1]

                                    # If this is in our dictionary, add to the kW field.
                                    if bus_name in evs_by_bus:

                                        # Use Regex to find the load pattern
                                        load_pattern = re.compile("kW=[0-9.]+")
                                        match = load_pattern.findall(line)[0]

                                        # Extract load and multiply that by number of ev charging
                                        # at this bus to get the updated load
                                        load_with_no_ev = float(match.split("=")[1])
                                        num_ev_charging = evs_by_bus[bus_name]
                                        load_with_ev_charging = (
                                            load_with_no_ev
                                            + num_ev_charging * load_per_charging_ev
                                        )

                                        # replace the original load part of the string
                                        replace_str = f"kW={load_with_ev_charging}"
                                        line_updated = line.replace(match, replace_str)
                                        dst.write(line_updated)
                                    else:
                                        # If no ev is charging here, write the original load.
                                        dst.write(line)
                                else:
                                    # If it's an empty line, write the original line.
                                    dst.write(line)

            dss.run_command(f"compile Master.dss")
            dss.run_command("Solve")


        dss.run_command(f"Export {export_option} {export_option}_{timestamp}.csv")
        timestamp += step_size
        last_evs_by_bus = evs_by_bus
    l.info("Done.")


if __name__ == "__main__":
    scenario_id = 2  
    load_per_charging_ev = 7.5
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler(sys.stdout))
    iteratively_solve_opendss(
        dst_path="../test",
        db_conn=sqlite3.connect("../data/UDS.db"),
        step_size=5,
        scenario_id=scenario_id,
        load_per_charging_ev=load_per_charging_ev,
    )
