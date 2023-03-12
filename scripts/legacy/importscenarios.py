import sqlite3
import csv
import numpy as np

# Output file
output_file = "output.csv"

# The probability that a random vehicle is electric
prob_ev = 0.5

conn = sqlite3.connect("../data/UDS.db")
c = conn.cursor()


with open("highdata.csv", mode="r", encoding="utf-8-sig") as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            for year in range(2020, 2051):
                taz = row["TAZ"]
                fracvehicle = round(0.01 * (float(row[str(year)])), 4)
                c.execute(
                    "INSERT INTO scenarios (taz, prediction, year, fractionevs) VALUES (?, 'high', ?, ?)",
                    (
                        taz,
                        year,
                        fracvehicle,
                    ),
                )

            line_count += 1
    print(f"Processed {line_count} lines.")

conn.commit()
conn.close()
