import mysql.connector

conn = mysql.connector.connect(
    host="thomas.proxy.rlwy.net",
    port=57765,
    user="root",
    password="FHohLRKPDraKjBnsDYNDCPXKCiPyihPM",
    database="railway"
)

cursor = conn.cursor()

cursor.execute("SHOW TABLES")

for table in cursor:
    print(table)

conn.close()