"""
This module is an interactive CLI to configure and run simulation. 
"""

from __future__ import unicode_literals
import sqlite3
import logging
from venv import create

import multitasking

from scripts.generatesumocfg import generate_sumocfg
from scripts.generatevehicles_lottery_based import create_vehicles
from scripts.generateflow import generate_flow
from scripts.solve_opendss import iteratively_solve_opendss
from scripts.simulate_sumo import simulate_sumo
from scripts.assign_charging_times_to_vehicles import assign_by_taz
from scripts.copy_files import (
    copy_evacuation_schedule_csv,
    copy_power_grid_files,
    copy_sumo_network_files,
)
from scripts.route_with_duarouter import route_with_duarouter


from time import time

"""
PARAMETERS
"""
database_path = "data/UDS.db"
working_dir = "./test"
region_name = "greensboro"

load_per_charging_ev = 7.5


evac_edge = "120108286#1"
tazs_to_evacuate = ["10404001"]
random_seed = 2022


"""
END OF PARAMETERS 
"""


# setup logging utilities
l = logging.getLogger("Simulator")
loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
fmt = logging.Formatter("%(asctime)s - [%(name)s]:  %(message)s")
# hdl = logging.StreamHandler(sys.stdout)
hdl = logging.FileHandler("output_multithreaded.log")
hdl.setFormatter(fmt)
for _l in loggers:
    _l.setLevel(logging.DEBUG)
    _l.addHandler(hdl)


multitasking.set_max_threads(8)
multitasking.set_engine("thread")  # "process" or "thread".


# a custom workflow.
for penetration in range(0, 90, 5):
    l.info(f"Running simulation for penetration rate {penetration}%...")

    @multitasking.task
    def workflow(penetration: int):
        conn = sqlite3.connect(database_path)
        path = working_dir + f"_penetration_{penetration}_threaded"

        generate_sumocfg(dst_path=path, region_name=region_name)

        copy_sumo_network_files(dst_path=path)
        copy_evacuation_schedule_csv(dst_path=path)
        copy_power_grid_files(dst_path=path)

        # multithreaded version requires special handling on the db side since it will be locked
        # create_vehicles(db_conn=conn, random_seed=random_seed)
        # assign_by_taz(dst_path=path, db_conn=conn)

        generate_flow(
            db_conn=conn,
            tazs=tazs_to_evacuate,
            dst_path=path,
            penetration=penetration,  # note that this number will change for each iteration.
            evac_edge=evac_edge,
            region_name=region_name,
        )
        route_with_duarouter(dst_path=path, region_name=region_name)

        simulate_sumo(dst_path=path, region_name=region_name)
        iteratively_solve_opendss(
            dst_path=path,
            db_conn=conn,
            step_size=5,
            penetration_constant=penetration,
            load_per_charging_ev=load_per_charging_ev,
        )
        conn.close()

    proc = workflow(penetration=penetration)
