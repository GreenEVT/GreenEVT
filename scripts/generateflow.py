"""
This script generates flows files required for routing.

Depends on:
- database

Generates:
- Flows files (required for routing, e.g. duarouter)
"""

import os
import sys
from typing import List
from xml.etree import ElementTree as ET
import sqlite3
import logging

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import sumolib

# BEGIN PARAMETERS

# END PARAMETERS

l = logging.getLogger("Flow Generator")


def generate_flow(
    db_conn: sqlite3.Connection,
    tazs: List,
    scenario_id: int,
    dst_path: str,
    evac_edge: str,
    region_name: str,
):
    """
    Function generates the flow xml file used for routing. Flow files specify which vehicle departs when,
    from where, to where. It does not contain the route that it will take to reach its desitnation. The flow
    files can be used by programs like SUMO duarouter to create route files which can be interpreted by SUMO
    simulator.

    :param db_conn: database connection.
    :param tazs: tazs to evacuate. Leave empty if all tazs are to be evacuated.
    :param scenario_id: id of the current scenario
    :param dst_path: destination file directory path.
    :param evac_edge: target destination evacution point, in form of a sumo edge.
    :param region_name: name of this project/simulation.
    """

    l.info("Generating vehicle flows...")
    dst_path = f"{dst_path}/sumo_generated/flows/"

    try:
        os.makedirs(f"{dst_path}")
    except FileExistsError:
        l.warning("Directories already exist. Continuing with file generation...")
    except Exception as e:
        l.error(f"Can't create directory. {e}")
        raise

    conn = db_conn
    c = conn.cursor()
    if len(tazs) == 0:
        taz_str = "WHERE taz > 0 "
    else:
        taz_str = "WHERE taz IN ("
        for taz in tazs:
            taz_str = taz_str + " '" + taz + "',"
        taz_str = taz_str[:-1] + ") "

    routes = ET.Element("routes")

    for row in c.execute(
        "SELECT vehicle_id, sumo_edge, ev, departure FROM vehicles " + taz_str + "AND scenario_id=? ORDER BY departure", (scenario_id,)
    ):
        (i, sumo_edge, ev, departure) = row
        flow = ET.SubElement(routes, "flow")
        flow.set("begin", str(departure))
        flow.set("number", "1")
        flow.set("id", str(i))
        flow.set("color", "0,1,0" if ev == 1 else "0.2,0.2,1")
        flow.set("to", evac_edge)
        flow.set("from", str(sumo_edge))
        flow.set("end", str(departure + 1))

    tree = ET.ElementTree(routes)
    dst_path += f"{region_name}.flows.xml"
    tree.write(dst_path)
    l.info("Done.")


if __name__ == "__main__":
    # Node that everyone should evacuate to.
    conn = sqlite3.connect("../data/UDS.db")
    evac_edge = "120108286#1"
    # TAZs to evacuate, empty list means no tazs (taz = []), e.g. taz = ['11101001', '12707001']. This example coveres the urban area of Greensboro, NC.
    tazs = [
        "10100001",
        "10200001",
        "10300001",
        "10401001",
        "10404001",
    ]
    # Scenario id
    scenario_id = 2 
    # where to put the output file
    current_dir = os.path.dirname(__file__)
    generate_flow(
        db_conn=conn,
        tazs=tazs,
        scenario_id=scenario_id,
        dst_path=current_dir,
        evac_edge=evac_edge,
        region_name="greensboro",
    )

#  List of all TAZs ['10100001', '10200001', '10300001', '10401001', '10403001', '10404001', '10500001', '10601001', '10602001', '10701001', '10702001', '10800001', '10900001', '11000001', '11101001', '11102001', '11200001', '11300001', '11400001', '11500001', '11601001', '11602001', '11904001', '11905001', '12503001', '12504001', '12505001', '12505002', '12508001', '12509001', '12510001', '12511001', '12511002', '12601001', '12601002', '12604001', '12607001', '12608001', '12609001', '12609002', '12610001', '12611001', '12612001', '12617001', '12703001', '12704001', '12705001', '12706001', '12707001', '12803001', '12803002', '12803003', '12803004', '12804001', '12805001', '15100001', '15300002', '15300004', '15300006', '15401001', '15402005', '15500001', '15600006', '15703001', '15704001', '15705001', '15705002', '15706001', '15707001', '15800004', '16003002', '16005001', '16006001', '16006002', '16007001', '16007002', '16009001', '16009002', '16010001', '16011001', '16101001', '16101002', '16102001', '16103001', '16306001', '16405001', '16405002', '16405003', '16406001', '16407001', '16408001', '16409001', '16409002', '16502001', '16503001', '16503002', '16505001', '16506001', '16506002', '16702006', '16800001', '17100003', '17100004', '17200003', '17200004', '98010001']
