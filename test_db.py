import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host="thomas.proxy.rlwy.net",
        port=57765,
        user="root",
        password="FHohLRKPDraKjBnsDYNDCPXKCiPyihPM",
        database="railway"
    )

try:
    conn = get_db_connection()
    print("✅ Connection Successful!")
    conn.close()
except Exception as e:
    print("❌ Connection Failed:")
    print(e)