import redshift_connector
from dotenv import load_dotenv
import os

REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
REDSHIFT_DB = os.getenv("REDSHIFT_DB")
REDSHIFT_USER = os.getenv("REDSHIFT_USER")
REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")

def connect_to_redshift():
    conn = redshift_connector.connect(
        host=REDSHIFT_HOST,
        port=5439,
        database=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD,
        timeout=120,
    )
    return conn


conn = connect_to_redshift()
print(conn)
conn.close()