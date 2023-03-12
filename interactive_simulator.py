"""
This module is an interactive CLI to configure and run simulation.
"""

from __future__ import unicode_literals
from pprint import pformat as pf
import os
import shutil
import sqlite3
import logging
import sys

from PyInquirer import style_from_dict, Token, prompt, Separator

from scripts.generatesumocfg import generate_sumocfg
from scripts.generatevehicles import create_vehicles
from scripts.generateflow import generate_flow
from scripts.solve_opendss import iteratively_solve_opendss
from scripts.simulate_sumo import simulate_sumo
from scripts.assign_charging_times_to_vehicles import assign_randomly
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
region_name = "greensboro"
scenario_name = "small_demo_high_2040_2hours"
working_dir = "./output/" + scenario_name

year_prediction = 2040
prediction_level = "medium" # base, medium, high
ev_penetration_rate = -1 # -1 use prediction data, [0, 1] fixed penetration rate
load_per_charging_ev = 7.2


charging_time = 8*60 #I n minutes
departure_window = 2*3600 # In seconds 


evac_edge = "120108286#1"

# Empty list if we want to evacuate all TAZs
tazs_to_evacuate = ["10701001", "10702001", "10800001", "10900001", "11000001", "11200001"]
#tazs_to_evacuate = []
random_seed = 2022

"""
END OF PARAMETERS
"""


# Ask questions

style = style_from_dict(
    {
        Token.Separator: "#5467cc",
        Token.QuestionMark: "#673ab7 bold",
        Token.Selected: "#54cc54",  # default
        Token.Pointer: "#673ab7 bold",
        Token.Instruction: "",  # default
        Token.Answer: "#f44336 bold",
        Token.Question: "",
    }
)

questions = [
    {
        "type": "list",
        "message": "select mode for the simulator",
        "name": "meta",
        "choices": [{"name": "Print to terminal"}, {"name": "Output to log file"}],
    },
    {
        "type": "checkbox",
        "message": "Configure the simulation (default config is provided)",
        "name": "config",
        "choices": [
            Separator("Copying Over Necessary Files"),
            {"name": "Copy Over Network Files", "checked": True},
            {"name": "Copy Over Evacuation Schedule File", "checked": True},
            {"name": "Copy Over Powergrid Files", "checked": True},

            Separator("Traffic Simulation Config"),
            {"name": "Generate Sumo Configurations", "checked": True},
            {"name": "Generate Vehicles", "checked": False},
            {"name": "Assign Charging and Depature Times to Vehicles", "checked": False},
            {"name": "Generate Flow", "checked": True},
            {"name": "Generate Routes", "checked": True},
            Separator("Run Simulations"),
            {"name": "Run SUMO traffic simulation", "checked": True},
            {"name": "Run OpenDSS power grid simulation", "checked": True},
        ],
        "validate": lambda answer: "You must choose at least one action."
        if len(answer) == 0
        else True,
    },
]


# collect answers
answers = prompt(questions, style=style)
meta = answers["meta"]
config = answers["config"]


# setup logging utilities
l = logging.getLogger("Simulator")
loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
fmt = logging.Formatter("%(asctime)s - [%(name)s]:  %(message)s")
if "Print to terminal" in meta:
    hdl = logging.StreamHandler(sys.stdout)
elif "Output to log file" in meta:
    hdl = logging.FileHandler("output.log")
else:
    raise Exception("You must select an output mode.")
hdl.setFormatter(fmt)
for _l in loggers:
    _l.setLevel(logging.DEBUG)
    _l.addHandler(hdl)

l.debug(f"workflow is: {pf(config)}")

# setup database connection and path var
conn = sqlite3.connect(database_path)
path = working_dir

# follow the workflow.
if "Generate Sumo Configurations" in config:
    generate_sumocfg(dst_path=path, region_name=region_name)

if "Generate Vehicles" in config:
    create_vehicles(db_conn=conn, scenario_name=scenario_name, year_prediction=year_prediction, level_predition=prediction_level, ev_penetration_rate=ev_penetration_rate, random_seed=random_seed, tazs=tazs_to_evacuate)

# Get the scenario id from the databse
c = conn.cursor()
c.execute("SELECT id FROM scenarios WHERE name = ?", (scenario_name,))
scenario_id=c.fetchone()[0]

if "Generate Flow" in config:
    generate_flow(
        db_conn=conn,
        tazs=tazs_to_evacuate,
        dst_path=path,
        scenario_id=scenario_id,
        evac_edge=evac_edge,
        region_name=region_name,
    )

if "Copy Over Network Files" in config:
    copy_sumo_network_files(dst_path=path)

if "Copy Over Evacuation Schedule File" in config:
    copy_evacuation_schedule_csv(dst_path=path)

if "Copy Over Powergrid Files" in config:
    copy_power_grid_files(dst_path=path)

if "Assign Charging and Depature Times to Vehicles" in config:
    assign_randomly(db_conn=conn, scenario_id=scenario_id, window=departure_window, charging_time=charging_time)

if "Generate Routes" in config:
    if "Generate Flow" not in config:
        l.warn("Flow files are not updated.")
    route_with_duarouter(dst_path=path, region_name=region_name)

if "Run SUMO traffic simulation" in config:
    if "Generate Routes" not in config:
        l.warn("Route files are not updated.")
    simulate_sumo(dst_path=path, region_name=region_name)

if "Run OpenDSS power grid simulation" in config:
    iteratively_solve_opendss(
        dst_path=path,
        db_conn=conn,
        step_size=5,
        scenario_id=scenario_id,
        load_per_charging_ev=load_per_charging_ev,
        export_option="Overloads"
    )

conn.close()
