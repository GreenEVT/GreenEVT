"""
This module integrates the following data-preprocessing functionalities into one single module:
- assign each bus in the database to a corresponding edge in the SUMO network
- assign each parcel in the database to its corresponding elecric bus
- assign each parcel in the database to its corresponding SUMO edge
- assign each parcel in the database to its corresponding TAZ.
"""


# Import the sumolib
import os, sys

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import sqlite3
import logging
from xml.etree import ElementTree as ET

import shapely.geometry
import shapely.wkb
import shapely.ops
import matplotlib.pyplot as plt
import sumolib
import pyproj

l = logging.getLogger("Data Preprocessor")


def assign_bus_to_edge(db_conn: sqlite3.Connection, net: sumolib.net.Net):
    """Function updates the bus table and gives each entry its corresponding SUMO edge.

    Args:
        db_conn (sqlite3.Connection): database connection
        net (sumolib.net.Net): sumo network object
    """
    l.info("Assigning buses to edges...")
    radius = 10
    c = db_conn.cursor()
    updates = []
    counter = 0
    res = [
        row for row in c.execute("SELECT id, long, lat FROM buses WHERE sumo_edge = 0")
    ]
    total = len(res)
    l.info(f"updates required: {total}")
    for row in res:
        counter += 1
        if counter % 1000 == 0:
            l.debug(f"progress: {counter} / {total}")
        x, y = net.convertLonLat2XY(row[1], row[2])
        edges = net.getNeighboringEdges(x, y, radius)
        if len(edges) > 0:
            # This sort key function is needed, since sometimes two edges are exactly on the same distance
            distancesAndEdges = sorted(
                [(dist, edge) for edge, dist in edges], key=lambda item: item[0]
            )
            dist, closestEdge = distancesAndEdges[0]
            updates.append((closestEdge.getID(), row[0]))
        else:
            ("No edge found")
    c.executemany("UPDATE buses SET sumo_edge=? WHERE id=?", updates)
    db_conn.commit()
    l.info("done.")


def assign_parcel_to_bus(db_conn: sqlite3.Connection):
    """function assigns parcel to its corresponding bus (by nearest location).

    Args:
        db_conn (sqlite3.Connection): database connection.
    """
    l.info("Assining parcels to buses...")
    # dist = 0.0
    # for i in range(0, len(buses)-1):
    # 	(ida, (loa, lata)) = buses[i]
    # 	shortdist = 10000.0
    # 	for j in range(i+1, len(buses)):
    # 		(idb, (lob, latb)) = buses[j]
    # 		tdist = math.sqrt((loa-lob)**2 + (lata -latb)**2)
    # 		if tdist < shortdist:
    # 			shortdist = tdist
    # 	dist = dist + shortdist
    # 	print(i)
    # print(dist/(len(buses)-1))
    # Result from above: Averge distance 0.0002214569908230549 degrees (Approximetely 80 feet = 24 meter)
    # Result from aboce with only active load: Aveage distance 0.0004327132767485107 degress

    c = db_conn.cursor()
    buses = []
    # For simplicity, let's read in all the buses
    for row in c.execute("SELECT id, long, lat FROM buses WHERE active_load > 0"):
        buses.append((row[0], (row[1], row[2])))

    max_busdistance = 2 * 0.0004327132767485107
    updates = []

    res = [
        row
        for row in c.execute(
            "SELECT ogc_fid, GEOMETRY FROM parcels WHERE taz > 0 AND bus_id == -2"
        )
    ]
    total = len(res)
    l.info(f"updates required: {total}")
    counter = 0
    for parcel in res:
        counter += 1
        if counter % 1000 == 0:
            l.debug(f"progress: {counter} / {total}")
        coord = shapely.wkb.loads(parcel[1])
        (plong, plat) = (coord.x, coord.y)
        min_dist = max_busdistance
        min_busid = -2

        for (busid, (buslong, buslat)) in buses:
            dist = math.sqrt((plong - buslong) ** 2 + (plat - buslat) ** 2)
            if dist < min_dist:
                min_dist = dist
                min_busid = busid
        updates.append((min_busid, parcel[0]))

    c.executemany("UPDATE parcels SET bus_id=? WHERE ogc_fid=?", updates)
    db_conn.commit()
    l.info("done.")


def assign_parcel_to_edge(db_conn: sqlite3.Connection, net: sumolib.net.Net):
    """assigns parcel to a SUMO edge.

    Args:
        db_conn (sqlite3.Connection): database connection.
        net (sumolib.net.Net): SUMO network object.
    """
    l.info("Assigning parcels to edges...")
    radius = 2000
    c = db_conn.cursor()

    updates = []

    res = [
        row
        for row in c.execute(
            'SELECT ogc_fid, GEOMETRY FROM parcels WHERE taz > 0 AND sumo_edge = "-2" '
        )
    ]
    total = len(res)
    l.info(f"updates required: {total}")
    counter = 0
    for parcel in res:
        counter += 1
        if counter % 1000 == 0:
            l.debug(f"progress: {counter} / {total}")
        coord = shapely.wkb.loads(parcel[1])
        x, y = net.convertLonLat2XY(coord.x, coord.y)
        edges = net.getNeighboringEdges(x, y, radius)
        if len(edges) > 0:
            # This sort key function is needed, since sometims two edges are exactly on the same distance
            distancesAndEdges = sorted(
                [(dist, edge) for edge, dist in edges], key=lambda item: item[0]
            )

            ce = None
            for dist, closestEdge in distancesAndEdges:
                t = closestEdge.getType()
                if ("highway" in t) and ("motorway" not in t):
                    ce = closestEdge
                    break
            if ce is not None:
                updates.append((ce.getID(), parcel[0]))
            else:
                print("Only highway edges found")
                updates.append((-2, parcel[0]))

        else:
            print("No edge found")
            updates.append((-2, parcel[0]))

    c.executemany("UPDATE parcels SET sumo_edge=? WHERE ogc_fid=?", updates)
    db_conn.commit()
    l.info("done.")


def assign_parcel_to_taz(db_conn: sqlite3.Connection):
    """function assigns parcel to its corresponding TAZ.

    Args:
        db_conn (sqlite3.Connection): database connection.
    """
    l.info("Assigning parcels to tazs...")
    c = db_conn.cursor()
    taz = []
    tazid = []
    for row in c.execute("SELECT GEOMETRY, tazce10 FROM taz "):
        taz.append(shapely.wkb.loads(row[0]))
        tazid.append((row[1], shapely.wkb.loads(row[0])))
    cu = shapely.ops.unary_union(taz)
    updates = []

    res = [
        row
        for row in c.execute(
            "SELECT ogc_fid, GEOMETRY FROM parcels WHERE taz =-1 LIMIT 100"
        )
    ]
    total = len(res)
    l.info(f"updates required: {total}")
    counter = 0
    for row in res:
        counter += 1
        if counter % 1000 == 0:
            l.debug(f"progress: {counter} / {total}")
        point = shapely.wkb.loads(row[1])
        tid = 0
        if point.within(cu):
            for (id, t) in tazid:
                if point.within(t):
                    tid = int(id)
                    break
        updates.append((tid, row[0]))
    c.executemany("UPDATE parcels SET taz=? WHERE ogc_fid=?", updates)
    db_conn.commit()
    l.info("done.")


if __name__ == "__main__":
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler(sys.stdout))
    current_dir = os.path.dirname(__file__)
    l.info("Loading sumo net...")
    net = sumolib.net.readNet(f"{current_dir}/../data/sumo_network/greensboro.net.xml")
    l.info("Net loaded...")
    with sqlite3.connect("../data/UDS.db") as db_conn:
        assign_bus_to_edge(db_conn, net)
        assign_parcel_to_bus(db_conn)
        assign_parcel_to_edge(db_conn, net)
        assign_parcel_to_taz(db_conn)
