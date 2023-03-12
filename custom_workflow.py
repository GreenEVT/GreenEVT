"""
This module is an interactive CLI to configure and run simulation. 
"""

from __future__ import unicode_literals
from random import random
import sqlite3
import logging

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
hdl = logging.FileHandler("output.log")
hdl.setFormatter(fmt)
for _l in loggers:
    _l.setLevel(logging.DEBUG)
    _l.addHandler(hdl)


# setup database connection and path var
conn = sqlite3.connect(database_path)

# this only needs to run once.
# create_vehicles(db_conn=conn, random_seed=random_seed)

# a custom workflow.
for penetration in range(0, 90, 5):
    l.info(f"Running simulation for penetration rate {penetration}%...")

    path = working_dir + f"_penetration_{penetration}"

    generate_sumocfg(dst_path=path, region_name=region_name)

    copy_sumo_network_files(dst_path=path)
    copy_power_grid_files(dst_path=path)

    # if we want to create a new profile for each run, uncomment these few lines.
    # create_vehicles(db_conn=conn, random_seed=random_seed)
    # copy_evacuation_schedule_csv(dst_path=path) # this file is required for the assign_by_taz function call, otherwise it can be omitted
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
