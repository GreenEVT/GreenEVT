"""
This script generates sumoconfigs that links all different files used in a sumo simulation together (routes, network, output logs, etc.)

Depends on:
- Nothing

Generates:
- sumocfg files (main config files passed in to sumo command to run simulation)
- add.xml files 
"""
import os
import logging


def sumoconfig_template(vars):
    temp = """<?xml version="1.0" encoding="UTF-8"?>

<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">

    <input>
        <net-file value="../../sumo_network/%(region_name)s.net.xml"/>
        <additional-files value="../../sumo_network/%(region_name)s.poly.xml,%(addfile)s"/>
        <route-files value="%(routingfile)s"/>
    </input>

    <output>
    	<summary value="%(stateoutputfile)s" /> <!-- Logs the state of the network at every timestep -->
    </output>

    <processing>
        <ignore-route-errors value="true"/>
    </processing>

    <report>
        <verbose value="true"/>
        <duration-log.statistics value="true"/>
        <no-step-log value="true"/>
    </report>

    <time>
         <time-to-teleport value="%(timetoteleport)s" />
	     <end value="%(maxtime)s" /> <!-- End time for the simulation, choose it so the simulation terminates properly, 86400 s = 24 hours -->
    </time>

</configuration>
	"""
    return temp % vars


def add_template(vars):
    temp = """<additional>
        <edgeData id="%(id)s" file="%(outputedge)s" excludeEmpty="true" freq="%(freq)s" />
</additional>"""
    return temp % vars


l = logging.getLogger("SUMO Config Generator")


def generate_sumocfg(dst_path: str, region_name: str):
    """
    Function generates the sumo configuration files needed to run SUMO simulation.
    Note that at the moment (2/16/2022) all the file paths (routes, network files) are hard-coded. Parameterized version coming in future.

    :param dst_path: path to put generated files into
    :param region_name: name of this simulation / region.
    """

    l.info("Generating sumo configs...")

    if type(dst_path) is not str:
        raise TypeError("dst_path must be a string")
    if len(dst_path) <= 0:
        raise ValueError("dst_path length must be > 0")

    dst_path = f"{dst_path}/sumo_generated"

    try:
        os.makedirs(dst_path)
        os.makedirs(f"{dst_path}/config")
        os.makedirs(f"{dst_path}/output")
    except FileExistsError:
        l.warning("Directories already exist. Continuing with file generation...")
    except Exception as e:
        l.error(f"Can't create directory. {e}")
        raise

    demandfile = f"../routes/{region_name}.rou.xml"
    outputstate = f"../output/{region_name}.log.xml"
    outputedge = f"../output/{region_name}_edge.log.xml"
    addfile = f"{region_name}.add.xml"
    configfile = f"{dst_path}/config/{region_name}.sumocfg"
    timetoteleport = "-1"
    maxtime = "86400"
    samplingfreq = "300"

    subs = {
        "addfile": addfile,
        "routingfile": demandfile,
        "stateoutputfile": outputstate,
        "timetoteleport": timetoteleport,
        "maxtime": maxtime,
        "region_name": region_name,
    }
    with open(configfile, "w") as f:
        f.write((sumoconfig_template(subs)))
        f.close()
    subs = {
        "id": region_name,
        "outputedge": outputedge,
        "freq": samplingfreq,
    }
    with open(f"{dst_path}/config/{addfile}", "w") as f:
        f.write((add_template(subs)))
        f.close()

    l.info("Done.")


if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    path_prefix = f"{current_dir}/../data/sumo_generated"
    generate_sumocfg(dst_path=path_prefix, region_name="greensboro")
