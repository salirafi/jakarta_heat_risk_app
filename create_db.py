"""
To create .db file from two tables.
This is for example.
It is still useful to create .db file from either fetch_bmkg_data_jakarta.py or fetch_region_border_big_data_jakarta.py.
"""
import sqlite3

conn = sqlite3.connect("heat_risk.db")
cursor = conn.cursor()

# list of SQL files and path
files = ["/sql_tables/heat_forecast_jakarta.sql", "/sql_tables/jakarta_kelurahan_boundary.sql"]

for file in files:
    with open(file, "r") as f:
        cursor.executescript(f.read())

conn.commit()
conn.close()
