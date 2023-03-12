import os
import shutil
from pprint import pprint as pp

for dirpath, dirs, files in os.walk("./"):
    if "Loads_0.dss" in files:
        pp(dirpath)
        src = f"{dirpath}/Loads_0.dss"
        dst = f"{dirpath}/Loads_original.dss"
        shutil.copy(src, dst)
