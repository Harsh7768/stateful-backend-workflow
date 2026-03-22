import psycopg

def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="workflow_db",
        user="postgres",
        password="1234$"
    )
