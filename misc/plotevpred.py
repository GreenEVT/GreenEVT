import sqlite3
import numpy as np
import matplotlib.pyplot as plt



database_path = "../data/UDS.db"
conn = sqlite3.connect(database_path)

cursor = conn.cursor()

f = open("high.dat", "w")
mat  = np.array([])

for year in range(2020, 2051):
	yl = []
	count = 0
	cursor.execute("SELECT year, taz, fractionevs FROM ev_estimates WHERE prediction = 'high' AND year = ? ORDER BY taz", [year])
	records = cursor.fetchall()
	for row in records:
		f.write(str(row[0]) + "\t" + str(count) + "\t" + str(row[2]) + "\n")
		count += 1
	f.write("\n")

f.close()
