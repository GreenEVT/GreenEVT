"""
This module wraps the sumo command in a subprocess so that the output of the command
can be captured by the logger.
"""


import logging
from subprocess import Popen, PIPE, STDOUT

l = logging.getLogger("SUMO Simulator")


def log_subprocess_output(pipe):
    global l
    for line in iter(pipe.readline, b""):  # b'\n'-separated lines
        l.info(line)


def simulate_sumo(dst_path: str, region_name: str):
    l.info("Starting a process to run sumo simulations...")
    process = Popen(
        f"sumo {dst_path}/sumo_generated/config/{region_name}.sumocfg",
        stdout=PIPE,
        stderr=STDOUT,
        shell=True,
    )
    with process.stdout:
        log_subprocess_output(process.stdout)
    exitcode = process.wait()  # 0 means successprocess.
    if exitcode != 0:
        l.error(f"SUMO subprocess exited with non-0 exit code {exitcode}")
    l.info("Done.")
    return
