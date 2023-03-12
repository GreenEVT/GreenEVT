import sqlite3
from matplotlib import pyplot as plt
import numpy as np


conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()

res = c.execute("SELECT name from sqlite_master where type='table'")
print([name for name in res])


res = c.execute(
    """SELECT SUM(b.reactive_load) as total_load, COUNT(*) as count, a.ev_threshold FROM
                (SELECT sumo_edge, ev_threshold FROM vehicles) a
                LEFT JOIN
                (SELECT sumo_edge, reactive_load FROM buses) b
                ON a.sumo_edge = b.sumo_edge
                GROUP BY a.ev_threshold
                """
)

data = np.array([r for r in res])
print(data)

for i in range(1, data.shape[0]):
    data[i] += data[i - 1]

data[:, 0] /= data[:, 1]

conn.close()
plt.plot((data[:, 0]))
plt.show()
