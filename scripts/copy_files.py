"""
Module provides copying utilities for copying over test files.
"""


import shutil
import logging

l = logging.getLogger("File Copier")


def copy_sumo_network_files(dst_path: str):
    l.info("Copying over SUMO network files...")
    try:
        shutil.copytree("./data/open_dss", f"{dst_path}/open_dss")
    except FileExistsError as e:
        l.warning("File already exists.")
    except Exception as e:
        raise
    l.info("done.\n")


def copy_evacuation_schedule_csv(dst_path: str):
    l.info("Copying over evacuation schedule csv...")
    try:
        shutil.copy("./data/evacuation_schedule_by_taz.csv", f"{dst_path}/")
    except FileExistsError as e:
        l.warning("File already exists.")
    except Exception as e:
        raise
    l.info("done.\n")


def copy_power_grid_files(dst_path: str):
    l.info("Copying over power grid files...")
    try:
        shutil.copytree("./data/sumo_network", f"{dst_path}/sumo_network")
    except FileExistsError as e:
        l.warning("File already exists.")
    except Exception as e:
        raise
    l.info("done.\n")
