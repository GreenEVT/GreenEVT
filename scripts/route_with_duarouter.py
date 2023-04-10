"""
This module wraps the duarouter command in a subprocess so that its output can be captured by the logger.
"""


import logging
import os
from subprocess import Popen, PIPE, STDOUT

l = logging.getLogger("duarouter")


def log_subprocess_output(pipe):
    global l
    for line in iter(pipe.readline, b""):  # b'\n'-separated lines
        l.info(line)


def route_with_duarouter(dst_path: str, region_name: str):
    l.info("Starting a process to run duarouter...")
    try:
        os.makedirs(f"{dst_path}/sumo_generated/routes")
    except FileExistsError as e:
        l.warning("File already exists.")
    process = Popen(
        f"duarouter"
        f" --route-files={dst_path}/sumo_generated/flows/{region_name}.flows.xml"
        f" --net={dst_path}/sumo_network/{region_name}.net.xml"
        f" --output-file={dst_path}/sumo_generated/routes/{region_name}.rou.xml"
        f" --repair=true"
        f" --remove-loops=true",
        f" --ignore-errors=true",
        stdout=PIPE,
        stderr=STDOUT,
        shell=True,
    )
    with process.stdout:
        log_subprocess_output(process.stdout)
    exitcode = process.wait()  # 0 means successprocess.
    if exitcode != 0:
        l.error(f"duarouter subprocess exited with non-0 exit code {exitcode}")
    return
